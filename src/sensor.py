from utils.logger import get_logger

class Sensor:
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.logger = get_logger(__name__)

    def test(self):
        self.logger.debug(f"Sensor {self.sensor_id} erreichbar.")
