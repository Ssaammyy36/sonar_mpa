import os
import pickle
import numpy as np
from typing import Optional, List, Any
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
            self.logger.error(f"Modell-Datei nicht gefunden: {model_path}")
            return

        try:
            if model_type == "pickle":
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.logger.info("Pickle-Modell erfolgreich geladen.")
            
            elif model_type == "onnx":
                try:
                    import onnxruntime as ort
                    self.model = ort.InferenceSession(model_path)
                    self.logger.info("ONNX-Modell erfolgreich geladen.")
                except ImportError:
                    self.logger.error("onnxruntime modul fehlt. Bitte 'pip install onnxruntime' ausführen.")
            
            else:
                self.logger.error(f"Unbekannter Modell-Typ: {model_type}")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Modells: {e}")

    def predict(self, measurements: List[Measurement]) -> Optional[str]:
        """
        Führt eine Klassifizierung auf den übergebenen Messdaten durch.
        """
        if not self.model:
            return None

        if not measurements:
            return None

        # Wir nehmen an, dass wir den ersten Ping klassifizieren wollen (analog zu CSV Export)
        measurement = measurements[0]
        
        if not isinstance(measurement, EchogramMeasurement):
            self.logger.warning("Klassifizierung nur für Echogramm-Daten unterstützt.")
            return None

        # Feature Extraction: Hier müssen wir sicherstellen, dass die Daten 
        # genau so aufbereitet werden, wie das Modell es erwartet.
        # Aktuell nehmen wir die Rohdaten (data_points) als Features.
        features = np.array(measurement.data_points).reshape(1, -1)
        
        try:
            prediction = None
            if self.config["model_type"] == "pickle":
                prediction = self.model.predict(features)[0]
            
            elif self.config["model_type"] == "onnx":
                # ONNX Runtime Interaktion
                input_name = self.model.get_inputs()[0].name
                # Annahme: Input ist float model
                prediction = self.model.run(None, {input_name: features.astype(np.float32)})[0][0]

            self.logger.info(f"Klassifizierungsergebnis: {prediction}")
            return str(prediction)

        except Exception as e:
            self.logger.error(f"Fehler bei der Klassifizierung: {e}")
            return None
