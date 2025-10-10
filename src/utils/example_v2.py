import time
import re
import matplotlib.pyplot as plt
from src import config
from src.echosounderapi.echosndr import DualEchosounder

def configure_echosounder(
        echosounder: DualEchosounder, 
        outputMode: str, 
        frequency: str, 
        interval: str, 
        pulseLength: str = "20", 
        samplFreq: str = "100000"):
    """Sets Configs."""
    print(f"\n--- Configuring sonar ---")

    # Set output mode (3=NMEA, 2=binary, 1=ASCII)
    echosounder.SetValue("IdOutput", outputMode)

    # Set frequency (high/low) 
    if frequency == "high" or frequency == "200kHz":
        echosounder.SendCommand("IdSetHighFreq")
    elif frequency == "low" or frequency == "50kHz":
        echosounder.SendCommand("IdSetLowFreq")
    else:
        print(f"Unknown frequency: {frequency}")
        return

    # Config 
    echosounder.SetValue("IdInterval", interval)        # Set shared ping interval [s 0,01..10]
    echosounder.SetValue("IdTxLength", pulseLength)     # Set pulse length [us 10..200]
    echosounder.SetValue("IdSamplFreq", samplFreq)      # Set sample frequency [6250..100,000 Hz]

    print(F"Configuration: {outputMode=}, {frequency=}, {interval=}, {pulseLength=}, {samplFreq=}")
    
def read_from_echosounder(echosounder: DualEchosounder, duration: float = 2.0) -> bytes | None:
    """Starts the echosounder, reads data for a duration, and returns the data."""
    print(f"\n--- Pinging for {duration} seconds ---")
    
    ## Read data
    if not echosounder.Start():
        print("Failed to start echosounder.")
        return None
    time.sleep(duration)
    data = echosounder.ReadData(1024)
    
    # Print data info
    if data:
        print(f"Read {len(data)} bytes.")
        return data
    else:
        print("No data read.")
        return None

def create_dualsonar() -> DualEchosounder | None:
    """Connects to, creates, detects, and configures the echosounder."""
    print(f"--- Connect to echosounder ---")
    
    # Create object 
    try:
        dual_sonar = DualEchosounder(f"\\\\.\\{config.COMPORT}", config.BAUDRATE)
    except Exception as e:
        print(f"Error: Unable to create Echosounder object. {e}")
        return None
    
    # Detect echosounder
    if not dual_sonar.Detect():
        print("Error: Echosounder not detected on the port.")
        return None   
    print(f"Echosounder detected successfully on {config.COMPORT} with {config.BAUDRATE} baud.")
    
    # Initial configuration of the sonar object
    dual_sonar.SetCurrentTime()

    return dual_sonar

def run_low_and_high_frequency_tests(dual_sonar: DualEchosounder):
    """Runs a sequence of frequency tests on the sonar."""

    # High Frequency Test
    print("\n--- Running High Frequency Test ---")
    configure_echosounder(echosounder=dual_sonar, frequency="high", interval="0.2", outputMode = "3")
    high_freq_data = read_from_echosounder(echosounder=dual_sonar, duration=2.0)
    if high_freq_data:
        print("\nReceived data:")
        depths = parse_depth_from_nmea(high_freq_data)
        if depths:
            print("\n\n--- Extracted Depth Values ---")
            for i, depth in enumerate(depths):
                print(f"  Measurement {i+1}: {depth:.3f} meters")
    dual_sonar.Stop() # Explicitly stop the sonar after the test

    # Low Frequency Test
    print("\n--- Running Low Frequency Test ---")
    configure_echosounder(echosounder=dual_sonar, frequency="low", interval="0.5", outputMode = "3")
    low_freq_data = read_from_echosounder(echosounder=dual_sonar, duration=2.0)
    if low_freq_data:
        print("\nReceived data:")
        print(low_freq_data.decode("latin_1"), end='')
    dual_sonar.Stop() # Explicitly stop the sonar after the test

def parse_depth_from_nmea(nmea_data: bytes) -> list[float]:
    """Parses NMEA data to extract depth values in meters from $SDDBT sentences."""
    print("\n--- Parsing NMEA Data ---")
    
    depths = []
    if not nmea_data:
        return depths

    # Decode byte string and split into lines
    decoded_data = nmea_data.decode("latin_1") # convert bytes to string
    lines = decoded_data.splitlines()

    for line in lines:
        # Check for the DBT (Depth Below Transducer) sentence
        if line.strip().startswith('$SDDBT'):
            parts = line.strip().split(',')
            # The NMEA format for SDDBT is: $SDDBT,depth_feet,f,depth_meters,M,...
            # We need the value at index 3, which is the depth in meters.
            if len(parts) > 4 and parts[4] == 'M':
                try:
                    depths.append(float(parts[3]))
                except (ValueError, IndexError):
                    # Ignore malformed sentences
                    pass
    return depths

def run_nmea_test(dual_sonar: DualEchosounder):
    """Runs a test to read NMEA data from the sonar."""
    print("\n--- Running NMEA Data Test ---")

    # Set Config to 
    configure_echosounder(echosounder=dual_sonar, frequency="high", interval="0.2", outputMode = "3")

    # Read data 
    nmea_data = read_from_echosounder(echosounder=dual_sonar, duration=2.0)
    if nmea_data:
        print("\nReceived NMEA data:")
        print(nmea_data.decode("latin_1"), end='')
    
        # Parse the NMEA data to extract depth
        depth_values = parse_depth_from_nmea(nmea_data)
        if depth_values:
            print(f"Found {len(depth_values)} depth measurements:")
            for i, depth in enumerate(depth_values):
                print(f"  Measurement {i+1}: {depth:.3f} meters")
        else:
            print("\n\n--- No depth data found in NMEA output. ---")

    dual_sonar.Stop() # Explicitly stop the sonar after the test

def parse_binary_data(bin_data: bytes) -> list[int]:
    """
    Parses the raw binary data from the sonar into a list of integer amplitudes.
    The data is expected to be a series of numbers separated by newlines.

    Args:
        bin_data: The raw byte string from the sonar.

    Returns:
        A list of integer amplitude values.
    """
    amplitudes = []
    if not bin_data:
        return amplitudes
    
    try:
        # Decode using 'latin_1' and split into individual lines/numbers
        decoded_data = bin_data.decode("latin_1")
        lines = decoded_data.strip().splitlines()

        for line in lines:
            if line:  # Ensure the line is not empty
                amplitudes.append(int(line))
    except (ValueError, UnicodeDecodeError) as e:
        print(f"Error parsing binary data: {e}")
    
    return amplitudes

def plot_echogram(amplitudes: list[int], title: str = "Sonar Echogram"):
    """
    Plots the sonar signal amplitude over the sample number using matplotlib.

    Args:
        amplitudes: A list of signal amplitude values.
        title: The title for the plot.
        mm_per_sample: The distance in millimeters that one sample represents.
    """
    if not amplitudes:
        print("No amplitude data available to plot.")
        return
    
    print(f"Plotting {len(amplitudes)} amplitude samples.")

    plt.figure(figsize=(12, 6))
    plt.plot(amplitudes)
    plt.title(title)
    plt.xlabel("Samples [N]")
    plt.ylabel("Signal Amplitude [bit 0..255]")
    plt.grid(True)
    plt.show()

def run_bin_test(dual_sonar: DualEchosounder):
    """Runs a test to read binary data from the sonar."""
    print("\n--- Running Binary Data Test ---")

    # Set Config to binary mode
    configure_echosounder(
        echosounder=dual_sonar, 
        frequency="high", 
        interval="0.2", 
        outputMode = "3", 
        pulseLength="20", 
        samplFreq="100000")

    # Read data 
    bin_data = read_from_echosounder(echosounder=dual_sonar, duration=2.0)
    if bin_data:
        print("\nReceived binary data:")

        # Convert in string
        decoded_data = bin_data.decode("latin_1")
        lines = decoded_data.strip().splitlines()
        for line in lines:
            if line:  # Ensure the line is not empty
                print(line)

        # Parse the data into a list of numbers
        amplitudes = parse_binary_data(bin_data)
        print(f"Successfully parsed {len(amplitudes)} amplitude samples.")
        # Plot the parsed data
        plot_echogram(amplitudes, title="Sonar Echo Amplitude (Binary Mode)")
    else:
        print("\n\nNo binary data received.")

    dual_sonar.Stop() # Explicitly stop the sonar after the test    

def main():
    """Main entry point of the script."""
    # Create and configure the sonar object only once.
    dual_sonar = create_dualsonar()
    
    if dual_sonar:
        # Run tests for different frequencies on the same object.
        run_bin_test(dual_sonar)

    print("\n\n--- Test complete ---")

if __name__ == "__main__":
    main()