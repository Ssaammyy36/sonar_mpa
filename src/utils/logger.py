import logging
import os
from datetime import datetime

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Konfiguriert und gibt einen Logger mit UTF-8-Kodierung zurück.

    Args:
        name (str, optional): Der Name des Loggers. Defaults to __name__.

    Returns:
        logging.Logger: Das konfigurierte Logger-Objekt.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Handler nur hinzufügen, wenn noch keine konfiguriert sind
    if not logger.handlers:
        # Formatter definieren
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)-15s:%(funcName)-28s - %(message)s',
            datefmt='%H:%M:%S' # Nur Stunde, Minute, Sekunde
        )
        
        # StreamHandler erstellen und Kodierung auf UTF-8 setzen
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # FileHandler erstellen
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = datetime.now().strftime("%d%m%Y_%H%M%S") + ".log"
        file_handler = logging.FileHandler(os.path.join(log_dir, log_file), encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
