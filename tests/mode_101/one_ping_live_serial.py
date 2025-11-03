from src.echosounderapi.echosndr import DualEchosounder
import time
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

COMPORT: str = "COM5"
BAUDRATE: int = 115200
OUTPUT_MODE: str = "101"  # 8 bit

try:
    ss = DualEchosounder(f"\\\\.\\{COMPORT}", BAUDRATE)
except Exception as e:
    print("Unable to open port:", e)
    sys.exit(1)

detected = ss.Detect()

if not detected:
    print("Port opened but echosounder is not detected")
    sys.exit(1)

# Konfiguration
ss.SetCurrentTime()
ss.SendCommand("IdSetHighFreq")
ss.SetValue("IdOutput", OUTPUT_MODE)

print("\n--- Start Live Ping Test --- (Drücke STRG+C zum Beenden)\n")

try:
    while True:
        ss.SetValue("IdPingonce", "1")     # einen Ping auslösen
        data = ss.ReadData(512)            # etwas größeren Puffer lesen
        if data:
            print(data.decode("latin_1"), end='', flush=True)
        time.sleep(0.05)                   # kleine Pause (50 ms)
except KeyboardInterrupt:
    print("\n--- Abbruch durch Benutzer ---")
finally:
    ss.close()
