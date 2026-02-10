# Copyright (c) EofE Ultrasonics Co., Ltd., 2024
import time
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
from src.echosounderapi.echosndr import DualEchosounder

COMPORT: str = "COM5"
BAUDRATE: int = 115200
OUTPUT_MODE: str = "4" # 8 bit

try:
    ss = DualEchosounder(f"\\\\.\\{COMPORT}", BAUDRATE)
except:
    print("Unable to open port")
else:
    detected = ss.Detect()

    if False == detected:
        print("Port opened but echosounder is not detected")
    else:
        ss.SetCurrentTime()              # Sync Echosounder's time with the host PC
        ss.SendCommand("IdSetHighFreq")  # Set High working frequency
        ss.SetValue("IdOutput", OUTPUT_MODE)     # Set outputmode 
        ss.SetValue("IdPingonce", "0") 

        #ss.Start()
        time.sleep(2.0)

        print("--- Start Ping Once Test ---")
        #print("Working Frequency:", ss.GetValue("IdGetWorkFreq"), "Hz")
        #time.sleep(2.0)                       # pause for 2 seconds
        data = ss.ReadData(128)               # read couple of bytes

        print(data.decode("latin_1"), end='') # Show data
        print(data)
            