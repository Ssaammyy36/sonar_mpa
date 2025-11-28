from src.logger import get_logger
from src.echosounderapi.echosndr import DualEchosounder
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

COMPORT: str = "COM5"
BAUDRATE: int = 115200
logger = get_logger(__name__)

try:
    ss = DualEchosounder(f"\\\\.\\{COMPORT}", BAUDRATE)
except:
    logger.warning("Unable to open port")
else:
    detected = ss.Detect()
    if False == detected:
        logger.warning("Port opened but echosounder is not detected")
    else:
        ss.SetCurrentTime()              # Sync Echosounder's time with the host PC
        ss.SendCommand("IdSetHighFreq")  # Set High working frequency
        ss.SetValue("IdOutput", "4")     # Set output #4
        # Set interval between pings 0.5 seconds
        ss.SetValue("IdInterval", "0.5")
        # ss.SendCommand("IdDefault") # zum Testen Default Einstellungen setzen

        if True == ss.Start():
            logger.debug("Start == True")

            # Set High working frequency
            ss.SendCommand("IdSetHighFreq")
            logger.debug(
                f"Working Frequency: {ss.GetValue('IdGetWorkFreq')} Hz")
            time.sleep(2.0)
            # data = ss.ReadData(2048)
            # read couple of bytes
            data = ss.ReadData(6800)
            # Show data
            logger.debug(data.decode("latin_1"))

            """"
            ss.SendCommand("IdSetLowFreq")                                              # Set High working frequency
            logger.debug(f"Working Frequency: {ss.GetValue('IdGetWorkFreq')} Hz")
            time.sleep(2.0)
            #data = ss.ReadData(2048)                                            # read couple of bytes
            data = ss.ReadData(20000)
            logger.debug(data.decode("latin_1"))  
            """                                  # Show data
