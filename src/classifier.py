import os
from typing import List, Optional
import config
from logger import get_logger
from data_types import Measurement
from ai.factory import AIFactory

class SonarClassifier:
    """
    Handhabt das Laden des ML-Modells und die Klassifizierung von Sonar-Daten.
    Fungiert jetzt als Facade für die modularen AI-Modelle in src/ai/.
    """
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.config = config.ANALYSIS_CONFIG
        self.model = None
        
        if self.config.get("enable_classification", False):
            self.load_active_model()

    def load_active_model(self):
        """Lädt das konfigurierte Modell über die Factory."""
        try:
            # Config laden 
            active_id = self.config.get("active_model_id")
            model_conf = self.config.get("models", {}).get(active_id)
            model_type = model_conf.get("type")
            model_path = model_conf.get("model_path")
            settings = model_conf.get("settings", {})

            # Pfad auflösen (relativ zum Project Root)
            if not os.path.exists(model_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                abs_model_path = os.path.join(base_dir, model_path)
                if os.path.exists(abs_model_path):
                    model_path = abs_model_path
                else:
                    self.logger.error(f"Modell-Datei nicht gefunden: {model_path}")
                    return

            # 1. Modell instanziieren via Factory
            self.logger.info(f"Initialisiere AI-Modell '{active_id}' (Typ: {model_type})...")
            self.model = AIFactory.create_model(model_type, settings)
            
            # 2. Gewichte laden
            self.model.load(model_path)
            
            self.logger.info(f"AI-Modell '{active_id}' erfolgreich geladen und bereit.")

        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des AI-Modells: {e}")
            self.model = None

    def predict_paired(self, data_low_list: List[Measurement], data_high_list: List[Measurement]) -> Optional[str]:
        """
        Delegiert die Vorhersage an das aktive Modell.
        """
        if not self.model:
            return None
            
        return self.model.predict(data_low_list, data_high_list)
