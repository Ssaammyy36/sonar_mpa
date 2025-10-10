import time
import re
from src import config
from src.echosounderapi.echosndr import DualEchosounder

def configure_echosounder(echosounder: DualEchosounder, frequency: str, interval: str):
    """Sets the frequency and ping interval on the echosounder."""
    print(f"\n--- Configuring for {frequency} frequency with {interval}s interval ---")

    # Set frequency and channel-specific gain
    if frequency == "high":
        echosounder.SendCommand("IdSetHighFreq")
    elif frequency == "low":
        echosounder.SendCommand("IdSetLowFreq")
    else:
        print(f"Unknown frequency: {frequency}")
        return

    # Set shared ping interval
    echosounder.SetValue("IdInterval", interval)
    
    # DEBUGGING: Use the new query_value function to get live data
    #print(f"High Freq Setting: {query_value(echosounder, 'IdGetHighFreq')} Hz")
    #print(f"Low Freq Setting: {query_value(echosounder, 'IdGetLowFreq')} Hz")
    #print(f"Actual Working Frequency: {query_value(echosounder, 'IdGetWorkFreq')} Hz")

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

def setup_dualsonar() -> DualEchosounder | None:
    """Connects to, creates, detects, and configures the echosounder."""
    print(f"--- Attempting to connect to echosounder on {config.COMPORT} at {config.BAUDRATE} baud. ---")
    
    # Create object 
    try:
        dual_sonar = DualEchosounder(f"\\\\.\\{config.COMPORT}", config.BAUDRATE)
    except Exception as e:
        print(f"Error: Unable to create Echosounder object. {e}")
        return None
    
    # Detect echosounder
    print("Port opened. Detecting echosounder...")
    if not dual_sonar.Detect():
        print("Error: Echosounder not detected on the port.")
        return None   
    print("Echosounder detected successfully.")
    
    # Initial configuration of the sonar object
    dual_sonar.SetCurrentTime()
    #dual_sonar.SetValue("IdOutput", config.OUTPUT_MODE)

    return dual_sonar

def run_low_and_high_frequency_tests(dual_sonar: DualEchosounder):
    """Runs a sequence of frequency tests on the sonar."""
    
    # High Frequency Test
    print("\n--- Running High Frequency Test ---")
    configure_echosounder(echosounder=dual_sonar, frequency="high", interval="0.2")
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
    configure_echosounder(echosounder=dual_sonar, frequency="low", interval="0.5")
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
    dual_sonar.SetValue("IdOutput", "3")  # Set to NMEA mode
    configure_echosounder(echosounder=dual_sonar, frequency="high", interval="0.2")

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

def main():
    """Main entry point of the script."""
    # Create and configure the sonar object only once.
    dual_sonar = setup_dualsonar()
    
    if dual_sonar:
        # Run tests for different frequencies on the same object.
        run_nmea_test(dual_sonar)

    print("\n\n--- Test complete ---")

if __name__ == "__main__":
    main()