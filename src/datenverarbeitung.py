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
            self.logger.debug(f"Typ der Daten: {type(bin_data)}")
            self.logger.debug("Parsing 12-bit binary data...")
            bit_arr = self.bytestring_to_bitarray(bin_data)

            # For further processing, we need the byte array
            byte_arr = np.packbits(bit_arr)

            # Decode using 'latin-1' which maps each byte to a character without errors.
            # This will produce a string, but it might not be human-readable if the data is not text.
            # It helps to visualize the raw byte values as characters.
            message["magic"] = byte_arr[0:8].tobytes().decode('latin-1')
            message["packet_id"] = byte_arr[8:10].tobytes().decode('latin-1')

            length_bytes = byte_arr[10:14].tobytes()
            message["length"] = int.from_bytes(
                length_bytes, 'little', signed=False)
            self.logger.debug(message)

        except (ValueError, UnicodeDecodeError) as e:
            self.logger.error(f"Fehler beim Parsen der Binärdaten: {e}")

        return message

    def bytestring_to_bitarray(self, byte_str):
        """
        Wandelt einen Bytestring in ein NumPy-Array von Bits (0en und 1en) um.
        Die Bits werden für die Log-Ausgabe in 8er-Paare gruppiert.
        """
        # Falls byte_str ein Text ist, z. B. "b'\x00\x89...'"
        if isinstance(byte_str, str):
            data = ast.literal_eval(byte_str)
        else:
            data = byte_str

        # In NumPy-Array umwandeln (1 Byte = 1 Element)
        byte_arr = np.frombuffer(data, dtype=np.uint8)

        # Bytes → Bits (jedes Byte wird in 8 Bits zerlegt)
        bit_arr = np.unpackbits(byte_arr)

        # Log the bits in 8er-Paare for display purposes
        self.logger.debug(f"Daten in Bit-Darstellung (gruppiert): {bit_arr.reshape(-1, 8)}")
        
        return bit_arr
