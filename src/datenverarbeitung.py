from utils.logger import get_logger
from typing import List, Optional
import matplotlib.pyplot as plt

class Datenverarbeitung:
    """
    Verarbeitet die empfangenen Sonar-Daten.

    Attributes:
        logger: Das Logging-Objekt für diese Klasse.
    """
    def __init__(self):
        """
        Initialisiert ein neues Datenverarbeitungs-Objekt.
        """
        self.logger = get_logger(__name__)

    def test(self):
        """Loggt eine Test-Nachricht, um die Erreichbarkeit zu prüfen."""
        self.logger.debug("Datenverarbeitung erreichbar.")

    def parse_nmea_tiefe(self, nmea_data: Optional[bytes]) -> List[float]:
        """Parst NMEA-Daten, um Tiefenwerte in Metern aus $SDDBT-Sätzen zu extrahieren."""
        tiefen = []
        if not nmea_data:
            return tiefen

        try:
            decoded_data = nmea_data.decode("latin_1")
            lines = decoded_data.splitlines()

            for line in lines:
                if line.strip().startswith('$SDDBT'):
                    parts = line.strip().split(',')
                    if len(parts) > 4 and parts[4] == 'M':
                        try:
                            tiefen.append(float(parts[3]))
                        except (ValueError, IndexError):
                            self.logger.warning(f"Fehler beim Parsen des NMEA-Satzes: {line}")
        except UnicodeDecodeError as e:
            self.logger.error(f"Fehler beim Dekodieren der NMEA-Daten: {e}")
        
        return tiefen

    def parse_binaer_daten(self, bin_data: Optional[bytes]) -> List[int]:
        """Parst die rohen Binärdaten vom Sonar in eine Liste von Amplituden."""
        amplituden = []
        if not bin_data:
            return amplituden
        
        try:
            decoded_data = bin_data.decode("latin_1")
            lines = decoded_data.strip().splitlines()

            for line in lines:
                if line:
                    amplituden.append(int(line))
        except (ValueError, UnicodeDecodeError) as e:
            self.logger.error(f"Fehler beim Parsen der Binärdaten: {e}")
        
        return amplituden

    def plotte_echogramm(self, amplituden: List[int], titel: str = "Sonar Echogramm"):
        """Stellt das Sonarsignal-Amplitude über die Zeit dar."""
        if not amplituden:
            self.logger.info("Keine Amplitudendaten zum Plotten vorhanden.")
            return
        
        self.logger.info(f"Plotte {len(amplituden)} Amplituden-Samples.")
        plt.figure(figsize=(12, 6))
        plt.plot(amplituden)
        plt.title(titel)
        plt.xlabel("Samples [N]")
        plt.ylabel("Signal Amplitude [bit 0..255]")
        plt.grid(True)
        plt.show()
    
    def parse_12_bit_binary_data(self, bin_data: Optional[bytes]) -> List[int]:
        """Parses the raw binary data from the sonar into a list of integer amplitudes."""
        amplituden = []
        if not bin_data:
            return amplituden
        try:
            # Each amplitude is represented by 2 bytes (16 bits), but only 12 bits are used
            for i in range(0, len(bin_data), 2):
                if i + 1 < len(bin_data):
                    # Combine two bytes and mask to get the lower 12 bits
                    amplitude = ((bin_data[i] << 8) | bin_data[i + 1]) & 0x0FFF
                    amplituden.append(amplitude)
        except (ValueError, UnicodeDecodeError) as e:
            self.logger.error(f"Fehler beim Parsen der Binärdaten: {e}")
        
        return amplituden
    
