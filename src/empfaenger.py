from utils.logger import get_logger

class Empfaenger:
    """
    Repraesentiert einen Empfaenger von Sonar-Daten.

    Attributes:
        name (str): Der Name des Empfaengers.
        logger: Das Logging-Objekt für diese Klasse.
    """
    def __init__(self, name: str):
        """
        Initialisiert ein neues Empfaenger-Objekt.

        Args:
            name (str): Der Name, der dem Empfaenger zugewiesen wird.
        """
        self.name = name
        self.logger = get_logger(__name__)

    def test(self):
        """Loggt eine Test-Nachricht, um die Erreichbarkeit zu pruefen."""
        self.logger.debug(f"Empfaenger {self.name} erreichbar.")
