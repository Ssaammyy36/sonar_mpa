try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    
import numpy as np
from typing import List, Optional, Any, Dict
from data_types import Measurement, EchogramMeasurement
from logger import get_logger
from .base import AbstractSonarModel

if TORCH_AVAILABLE:
    class SimpleLSTM(nn.Module):
        # Definition needs to match the saved one!
        def __init__(self, input_size=1, hidden_size=32, num_layers=1, num_classes=3):
            super(SimpleLSTM, self).__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, num_classes)
            
        def forward(self, x):
            # Initialize hidden state with zeros
            h0 = torch.zeros(1, x.size(0), 32).to(x.device) 
            c0 = torch.zeros(1, x.size(0), 32).to(x.device)
            out, _ = self.lstm(x, (h0, c0))
            out = self.fc(out[:, -1, :])
            return out
else:
    class SimpleLSTM: pass

class LSTMSonarModel(AbstractSonarModel):
    def __init__(self, settings: Dict[str, Any] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = settings or {}
        self.model = None
        self.device = torch.device('cpu') if TORCH_AVAILABLE else None
        self.labels = {}
        self.seq_len = 300 # Default from training script

        self.mean = 0.0
        self.std = 1.0

    def load(self, model_path: str):
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch ist nicht installiert. LSTM Modell kann nicht geladen werden.")
            return

        try:
            # Load checkpoint
            checkpoint = torch.load(model_path, map_location=self.device)
            # Load metadata
            self.seq_len = checkpoint.get("input_len", 300)
            self.labels = checkpoint.get("labels", {})
            self.mean = checkpoint.get("mean", 0.0)
            self.std = checkpoint.get("std", 1.0)
            
            # Reconstruct model architecture
            self.model = SimpleLSTM(input_size=1, hidden_size=32, num_classes=3) 
            self.model.load_state_dict(checkpoint["model_state"])
            self.model.eval()
            
            self.logger.info(f"LSTM Modell geladen (SeqLen={self.seq_len}, Mean={self.mean:.2f}, Std={self.std:.2f})")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des LSTM: {e}")

    def predict(self, data_low: List[Measurement], data_high: List[Measurement]) -> Optional[str]:
        if not TORCH_AVAILABLE or not self.model:
            return None
            
        # Example Logic: Concatenate Low + High raw data and feed to LSTM
        # Or just use High Frequency data if that's what was trained on.
        # For this demo, let's use High Frequency.
        
        if not data_high or not isinstance(data_high[0], EchogramMeasurement):
            return None
            
        raw_signal = data_high[0].data_points
        
        # Preprocessing: Pad or Truncate to seq_len
        processed_sig = self._preprocess(raw_signal, self.seq_len)
        
        # Normalize
        if self.std > 1e-6:
             processed_sig = (processed_sig - self.mean) / self.std

        # To Tensor: (Batch, Seq, Feature) -> (1, 300, 1)
        input_tensor = torch.tensor(processed_sig, dtype=torch.float32).unsqueeze(0).unsqueeze(2)
        
        with torch.no_grad():
            outputs = self.model(input_tensor)
            _, predicted_idx = torch.max(outputs, 1)
            
        idx = predicted_idx.item()
        return self.labels.get(idx, str(idx))

    def _preprocess(self, signal: List[int], target_len: int) -> np.ndarray:
        arr = np.array(signal)
        current_len = len(arr)
        
        if current_len == target_len:
            return arr
        elif current_len > target_len:
            return arr[:target_len]
        else:
            # Pad with zeros at the end
            padding = np.zeros(target_len - current_len)
            return np.concatenate([arr, padding])
