import pickle
import sys
import os

model_path = r"c:\Users\samso\Documents\00 Uni\Semester 9\sonar_mpa\models\sonar_model.pkl"

print(f"Loading model from {model_path}")
try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print("Model loaded successfully.")
    print(f"Model type: {type(model)}")
    
    if hasattr(model, 'estimators_'):
        print(f"estimators_ present. Count: {len(model.estimators_)}")
    else:
        print("ERROR: estimators_ attribute missing!")
        
except Exception as e:
    print(f"Failed to load model: {e}")
