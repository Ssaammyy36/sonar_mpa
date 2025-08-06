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
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # StreamHandler erstellen und Kodierung auf UTF-8 setzen
        handler = logging.StreamHandler()
        try:
            # Diese Methode ist robust und funktioniert ab Python 3.7+
            handler.stream.reconfigure(encoding='utf-8')
        except TypeError:
            # Fallback für ältere Versionen oder andere Stream-Typen
            # In den meisten modernen Umgebungen sollte dies nicht notwendig sein
            pass

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
