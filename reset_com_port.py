
import serial
try:
    s = serial.Serial('COM5', 115200, timeout=1)
    s.dtr = False
    s.rts = False
    s.close()
    print("Successfully set DTR and RTS to False for COM5")
except Exception as e:
    print(f"An error occurred: {e}")
