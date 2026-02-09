import sys
import os
import joblib

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from classifier import SonarClassifier
    from config import ANALYSIS_CONFIG
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def verify_load():
    print("Attempting to load SonarClassifier...")
    classifier = SonarClassifier()
    if classifier.model:
        print("SUCCESS: Model loaded successfully!")
        print(f"Model type: {type(classifier.model)}")
        
        # Optional: Try a dummy prediction to be absolutely sure
        try:
            # Create dummy features (318 floats as expected by predict_paired logic, but model expects whatever PCA+Stats needs)
            # The model expects [8 stats + 24% PCA components]
            # Actually we can just check if predict exists.
            print("Model has predict method: ", hasattr(classifier.model, "predict"))
        except Exception as e:
            print(f"WARNING: Model loaded but basic check failed: {e}")
            
    else:
        print("FAILURE: Model failed to load (classifier.model is None).")
        sys.exit(1)

if __name__ == "__main__":
    verify_load()
