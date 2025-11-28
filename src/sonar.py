import time
from typing import Optional

from src.logger import get_logger
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

    def konfigurieren(self, output_mode: str, frequency: str, settings: Optional[dict] = None):
        """Konfiguriert das Echolot mit den gegebenen Parametern."""

        # Check
        if not self.echosounder:
            self.logger.warning(
                "Sonar nicht verbunden. Konfiguration nicht möglich.")
            return

        # Config
        self.echosounder.SetValue("IdOutput", output_mode)

        # Wähle die Frequenz basierend auf der Konfiguration
        freq_config = config.FREQUENCIES.get(frequency)
        if freq_config and "command" in freq_config:
            command = freq_config["command"]
            self.echosounder.SendCommand(command)
            self.logger.info(
                f"Konfiguration: {output_mode=}, frequency='{frequency}' (Befehl: {command})")
        else:
            self.logger.error(
                f"Frequenz '{frequency}' ist nicht oder nicht vollständig in config.py definiert.")
            return

        # Wende spezifische Modus-Einstellungen an, falls vorhanden
        if settings:
            self.logger.info("Wende spezifische Modus-Einstellungen an:")
            for key, value in settings.items():
                # `read_timeout` ist eine reine Software-Einstellung und wird nicht an das Sonar gesendet
                if key != "read_timeout":
                    self.echosounder.SetValue(key, str(value))
                    self.logger.info(f"  -> {key}: {value}")

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
        data = self.echosounder.ReadData(4096)  # 2^12 = 4096 ist der Standard

        # Checken
        if data:
            self.logger.debug(f"Daten empfangen mit der Länge {len(data)}")
        else:
            self.logger.debug("Keine Daten vom Sonar empfangen.")

        self.echosounder.Stop()
        return data
