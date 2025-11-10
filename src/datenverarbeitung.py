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
    
    def pars_data_form_echogram(self, text: str) -> list[int]:
        """
        Extrahiert den ersten Datenblock, der nach '##DataStart' beginnt.
        Der Block endet entweder bei '##DataEnd' oder am Ende des Strings.
        """
        start_marker = "##DataStart"
        end_marker = "##DataEnd"
        
        # Finde die Startposition nach dem Start-Marker
        start_index = text.find(start_marker)
        if start_index == -1:
            print("Start-Marker wurde nicht gefunden")
            return []

        # Die eigentlichen Daten beginnen nach dem Marker
        daten_start_index = start_index + len(start_marker)

        # Suche nach dem End-Marker, aber erst *nachdem* der Start-Marker kam
        end_index = text.find(end_marker, daten_start_index)

        if end_index == -1:
            # Kein End-Marker gefunden: Nimm alles ab dem Start-Marker bis zum Ende
            daten_block_text = text[daten_start_index:]
        else:
            # End-Marker gefunden: Nimm den Teil dazwischen
            daten_block_text = text[daten_start_index:end_index]
            
        # Bereinige den Block und extrahiere die Zahlen
        daten_punkte = [int(wert) for wert in daten_block_text.strip().split() if wert.strip().isdigit()]
        return daten_punkte
    
    def plotte_datenpunkte(self, datenpunkte: List[int], titel: str = "Echogramm-Daten"):
        """Erstellt und zeigt ein Liniendiagramm für eine Liste von Datenpunkten."""
        
        if not datenpunkte:
            self.logger.warning("Keine Datenpunkte zum Plotten vorhanden.")
            return

        self.logger.info(f"Erstelle Plot für {len(datenpunkte)} Datenpunkte...")

        # Erstellt eine neue Figur (das Fenster) und eine Achse (das Diagramm darin)
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plottet die Datenpunkte auf der Achse
        ax.plot(datenpunkte)

        # Fügt Titel und Beschriftungen hinzu, um das Diagramm verständlich zu machen
        ax.set_title(titel)
        ax.set_xlabel("Datenpunkt-Index")
        ax.set_ylabel("Intensität (Rohwert)")
        ax.grid(True)  # Fügt ein Gitter für bessere Lesbarkeit hinzu

        # Passt das Layout an und zeigt das Plot-Fenster an
        plt.tight_layout()
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
            message["length"] = int.from_bytes(length_bytes, 'little', signed=False)

            
            self.logger.debug(message)

        except (ValueError, UnicodeDecodeError) as e:
            self.logger.error(f"Fehler beim Parsen der Binärdaten: {e}")

        return message
