from abc import ABC, abstractmethod
from typing import List, Optional
from data_types import Measurement

class AbstractSonarModel(ABC):
    """
    Abstrakte Basisklasse für alle Sonar-KI-Modelle.
    Jedes Modell ist selbst dafür verantwortlich, wie es geladen wird
    und wie es die Rohdaten verarbeitet (Feature Engineering).
    """

    @abstractmethod
    def load(self, model_path: str):
        """
        Lädt das Modell von der Festplatte.
        """
        pass

    @abstractmethod
    def predict(self, data_low: List[Measurement], data_high: List[Measurement]) -> Optional[str]:
        """
        Führt eine Vorhersage basierend auf den Rohdaten durch.
        
        Args:
            data_low: Liste von Messungen der niedrigen Frequenz (z.B. 50kHz)
            data_high: Liste von Messungen der hohen Frequenz (z.B. 200kHz)
            
        Returns:
            Der vorhergesagte Klassenname als String oder None bei Fehler.
        """
        pass
