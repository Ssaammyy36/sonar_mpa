import os
import pickle
import numpy as np
from typing import Optional, List, Tuple
import config
from logger import get_logger
from data_types import Measurement, EchogramMeasurement

class SonarClassifier:
    """
    Handhabt das Laden des ML-Modells und die Klassifizierung von Sonar-Daten.
    """
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.config = config.ANALYSIS_CONFIG
        self.model = None
        
        if self.config["enable_classification"]:
            self.load_model()

    def load_model(self):
        """Lädt das Modell basierend auf der Konfiguration."""
        model_path = self.config["model_path"]
        model_type = self.config["model_type"]

        if not os.path.exists(model_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            abs_model_path = os.path.join(base_dir, model_path)
            
            if os.path.exists(abs_model_path):
                model_path = abs_model_path
                self.logger.info(f"Modell-Pfad korrigiert auf: {model_path}")
            else:
                self.logger.error(f"Modell-Datei nicht gefunden: {model_path}")
                return

        try:
            if model_type == "pickle":
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.logger.info("Pickle-Modell erfolgreich geladen.")
            
            elif model_type == "onnx":
                import onnxruntime as ort
                self.model = ort.InferenceSession(model_path)
                self.logger.info("ONNX-Modell erfolgreich geladen.")
            else:
                self.logger.error(f"Unbekannter Modell-Typ: {model_type}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Modells: {e}")

    def process_signal(self, sig: np.ndarray, win_len: int, p_mask: int, v_start: int) -> Tuple[List[float], np.ndarray]:
        """
        Extrahiert Features aus einem Signal (Portierung aus Notebook).
        Returns: 
            [raw_energy, peak_val_raw, peak_norm, width], aligned_window_norm
        """
        sig_len = len(sig)
        
        # 1. Peak
        roi_start = min(sig_len, p_mask)
        if roi_start >= sig_len: 
            peak_idx = 0
        else: 
            peak_idx = roi_start + np.argmax(sig[roi_start:])
        
        peak_val_raw = sig[peak_idx] if peak_idx < sig_len else 0
        
        # 2. Valley (vor dem Peak)
        v_s = min(sig_len, v_start)
        v_e = peak_idx
        if v_s >= v_e: 
            valley_idx = v_s
        else: 
            valley_idx = v_s + np.argmin(sig[v_s:v_e])
            
        valley_val = sig[valley_idx] if valley_idx < sig_len else 0
        
        # 3. Onset (Schwellwert bei 10%)
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
        raw_energy = np.sum(aligned_window**2)    # Wie viel Energie steckt im Echo?
        s_val = np.std(aligned_window)            # Standardabweichung
        m_val = np.mean(aligned_window)           # Mittelwert
        
        if s_val > 1e-9: 
            aligned_window_norm = (aligned_window - m_val) / s_val
        else: 
            aligned_window_norm = aligned_window - m_val
            
        # Stats (Width calculation)
        loc = peak_idx - start_idx
        loc = max(0, min(win_len - 1, loc))
        peak_norm = aligned_window_norm[loc]    # Normalisierter Peak
        half_val = peak_norm * 0.5              
        
        left_part = aligned_window_norm[:loc]
        left_idxs = np.where(left_part < half_val)[0]
        left_idx = left_idxs[-1] if len(left_idxs) > 0 else 0
        
        right_part = aligned_window_norm[loc:]
        right_idxs = np.where(right_part < half_val)[0]
        width_idx = (loc + right_idxs[0]) if len(right_idxs) > 0 else (win_len - 1)
        width = width_idx - left_idx                                                    # Breite des Echos
        
        return [raw_energy, peak_val_raw, peak_norm, width], aligned_window_norm

    def predict_paired(self, data_low_list: List[Measurement], data_high_list: List[Measurement]) -> Optional[str]:
        """
        Klassifiziert basierend auf einem Paar von HF und LF Messungen.
        Extrahiert Features identisch zum MATLAB Notebook.
        """
        if not self.model or not data_low_list or not data_high_list:
            return None

        m_low = data_low_list[0]
        m_high = data_high_list[0]

        if not isinstance(m_low, EchogramMeasurement) or not isinstance(m_high, EchogramMeasurement):
            self.logger.warning("Klassifizierung nur für Echogramm-Daten.")
            return None

        # Parameter aus config oder hardecoded (müssen zum Training passen!)
        # Notebook defaults: win_len=155, HF(30, 20), LF(78, 55)
        WIN_LEN = 155 
        
        sig_hf = np.array(m_high.data_points)
        sig_lf = np.array(m_low.data_points)

        # Feature Extraction
        stats_hf, win_hf = self.process_signal(sig_hf, WIN_LEN, 30, 20)
        stats_lf, win_lf = self.process_signal(sig_lf, WIN_LEN, 78, 55)

        # Concatenate: [stats_hf, stats_lf, win_hf, win_lf]
        # Shape: 4 + 4 + 155 + 155 = 318 Features
        features = np.concatenate([stats_hf, stats_lf, win_hf, win_lf]).reshape(1, -1)

        try:
            prediction = None
            if self.config["model_type"] == "pickle":
                prediction = self.model.predict(features)[0]
            elif self.config["model_type"] == "onnx":
                input_name = self.model.get_inputs()[0].name
                prediction = self.model.run(None, {input_name: features.astype(np.float32)})[0][0]

            return str(prediction)

        except Exception as e:
            self.logger.error(f"Fehler bei Paired-Prediction: {e}")
            return None

    def predict(self, measurements: List[Measurement], frequency: str) -> Optional[str]:
        """Legacy Single-Frequency Prediction (falls benötigt)"""
        # ... (Alter Code bleibt ggf. als Fallback oder Dummy)
        return None
