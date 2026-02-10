import os
import re
import glob
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score

# --- CONFIGURATION ---
WINDOW_LEN = 155
RANDOM_STATE = 42
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_PATH, '../../data')

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
plt.rcParams['figure.figsize'] = (12, 6)

# --- HELPER FUNCTIONS (Reused) ---

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def process_signal_fast(sig, win_len, p_mask, v_start):
    sig_len = len(sig)
    
    # Peak
    roi_start = min(sig_len, p_mask)
    if roi_start >= sig_len: peak_idx = 0
    else: peak_idx = roi_start + np.argmax(sig[roi_start:])
    peak_val_raw = sig[peak_idx] if peak_idx < sig_len else 0
    
    # Valley
    v_s = min(sig_len, v_start)
    v_e = peak_idx
    if v_s >= v_e: valley_idx = v_s
    else: valley_idx = v_s + np.argmin(sig[v_s:v_e])
    valley_val = sig[valley_idx] if valley_idx < sig_len else 0
    
    # Onset
    threshold = valley_val + (peak_val_raw - valley_val) * 0.10
    rise_segment = sig[valley_idx:peak_idx] if valley_idx < peak_idx else np.array([])
    if len(rise_segment) == 0: onset_abs = valley_idx
    else:
        below_idxs = np.where(rise_segment < threshold)[0]
        if len(below_idxs) > 0: onset_abs = valley_idx + below_idxs[-1]
        else: onset_abs = valley_idx
            
    # Window
    start_idx = onset_abs
    end_idx = start_idx + win_len
    aligned_window = np.zeros(win_len)
    
    read_start = max(0, start_idx)
    read_end = min(sig_len, end_idx)
    write_start = read_start - start_idx
    
    length = read_end - read_start
    if length > 0 and write_start < win_len:
        write_end = min(write_start + length, win_len)
        aligned_window[write_start:write_end] = sig[read_start:read_start + (write_end - write_start)]
        
    # Features
    raw_energy = np.sum(aligned_window**2)
    s_val = np.std(aligned_window)
    m_val = np.mean(aligned_window)
    if s_val > 1e-9: aligned_window_norm = (aligned_window - m_val) / s_val
    else: aligned_window_norm = aligned_window - m_val
        
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

def _sniff_csv_separator(filepath):
    with open(filepath, 'r', errors='ignore') as f:
        line = f.readline()
    if line.count(';') > line.count(','): return ';', ','
    return ',', '.'

def load_data_and_extract():
    """Loads all data and extracts features."""
    data_frames = []
    print(f"Searching for data in {DATA_ROOT}...")
    for d in DATA_DIRS:
        files = glob.glob(os.path.join(DATA_ROOT, d, '**', '*.csv'), recursive=True)
        for f in files:
            try:
                sep, dec = _sniff_csv_separator(f)
                df = pd.read_csv(f, sep=sep, decimal=dec, names=EXPECTED_COLS, header=None, skiprows=1, on_bad_lines='skip', engine='python')
                if len(df.columns) < 5:
                     df = pd.read_csv(f, sep=',', decimal='.', names=EXPECTED_COLS, header=None, skiprows=1, on_bad_lines='skip', engine='python')
                df['source_file'] = f
                data_frames.append(df)
            except Exception: pass
            
    if not data_frames: raise RuntimeError("No valid data files found.")
    full_df = pd.concat(data_frames, ignore_index=True).fillna(0)
    
    # Pair & Extract
    unique_files = full_df['source_file'].unique()
    X_list, Y_list = [], []
    
    for f in unique_files:
        df_file = full_df[full_df['source_file'] == f]
        df_high = df_file[df_file['Frequency'].str.lower() == 'high'].sort_values('Timestamp')
        df_low = df_file[df_file['Frequency'].str.lower() == 'low'].sort_values('Timestamp')
        
        n = min(len(df_high), len(df_low))
        if n == 0: continue
            
        df_high, df_low = df_high.iloc[:n], df_low.iloc[:n]
        hf_cols = sorted([c for c in EXPECTED_COLS if c.startswith('S_')], key=natural_sort_key)
        lf_cols = sorted([c for c in EXPECTED_COLS if c.startswith('S_')], key=natural_sort_key)
        
        if any(c not in df_high.columns for c in hf_cols): continue
            
        data_hf, data_lf = df_high[hf_cols].values, df_low[lf_cols].values
        labels = df_high['class_name'].values
        
        for i in range(n):
            stats_hf, win_hf = process_signal_fast(data_hf[i], WINDOW_LEN, 30, 20)
            stats_lf, win_lf = process_signal_fast(data_lf[i], WINDOW_LEN, 78, 55)
            # Full feature vector: 8 stats + 310 raw points
            X_list.append(np.concatenate([stats_hf, stats_lf, win_hf, win_lf]))
            Y_list.append(labels[i])
            
    return np.array(X_list), np.array(Y_list)

# --- EXPERIMENTS ---

def run_experiment_A(X_train, X_test, Y_train, Y_test):
    print("\n" + "="*50)
    print("EXPERIMENT A: Preprocessing Impact")
    print("="*50)
    
    results = []
    
    # Split into Stats (first 8) and Wave (rest)
    NUM_STATS = 8
    
    # 1. RAW (No Scaler, No PCA)
    # We use all features directly
    model = RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE)
    model.fit(X_train, Y_train)
    acc = accuracy_score(Y_test, model.predict(X_test))
    results.append({'Config': 'No Scaler, No PCA', 'Accuracy': acc})
    print(f"1. No Scaler, No PCA: {acc*100:.1f}%")

    # 2. SCALED ONLY
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)
    model.fit(X_train_sc, Y_train)
    acc = accuracy_score(Y_test, model.predict(X_test_sc))
    results.append({'Config': 'Scaler Only', 'Accuracy': acc})
    print(f"2. Scaler Only:       {acc*100:.1f}%")
    
    # 3. PCA ONLY (Fit PCA on raw wave data)
    # Note: PCA usually requires centering, but we test strictly "No Scaler"
    X_wave_train = X_train[:, NUM_STATS:]
    X_wave_test = X_test[:, NUM_STATS:]
    X_stats_train = X_train[:, :NUM_STATS]
    X_stats_test = X_test[:, :NUM_STATS]
    
    pca = PCA(n_components=0.24, random_state=RANDOM_STATE) # Use same ratio target
    X_pca_train = pca.fit_transform(X_wave_train)
    X_pca_test = pca.transform(X_wave_test)
    
    X_train_pca = np.hstack([X_stats_train, X_pca_train])
    X_test_pca = np.hstack([X_stats_test, X_pca_test])
    
    model.fit(X_train_pca, Y_train)
    acc = accuracy_score(Y_test, model.predict(X_test_pca))
    results.append({'Config': 'PCA Only (No Scaler)', 'Accuracy': acc})
    print(f"3. PCA Only:          {acc*100:.1f}% (Components: {pca.n_components_})")
    
    # 4. STANDARD (Scaler + PCA)
    scaler_wave = StandardScaler()
    X_wave_train_std = scaler_wave.fit_transform(X_wave_train)
    X_wave_test_std = scaler_wave.transform(X_wave_test)
    
    pca_std = PCA(n_components=0.24, random_state=RANDOM_STATE)
    X_pca_train_std = pca_std.fit_transform(X_wave_train_std)
    X_pca_test_std = pca_std.transform(X_wave_test_std)
    
    X_train_std = np.hstack([X_stats_train, X_pca_train_std])
    X_test_std = np.hstack([X_stats_test, X_pca_test_std])
    
    model.fit(X_train_std, Y_train)
    acc = accuracy_score(Y_test, model.predict(X_test_std))
    results.append({'Config': 'Scaler + PCA (Std)', 'Accuracy': acc})
    print(f"4. Scaler + PCA:      {acc*100:.1f}% (Components: {pca_std.n_components_})")
    
    # Plot results
    df_res = pd.DataFrame(results)
    plt.figure(figsize=(10, 5))
    sns.barplot(data=df_res, x='Config', y='Accuracy', hue='Config', palette='viridis', legend=False)
    plt.title("Impact of Preprocessing on Model Accuracy")
    plt.ylim(0, 1.0)
    for index, row in df_res.iterrows():
        plt.text(index, row.Accuracy + 0.02, f'{row.Accuracy*100:.1f}%', color='black', ha="center")
    plt.savefig(os.path.join(BASE_PATH, 'experiment_A_results.png'))
    plt.close()

def run_experiment_B(X_train, X_test, Y_train, Y_test):
    print("\n" + "="*50)
    print("EXPERIMENT B: PCA Variance Optimization")
    print("="*50)
    
    NUM_STATS = 8
    X_wave_train = X_train[:, NUM_STATS:]
    X_wave_test = X_test[:, NUM_STATS:]
    X_stats_train = X_train[:, :NUM_STATS]
    X_stats_test = X_test[:, :NUM_STATS]
    
    # Always scale before PCA for this test (best practice)
    scaler = StandardScaler()
    X_wave_train_std = scaler.fit_transform(X_wave_train)
    X_wave_test_std = scaler.transform(X_wave_test)
    
    variances = np.linspace(0.10, 0.99, 20)
    results = []
    
    best_acc = 0
    best_var = 0
    
    print("Testing variances:", end=" ")
    for var in variances:
        # PCA
        pca = PCA(n_components=var, random_state=RANDOM_STATE)
        X_pca_train = pca.fit_transform(X_wave_train_std)
        X_pca_test = pca.transform(X_wave_test_std)
        
        # Combine
        X_train_final = np.hstack([X_stats_train, X_pca_train])
        X_test_final = np.hstack([X_stats_test, X_pca_test])
        
        # Train
        model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE) # Faster for loop
        model.fit(X_train_final, Y_train)
        
        acc = accuracy_score(Y_test, model.predict(X_test_final))
        n_comps = pca.n_components_
        
        results.append({
            'Variance': var,
            'Accuracy': acc,
            'Components': n_comps
        })
        
        if acc > best_acc:
            best_acc = acc
            best_var = var
            
        print(".", end="", flush=True)
        
    print(f"\n\nBest Accuracy: {best_acc*100:.1f}% with Variance: {best_var:.2f}")
    
    # Plot
    df_res = pd.DataFrame(results)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    sns.lineplot(data=df_res, x='Variance', y='Accuracy', ax=ax1, marker='o', color='b', label='Accuracy')
    ax1.set_ylabel('Test Accuracy', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_ylim(0, 1.05)
    
    ax2 = ax1.twinx()
    sns.lineplot(data=df_res, x='Variance', y='Components', ax=ax2, marker='x', color='r', linestyle='--', label='Num Components')
    ax2.set_ylabel('Number of Components', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    plt.title(f"Optimal PCA Variance Search (Best: {best_var:.2f})")
    plt.savefig(os.path.join(BASE_PATH, 'experiment_B_results.png'))
    plt.close()

if __name__ == "__main__":
    try:
        # Load
        X_all, Y_all = load_data_and_extract()
        print(f"Total Samples: {len(Y_all)}")
        
        # Split (Single split for consistency across all tests)
        X_train, X_test, Y_train, Y_test = train_test_split(
            X_all, Y_all, test_size=0.2, random_state=RANDOM_STATE, stratify=Y_all
        )
        print(f"Train: {len(X_train)} | Test: {len(X_test)}")
        
        # Run Experiments
        run_experiment_A(X_train, X_test, Y_train, Y_test)
        run_experiment_B(X_train, X_test, Y_train, Y_test)
        
    except Exception as e:
        print(f"Error: {e}")
