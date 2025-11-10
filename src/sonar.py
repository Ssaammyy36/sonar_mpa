import time
from typing import Optional

from utils.logger import get_logger
from echosounderapi.echosndr import DualEchosounder
import config


class Sonar:
    """Repräsentiert das Sonar-Gerät und kapselt die Hardware-Kommunikation."""

    def __init__(self):
        """Initialisiert ein neues Sonar-Objekt."""
        self.logger = get_logger(__name__)
        self.echosounder: Optional[DualEchosounder] = None

    def verbinden(self) -> bool:
        """Stellt die Verbindung zum Echolot her."""
        self.logger.info(
            f"Versuche, Sonar auf Port {config.COMPORT} zu verbinden...")
        try:
            self.echosounder = DualEchosounder(
                f"\\\\.\\{config.COMPORT}", config.BAUDRATE)
        except Exception as e:
            self.logger.error(
                f"Fehler beim Erstellen des Echosounder-Objekts: {e}")
            return False

        if not self.echosounder.Detect():
            self.logger.error("Echolot auf dem Port nicht erkannt.")
            self.echosounder = None
            return False

        self.logger.info(
            f"Echolot erfolgreich auf {config.COMPORT} mit {config.BAUDRATE} Baud erkannt.")
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

    def konfigurieren(self, output_mode: str, frequency: str):
        """Konfiguriert das Echolot mit den gegebenen Parametern."""
        
        # Check
        if not self.echosounder:
            self.logger.warning("Sonar nicht verbunden. Konfiguration nicht möglich.")
            return

        # Config
        self.echosounder.SetValue("IdOutput", output_mode)

        if frequency in ("high", "200kHz"):
            self.echosounder.SendCommand("IdSetHighFreq")
        elif frequency in ("low", "50kHz"):
            self.echosounder.SendCommand("IdSetLowFreq")
        else:
            self.logger.error(f"Unbekannte Frequenz: {frequency}")
            return
        self.logger.info(f"Konfiguration: {output_mode=}, {frequency=}")

        # für Mode 4
        self.echosounder.SetValue("IdRange", "3000")
        self.echosounder.SetValue("IdInterval", "1")
        self.echosounder.SetValue("IdDeadzone", "200")
        self.echosounder.SetValue("IdTxLength", "50")
        self.echosounder.SetValue("IdTxPower", "-6")
        self.echosounder.SetValue("IdGain", "-6")
                                   

    def daten_lesen(self, dauer: float = 2.0) -> Optional[bytes]:
        """Startet das Pingen, liest für eine bestimmte Dauer und gibt die Daten zurück. Print mit hex"""
        
        # Check for Sonar Objekt
        if not self.echosounder:
            self.logger.warning(
                "Sonar nicht verbunden. Datenlesen nicht möglich.")
            return None

        # Scannen 
        self.logger.info(f"Starte Ping für {dauer} Sekunden...")
        if not self.echosounder.Start():
            self.logger.error("Starten des Echolots fehlgeschlagen.")
            return None
        time.sleep(dauer)
        data = self.echosounder.ReadData(10000)

        # Checken  
        if data:
            self.logger.debug(f"Daten empfangen mit der Länge {len(data)}")
        else:
            self.logger.debug("Keine Daten vom Sonar empfangen.")

        self.echosounder.Stop()  
        return data
