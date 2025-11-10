import time
import sys
from pathlib import Path

# Path 
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.echosounderapi.echosndr import DualEchosounder
from src.utils.logger import get_logger
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
            ss.SendCommand("IdSetHighFreq")                                             # Set High working frequency
            logger.debug(f"Working Frequency: {ss.GetValue('IdGetWorkFreq')} Hz")
            time.sleep(TIME)
            data = ss.ReadData(DATA_BUFFER)                                             # read couple of bytes
            logger.debug(data)                                # Show data
            

            # Low
            ss.SendCommand("IdSetLowFreq")                                              # Set High working frequency
            logger.debug(f"Working Frequency: {ss.GetValue('IdGetWorkFreq')} Hz")
            time.sleep(TIME)
            data = ss.ReadData(DATA_BUFFER)
            logger.debug(data)  

