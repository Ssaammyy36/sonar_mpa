import os
import re
import glob
import joblib
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.metrics import confusion_matrix, accuracy_score, classification_report

# --- CONFIGURATION ---
WINDOW_LEN = 155
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_PATH, '../../data')
MODEL_FILE = os.path.join(BASE_PATH, 'sonar_model.pkl')

DATA_DIRS = [
    'messung_08_01_26',
    'messung_15_12_25',
    'überprüfung_08_01_26',
    'messung_09_02_26'
]

EXPECTED_COLS = ['Timestamp', 'class_name', 'Frequency', 'NMEA_Depth_m', 
                 'PulseLength_us', 'Sampling_Freq_Hz', 'Prediction'] + \
                [f'S_{i}' for i in range(400)]

sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 11

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def process_signal_fast(sig, win_len, p_mask, v_start):
    """
    Extracts features (Energy, Peak, Width) and the aligned window from a signal.
    """
    sig_len = len(sig)
    
    # 1. Detect Peak
    roi_start = min(sig_len, p_mask)
    if roi_start >= sig_len:
        peak_idx = 0
    else:
        peak_idx = roi_start + np.argmax(sig[roi_start:])
    
    peak_val_raw = sig[peak_idx] if peak_idx < sig_len else 0
    
    # 2. Detect Valley
    v_s = min(sig_len, v_start)
    v_e = peak_idx
    if v_s >= v_e:
        valley_idx = v_s
    else:
        valley_idx = v_s + np.argmin(sig[v_s:v_e])
    
    valley_val = sig[valley_idx] if valley_idx < sig_len else 0
    
    # 3. Detect Onset
    threshold = valley_val + (peak_val_raw - valley_val) * 0.10
    rise_segment = sig[valley_idx:peak_idx] if valley_idx < peak_idx else np.array([])
    
    if len(rise_segment) == 0:
        onset_abs = valley_idx
    else:
        below_idxs = np.where(rise_segment < threshold)[0]
        if len(below_idxs) > 0:
            onset_abs = valley_idx + below_idxs[-1]
        else:
            onset_abs = valley_idx
            
    # 4. Extract Window
    start_idx = onset_abs
    end_idx = start_idx + win_len
    aligned_window = np.zeros(win_len)
    
    read_start = max(0, start_idx)
    read_end = min(sig_len, end_idx)
    write_start = read_start - start_idx
    
    length = read_end - read_start
    if length > 0 and write_start < win_len:
        # Prevent overflow
        write_end = min(write_start + length, win_len)
        aligned_window[write_start:write_end] = sig[read_start:read_start + (write_end - write_start)]
        
    # 5. Features
    raw_energy = np.sum(aligned_window**2)
    s_val = np.std(aligned_window)
    m_val = np.mean(aligned_window)
    
    if s_val > 1e-9:
        aligned_window_norm = (aligned_window - m_val) / s_val
    else:
        aligned_window_norm = aligned_window - m_val
        
    # Width
    loc = peak_idx - start_idx
    loc = max(0, min(win_len - 1, loc))
    peak_norm = aligned_window_norm[loc]
    half_val = peak_norm * 0.5
    
    left_part = aligned_window_norm[:loc]
    left_idxs = np.where(left_part < half_val)[0]
    left_idx = left_idxs[-1] if len(left_idxs) > 0 else 0
    
    right_part = aligned_window_norm[loc:]
    right_idxs = np.where(right_part < half_val)[0]
    width_idx = (loc + right_idxs[0]) if len(right_idxs) > 0 else (win_len - 1)
    width = width_idx - left_idx
    
    return [raw_energy, peak_val_raw, peak_norm, width], aligned_window_norm

def plot_signal_details(ax, sig, win_len, p_mask, v_start, title):
    """Visualizes the signal processing steps (Peak, Valley, Onset) on a given axis."""
    sig_len = len(sig)
    
    # 1. Re-calculate points (same logic as process_signal)
    roi_start = min(sig_len, p_mask)
    if roi_start >= sig_len:
        peak_idx = 0
    else:
        peak_idx = roi_start + np.argmax(sig[roi_start:])
    
    v_s = min(sig_len, v_start)
    if v_s >= peak_idx:
        valley_idx = v_s
    else:
        valley_idx = v_s + np.argmin(sig[v_s:peak_idx])
        
    peak_val = sig[peak_idx]
    valley_val = sig[valley_idx]
    
    threshold = valley_val + (peak_val - valley_val) * 0.10
    rise_segment = sig[valley_idx:peak_idx] if valley_idx < peak_idx else np.array([])
    
    if len(rise_segment) > 0:
        below_idxs = np.where(rise_segment < threshold)[0]
        onset_abs = valley_idx + (below_idxs[-1] if len(below_idxs) > 0 else 0)
    else:
        onset_abs = valley_idx

    # 2. Draw Plot
    ax.plot(sig, color='#7f8c8d', alpha=0.6, label='Raw Signal')
    ax.plot(peak_idx, peak_val, 'rx', markersize=10, markeredgewidth=2, label='Peak')
    ax.plot(valley_idx, valley_val, 'bv', markersize=10, label='Valley')
    ax.plot(onset_abs, sig[onset_abs], 'go', markersize=8, label='Onset')

    # Visualise Window
    ax.axvspan(onset_abs, onset_abs + win_len, color='#2ecc71', alpha=0.15, label='Window')
    ax.hlines(threshold, valley_idx, peak_idx, colors='orange', linestyles='--', label='Threshold')

    ax.set_title(title)
    ax.legend(loc='upper right', fontsize='small')
    ax.grid(True, alpha=0.3)

def _sniff_csv_separator(filepath):
    with open(filepath, 'r', errors='ignore') as f:
        line = f.readline()
    if line.count(';') > line.count(','):
        return ';', ','
    return ',', '.'

def load_all_data(root_path, dir_names):
    data_frames = []
    print(f"Searching for data in {root_path}...")
    
    for d in dir_names:
        search_pattern = os.path.join(root_path, d, '**', '*.csv')
        files = glob.glob(search_pattern, recursive=True)
        print(f"  -> {d}: Found {len(files)} CSV files.")
        
        for f in files:
            try:
                sep, dec = _sniff_csv_separator(f)
                df = pd.read_csv(
                    f, sep=sep, decimal=dec, 
                    names=EXPECTED_COLS, 
                    header=None, skiprows=1,
                    on_bad_lines='skip', engine='python'
                )
                if len(df.columns) < 5:
                     df = pd.read_csv(
                        f, sep=',', decimal='.', 
                        names=EXPECTED_COLS, 
                        header=None, skiprows=1,
                        on_bad_lines='skip', engine='python'
                    )
                df['source_file'] = f
                data_frames.append(df)
            except Exception as e:
                print(f"Skipping {f}: {e}")
                
    if not data_frames:
        raise RuntimeError("No valid data files found.")
        
    full_df = pd.concat(data_frames, ignore_index=True)
    full_df.fillna(0, inplace=True)
    print(f"Total data loaded: {len(full_df)} rows.")
    return full_df

def extract_features(df_all, win_len):
    unique_files = df_all['source_file'].unique()
    X_list = []
    Y_list = []
    hf_raw_list = []
    lf_raw_list = []
    files_list = []
    
    print(f"Processing pairs from {len(unique_files)} files...")
    
    for f in unique_files:
        df_file = df_all[df_all['source_file'] == f]
        df_high = df_file[df_file['Frequency'].str.lower() == 'high'].sort_values('Timestamp')
        df_low  = df_file[df_file['Frequency'].str.lower() == 'low'].sort_values('Timestamp')
        
        n_samples = min(len(df_high), len(df_low))
        if n_samples == 0: continue
            
        df_high = df_high.iloc[:n_samples]
        df_low  = df_low.iloc[:n_samples]
        
        hf_cols = sorted([c for c in EXPECTED_COLS if c.startswith('S_')], key=natural_sort_key)
        lf_cols = sorted([c for c in EXPECTED_COLS if c.startswith('S_')], key=natural_sort_key)
        
        if any(c not in df_high.columns for c in hf_cols): continue
            
        data_hf = df_high[hf_cols].values
        data_lf = df_low[lf_cols].values
        labels = df_high['class_name'].values
        
        for i in range(n_samples):
            # Optimised parameters for High vs Low frequency (matching training script)
            stats_hf, win_hf = process_signal_fast(data_hf[i], win_len, 30, 20)
            stats_lf, win_lf = process_signal_fast(data_lf[i], win_len, 78, 55)
            
            X_list.append(np.concatenate([stats_hf, stats_lf, win_hf, win_lf]))
            Y_list.append(labels[i])
            hf_raw_list.append(data_hf[i])
            lf_raw_list.append(data_lf[i])
            files_list.append(f)
            
    return np.array(X_list), np.array(Y_list), np.array(hf_raw_list), np.array(lf_raw_list), np.array(files_list)

if __name__ == "__main__":
    try:
        # 1. Load Data
        df_all = load_all_data(DATA_ROOT, DATA_DIRS)
        
        # 2. Extract Features
        X_all, Y_all, raw_hf_all, raw_lf_all, files_all = extract_features(df_all, WINDOW_LEN)
        
        if len(Y_all) == 0:
            raise RuntimeError("No valid samples extracted.")
            
        print(f"\nTotal Samples for Evaluation: {len(Y_all)}")
        
        if len(Y_all) == 0:
            raise RuntimeError("No valid samples extracted.")
            
        print(f"\nTotal Samples for Evaluation: {len(Y_all)}")
        
        # 3. Load Model (Auto-detect latest)
        model_files = glob.glob(os.path.join(BASE_PATH, 'sonar_model_*.pkl'))
        if not model_files:
            # Fallback for backward compatibility
            if os.path.exists(MODEL_FILE):
                latest_model = MODEL_FILE
            else:
                raise FileNotFoundError("No 'sonar_model_*.pkl' files found.")
        else:
            # Sort by modification time, newest first
            latest_model = max(model_files, key=os.path.getmtime)
            
        print(f"Loading model from {latest_model}...")
        checkpoint = joblib.load(latest_model)
        model = checkpoint['model']
        pca = checkpoint['pca']
        scaler = checkpoint['scaler']
        
        # 4. Preprocess Pipeline
        NUM_STATS = 8
        X_stats = X_all[:, :NUM_STATS]
        X_wave = X_all[:, NUM_STATS:]
        
        # Scale & Transform
        if scaler:
            X_wave_std = scaler.transform(X_wave)
        else:
            X_wave_std = X_wave
            
        if pca:
            X_pca = pca.transform(X_wave_std)
            wave_features = X_pca
        else:
            wave_features = X_wave_std
        
        # Combine
        X_final = np.hstack([X_stats, wave_features])
        
        # 5. Evaluate
        Y_pred = model.predict(X_final)
        acc = accuracy_score(Y_all, Y_pred)
        
        print("\n" + "="*40)
        print(f"FULL DATASET ACCURACY: {acc * 100:.1f}%")
        print("="*40)
        print("\nClassification Report:")
        print(classification_report(Y_all, Y_pred))

        # 6. Error Analysis per Dataset (Text Report)
        print("\n" + "="*40)
        print("ERROR ANALYSIS PER DATASET (FULL DATA)")
        print("="*40)
        
        errors_mask = Y_all != Y_pred
        incorrect_files = [os.path.basename(f) for f in files_all[errors_mask]]
        
        # Count total vs incorrect per file
        total_file_counts = pd.Series([os.path.basename(f) for f in files_all]).value_counts().sort_index()
        error_file_counts = pd.Series(incorrect_files).value_counts().reindex(total_file_counts.index, fill_value=0)
        
        df_errors = pd.DataFrame({'Total Samples': total_file_counts, 'Wrong Predictions': error_file_counts})
        df_errors['Error Rate %'] = (df_errors['Wrong Predictions'] / df_errors['Total Samples'] * 100).fillna(0)
        
        print(df_errors.sort_values('Error Rate %', ascending=False).to_string(formatters={'Error Rate %': '{:.1f}%'.format}))
        print("="*40)
        
        # 7. Visualization - Separate Figures
        print("\nVisualizing Results...")
        
        # Figure 1: Signal Examples
        plt.figure(figsize=(12, 6))
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)
        sample_label = Y_all[0]
        # Use first sample for visualization
        plot_signal_details(ax1, raw_hf_all[0], WINDOW_LEN, 30, 20, f"HIGH Frequency - {sample_label}")
        plot_signal_details(ax2, raw_lf_all[0], WINDOW_LEN, 78, 55, f"LOW Frequency - {sample_label}")
        plt.tight_layout()
        plt.show()

        # Figure 2: Data Distribution (Total Samples per File)
        plt.figure(figsize=(12, 6))
        total_file_counts.plot(kind='bar', color='#3498db', alpha=0.8)
        plt.title("Total Samples per Source File")
        plt.ylabel("Number of Samples")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

        # Figure 3: Confusion Matrix
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(Y_all, Y_pred)
        classes = np.unique(Y_all)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
        plt.title(f"Confusion Matrix (Full Data, Acc: {acc:.1%})")
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.tight_layout()
        plt.show()
        
        # Figure 4: Error Analysis per Dataset (Plot)
        plt.figure(figsize=(12, 6))
        df_errors[['Total Samples', 'Wrong Predictions']].plot(kind='bar', color=['#95a5a6', '#e74c3c'], width=0.8)
        plt.title("Error Analysis: Wrong Predictions per Source File")
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"\nERROR: {e}")
