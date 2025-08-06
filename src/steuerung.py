from utils.logger import get_logger
from sensor import Sensor
from empfaenger import Empfaenger
from datenverarbeitung import Datenverarbeitung

class Steuerung:
    """
    Steuert den gesamten Ablauf der Sonar-Messung und -Verarbeitung.
    Diese Klasse initialisiert alle notwendigen Komponenten.
    """
    def __init__(self):
        """Initialisiert die Steuerung und alle Kernkomponenten."""
        self.logger = get_logger(__name__)
        
        # Die Steuerung erstellt und besitzt die anderen Objekte
        self.sensor = Sensor("S1")
        self.empfaenger = Empfaenger("E1")
        self.datenverarbeitung = Datenverarbeitung()
        
        self.logger.debug("Steuerung und alle Komponenten initialisiert.")

    def teste_komponenten(self):
        """Führt einen einfachen Erreichbarkeitstest für alle Komponenten aus."""
        self.logger.info("Starte Komponenten-Test...")
        
        # Hier kommt deine eigentliche Programmlogik hin
        # Fürs Erste rufen wir die Test-Methoden auf:
        self.sensor.test()
        self.empfaenger.test()
        self.datenverarbeitung.test()
        self.logger.debug("Steuerung erreichbar.")
        
        self.logger.info("Komponenten-Test beendet.")
