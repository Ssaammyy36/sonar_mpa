from utils.logger import get_logger

# Logger = besser asl print für übersichlichliche Ausgaben
logger = get_logger(__name__)

def main():
    logger.info("Programm startet.")
    # ...
    logger.warning("Dies ist nur ein Beispiel.")
    logger.error("Hier ist ein Fehler aufgetreten!")

if __name__ == "__main__":
    main()
