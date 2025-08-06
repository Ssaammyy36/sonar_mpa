from utils.logger import get_logger

class Steuerung:
    """
    Steuert den Ablauf der Sonar-Messung.

    Attributes:
        logger: Das Logging-Objekt für diese Klasse.
    """
    def __init__(self):
        """
        Initialisiert ein neues Steuerungs-Objekt.
        """
        self.logger = get_logger(__name__)

    def test(self):
        """Loggt eine Test-Nachricht, um die Erreichbarkeit zu prüfen."""
        self.logger.debug("Steuerung erreichbar.")
