from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class TestSzenario:
    """Definiert ein geplantes Testszenario."""
    mode_id: str
    class_name: str
    frequency: str = "low"

@dataclass
class Measurement:
    """Basisklasse für alle Messungen."""
    timestamp: datetime
    raw_data: bytes
    
@dataclass
class EchogramMeasurement(Measurement):
    """Spezifische Messung für Echogramm-Daten."""
    header: Dict[str, str]
    data_points: List[int]

@dataclass
class NMEAMeasurement(Measurement):
    """Spezifische Messung für NMEA-Tiefendaten."""
    depth_meters: float

@dataclass
class BinaryMeasurement(Measurement):
    """Spezifische Messung für Binärdaten."""
    hex_content: str
