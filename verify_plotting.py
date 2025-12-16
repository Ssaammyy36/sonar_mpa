
import pandas as pd
import os
import matplotlib.pyplot as plt

# Pfad zu den Daten
base_path = r'c:\Users\samso\Documents\00 Uni\Semester 9\sonar_mpa\data\messung_15_12_25'
files = [
    'grabel_training_data.csv',
    'sand_training_data.csv', 
    'stone_training_data.csv'
]

# Daten einlesen
data_frames = []
for file in files:
    file_path = os.path.join(base_path, file)
    try:
        df = pd.read_csv(file_path, sep=';')
        print(f"Loaded {file} with shape {df.shape}")
        data_frames.append(df)
    except Exception as e:
        print(f"Error loading {file}: {e}")

if not data_frames:
    print("No data loaded.")
    exit(1)

# Zusammenfügen
full_df = pd.concat(data_frames, ignore_index=True)

# Filtern
amplitude_cols = [col for col in full_df.columns if col.startswith('S_')]
selected_cols = ['class_name', 'Frequency'] + amplitude_cols

# Check if Frequency exists
if 'Frequency' not in full_df.columns:
    print("Error: 'Frequency' column not found in data!")
    print(f"Columns found: {full_df.columns}")
    exit(1)

final_df = full_df[selected_cols]
print(f"Final DF shape: {final_df.shape}")

# Plotting logic verify
combinations = final_df[['class_name', 'Frequency']].drop_duplicates().values
combinations = sorted(combinations, key=lambda x: (x[0], x[1]))
print(f"Found combinations: {combinations}")

if len(combinations) != 6:
    print(f"Warning: Expected 6 combinations, found {len(combinations)}")

print("Verification script finished successfully.")
