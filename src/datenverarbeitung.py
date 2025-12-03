from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any
import numpy as np
import csv
import os
from datetime import datetime

from logger import get_logger
from visualisierung import Visualisierung

# --- Interfaces & Strategies ---

class DataProcessor(ABC):
    """
    Abstrakte Basisklasse für alle Daten-Prozessoren.
    """
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> Any:
        """
        Verarbeitet die Rohdaten und gibt das Ergebnis zurück.
        """
        pass

class NMEAProcessor(DataProcessor):
    """
    Verarbeitet NMEA-Daten (z.B. Tiefenwerte).
    """
    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[float]:
        tiefen = []
        if not raw_data:
            return tiefen

        try:
            decoded_data = raw_data.decode("latin_1")
            lines = decoded_data.splitlines()

            for line in lines:
                if line.strip().startswith('$SDDBT'):
                    parts = line.strip().split(',')
                    if len(parts) > 4 and parts[4] == 'M':
                        try:
                            tiefen.append(float(parts[3]))
                        except (ValueError, IndexError):
                            self.logger.warning(f"Fehler beim Parsen des NMEA-Satzes: {line}")
            
            if tiefen:
                formatierte_tiefen = ", ".join([f"{t:.2f}m" for t in tiefen])
                self.logger.info(f"{len(tiefen)} Tiefenwerte geparst: [{formatierte_tiefen}]")
            else:
                self.logger.info("Keine gültigen Tiefenwerte ($SDDBT) in den NMEA-Daten gefunden.")

        except UnicodeDecodeError as e:
            self.logger.error(f"Fehler beim Dekodieren der NMEA-Daten: {e}")

        return tiefen

class EchogramProcessor(DataProcessor):
    """
    Verarbeitet Echogramm-Daten (ASCII) und kümmert sich optional um Visualisierung.
    """
    def __init__(self, visualisierung: Optional[Visualisierung] = None, plot: bool = False):
        super().__init__()
        self.visualisierung = visualisierung
        self.should_plot = plot

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[List[int]]:
        if not raw_data:
            return []

        echogram_str = raw_data.decode("latin_1")
        measurements = self._parse_echogram_string(echogram_str)

        if measurements:
            self.logger.info(f"{len(measurements)} Ping(s) mit insgesamt {sum(len(p) for p in measurements)} Datenpunkten geparst.")
            
            if self.should_plot and self.visualisierung:
                self._plot_measurements(measurements, mode_name, settings)
        else:
            self.logger.warning("Keine gültigen Datenblöcke im Echogramm gefunden.")

        return measurements

    def _parse_echogram_string(self, text: str) -> List[List[int]]:
        """Extrahiert Datenblöcke zwischen ##DataStart und ##DataEnd/#DeviceID."""
        start_marker = "##DataStart"
        end_marker_1 = "##DataEnd"
        end_marker_2 = "#DeviceID"

        alle_daten_bloecke = []
        current_pos = 0

        while True:
            start_index = text.find(start_marker, current_pos)
            if start_index == -1:
                break

            daten_start_index = start_index + len(start_marker)
            end_index_1 = text.find(end_marker_1, daten_start_index)
            end_index_2 = text.find(end_marker_2, daten_start_index)

            end_index = -1
            if end_index_1 != -1 and end_index_2 != -1:
                end_index = min(end_index_1, end_index_2)
            elif end_index_1 != -1:
                end_index = end_index_1
            elif end_index_2 != -1:
                end_index = end_index_2

            if end_index == -1:
                daten_block_text = text[daten_start_index:]
                current_pos = len(text)
            else:
                daten_block_text = text[daten_start_index:end_index]
                current_pos = end_index

            daten_punkte = [int(wert) for wert in daten_block_text.strip().split() if wert.strip().isdigit()]
            if daten_punkte:
                alle_daten_bloecke.append(daten_punkte)

            if end_index == -1:
                break

        return alle_daten_bloecke

    def _plot_measurements(self, measurements: List[List[int]], mode_name: str, settings: dict):
        self.logger.info(f"Erstelle Plots für {len(measurements)} Messungen...")
        current_settings = settings if settings else {}
        for i, block in enumerate(measurements):
            t_s, _, amps_norm = self._berechne_metadaten(block, current_settings)
            t_ms = t_s * 1000
            self.visualisierung.plotte_datenpunkte(
                t_ms,
                amps_norm,
                titel=f"Echogramm für Modus '{mode_name}'",
                block_index=i
            )

    def _berechne_metadaten(self, amplituden_block: List[int], settings: dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        raw_amps = np.array(amplituden_block)
        num_samples = len(raw_amps)

        if num_samples == 0:
            return np.array([]), np.array([]), np.array([])

        try:
            fs_val = settings.get("freqIdSamplFreq", {})
            fs = float(fs_val) if fs_val else 100000.0
        except (ValueError, TypeError):
            fs = 100000.0

        time_axis_s = np.arange(num_samples) / fs
        sound_speed = 1500.0
        dist_axis_m = (time_axis_s * sound_speed) / 2

        min_val = raw_amps.min()
        max_val = raw_amps.max()

        if max_val > min_val:
            amps_norm = (raw_amps - min_val) / (max_val - min_val)
        else:
            amps_norm = np.zeros_like(raw_amps, dtype=float)

        return time_axis_s, dist_axis_m, amps_norm

class BinaryProcessor(DataProcessor):
    """
    Verarbeitet Binärdaten (Placeholder für zukünftige Implementierung).
    """
    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> dict:
        hex_repr = raw_data.hex(' ')
        self.logger.info(f"Binärdaten empfangen ({len(raw_data)} Bytes). Hex: {hex_repr[:50]}...")
        
        # Hier könnte die parse_12_bit_binary_data Logik rein
        return {"raw_hex": hex_repr}

# --- Main Class ---

class Datenverarbeitung:
    """
    Hauptklasse, die als Dispatcher fungiert und die passenden Processors aufruft.
    """

    def __init__(self, run_dir: str):
        self.logger = get_logger(__name__)
        self.run_dir = run_dir
        self.visualisierung = Visualisierung(self.run_dir)
        
        # Registrierung der Strategien
        self.processors = {
            "nmea": NMEAProcessor(),
            "echogram": EchogramProcessor(self.visualisierung, plot=False),
            "echogram_plotted": EchogramProcessor(self.visualisierung, plot=True),
            "binary": BinaryProcessor()
        }

    def verarbeite_daten(self, data_type: str, sensor_daten: Optional[bytes], mode_name: str, settings: Optional[dict] = None) -> Any:
        """
        Delegiert die Verarbeitung an den passenden Processor.
        """
        if not sensor_daten:
            self.logger.warning(f"Keine Daten für Modus '{mode_name}' empfangen.")
            return None

        processor = self.processors.get(data_type)
        if not processor:
            self.logger.error(f"Unbekannter Datentyp '{data_type}'.")
            return None

        self.logger.info(f"Verarbeite Daten für Modus '{mode_name}' mit Processor '{processor.__class__.__name__}'...")
        return processor.process(sensor_daten, mode_name, settings or {})

    def append_ping_to_csv(self, daten_bloecke: List[List[int]], settings: dict, filename: str = "training_data.csv"):
        """
        Hängt den ersten Datenblock (Ping) an eine CSV-Datei an.
        """
        if not daten_bloecke:
            self.logger.warning("Keine Datenblöcke zum Schreiben in CSV vorhanden.")
            return
            
        # Wenn daten_bloecke kein List[List[int]] ist (z.B. bei NMEA), abbrechen
        if not isinstance(daten_bloecke, list) or not daten_bloecke or not isinstance(daten_bloecke[0], list):
             self.logger.debug("Datenformat nicht geeignet für CSV-Export (erwarte List[List[int]]).")
             return

        daten_block = daten_bloecke[0]
        filepath = os.path.join(self.run_dir, filename)
        file_exists = os.path.exists(filepath)

        header = [
            "Timestamp", "class_name", "Frequency", "NMEA_Depth_m",
            "PulseLength_us", "Sampling_Freq_Hz"
        ]
        header.extend([f"S_{i}" for i in range(len(daten_block))])

        row_data = [
            datetime.now().isoformat(),
            settings.get("class_name"),
            settings.get("frequency"),
            "Platzhalter: NMEA_Depth_m",
            settings.get("IdTxLength"),
            settings.get("IdSamplFreq")
        ]
        row_data.extend(daten_block)

        try:
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=";")
                if not file_exists:
                    writer.writerow(header)
                writer.writerow(row_data)
            self.logger.info(f"Daten erfolgreich in '{filepath}' geschrieben.")
        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der CSV-Datei '{filepath}': {e}")
