# Copyright (c) EofE Ultrasonics Co., Ltd., 2024
import time
import os
import sys

# ensure local libs/echosounderapi is importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib_path = os.path.join(project_root, "libs", "echosounderapi")
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from echosndr import DualEchosounder

COMPORT = "COM5"
BAUDRATE = 115200

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
        ss.SetValue("IdOutput", "3")     # Set output #3
        ss.SetValue("IdInterval", "0.2") # Set interval between pings 0.2 seconds
        
        if True == ss.Start(): 
            print("Working Frequency:", ss.GetValue("IdGetWorkFreq"), "Hz")
            time.sleep(2.0)                       # pause for 2 seconds
            data = ss.ReadData(128)               # read couple of bytes
            print(data.decode("latin_1"), end='') # Show data
            
            ss.SendCommand("IdSetLowFreq")        # Set Low working frequency
            ss.SetValue("IdInterval", "0.5")      # Change interval
            print("Working Frequency:", ss.GetValue("IdGetWorkFreq"), "Hz")
            time.sleep(2.0)
            data = ss.ReadData(128)               # read couple of bytes
            print(data.decode("latin_1"), end='') # Show data
