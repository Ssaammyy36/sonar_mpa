from utils.logger import get_logger

class Empfaenger:
    def __init__(self, name):
        self.name = name
        self.logger = get_logger(__name__)

    def test(self):
        self.logger.debug(f"Empfänger {self.name} erreichbar.")
