import sys
import os
import numpy as np
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from classifier import SonarClassifier
from data_types import EchogramMeasurement
import config

def main():
    print("--- Starting Verification of Refactored Classifier ---")
    
    # Check Config
    print(f"Active Model ID in Config: {config.ANALYSIS_CONFIG.get('active_model_id')}")
    
    # Initialize Classifier
    try:
        classifier = SonarClassifier()
        print("Classifier initialized successfully.")
    except Exception as e:
        print(f"FAILED to initialize Classifier: {e}")
        return

    if classifier.model:
        print(f"Loaded Model Class: {type(classifier.model)}")
        from ai.legacy import LegacyFeatureModel
        if isinstance(classifier.model, LegacyFeatureModel):
            print("SUCCESS: Correct model type (LegacyFeatureModel) loaded.")
        else:
            print(f"WARNING: Unexpected model type: {type(classifier.model)}")
    else:
        print("WARNING: No model loaded inside Classifier (check config/paths).")

    # Mock Data Creation
    print("\n--- Testing Prediction with Mock Data ---")
    
    # Create dummy echogram data (random noise mimicking signal)
    # Win len 3000 (typical range)
    dummy_data = [int(x) for x in np.random.randint(0, 255, 3000)]
    
    # 10022026_112831 (from user logs)
    m_low = EchogramMeasurement(
        timestamp=datetime.now(),
        raw_data=b'',
        header={"Depth": "10.0"},
        data_points=dummy_data
    )
    
    m_high = EchogramMeasurement(
        timestamp=datetime.now(),
        raw_data=b'',
        header={"Depth": "10.0"},
        data_points=dummy_data
    )

    # Predict
    try:
        prediction = classifier.predict_paired([m_low], [m_high])
        print(f"Prediction Result: {prediction}")
        if prediction is not None:
             print("SUCCESS: Prediction logic executed without crashing.")
        else:
             print("NOTE: Prediction returned None (expected if no actual model file found or mock data invalid).")
    except Exception as e:
        print(f"FAILED during prediction: {e}")

if __name__ == "__main__":
    main()
