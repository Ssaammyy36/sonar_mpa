import logging

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
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S' # Nur Stunde, Minute, Sekunde
        )
        
        # StreamHandler erstellen und Kodierung auf UTF-8 setzen
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
