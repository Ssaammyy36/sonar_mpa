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
    """Abstrakte Basisklasse für alle Daten-Prozessoren."""
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> Any:
        """Verarbeitet die Rohdaten und gibt das Ergebnis zurück."""
        pass

    @abstractmethod
    def _convert(self, raw_data: bytes) -> Any:
        """Konvertiert die Rohdaten in ein verarbeitbares Format."""
        pass

class NMEAProcessor(DataProcessor):
    """
    Verarbeitet NMEA-Daten (z.B. Tiefenwerte).
    """
    def _convert(self, raw_data: bytes) -> str:
        return raw_data.decode("latin_1")

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[float]:
        tiefen = []
        if not raw_data:
            return tiefen

        try:
            decoded_data = self._convert(raw_data)

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
    """Verarbeitet Echogramm-Daten (ASCII)."""
    def __init__(self, visualisierung: Optional[Visualisierung] = None, plot: bool = False):
        super().__init__()
        self.visualisierung = visualisierung
        self.should_plot = plot

    def _convert(self, raw_data: bytes) -> str:
        return raw_data.decode("latin_1")

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[Tuple[dict, List[int]]]:
        if not raw_data:
            return []

        echogram_str = self._convert(raw_data)
        packets = self._extract_packets(echogram_str)
        
        measurements = []
        for packet in packets:
            header = self._extract_header(packet)
            data = self._extract_data(packet)
            if data:
                measurements.append((header, data))

        if measurements:
            self.logger.info(f"{len(measurements)} Ping(s) mit insgesamt {sum(len(p[1]) for p in measurements)} Datenpunkten geparst.")
            
            if self.should_plot and self.visualisierung:
                self._plot_measurements(measurements, mode_name, settings)
        else:
            self.logger.warning("Keine gültigen Datenblöcke im Echogramm gefunden.")

        return measurements

    def _extract_packets(self, text: str) -> List[str]:
        """
        Zerlegt den Text in einzelne Pakete.
        Start: #DeviceID (oder DeviceID am Anfang)
        Ende: ##DataEnd ODER nächstes #DeviceID
        """
        packets = []
        start_marker = "#DeviceID"
        end_marker_data = "##DataEnd"
        
        current_pos = 0
        while True:
            start_index = text.find(start_marker, current_pos)
            
            # Fallback: Wenn der Text mit "DeviceID" beginnt (ohne #), ist das der Start des ersten Pakets
            if current_pos == 0 and start_index != 0 and text.startswith("DeviceID"):
                start_index = 0
            
            if start_index == -1:
                break
            
            # Suche nach dem nächsten Start-Marker (Beginn des nächsten Pakets)
            next_start_index = text.find(start_marker, start_index + len(start_marker))
            
            # Suche nach dem DataEnd-Marker
            data_end_index = text.find(end_marker_data, start_index)
            
            end_index = -1
            
            # Bestimme das Ende des aktuellen Pakets
            if data_end_index != -1:
                # Wenn ##DataEnd gefunden wurde, prüfen wir, ob es zum aktuellen Paket gehört
                # (d.h. es kommt VOR dem nächsten #DeviceID)
                if next_start_index == -1 or data_end_index < next_start_index:
                    end_index = data_end_index + len(end_marker_data)
                else:
                    end_index = next_start_index
            elif next_start_index != -1:
                end_index = next_start_index
            else:
                end_index = len(text)
                
            packet = text[start_index:end_index]
            
            # Repariere fehlendes # am Anfang, damit der Header-Parser funktioniert
            if not packet.startswith("#"):
                packet = "#" + packet
                
            packets.append(packet)
            
            current_pos = end_index
            # Wenn wir am Ende des Textes sind, abbrechen
            if current_pos >= len(text):
                break
        self.logger.debug(f"Pakete extrahiert: {len(packets)}")        
        return packets

    def _extract_header(self, packet: str) -> dict:
        """Extrahiert den Header-Teil (von #DeviceID bis ##DataStart)."""
        end_marker = "##DataStart"
        end_index = packet.find(end_marker)
        
        if end_index == -1:
            header_text = packet
        else:
            header_text = packet[:end_index]

        self.logger.debug(f"Header extrahiert: {header_text}")
        return self._parse_header_section(header_text)

    def _extract_data(self, packet: str) -> List[int]:
        """Extrahiert die Daten (nach ##DataStart bis Ende/##DataEnd)."""
        start_marker = "##DataStart"
        start_index = packet.find(start_marker)
        
        if start_index == -1:
            return []
            
        data_text = packet[start_index + len(start_marker):]
        
        # Falls ##DataEnd im String enthalten ist, schneiden wir es ab
        # (obwohl _extract_packets es ggf. schon inkludiert hat, wollen wir nur die Zahlen)
        end_marker = "##DataEnd"
        end_index = data_text.find(end_marker)
        if end_index != -1:
            data_text = data_text[:end_index]

        self.logger.debug(f"Datenpunkte geparst: {data_text}")    
        return [int(wert) for wert in data_text.strip().split() if wert.strip().isdigit()]

    def _parse_header_section(self, text: str) -> dict:
        """Parst Zeilen, die mit '#' beginnen, in ein Dictionary."""
        header = {}
        for line in text.splitlines():
            line = line.strip()
            # Ignoriere Marker wie ##DataStart und Trennlinien wie #---------------
            if line.startswith("#") and not line.startswith("##") and not line.startswith("#-"): 
                content = line[1:].strip()
                
                key = None
                val = None
                
                if ':' in content:
                    key, val = content.split(':', 1)
                elif '=' in content:
                    key, val = content.split('=', 1)
                else:
                    # Versuche Split am ersten Whitespace (für Format "#Key Value")
                    parts = content.split(None, 1)
                    if len(parts) == 2:
                        key, val = parts
                
                if key and val:
                    header[key.strip()] = val.strip()
                    
        self.logger.debug(f"Header geparst: {header}")
        return header

    def _plot_measurements(self, measurements: List[Tuple[dict, List[int]]], mode_name: str, settings: dict):
        self.logger.info(f"Erstelle Plots für {len(measurements)} Messungen...")
        current_settings = settings if settings else {}
        for i, (header, block) in enumerate(measurements):
            t_s, _, amps_norm = self._berechne_metadaten(block, current_settings)
            t_ms = t_s * 1000
            
            titel_suffix = ""
            if "Depth" in header:
                titel_suffix = f" (Tiefe: {header['Depth']})"
            
            self.visualisierung.plotte_datenpunkte(
                t_ms,
                amps_norm,
                titel=f"Echogramm für Modus '{mode_name}'{titel_suffix}",
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
    def _convert(self, raw_data: bytes) -> str:
        return raw_data.hex(' ')

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> dict:
        hex_repr = self._convert(raw_data)
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

    def append_ping_to_csv(self, daten_bloecke: Any, settings: dict, filename: str = "training_data.csv"):
        """
        Hängt den ersten Datenblock (Ping) an eine CSV-Datei an.
        Akzeptiert jetzt auch Tupel (Header, Daten) vom EchogramProcessor.
        """
        if not daten_bloecke:
            self.logger.warning("Keine Datenblöcke zum Schreiben in CSV vorhanden.")
            return
            
        # Extrahiere Daten und Header
        daten_block = []
        header_data = {}

        # Fall 1: EchogramProcessor liefert [(header, data), ...]
        if isinstance(daten_bloecke, list) and daten_bloecke and isinstance(daten_bloecke[0], tuple):
            header_data, daten_block = daten_bloecke[0]
        # Fall 2: Legacy/Anderer Processor liefert [data, ...]
        elif isinstance(daten_bloecke, list) and daten_bloecke and isinstance(daten_bloecke[0], list):
            daten_block = daten_bloecke[0]
        else:
             self.logger.debug(f"Datenformat nicht geeignet für CSV-Export: {type(daten_bloecke)}")
             return

        filepath = os.path.join(self.run_dir, filename)
        file_exists = os.path.exists(filepath)

        header = [
            "Timestamp", "class_name", "Frequency", "NMEA_Depth_m",
            "PulseLength_us", "Sampling_Freq_Hz"
        ]
        header.extend([f"S_{i}" for i in range(len(daten_block))])

        # Versuche Tiefe aus Header zu lesen (Keys könnten variieren, z.B. "Depth", "Tiefe", "Altitude")
        nmea_depth = header_data.get("Depth", header_data.get("Tiefe", header_data.get("Altitude", "NaN")))

        row_data = [
            datetime.now().isoformat(),
            settings.get("class_name"),
            settings.get("frequency"),
            nmea_depth, # Hier wird der Wert aus dem Header eingetragen
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
