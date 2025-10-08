import serial

def connect_to_serial_port(port: str, baudrate: int, **kwargs) -> serial.Serial | None:
    """Attempts to connect to a serial port and returns the serial object."""
    try:
        # Open serial port
        ser = serial.Serial(port=port, baudrate=baudrate, **kwargs)
        print(f"Successfully opened port {port}")
        return ser
    except serial.SerialException as e:
        # Failed
        print(f"Error opening port {port}: {e}")
        return None

def check_for_data(ser: serial.Serial, listen_time: float = 2.0) -> bytes | None:
    """Listens on an open serial port for a short period and returns any received data."""
    # Check if the port is open
    if not ser.is_open:
        print("Error: Serial port is not open.")
        return None

    # Set the read timeout for this specific operation
    print(f"Listening on {ser.port} for {listen_time} second(s)...")
    original_timeout = ser.timeout
    ser.timeout = listen_time 
    data = ser.read(1024)
    ser.timeout = original_timeout # Restore original timeout

    if data:
        print(f"Received {len(data)} bytes.")
        return data
    else:
        print("No data received.")
        return None

if __name__ == '__main__':
    # Connecting
    print("--- Example: Connecting, checking for data, then closing ---")
    ser_port = connect_to_serial_port(
        port='COM5',
        baudrate=115200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.SEVENBITS,
        timeout=1  # Default timeout for operations after connection
    )

    # Check Connection
    if ser_port:
        # Read data
        received_data = check_for_data(ser_port, listen_time=2)
        
        if received_data:
            print("Data received:")
            try:
                print(received_data.decode('utf-8'))
            except UnicodeDecodeError:
                print(received_data)
        
        # Close the port 
        print("Closing port.")
        ser_port.close()
    else:
        # No connection
        print("Connection failed.")
