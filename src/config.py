# Allgemeine serielle Einstellungen
COMPORT: str = "COM5"
BAUDRATE: int = 115200

# Definitionen der verfügbaren Frequenzen, inklusive der zugehörigen Hardware-Befehle
FREQUENCIES = {
    "low": {
        "name": "50kHz",
        "command": "IdSetLowFreq"
    },
    "high": {
        "name": "200kHz",
        "command": "IdSetHighFreq"
    }
}

# Strukturierte Definition aller verfügbaren Sonar-Modi
# Dies ermöglicht es der Steuerungs-Klasse, die Details eines Modus nachzuschlagen,
# anstatt sie in if/else-Blöcken hart zu kodieren.
MODES = {
    "2": {
        "name": "10bit-Echogram",
        "output_mode_id": "2",
        "data_type": "echogram",  # Ein Bezeichner für die Art der Datenverarbeitung
        "description": "Verarbeitet 10-Bit Echogramm-Daten (ASCII)."
    },
    "3": {
        "name": "NMEA",
        "output_mode_id": "3",
        "data_type": "nmea",
        "description": "Verarbeitet NMEA-Tiefendaten ($SDDBT)."
    },
    "4": {
        "name": "12bit-Echogram",
        "output_mode_id": "4",
        "data_type": "echogram_plotted", # Eigener Typ, um Plotting auszulösen
        "description": "Verarbeitet 12-Bit Echogramm-Daten (ASCII) und stellt sie grafisch dar.",
        "settings": {
            "low": {
                "IdSamplFreq": "100000", # 6250, 12500, 25000, 50000, 100000
                "IdRange": "3000",
                "IdInterval": "1",
                "IdDeadzone": "200",
                "IdTxLength": "10",
                "IdTxPower": "0",
                "IdGain": "0",
                "read_timeout": 2.0
            },
            "high": {
                # Hier könnten bei Bedarf andere Werte für die hohe Frequenz stehen
                "IdSamplFreq": "100000", # 6250, 12500, 25000, 50000, 100000
                "IdRange": "3000",
                "IdInterval": "1",
                "IdDeadzone": "200",
                "IdTxLength": "10",
                "IdTxPower": "0",
                "IdGain": "0",
                "read_timeout": 2.0
            }
        }
    },
    "100": {
        "name": "12bit-Binary",
        "output_mode_id": "100",
        "data_type": "binary",
        "description": "Verarbeitet rohe 12-Bit Binärdaten."
    },
    "101": {
        "name": "8bit-Binary",
        "output_mode_id": "101",
        "data_type": "binary",
        "description": "Verarbeitet rohe 8-Bit Binärdaten."
    }
}

