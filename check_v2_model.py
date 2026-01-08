
import pickle
import os
import sklearn
from sklearn.ensemble import RandomForestClassifier

print(f"Current sklearn version: {sklearn.__version__}")

model_path = r'models/sonar_model_v2.pkl'

if not os.path.exists(model_path):
    print(f"Error: {model_path} does not exist.")
else:
    print(f"Loading {model_path}...")
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        print("Model loaded.")
        print(f"Model type: {type(model)}")
        
        try:
            _ = model.estimators_
            print("SUCCESS: model.estimators_ attribute exists.")
        except AttributeError as e:
            print(f"FAILURE: AttributeError encountered: {e}")
            print("This confirms the model is incompatible or not fitted correctly.")
            
    except Exception as e:
        print(f"Error loading model: {e}")
