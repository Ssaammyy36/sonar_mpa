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

# --- Feature Based Model (Base) ---
class FeatureBasedModel(AbstractSonarModel):
    """
    Basisklasse für alle Modelle, die auf klassischer Feature-Extraction basieren.
    Implementiert Laden, Signalverarbeitung und Vorhersage zentral.
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
                self.logger.info(f"{self.__class__.__name__} geladen (mit Scaler/PCA).")
            else:
                self.model = data
                self.logger.warning(f"{self.__class__.__name__} geladen (ohne Scaler/PCA - altes Format oder direktes Modell).")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden von {self.__class__.__name__}: {e}")

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
        try:
            if not self.model:
                self.logger.warning(f"Kein Modell geladen ({self.__class__.__name__}).")
                return None

            m_low = data_low[0]
            m_high = data_high[0]
            
            sig_hf = np.array(m_high.data_points)
            sig_lf = np.array(m_low.data_points)

            win_len = self.settings.get("win_len", 155)
            p_mask_hf = self.settings.get("p_mask_hf", 30)
            v_start_hf = self.settings.get("v_start_hf", 20)
            p_mask_lf = self.settings.get("p_mask_lf", 78)
            v_start_lf = self.settings.get("v_start_lf", 55)

            stats_hf, win_hf = self.process_signal(sig_hf, win_len, p_mask_hf, v_start_hf)
            stats_lf, win_lf = self.process_signal(sig_lf, win_len, p_mask_lf, v_start_lf)
            stats = np.concatenate([stats_hf, stats_lf])
            wave = np.concatenate([win_hf, win_lf])
            
            if self.scaler and self.pca:
                wave_std = self.scaler.transform(wave.reshape(1, -1))
                wave_pca = self.pca.transform(wave_std)
                features = np.hstack([stats.reshape(1, -1), wave_pca])
            else:
                 features = np.concatenate([stats, wave]).reshape(1, -1)

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
            self.logger.error(f"Fehler bei Prediction ({self.__class__.__name__}): {e}")
            return None

# --- Concrete Models ---
class RandomForestModel(FeatureBasedModel):
    pass

class MLPModel(FeatureBasedModel):
    pass

class SVMModel(FeatureBasedModel):
    pass

class RnnModel(FeatureBasedModel):
    pass

# --- Factory Function ---
def create_ai_model(config_type: str, settings: Dict[str, Any]) -> AbstractSonarModel:
    if config_type == "random_forest":
        return RandomForestModel(settings)
    elif config_type == "mlp":
        return MLPModel(settings)
    elif config_type == "svm":
        return SVMModel(settings)
    elif config_type == "rnn":
        return RnnModel(settings)
    elif config_type == "legacy_feature_based": 
        return RandomForestModel(settings)
    else:
        raise ValueError(f"Unbekannter Modell-Typ: {config_type}")
