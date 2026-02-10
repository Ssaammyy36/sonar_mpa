from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any, Dict, Type
import numpy as np
import logging
import os
import joblib

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from data_types import Measurement, EchogramMeasurement
from logger import get_logger

# --- Base Interface ---
class AbstractSonarModel(ABC):
    """
    Abstrakte Basisklasse für alle Sonar-KI-Modelle.
    Definiert die Schnittstelle, die alle Modelle implementieren müssen.
    """
    
    @abstractmethod
    def load(self, model_path: str):
        """
        Lädt das Modell (Gewichte, Konfiguration) von der Festplatte.
        """
        pass

    @abstractmethod
    def predict(self, data_low: List[Measurement], data_high: List[Measurement]) -> Optional[str]:
        """
        Führt eine Vorhersage basierend auf den Rohdaten durch.
        """
        pass

# --- Random Forest Model (Legacy) ---
class RandomForestModel(AbstractSonarModel):
    """
    Implementiert die klassische Feature-Extraction-Pipeline und einen ML-Classifier (z.B. Random Forest).
    """
    def __init__(self, settings: Dict[str, Any] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = settings or {}
        self.model = None
        self.scaler = None
        self.pca = None

    def load(self, model_path: str):
        try:          
            data = joblib.load(model_path)
            if isinstance(data, dict):
                self.model = data.get("model")
                self.scaler = data.get("scaler")
                self.pca = data.get("pca")
                self.logger.info("Random Forest Modell geladen.")
            else:
                self.model = data
                self.logger.warning("Altes Modellformat geladen (ohne Scaler/PCA).")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des RF-Modells: {e}")

    def process_signal(self, sig: np.ndarray, win_len: int, p_mask: int, v_start: int) -> Tuple[List[float], np.ndarray]:
        """
        Extrahiert Features aus einem Signal (Portierung aus Notebook).

        Args:
            sig (np.ndarray): Das rohe Signal (Datenpunkte).
            win_len (int): Die Länge des Fensters für die Feature-Extraktion (z.B. 155).
            p_mask (int): Index, ab dem nach dem ersten Peak gesucht wird (vermeidet Nahbereichs-Rauschen).
            v_start (int): Start-Index für die Valley-Suche (vor dem Peak).
        
        Returns:
            Tuple[List[float], np.ndarray]: Eine Liste der Features [Energy, PeakVal, PeakNorm, Width] und das normalisierte Fenster.
        """
        try:
            sig_len = len(sig)
            
            # 1. Peak
            roi_start = min(sig_len, p_mask)
            if roi_start >= sig_len: peak_idx = 0
            else: peak_idx = roi_start + np.argmax(sig[roi_start:])
            peak_val_raw = sig[peak_idx] if peak_idx < sig_len else 0
            
            # 2. Valley
            v_s = min(sig_len, v_start)
            v_e = peak_idx
            if v_s >= v_e: valley_idx = v_s
            else: valley_idx = v_s + np.argmin(sig[v_s:v_e])
            valley_val = sig[valley_idx] if valley_idx < sig_len else 0
            
            # 3. Onset
            threshold = valley_val + (peak_val_raw - valley_val) * 0.10
            rise_segment = sig[valley_idx:peak_idx] if valley_idx < peak_idx else np.array([])
            if len(rise_segment) == 0: onset_abs = valley_idx
            else:
                below_idx = np.where(rise_segment < threshold)[0]
                onset_abs = valley_idx + (below_idx[-1] if len(below_idx) > 0 else 0)
                
            # 4. Window
            start_idx = onset_abs
            end_idx   = start_idx + win_len
            aligned_window = np.zeros(win_len)
            read_start = max(0, start_idx)
            read_end   = min(sig_len, end_idx)
            write_start = read_start - start_idx
            write_end   = write_start + (read_end - read_start)
            if read_start < read_end and write_start < win_len:
                aligned_window[write_start:write_end] = sig[read_start:read_end]
                
            # 5. Features (Energy, PeakVal, PeakNorm, Width)
            raw_energy = np.sum(aligned_window**2)
            s_val = np.std(aligned_window)
            m_val = np.mean(aligned_window)
            if s_val > 1e-9: aligned_window_norm = (aligned_window - m_val) / s_val
            else: aligned_window_norm = aligned_window - m_val
                
            loc = peak_idx - start_idx
            loc = max(0, min(win_len - 1, loc))
            peak_norm = aligned_window_norm[loc]
            
            half_val = peak_norm * 0.5              
            left_part = aligned_window_norm[:loc]
            left_idxs = np.where(left_part < half_val)[0]
            left_idx = left_idxs[-1] if len(left_idxs) > 0 else 0
            
            right_part = aligned_window_norm[loc:]
            right_idxs = np.where(right_part < half_val)[0]
            width_idx = (loc + right_idxs[0]) if len(right_idxs) > 0 else (win_len - 1)
            width = width_idx - left_idx
            
            return [raw_energy, peak_val_raw, peak_norm, width], aligned_window_norm

        except Exception as e:
            self.logger.error(f"Fehler in process_signal: {e}")
            return [0.0, 0.0, 0.0, 0.0], np.zeros(win_len)

    def predict(self, data_low: List[Measurement], data_high: List[Measurement]) -> Optional[str]:

        # Umwandeln der Daten in numpy Arrays
        m_low = data_low[0]
        m_high = data_high[0]
        
        sig_hf = np.array(m_high.data_points)
        sig_lf = np.array(m_low.data_points)

        # Features berechnen und zusammenfügen
        win_len = self.settings.get("win_len", 155)
        p_mask_hf = self.settings.get("p_mask_hf", 30)
        v_start_hf = self.settings.get("v_start_hf", 20)
        p_mask_lf = self.settings.get("p_mask_lf", 78)
        v_start_lf = self.settings.get("v_start_lf", 55)

        stats_hf, win_hf = self.process_signal(sig_hf, win_len, p_mask_hf, v_start_hf)
        stats_lf, win_lf = self.process_signal(sig_lf, win_len, p_mask_lf, v_start_lf)
        stats = np.concatenate([stats_hf, stats_lf])
        wave = np.concatenate([win_hf, win_lf])
        
        try:
            if self.scaler and self.pca:
                wave_std = self.scaler.transform(wave.reshape(1, -1))
                wave_pca = self.pca.transform(wave_std)
                features = np.hstack([stats.reshape(1, -1), wave_pca])
            else:
                 features = np.concatenate([stats, wave]).reshape(1, -1)

            # Vorhersage & Wahrscheinlichkeiten
            prediction = self.model.predict(features)[0]
            log_msg = f"Vorhersage: {prediction}"

            if hasattr(self.model, "predict_proba"):
                try:
                    probs = self.model.predict_proba(features)[0]
                    classes = self.model.classes_
                    prob_str = ", ".join([f"{cls}: {p:.2f}" for cls, p in zip(classes, probs)])
                    log_msg += f" | {prob_str}"
                except Exception as e:
                    self.logger.warning(f"Keine Wahrscheinlichkeiten verfügbar: {e}")
            
            self.logger.info(log_msg)

            return str(prediction)
        except Exception as e:
            self.logger.error(f"Fehler bei RF-Prediction: {e}")
            return None

# --- LSTM Model ---
if TORCH_AVAILABLE:
    class SimpleLSTM(nn.Module):
        def __init__(self, input_size=1, hidden_size=32, num_layers=1, num_classes=3):
            super(SimpleLSTM, self).__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, num_classes)
            
        def forward(self, x):
            h0 = torch.zeros(1, x.size(0), 32).to(x.device) 
            c0 = torch.zeros(1, x.size(0), 32).to(x.device)
            out, _ = self.lstm(x, (h0, c0))
            out = self.fc(out[:, -1, :])
            return out
else:
    class SimpleLSTM: pass

class LSTMModel(AbstractSonarModel):
    def __init__(self, settings: Dict[str, Any] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = settings or {}
        self.model = None
        self.device = torch.device('cpu') if TORCH_AVAILABLE else None
        self.labels = {}
        self.seq_len = 300 
        self.mean = 0.0
        self.std = 1.0

    def load(self, model_path: str):
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch nicht verfügbar.")
            return

        try:
             # Try relative to project root
            if not os.path.exists(model_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                abs_path = os.path.join(base_dir, model_path)
                if os.path.exists(abs_path):
                    model_path = abs_path

            checkpoint = torch.load(model_path, map_location=self.device)
            self.seq_len = checkpoint.get("input_len", 300)
            self.labels = checkpoint.get("labels", {})
            self.mean = checkpoint.get("mean", 0.0)
            self.std = checkpoint.get("std", 1.0)
            
            self.model = SimpleLSTM(input_size=1, hidden_size=32, num_classes=3) 
            self.model.load_state_dict(checkpoint["model_state"])
            self.model.eval()
            self.logger.info(f"LSTM geladen (Seq={self.seq_len}, Mean={self.mean:.2f})")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des LSTM: {e}")

    def _preprocess(self, signal: List[int], target_len: int) -> np.ndarray:
        arr = np.array(signal)
        current_len = len(arr)
        if current_len == target_len: return arr
        elif current_len > target_len: return arr[:target_len]
        else:
            padding = np.zeros(target_len - current_len)
            return np.concatenate([arr, padding])

    def predict(self, data_low: List[Measurement], data_high: List[Measurement]) -> Optional[str]:
        if not TORCH_AVAILABLE or not self.model: return None
        if not data_high or not isinstance(data_high[0], EchogramMeasurement): return None
            
        raw_signal = data_high[0].data_points
        processed_sig = self._preprocess(raw_signal, self.seq_len)
        
        if self.std > 1e-6:
             processed_sig = (processed_sig - self.mean) / self.std

        input_tensor = torch.tensor(processed_sig, dtype=torch.float32).unsqueeze(0).unsqueeze(2)
        
        with torch.no_grad():
            outputs = self.model(input_tensor)
            _, predicted_idx = torch.max(outputs, 1)
            
        idx = predicted_idx.item()
        return self.labels.get(idx, str(idx))

# --- Factory Function ---
def create_ai_model(config_type: str, settings: Dict[str, Any]) -> AbstractSonarModel:
    if config_type == "random_forest":
        return RandomForestModel(settings)
    elif config_type == "lstm":
        return LSTMModel(settings)
    elif config_type == "legacy_feature_based": # Backward compat
        return RandomForestModel(settings)
    elif config_type == "lstm_demo": # Backward compat
        return LSTMModel(settings)
    else:
        raise ValueError(f"Unbekannter Modell-Typ: {config_type}")
