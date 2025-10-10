import time
from typing import Optional

from utils.logger import get_logger
from echosounderapi.echosndr import DualEchosounder
import config

class Sonar:
    """
    Repräsentiert das Sonar-Gerät und kapselt die Hardware-Kommunikation.

    Attributes:
        sonar_id (str): Die eindeutige ID des Sonars.
        logger: Das Logging-Objekt für diese Klasse.
        echosounder (DualEchosounder): Das API-Objekt für die Sonar-Steuerung.
    """
    def __init__(self, sonar_id: str):
        """
        Initialisiert ein neues Sonar-Objekt.

        Args:
            sonar_id (str): Die ID, die dem Sonar zugewiesen wird.
        """
        self.sonar_id = sonar_id
        self.logger = get_logger(__name__)
        self.echosounder: Optional[DualEchosounder] = None

    def verbinden(self) -> bool:
        """Stellt die Verbindung zum Echolot her."""
        self.logger.info(f"Versuche, Sonar '{self.sonar_id}' auf Port {config.COMPORT} zu verbinden...")
        try:
            self.echosounder = DualEchosounder(f"\\\\.\\{config.COMPORT}", config.BAUDRATE)
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Echosounder-Objekts: {e}")
            return False

        if not self.echosounder.Detect():
            self.logger.error("Echolot auf dem Port nicht erkannt.")
            self.echosounder = None
            return False

        self.logger.info(f"Echolot erfolgreich auf {config.COMPORT} mit {config.BAUDRATE} Baud erkannt.")
        self.echosounder.SetCurrentTime()
        return True

    def trennen(self):
        """Stoppt das Echolot und gibt die Ressourcen frei."""
        if self.echosounder:
            self.logger.info("Stoppe Echolot und trenne Verbindung.")
            self.echosounder.Stop()
            # Die DualEchosounder-Klasse hat keine explizite disconnect/close-Methode.
            # Das Objekt wird vom Garbage Collector entfernt.
            self.echosounder = None

    def konfigurieren(self, output_mode: str, frequency: str, interval: str, pulse_length: str = "20", sampl_freq: str = "100000"):
        """Konfiguriert das Echolot mit den gegebenen Parametern."""
        if not self.echosounder:
            self.logger.warning("Sonar nicht verbunden. Konfiguration nicht möglich.")
            return

        self.logger.info("Konfiguriere Echolot...")
        self.echosounder.SetValue("IdOutput", output_mode)

        if frequency in ("high", "200kHz"):
            self.echosounder.SendCommand("IdSetHighFreq")
        elif frequency in ("low", "50kHz"):
            self.echosounder.SendCommand("IdSetLowFreq")
        else:
            self.logger.error(f"Unbekannte Frequenz: {frequency}")
            return

        self.echosounder.SetValue("IdInterval", interval)
        self.echosounder.SetValue("IdTxLength", pulse_length)
        self.echosounder.SetValue("IdSamplFreq", sampl_freq)
        self.logger.info(f"Konfiguration: {output_mode=}, {frequency=}, {interval=}, {pulse_length=}, {sampl_freq=}")

    def daten_lesen(self, dauer: float = 2.0) -> Optional[bytes]:
        """Startet das Pingen, liest für eine bestimmte Dauer und gibt die Daten zurück."""
        if not self.echosounder:
            self.logger.warning("Sonar nicht verbunden. Datenlesen nicht möglich.")
            return None

        self.logger.info(f"Starte Ping für {dauer} Sekunden...")
        if not self.echosounder.Start():
            self.logger.error("Starten des Echolots fehlgeschlagen.")
            return None
        
        time.sleep(dauer)
        data = self.echosounder.ReadData(1024) # Buffer size, kann angepasst werden
        self.echosounder.Stop() # Stoppt das Pingen nach dem Lesen
        return data

    def test(self):
        """Loggt eine Test-Nachricht, um die Erreichbarkeit zu prüfen."""
        self.logger.debug(f"Sonar {self.sonar_id} erreichbar.")
