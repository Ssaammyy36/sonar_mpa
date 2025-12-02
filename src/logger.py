import logging
import os
from datetime import datetime

# Globale Variable, um zu prüfen, ob das Logging bereits konfiguriert wurde
_logging_configured = False


def setup_logging(log_dir: str):
    """
    Konfiguriert das Root-Logging-System, um in eine Datei und die Konsole zu schreiben.
    Diese Funktion sollte nur einmal beim Start der Anwendung aufgerufen werden.
    """
    global _logging_configured
    if _logging_configured:
        return

    # Sicherstellen, dass das Log-Verzeichnis existiert
    os.makedirs(log_dir, exist_ok=True)
    file_name = "sonar_loggs_" + datetime.now().strftime("%d%m%Y_%H%M%S") + ".log"
    log_file_path = os.path.join(log_dir, file_name)

    # Formatter definieren
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(name)-15s:%(funcName)-28s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Alle bestehenden Handler entfernen, um Duplikate zu vermeiden
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # StreamHandler für die Konsole
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # FileHandler für die Datei
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Unterdrücke Debug-Nachrichten von externen Bibliotheken
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    _logging_configured = True
    logging.info(f"Logging konfiguriert. Log-Datei unter: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Gibt einen Logger mit dem angegebenen Namen zurück.
    Die Konfiguration wird durch setup_logging() übernommen.
    """
    return logging.getLogger(name)
