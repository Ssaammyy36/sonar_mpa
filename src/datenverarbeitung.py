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

    def verarbeite_daten(self, data_type: str, sensor_daten: Optional[bytes], mode_name: str):
        """
        Zentrale Methode zur Verarbeitung von Sensordaten basierend auf dem Datentyp.
        """
        if not sensor_daten:
            self.logger.warning(f"Keine Daten für Modus '{mode_name}' empfangen.")
            return

        self.logger.info(f"Verarbeite Daten für Modus '{mode_name}' mit Datentyp '{data_type}'...")

        if data_type == "nmea":
            tiefen = self.parse_nmea_tiefe(sensor_daten)
            if tiefen:
                formatierte_tiefen = ", ".join([f"{t:.2f}m" for t in tiefen])
                self.logger.info(f"{len(tiefen)} Tiefenwerte geparst: [{formatierte_tiefen}]")
            else:
                self.logger.info("Keine gültigen Tiefenwerte ($SDDBT) in den NMEA-Daten gefunden.")

        elif data_type in ("echogram", "echogram_plotted"):
            echogram_str = sensor_daten.decode("latin_1")
            measurements = self.pars_data_form_echogram(echogram_str)
            if measurements:
                self.logger.info(f"{len(measurements)} Ping(s) mit insgesamt {sum(len(p) for p in measurements)} Datenpunkten geparst.")
                if data_type == "echogram_plotted":
                    self.plotte_datenpunkte(measurements, titel=f"Echogramm für Modus '{mode_name}'")
            else:
                self.logger.warning("Keine gültigen Datenblöcke im Echogramm gefunden.")

        elif data_type == "binary":
            hex_repr = sensor_daten.hex(' ')
            self.logger.info(f"Binärdaten empfangen ({len(sensor_daten)} Bytes). Hex-Darstellung: {hex_repr[:90]}...")
            # Hier könnte die spezifische Binär-Verarbeitung (z.B. parse_12_bit_binary_data) aufgerufen werden.
            # Aktuell wird nur die Hex-Repräsentation geloggt.
            self.logger.info("Binär-Verarbeitung ist noch nicht vollständig implementiert.")

        else:
            self.logger.error(f"Unbekannter Datentyp '{data_type}'. Daten können nicht verarbeitet werden.")

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
    
    def pars_data_form_echogram(self, text: str) -> List[List[int]]:
        """
        Extrahiert alle Datenblöcke, die mit '##DataStart' beginnen.
        Ein Datenblock endet entweder mit '##DataEnd' oder vor dem nächsten '#DeviceID'.
        Gibt eine Liste von Listen zurück, wobei jede innere Liste einen Datenblock darstellt.
        """
        start_marker = "##DataStart"
        end_marker_1 = "##DataEnd"
        end_marker_2 = "#DeviceID"
        
        alle_daten_bloecke = []
        current_pos = 0
        
        while True:
            # Finde die Startposition des nächsten Pakets
            start_index = text.find(start_marker, current_pos)
            if start_index == -1:
                # Kein weiteres Paket gefunden
                break

            daten_start_index = start_index + len(start_marker)

            # Finde die Position des nächsten End-Markers
            end_index_1 = text.find(end_marker_1, daten_start_index)
            end_index_2 = text.find(end_marker_2, daten_start_index)

            # Wähle den frühesten End-Marker
            end_index = -1
            if end_index_1 != -1 and end_index_2 != -1:
                end_index = min(end_index_1, end_index_2)
            elif end_index_1 != -1:
                end_index = end_index_1
            elif end_index_2 != -1:
                end_index = end_index_2
            
            daten_block_text = ""
            if end_index == -1:
                # Keiner der End-Marker gefunden, nimm den Rest des Textes
                daten_block_text = text[daten_start_index:]
                current_pos = len(text) # beende die Schleife
            else:
                daten_block_text = text[daten_start_index:end_index]
                current_pos = end_index

            daten_punkte = [int(wert) for wert in daten_block_text.strip().split() if wert.strip().isdigit()]
            if daten_punkte:
                alle_daten_bloecke.append(daten_punkte)
            
            if end_index == -1:
                break

        if not alle_daten_bloecke:
            self.logger.warning(f"Keine gültigen Datenblöcke mit '{start_marker}' im Text gefunden.")
        else:
            self.logger.info(f"{len(alle_daten_bloecke)} Datenpakete gefunden und geparst.")

        return alle_daten_bloecke
    
    def plotte_datenpunkte(self, daten_bloecke: List[List[int]], titel: str = "Echogramm-Daten"):
        """
        Erstellt und zeigt ein Liniendiagramm für alle Amplituden aus allen Datenblöcken.
        Alle Datenpunkte werden zu einer einzigen Linie zusammengefügt.
        """
        
        if not daten_bloecke:
            self.logger.warning("Keine Datenpunkte zum Plotten vorhanden.")
            return

        self.logger.info(f"Erstelle Plot für {len(daten_bloecke)} Datenblock/Blöcke...")

        # Füge alle Datenpunkte aus allen Blöcken zu einer einzigen Liste zusammen
        alle_amplituden = [punkt for block in daten_bloecke for punkt in block]

        # Erstellt eine neue Figur (das Fenster) und eine Achse (das Diagramm darin)
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plottet alle Amplituden als eine einzige Linie
        ax.plot(alle_amplituden, label='Alle Amplituden')

        # Fügt Titel und Beschriftungen hinzu
        ax.set_title(titel)
        ax.set_xlabel("Datenpunkt-Index (über alle Pings)")
        ax.set_ylabel("Intensität (Rohwert)")
        ax.grid(True)
        ax.legend()

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
