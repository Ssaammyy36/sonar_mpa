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

# Definitionen der verfügbaren Klassen
CLASSES = {
    "Gravel",
    "Sand",
    "Soil",
    "Vertical tub",
    "Horizontal tub",
    "Test"
}

# Allgemeine Logging-Einstellungen
LOGGING_CONFIG = {
    "plot_echograms": True,
    "save_csv": True,
    "log_raw_data": False
}

# Strukturierte Definition aller verfügbaren Sonar-Modi
MODES = {
    "2": {
        "name": "10bit-Echogram",
        "output_mode_id": "2",
        "data_type": "echogram",
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
        "data_type": "echogram",
        "description": "Verarbeitet 12-Bit Echogramm-Daten (ASCII) und stellt sie grafisch dar.",
        "settings": {
            "low": {
                "IdSamplFreq": "100000", # 6250, 12500, 25000, 50000, 100000
                "IdRange": "3000",
                "IdInterval": "1",
                "IdDeadzone": "200",
                "IdTxLengthL": "100",
                "IdTxPower": "0",
                "IdGain": "0",
                "read_timeout": 2.0
            },
            "high": {
                "IdSamplFreq": "100000", # 6250, 12500, 25000, 50000, 100000
                "IdRange": "3000",
                "IdInterval": "1",
                "IdDeadzone": "200",
                "IdTxLengthH": "100",
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

