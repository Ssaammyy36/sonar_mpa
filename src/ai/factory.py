from typing import Dict, Any, Type
from .base import AbstractSonarModel
from .random_forest import RandomForestFeatureModel
from .lstm import LSTMSonarModel

class AIFactory:
    """
    Factory-Klasse zur Erstellung von KI-Modell-Instanzen basierend auf der Konfiguration.
    """
    
    _REGISTRY: Dict[str, Type[AbstractSonarModel]] = {
        "random_forest": RandomForestFeatureModel,
        "lstm_demo": LSTMSonarModel,
    }

    @staticmethod
    def create_model(config_type: str, settings: Dict[str, Any]) -> AbstractSonarModel:
        """
        Erstellt eine Instanz des angeforderten Modells.
        
        Args:
            config_type: Der Typ-String aus der Config (z.B. "legacy_feature_based").
            settings: Das Settings-Dictionary für das Modell.
            
        Returns:
            Eine Instanz, die von AbstractSonarModel erbt.
        """
        model_class = AIFactory._REGISTRY.get(config_type)
        if not model_class:
            raise ValueError(f"Unbekannter AI-Modell-Typ: {config_type}")
            
        return model_class(settings=settings)
