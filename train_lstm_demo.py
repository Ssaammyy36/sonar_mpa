import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import glob
import pandas as pd

try:
    if torch.cuda.is_available():
        DEVICE = "cuda"
    else:
        DEVICE = "cpu"
except:
    DEVICE = "cpu"

print(f"Using Device: {DEVICE}")

# --- Simples LSTM Modell ---
class SimpleLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=1, num_classes=3):
        super(SimpleLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
        
    def forward(self, x):
        h0 = torch.zeros(1, x.size(0), 32).to(x.device)
        c0 = torch.zeros(1, x.size(0), 32).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

def find_csv_files(root_dir):
    csv_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".csv") and "messung" in root: # Filtern nach Messungsordnern
                csv_files.append(os.path.join(root, file))
    return csv_files

def train_real_model():
    print("--- 1. Daten laden ---")
    data_dir = "data"
    SEQ_LEN = 300 
    
    csv_files = find_csv_files(data_dir)
    print(f"Gefundene CSV-Dateien: {len(csv_files)}")
    
    all_sequences = []
    all_labels = []
    
    label_map = {"Sand": 0, "Gravel": 1, "Stones": 2, "Stone": 2} # Sicherstellen, dass Stone und Stones dabei ist
    
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path, delimiter=";")
            if 'Frequency' in df.columns:
                df = df[df['Frequency'] == 'high']
            
            if df.empty:
                continue

            data_cols = [c for c in df.columns if c.startswith("S_")]
            if not data_cols:
                continue
                
            X_df = df[data_cols].fillna(0) # IMPORTANT: Handle NaNs
            X_raw = X_df.values
            y_raw = df['class_name'].values
            
            for i in range(len(X_raw)):
                label_str = str(y_raw[i]).strip()
                label_int = -1
                for key, val in label_map.items():
                    if key.lower() == label_str.lower():
                        label_int = val
                        break
                
                if label_int != -1:
                    sig = X_raw[i]
                    # Preprocessing
                    if len(sig) > SEQ_LEN:
                        sig = sig[:SEQ_LEN]
                    elif len(sig) < SEQ_LEN:
                        sig = np.pad(sig, (0, SEQ_LEN - len(sig)), 'constant')
                    
                    # Sanity Check for NaNs/Infs
                    if np.isnan(sig).any() or np.isinf(sig).any():
                        sig = np.nan_to_num(sig)
                        
                    all_sequences.append(sig)
                    all_labels.append(label_int)
                    
        except Exception as e:
            print(f"Fehler bei {file_path}: {e}")

    if not all_sequences:
        print("FEHLER: Keine validen Trainingsdaten gefunden!")
        return

    # Numpy -> Tensor
    X_np = np.array(all_sequences, dtype=np.float32)
    # Simple Normalization
    X_mean = X_np.mean()
    X_std = X_np.std() + 1e-6
    X_np = (X_np - X_mean) / X_std
    
    y_np = np.array(all_labels, dtype=np.int64)
    
    X_tensor = torch.tensor(X_np).unsqueeze(2).to(DEVICE) # (Batch, Seq, 1)
    y_tensor = torch.tensor(y_np).to(DEVICE)
    
    print(f"\nDatensatz fertig: {X_tensor.shape} Samples")
    print(f"Verteilung: {np.bincount(y_np)} (Sand, Gravel, Stones)") 
    
    # --- 2. Training ---
    print("\n--- 2. Training starten ---")
    model = SimpleLSTM(input_size=1, hidden_size=32, num_classes=3).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001) # Learning Rate slightly reduced
    
    model.train()
    epochs = 50
    batch_size = 16 # Smaller batch size for small dataset
    dataset_size = len(X_tensor)
    indices = np.arange(dataset_size)
    
    for epoch in range(epochs):
        np.random.shuffle(indices)
        epoch_loss = 0
        correct = 0
        
        for i in range(0, dataset_size, batch_size):
            batch_idx = indices[i:i+batch_size]
            X_batch = X_tensor[batch_idx]
            y_batch = y_tensor[batch_idx]
            
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * len(batch_idx) # weighted by batch size
            
            _, predicted = torch.max(outputs.data, 1)
            correct += (predicted == y_batch).sum().item()
            
        avg_loss = epoch_loss / dataset_size
        accuracy = 100 * correct / dataset_size
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f} | Acc: {accuracy:.2f}%")
        
    # --- 3. Speichern ---
    save_dir = "models"
    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "lstm_demo.pth")
    
    inference_map = {0: "Sand", 1: "Gravel", 2: "Stones"}
    
    save_dict = {
        "model_state": model.state_dict(),
        "labels": inference_map,
        "input_len": SEQ_LEN,
        "mean": X_mean,
        "std": X_std
    }
    
    torch.save(save_dict, model_path)
    print(f"\nModell gespeichert unter: {model_path} (Mean={X_mean:.4f}, Std={X_std:.4f})")
    print("Fertig.")

if __name__ == "__main__":
    train_real_model()
