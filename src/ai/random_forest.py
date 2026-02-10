import os
import joblib
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from logger import get_logger
from data_types import Measurement, EchogramMeasurement
from .base import AbstractSonarModel

class RandomForestFeatureModel(AbstractSonarModel):
    """
    Implementiert die klassische Feature-Extraction-Pipeline (wie im MATLAB/Jupyter Notebook).
    Nutzt handgefertigte Features (Energy, Width, Peak, etc.) und einen ML-Classifier (z.B. Random Forest).
    """

    def __init__(self, settings: Dict[str, Any] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.model = None
        self.scaler = None
        self.pca = None
        self.settings = settings or {}
        # Default Window Length aus alten Notebooks, falls nicht in Config
        self.win_len = self.settings.get("win_len", 155) 

    def load(self, model_path: str):
        """Lädt das Pickle-Modell (inkl. Scaler/PCA falls vorhanden)."""
        if not os.path.exists(model_path):
             self.logger.error(f"Modell-Datei nicht gefunden: {model_path}")
             return

        try:
            data = joblib.load(model_path)
            if isinstance(data, dict):
                self.model = data.get("model")
                self.scaler = data.get("scaler")
                self.pca = data.get("pca")
                self.logger.info(f"Legacy-Modell geladen from {model_path} (Scaler={bool(self.scaler)}, PCA={bool(self.pca)})")
            else:
                self.model = data
                self.scaler = None
                self.pca = None
                self.logger.warning("Altes Modellformat geladen (ohne Scaler/PCA).")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Legacy-Modells: {e}")

    def predict(self, data_low: List[Measurement], data_high: List[Measurement]) -> Optional[str]:
        if not self.model:
            self.logger.warning("Kein Modell geladen.")
            return None
        
        if not data_low or not data_high:
            return None

        m_low = data_low[0]
        m_high = data_high[0]

        if not isinstance(m_low, EchogramMeasurement) or not isinstance(m_high, EchogramMeasurement):
            self.logger.warning("Legacy-Modell benötigt Echogramm-Daten.")
            return None

        try:
            # Daten extrahieren
            sig_hf = np.array(m_high.data_points)
            sig_lf = np.array(m_low.data_points)

            # Feature Extraction (Hardcoded Parameter passend zum Training)
            # HF(30, 20), LF(78, 55)
            stats_hf, win_hf = self._process_signal(sig_hf, self.win_len, 30, 20)
            stats_lf, win_lf = self._process_signal(sig_lf, self.win_len, 78, 55)

            # Feature Engineering Pipeline
            stats = np.concatenate([stats_hf, stats_lf]) # 8 features
            wave = np.concatenate([win_hf, win_lf])      # 310 features

            if self.scaler and self.pca:
                # 1. Waveform skalieren
                wave_std = self.scaler.transform(wave.reshape(1, -1))
                # 2. PCA anwenden
                wave_pca = self.pca.transform(wave_std)
                # 3. Mit Stats kombinieren
                features = np.hstack([stats.reshape(1, -1), wave_pca]) 
            else:
                # Fallback: Alles verketten (Legacy Raw)
                features = np.concatenate([stats, wave]).reshape(1, -1)

            # Vorhersage
            prediction = self.model.predict(features)[0]
            return str(prediction)

        except Exception as e:
            self.logger.error(f"Fehler bei Prediction im Legacy-Modell: {e}")
            return None

    def _process_signal(self, sig: np.ndarray, win_len: int, p_mask: int, v_start: int) -> Tuple[List[float], np.ndarray]:
        """
        Extrahiert Features aus einem Signal.
        Interne Hilfsmethode, identisch zur alten Implementierung.
        """
        sig_len = len(sig)
        
        # 1. Peak
        roi_start = min(sig_len, p_mask)
        peak_idx = 0 if roi_start >= sig_len else roi_start + np.argmax(sig[roi_start:])
        peak_val_raw = sig[peak_idx] if peak_idx < sig_len else 0
        
        # 2. Valley
        v_s = min(sig_len, v_start)
        v_e = peak_idx
        valley_idx = v_s if v_s >= v_e else v_s + np.argmin(sig[v_s:v_e])
        valley_val = sig[valley_idx] if valley_idx < sig_len else 0
        
        # 3. Onset
        threshold = valley_val + (peak_val_raw - valley_val) * 0.10
        rise_segment = sig[valley_idx:peak_idx] if valley_idx < peak_idx else np.array([])
        
        if len(rise_segment) == 0: 
            onset_abs = valley_idx
        else:
            below_idx = np.where(rise_segment < threshold)[0]
            onset_abs = valley_idx + (below_idx[-1] if len(below_idx) > 0 else 0)
            
        # 4. Window Extraction
        start_idx = onset_abs
        end_idx   = start_idx + win_len
        aligned_window = np.zeros(win_len)
        
        read_start = max(0, start_idx)
        read_end   = min(sig_len, end_idx)
        write_start = read_start - start_idx
        write_end   = write_start + (read_end - read_start)
        
        if read_start < read_end and write_start < win_len:
            aligned_window[write_start:write_end] = sig[read_start:read_end]
            
        # 5. Features
        raw_energy = np.sum(aligned_window**2)
        s_val = np.std(aligned_window)
        m_val = np.mean(aligned_window)
        
        aligned_window_norm = (aligned_window - m_val) / s_val if s_val > 1e-9 else aligned_window - m_val
            
        # Stats (Width calculation)
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
