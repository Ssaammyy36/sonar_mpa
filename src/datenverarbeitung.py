from utils.logger import get_logger
from typing import List, Optional
import matplotlib.pyplot as plt
import ast
import numpy as np
np.set_printoptions(threshold=np.inf)


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
                            self.logger.warning(
                                f"Fehler beim Parsen des NMEA-Satzes: {line}")
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
        """Parses the raw binary data from the sonar into a dictionary with the meaning of the bytes."""
        message = {}
        if not bin_data:
            return bin_data
        try:
            self.logger.debug(type(bin_data))
            # Abfragen, ob Daten von Sensor oder aus Datei kommen
            #if type(bin_data) == str:
            #    bin_data = bytestring_to_bin(bin_data)
            #else
            
            self.logger.debug("Parsing 12-bit binary data...")    
            bin_data = self.bytestring_to_bin(bin_data)

            data = bin_data[0: 8]  # Lese die ersten 8 bytes
            message["magic"] = data

            data = bin_data[8: 10]
            message["packet_id"] = data

            data = bin_data[10: 14]
            message["length"] = data

            self.logger.debug(message)
        except (ValueError, UnicodeDecodeError) as e:
            self.logger.error(f"Fehler beim Parsen der Binärdaten: {e}")

        return message


    def bytestring_to_array(self, byte_str):
        """
        Wandelt ein Byte-String-Literal oder bytes-Objekt in ein NumPy-Array um,
        das die Rohdaten als uint8 enthält. Ideal für Sensordatenverarbeitung.
        """
        # Falls byte_str ein Text ist, z. B. "b'\x00\x89...'"
        data = ast.literal_eval(byte_str)

        # In NumPy-Array umwandeln (1 Byte = 1 Element)
        arr = np.frombuffer(data, dtype=np.uint8)
        return arr


    def bytestring_to_bin(self, byte_str):
        """
        Wandelt ein Byte-String-Literal oder bytes-Objekt in ein NumPy-Array aus Bits (0/1) um.
        Ideal für die bitweise Analyse oder Dekodierung von Sensordaten.
        """
        # Falls byte_str ein Text ist, z. B. "b'\x00\x89...'"
        if isinstance(byte_str, str):
            data = ast.literal_eval(byte_str)
        else:
            data = byte_str

        # Bytes → NumPy-Array (uint8)
        byte_array = np.frombuffer(data, dtype=np.uint8)

        # Bytes → Bits (jedes Byte wird in 8 Bits zerlegt)
        bit_array = np.unpackbits(byte_array)

        self.logger.debug(f"Daten in bin Darstellung: {bit_array}")
        return bit_array