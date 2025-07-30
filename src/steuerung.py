from utils.logger import get_logger

class Steuerung:
    def __init__(self):
        self.logger = get_logger(__name__)

    def test(self):
        self.logger.debug("Steuerung erreichbar.")
