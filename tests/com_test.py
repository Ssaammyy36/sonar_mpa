import serial
print(serial.__file__)

try:
    ser = serial.Serial(
        port='COM5',
        baudrate=115200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.SEVENBITS,
        timeout=1
    )
    print("Port COM5 opened successfully")
    ser.close()
    print("Port COM5 closed successfully")
except AttributeError:
    print("AttributeError: This is likely due to a conflict with the 'serial' package.")
    print("Please ensure 'pyserial' is installed and there are no files named 'serial.py' in your project.")
except serial.SerialException as e:
    print(f"Error opening port COM5: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")