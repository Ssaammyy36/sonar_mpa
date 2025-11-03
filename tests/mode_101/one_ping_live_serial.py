import time
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
from src.echosounderapi.echosndr import DualEchosounder

# Config
COMPORT: str = "COM5"
BAUDRATE: int = 115200
OUTPUT_MODE: str = "101"  # 8 bit

try:
    ss = DualEchosounder(f"\\\\.\\{COMPORT}", BAUDRATE)
except Exception as e:
    print("Unable to open port:", e)
    sys.exit(1)
else:
    detected = ss.Detect()

    if False == detected:
        print("Port opened but echosounder is not detected")
    else:
        # Konfiguration
        ss.SetCurrentTime()
        ss.SendCommand("IdSetHighFreq")
        ss.SetValue("IdOutput", OUTPUT_MODE)
        ss.SetValue("IdInterval", "0.2") # Set interval between pings 0.2 seconds

        print("\n--- Start Live Ping Test --- (Drücke STRG+C zum Beenden)\n")

        if True == ss.Start(): 
            while True:
                #ss.SetValue("IdPingonce", "1")     # einen Ping auslösen
                #data = ss.ReadData(512)            # etwas größeren Puffer lesen

                ss.Start()

                print("Working Frequency:", ss.GetValue("IdGetWorkFreq"), "Hz")
                time.sleep(1.0)                       # pause for 2 seconds
                data = ss.ReadData(128)               # read couple of bytes
                
                if data: 
                    print(data.decode("latin_1"), end='') # Show data
                else: 
                    print(":(") 

        except KeyboardInterrupt:
            print("--- Abbruch durch Benutzer ---")
        finally:
            ss.close()
