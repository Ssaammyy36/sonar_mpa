from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any
import numpy as np
import csv
import os
from datetime import datetime
import config

from logger import get_logger
from logger import get_logger
from data_types import Measurement, EchogramMeasurement, NMEAMeasurement, BinaryMeasurement

# --- Interfaces & Strategies ---

class DataProcessor(ABC):
    """Abstrakte Basisklasse für alle Daten-Prozessoren."""
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[Measurement]:
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

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[NMEAMeasurement]:
        measurements = []
        if not raw_data:
            return measurements

        try:
            decoded_data = self._convert(raw_data)

            lines = decoded_data.splitlines()
            for line in lines:
                if line.strip().startswith('$SDDBT'):
                    parts = line.strip().split(',')
                    if len(parts) > 4 and parts[4] == 'M':
                        try:
                            depth = float(parts[3])
                            measurements.append(NMEAMeasurement(
                                timestamp=datetime.now(),
                                raw_data=raw_data,
                                depth_meters=depth
                            ))
                        except (ValueError, IndexError):
                            self.logger.warning(f"Fehler beim Parsen des NMEA-Satzes: {line}")
            
            if measurements:
                formatierte_tiefen = ", ".join([f"{m.depth_meters:.2f}m" for m in measurements])
                self.logger.info(f"{len(measurements)} Tiefenwerte geparst: [{formatierte_tiefen}]")
            else:
                self.logger.info("Keine gültigen Tiefenwerte ($SDDBT) in den NMEA-Daten gefunden.")

        except UnicodeDecodeError as e:
            self.logger.error(f"Fehler beim Dekodieren der NMEA-Daten: {e}")

        return measurements

class EchogramProcessor(DataProcessor):
    """Verarbeitet Echogramm-Daten (ASCII)."""
    """Verarbeitet Echogramm-Daten (ASCII)."""
    def __init__(self):
        super().__init__()

    def _convert(self, raw_data: bytes) -> str:
        return raw_data.decode("latin_1")

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[EchogramMeasurement]:
        if not raw_data:
            return []

        echogram_str = self._convert(raw_data)
        packets = self._extract_packets(echogram_str)
        
        measurements = []
        for packet in packets:
            header = self._extract_header(packet)
            data = self._extract_data(packet)
            if data:
                measurements.append(EchogramMeasurement(
                    timestamp=datetime.now(),
                    raw_data=raw_data, # Hier könnte man theoretisch das spezifische Paket-Byte speichern
                    header=header,
                    data_points=data
                ))

        if measurements:
            self.logger.info(f"{len(measurements)} Ping(s) mit insgesamt {sum(len(m.data_points) for m in measurements)} Datenpunkten geparst.")
            
            self.logger.info(f"{len(measurements)} Ping(s) mit insgesamt {sum(len(m.data_points) for m in measurements)} Datenpunkten geparst.")
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

        #self.logger.debug(f"Header extrahiert: {header_text}")
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

        #self.logger.debug(f"Datenpunkte geparst: {data_text}")    
        # Kommas durch Leerzeichen ersetzen, falls die Daten kommagetrennt sind
        cleaned_text = data_text.replace(',', ' ')
        
        daten_punkte = []
        for wert in cleaned_text.split():
            wert = wert.strip()
            if wert.isdigit():
                daten_punkte.append(int(wert))
        
        self.logger.debug(f"Datenpunkte geparst: {daten_punkte}")
        return daten_punkte

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



class BinaryProcessor(DataProcessor):
    """
    Verarbeitet Binärdaten (Placeholder für zukünftige Implementierung).
    """
    def _convert(self, raw_data: bytes) -> str:
        return raw_data.hex(' ')

    def process(self, raw_data: bytes, mode_name: str, settings: dict) -> List[BinaryMeasurement]:
        hex_repr = self._convert(raw_data)
        self.logger.info(f"Binärdaten empfangen ({len(raw_data)} Bytes). Hex: {hex_repr[:50]}...")
        
        # Hier könnte die parse_12_bit_binary_data Logik rein
        return [BinaryMeasurement(
            timestamp=datetime.now(),
            raw_data=raw_data,
            hex_content=hex_repr
        )]

# --- Main Class ---

class Datenverarbeitung:
    """
    Hauptklasse, die als Dispatcher fungiert und die passenden Processors aufruft.
    """

    def __init__(self, run_dir: str):
        self.logger = get_logger(__name__)
        self.run_dir = run_dir
        
        # Registrierung der Strategien
        self.processors = {
            "nmea": NMEAProcessor(),
            "echogram": EchogramProcessor(),
            "binary": BinaryProcessor()
        }

    def verarbeite_daten(self, data_type: str, sensor_daten: Optional[bytes], mode_name: str, settings: Optional[dict] = None) -> List[Measurement]:
        """
        Delegiert die Verarbeitung an den passenden Processor.
        """
        if not sensor_daten:
            self.logger.warning(f"Keine Daten für Modus '{mode_name}' empfangen.")
            return []

        processor = self.processors.get(data_type)
        if not processor:
            self.logger.error(f"Unbekannter Datentyp '{data_type}'.")
            return None

        self.logger.info(f"Verarbeite Daten für Modus '{mode_name}' mit Processor '{processor.__class__.__name__}'...")
        return processor.process(sensor_daten, mode_name, settings or {})

    def append_ping_to_csv(self, data_packages: List[Measurement], settings: dict, filename: str = "training_data.csv"):
        """
        Hängt den ersten Datenblock (Ping) an eine CSV-Datei an.
        """
        if not data_packages:
            self.logger.warning("Keine Datenblöcke zum Schreiben in CSV vorhanden.")
            return
            
        # Wir nehmen den ersten Ping aus dem Paket (falls mehrere drin sind)
        # TODO: Iteration über alle Pings im Paket?
        measurement = data_packages[0]
        
        daten_block = []
        header_data = {}
        nmea_depth = "NaN"

        if isinstance(measurement, EchogramMeasurement):
            header_data = measurement.header
            daten_block = measurement.data_points
            # Versuche Tiefe aus Header zu lesen
            nmea_depth = header_data.get("Depth", header_data.get("Tiefe", header_data.get("Altitude", "NaN")))
        elif isinstance(measurement, NMEAMeasurement):
            nmea_depth = measurement.depth_meters
            # NMEA hat keine Echogramm-Datenpunkte
            daten_block = [] 
        else:
             self.logger.debug(f"Datenformat nicht geeignet für CSV-Export: {type(measurement)}")
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
