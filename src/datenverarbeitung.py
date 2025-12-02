from logger import get_logger
from typing import List, Optional
import matplotlib.pyplot as plt
import ast
import csv
import numpy as np
import os
from datetime import datetime
from typing import Tuple, List, Optional
from visualisierung import Visualisierung

np.set_printoptions(threshold=np.inf)


class Datenverarbeitung:
    """
    Verarbeitet die empfangenen Sonar-Daten.

    Attributes:
        logger: Das Logging-Objekt für diese Klasse.
        run_dir: Das Verzeichnis für den aktuellen Programmlauf.
    """

    def __init__(self, run_dir: str):
        """
        Initialisiert ein neues Datenverarbeitungs-Objekt.

        Args:
            run_dir (str): Das Verzeichnis für diesen Programmlauf, in dem Logs und Plots gespeichert werden.
        """
        self.logger = get_logger(__name__)
        self.run_dir = run_dir
        self.visualisierung = Visualisierung(self.run_dir)

    def verarbeite_daten(self, data_type: str, sensor_daten: Optional[bytes], mode_name: str, settings: Optional[dict] = None) -> List[List[int]]:
        """
        Zentrale Methode zur Verarbeitung von Sensordaten basierend auf dem Datentyp.
        """
        if not sensor_daten:
            self.logger.warning(
                f"Keine Daten für Modus '{mode_name}' empfangen.")
            return

        self.logger.info(
            f"Verarbeite Daten für Modus '{mode_name}' mit Datentyp '{data_type}'...")

        if data_type == "nmea":
            tiefen = self.parse_nmea_tiefe(sensor_daten)
            if tiefen:
                formatierte_tiefen = ", ".join([f"{t:.2f}m" for t in tiefen])
                self.logger.info(
                    f"{len(tiefen)} Tiefenwerte geparst: [{formatierte_tiefen}]")
            else:
                self.logger.info(
                    "Keine gültigen Tiefenwerte ($SDDBT) in den NMEA-Daten gefunden.")

        elif data_type in ("echogram", "echogram_plotted"):
            echogram_str = sensor_daten.decode("latin_1")
            measurements = self.pars_data_form_echogram(echogram_str)
            if measurements:
                self.logger.info(
                    f"{len(measurements)} Ping(s) mit insgesamt {sum(len(p) for p in measurements)} Datenpunkten geparst.")
                if data_type == "echogram_plotted":
                    self.logger.info(
                        f"Erstelle und speichere {len(measurements)} Plot(s) im Ordner '{self.run_dir}'...")
                    current_settings = settings if settings else {}
                    for i, block in enumerate(measurements):
                        t_s, _, amps_norm = self.berechne_metadaten(
                            block, current_settings)
                        t_ms = t_s * 1000
                        self.visualisierung.plotte_datenpunkte(
                            t_ms,
                            amps_norm,
                            titel=f"Echogramm für Modus '{mode_name}'",
                            block_index=i
                        )
                return measurements
            else:
                self.logger.warning(
                    "Keine gültigen Datenblöcke im Echogramm gefunden.")

        elif data_type == "binary":
            hex_repr = sensor_daten.hex(' ')
            self.logger.info(
                f"Binärdaten empfangen ({len(sensor_daten)} Bytes). Hex-Darstellung: {hex_repr[:90]}...")
            # Hier könnte die spezifische Binär-Verarbeitung (z.B. parse_12_bit_binary_data) aufgerufen werden.
            # Aktuell wird nur die Hex-Repräsentation geloggt.
            self.logger.info(
                "Binär-Verarbeitung ist noch nicht vollständig implementiert.")

        else:
            self.logger.error(
                f"Unbekannter Datentyp '{data_type}'. Daten können nicht verarbeitet werden.")

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
                current_pos = len(text)  # beende die Schleife
            else:
                daten_block_text = text[daten_start_index:end_index]
                current_pos = end_index

            daten_punkte = [int(wert) for wert in daten_block_text.strip(
            ).split() if wert.strip().isdigit()]
            if daten_punkte:
                alle_daten_bloecke.append(daten_punkte)

            if end_index == -1:
                break

        if not alle_daten_bloecke:
            self.logger.warning(
                f"Keine gültigen Datenblöcke mit '{start_marker}' im Text gefunden.")
        else:
            self.logger.info(
                f"{len(alle_daten_bloecke)} Datenpakete gefunden und geparst.")

        return alle_daten_bloecke

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

    def berechne_metadaten(self, amplituden_block: List[int], settings: Optional[dict] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Berechnet Zeit- und Distanzachsen basierend auf den Settings.

        Args:
            amplituden_block: Liste der gemessenen Intensitäten.
            settings: Das Dictionary mit den Parametern (z.B. 'IdSamplFreq').

        Returns:
            t_s (np.array): Zeitachse in Sekunden
            d_m (np.array): Distanzachse in Metern
            amps (np.array): Die Intensitäten als Numpy-Array
        """
        # 1. Daten in Numpy-Array wandeln
        raw_amps = np.array(amplituden_block)
        num_samples = len(raw_amps)

        if num_samples == 0:
            return np.array([]), np.array([]), np.array([])

        # 2. Sampling-Rate aus Settings holen (String -> Float Konvertierung!)
        # Default auf 100kHz, falls Schlüsselfehler oder leer
        try:
            fs_val = settings.get("freqIdSamplFreq", {})
            fs = float(fs_val) if fs_val else 100000.0
        except (ValueError, TypeError):
            self.logger.warning(
                "Konnte IdSamplFreq nicht lesen, nutze Default 100kHz")
            fs = 100000.0

        # 3. Zeitachse berechnen (Sekunden)
        time_axis_s = np.arange(num_samples) / fs

        # 4. Distanzachse berechnen (Meter, Hin-und-Zurück / 2)
        sound_speed = 1500.0  # m/s
        dist_axis_m = (time_axis_s * sound_speed) / 2

        # 5. Normierung (Min-Max)
        # Verhindert Division durch Null, falls alle Werte gleich sind (z.B. Sensor sieht schwarz)
        min_val = raw_amps.min()
        max_val = raw_amps.max()

        if max_val > min_val:
            amps_norm = (raw_amps - min_val) / (max_val - min_val)
        else:
            # Oder raw_amps / max_val, je nach Wunsch
            amps_norm = np.zeros_like(raw_amps, dtype=float)

        return time_axis_s, dist_axis_m, amps_norm

    def append_ping_to_csv(self, daten_bloecke: List[List[int]], class_name: str, settings: dict, filename: str = "training_data.csv"):
        """
        Hängt den ersten Datenblock (Ping) aus einer Liste zusammen mit Metadaten an eine CSV-Datei im Run-Verzeichnis an.
        Diese Funktion ist für das Erstellen von Trainingsdaten für Machine Learning gedacht.
        Wenn die Datei nicht existiert, wird sie mit einem Header erstellt.

        Args:
            daten_bloecke (List[List[int]]): Eine Liste von Datenblöcken. Nur der erste Block wird verwendet.
            class_name (str): Die Klassifizierung des Untergrunds (z.B. "Sand", "Schlamm").
            settings (dict): Ein Dictionary mit den Sensor-Metadaten.
            filename (str, optional): Der Dateiname. Standardmäßig "training_data.csv".
        """
        if not daten_bloecke:
            self.logger.warning("Keine Datenblöcke zum Schreiben in CSV vorhanden.")
            return

        daten_block = daten_bloecke[0]
        self.logger.info(f"Füge ersten Ping-Datenblock zur CSV-Datei '{filename}' im Verzeichnis '{self.run_dir}' hinzu...")

        filepath = os.path.join(self.run_dir, filename)
        file_exists = os.path.exists(filepath)

        # Spaltennamen definieren
        header = [
            "Timestamp", "Label", "Frequency", "NMEA_Depth_m",
            "PulseLength_us", "Sampling_Freq_Hz"
        ]
        # Dynamische Spalten für die Samples hinzufügen
        header.extend([f"S_{i}" for i in range(len(daten_block))])

        # Datenzeile vorbereiten
        row_data = [
            datetime.now().isoformat(),
            class_name,
            "Platzhalter: Frequenz",
            "Platzhalter: Altitude",
            # settings.get("frequency_name", ""),
            # settings.get("nmea_depth", ""),
            settings.get("IdTxLength", ""),
            settings.get("IdSamplFreq", "")
        ]
        row_data.extend(daten_block)

        try:
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=";")
                # Header schreiben, wenn die Datei neu ist
                if not file_exists:
                    writer.writerow(header)
                # Datenzeile schreiben
                writer.writerow(row_data)
            self.logger.info(f"Daten erfolgreich in '{filepath}' geschrieben.")
        except IOError as e:
            self.logger.error(
                f"Fehler beim Schreiben der CSV-Datei '{filepath}': {e}")
