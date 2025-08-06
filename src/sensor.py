from utils.logger import get_logger

class Sensor:
    """
    Repräsentiert einen einzelnen Sonar-Sensor.

    Attributes:
        sensor_id (str): Die eindeutige ID des Sensors.
        logger: Das Logging-Objekt für diese Klasse.
    """
    def __init__(self, sensor_id: str):
        """
        Initialisiert ein neues Sensor-Objekt.

        Args:
            sensor_id (str): Die ID, die dem Sensor zugewiesen wird.
        """
        self.sensor_id = sensor_id
        self.logger = get_logger(__name__)

    def test(self):
        """Loggt eine Test-Nachricht, um die Erreichbarkeit zu prüfen."""
        self.logger.debug(f"Sensor {self.sensor_id} erreichbar.")
