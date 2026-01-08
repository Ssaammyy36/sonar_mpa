
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import os

def retrain():
    print("Loading training data...")
    base_path = r'c:\Users\samso\Documents\00 Uni\Semester 9\sonar_mpa\data\messung_15_12_25'
    files = ['grabel_training_data.csv', 'sand_training_data.csv', 'stone_training_data.csv']
    
    dfs = []
    for f in files:
        file_path = os.path.join(base_path, f)
        if os.path.exists(file_path):
            print(f"Reading {file_path}...")
            df = pd.read_csv(file_path, delimiter=';') # Assuming delimiter is semi-colon based on typical German csv, need to verify or try default.
            # Convert decimal comma to dot if string, or handle potential parsing issues
            # But the notebook display looked normal. pandas read_csv default is comma.
            # Let's try comma first, if not I'll have to check.
            # Actually, standard pandas csv usually comma.
            dfs.append(df)
        else:
            print(f"Warning: File {file_path} not found.")
            
    if not dfs:
        print("No data found.")
        return

    full_df = pd.concat(dfs, ignore_index=True)
    print(f"Total samples: {len(full_df)}")

    # Identify amplitude columns
    amplitude_cols = [col for col in full_df.columns if col.startswith('S_')]
    
    # Sort amplitude columns to ensure correct order S_0, S_1...
    # Assuming standard sorting might sort S_1, S_10, S_2... so we might need natural sort if necessary.
    # But usually S_0, S_1...S_9, S_10 implies natural sort if numeric part is considered.
    # Let's rely on the order provided or ensure key sorting.
    amplitude_cols.sort(key=lambda x: int(x.split('_')[1]))
    
    print(f"Amplitude columns found: {len(amplitude_cols)}")

    # Prepare X and y
    # src/classifier.py appends frequency code to the END of amplitudes.
    # So X should be [S_0...S_n, Frequency]
    
    # Process Frequency
    # classifier.py: freq_code = 0 if frequency == "low" else 1
    # We must match this.
    
    # Filter valid frequencies
    valid_mask = full_df['Frequency'].isin(['low', 'high'])
    full_df = full_df[valid_mask].copy()
    
    full_df['Frequency_Code'] = full_df['Frequency'].map({'low': 0, 'high': 1})
    
    # Process Amplitudes (Handle NaNs)
    # Check for NaNs
    if full_df[amplitude_cols].isnull().values.any():
        print("NaNs found in amplitude columns. Filling with 0.")
        full_df[amplitude_cols] = full_df[amplitude_cols].fillna(0)
        
    X_amplitudes = full_df[amplitude_cols].values
    X_freq = full_df['Frequency_Code'].values.reshape(-1, 1)
    
    X = np.hstack((X_amplitudes, X_freq))
    
    y = full_df['class_name'].values
    
    # Check if target is not encoded. RF in sklearn handles numeric targets for classification? 
    # RF classifier can handle string labels in y? No, it usually prefers simple targets but recent versions might auto-encode. 
    # Best to Encode.
    # But classifier.py expects the prediction to be the class name string?
    # classifier.py: 
    # prediction = self.model.predict(features)[0]
    # return str(prediction)
    # If the model returns 'Gravel', str('Gravel') is 'Gravel'.
    # If the model returns 0, str(0) is '0'.
    # sklearn classifiers trained on string y usually return string predictions.
    
    print(f"Training RandomForestClassifier with {X.shape[0]} samples and {X.shape[1]} features...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    
    print("Training complete.")
    
    output_path = r'c:\Users\samso\Documents\00 Uni\Semester 9\sonar_mpa\models\sonar_model_v2.pkl'
    print(f"Saving model to {output_path}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(clf, f)
        
    print("Model saved successfully.")

if __name__ == '__main__':
    try:
        retrain()
    except Exception as e:
        print(f"An error occurred: {e}")
