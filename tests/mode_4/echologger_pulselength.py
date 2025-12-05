# Copyright (c) EofE Ultrasonics Co., Ltd., 2024
from echosndr import SingleEchosounder
from echosndr import DualEchosounder
import time
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
        ss.SetValue("IdOutput", "2")     # Set output #2
        ss.SetValue("IdInterval", "1")   # Set interval between pings 1 seconds
       
        if True == ss.Start():
            print("Pulse Lenght:", ss.GetValue("IdTxLength"), "uks")
            ss.SetValue("IdTxLength", "40")       # Change Tx Length for current working frequency
            print("Pulse Lenght:", ss.GetValue("IdTxLength"), "uks")
            ss.SetValue("IdTxLengthH", "60")      # Change Tx Length for high working frequency
            print("Pulse Lenght High:", ss.GetValue("IdTxLengthH"), "uks")
            ss.SetValue("IdTxLengthL", "70")      # Change Tx Length for low working frequency
            print("Pulse Lenght Low:", ss.GetValue("IdTxLengthL"), "uks")
            time.sleep(2.0)                       # pause for 2 seconds
            data = ss.ReadData(10000)             # read couple of bytes
            print(data.decode("latin_1"), end='') # Show data