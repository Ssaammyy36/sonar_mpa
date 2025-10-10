import time
import re
from src import config
from src.echosounderapi.echosndr import DualEchosounder

def query_value(echosounder: DualEchosounder, command_id: str) -> str | None:
    """
    Actively queries a value from the echosounder by sending a command
    and parsing the live response.

    This is a workaround for the library's GetValue(), which may return a
    cached value.

    Args:
        echosounder: The echosounder object.
        command_id: The ID of the command to query (e.g., 'IdGetWorkFreq').

    Returns:
        The queried value as a string, or None if not found.
    """
    echosounder.SendCommand(command_id)
    response = echosounder.RecvResponse()
    
    # Find the regex for the command_id in the internal command list
    cmd_tuple = next((cmd for cmd in echosounder._sonarcommands if cmd[0] == command_id), None)
    
    if response and cmd_tuple and cmd_tuple[3]:
        match = re.search(cmd_tuple[3], response)
        if match:
            return match.group(1)
    return None

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
    print(f"High Freq Setting: {query_value(echosounder, 'IdGetHighFreq')} Hz")
    print(f"Low Freq Setting: {query_value(echosounder, 'IdGetLowFreq')} Hz")
    print(f"Actual Working Frequency: {query_value(echosounder, 'IdGetWorkFreq')} Hz")

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
    dual_sonar.SetValue("IdOutput", config.OUTPUT_MODE)
    
    return dual_sonar

def run_sonar_tests(dual_sonar: DualEchosounder):
    """Runs a sequence of frequency tests on the sonar."""
    
    # High Frequency Test
    print("\n--- Running High Frequency Test ---")
    configure_echosounder(echosounder=dual_sonar, frequency="high", interval="0.2")
    high_freq_data = read_from_echosounder(echosounder=dual_sonar, duration=2.0)
    if high_freq_data:
        print("\nReceived data:")
        print(high_freq_data.decode("latin_1"), end='')
    dual_sonar.Stop() # Explicitly stop the sonar after the test

    # Low Frequency Test
    print("\n--- Running Low Frequency Test ---")
    configure_echosounder(echosounder=dual_sonar, frequency="low", interval="0.5")
    low_freq_data = read_from_echosounder(echosounder=dual_sonar, duration=2.0)
    if low_freq_data:
        print("\nReceived data:")
        print(low_freq_data.decode("latin_1"), end='')
    dual_sonar.Stop() # Explicitly stop the sonar after the test

def main():
    """Main entry point of the script."""
    # Create and configure the sonar object only once.
    dual_sonar = setup_dualsonar()
    
    if dual_sonar:
        # Run tests for different frequencies on the same object.
        run_sonar_tests(dual_sonar)

    print("\n\n--- Test complete ---")


if __name__ == "__main__":
    main()