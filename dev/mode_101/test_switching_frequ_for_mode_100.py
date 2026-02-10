from src.logger import get_logger
from src.echosounderapi.echosndr import DualEchosounder
import time
import sys
from pathlib import Path

# Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

# Configs
COMPORT: str = "COM5"               # COM5
BAUDRATE: int = 115200              # 115200
ID_OUTPUT: str = "101"              #
ID_INTERVAL: str = "0.5"            # 0.2
TIME: float = 2.0                   # 2.0
DATA_BUFFER: int = 6800             # 128

# Connect
try:
    ss = DualEchosounder(f"\\\\.\\{COMPORT}", BAUDRATE)
except:
    logger.warning("Unable to open port")
else:
    detected = ss.Detect()
    if False == detected:
        logger.warning("Port opened but echosounder is not detected")
    else:
        # Setup
        ss.SetCurrentTime()
        ss.SendCommand("IdSetHighFreq")
        ss.SetValue("IdOutput", ID_OUTPUT)
        ss.SetValue("IdInterval", ID_INTERVAL)

        if True == ss.Start():
            logger.debug("Start == True")

            # High
            # Set High working frequency
            ss.SendCommand("IdSetHighFreq")
            logger.debug(
                f"Working Frequency: {ss.GetValue('IdGetWorkFreq')} Hz")
            time.sleep(TIME)
            # read couple of bytes
            data = ss.ReadData(DATA_BUFFER)
            logger.debug(data)                                # Show data

            # Low
            # Set High working frequency
            ss.SendCommand("IdSetLowFreq")
            logger.debug(
                f"Working Frequency: {ss.GetValue('IdGetWorkFreq')} Hz")
            time.sleep(TIME)
            data = ss.ReadData(DATA_BUFFER)
            logger.debug(data)
