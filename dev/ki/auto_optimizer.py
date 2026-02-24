import os
import re
import glob
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import joblib
from datetime import datetime

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import StratifiedKFold, ParameterGrid, cross_val_score
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, classification_report


# Models
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier

# --- CONFIGURATION ---
WINDOW_LEN = 155
RANDOM_STATE = 42
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_PATH, '../../data')
RESULTS_DIR = os.path.join(BASE_PATH, 'optimization_results')
os.makedirs(RESULTS_DIR, exist_ok=True)

DATA_DIRS = [
    'messung_08_01_26',
    'messung_15_12_25',
    'messung_09_02_26',
    'messung_10_02_26'
]

EXPECTED_COLS = ['Timestamp', 'class_name', 'Frequency', 'NMEA_Depth_m', 
                 'PulseLength_us', 'Sampling_Freq_Hz', 'Prediction'] + \
                [f'S_{i}' for i in range(400)]

# --- PREPROCESSING GRID ---
# Explicitly requested PCA range (Reduced to 3 values + None)
PCA_VARIANCES = [0.24, 0.95, 0.99]
# Add 'None' to represent "No PCA"
PCA_OPTIONS = [None] + PCA_VARIANCES

SCALER_OPTIONS = [None, 'StandardScaler']

# --- MODEL HYPERPARAMETER GRIDS ---
# We use lists of dictionaries for more flexibility if needed
PARAM_GRIDS = {
    'rf': {
        'model': RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1),
        'params': {
            'n_estimators': [100, 300],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5]
        }
    },
    'svm': {
        'model': SVC(random_state=RANDOM_STATE, max_iter=10000), # added max_iter to prevent hanging on unscaled data
        'params': {
            'C': [0.1, 1, 10],
            'kernel': ['rbf', 'linear'],
            'gamma': ['scale', 'auto']
        }
    },
    'knn': {
        'model': KNeighborsClassifier(n_jobs=-1),
        'params': {
            'n_neighbors': [3, 5, 7, 11],
            'weights': ['uniform', 'distance'],
            'metric': ['euclidean', 'manhattan']
        }
    },
    'gb': {
        'model': GradientBoostingClassifier(random_state=RANDOM_STATE),
        'params': {
            'n_estimators': [100, 200],
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 5]
        }
    },
    'mlp': {
        'model': MLPClassifier(random_state=RANDOM_STATE, max_iter=1000),
        'params': {
            'hidden_layer_sizes': [(50,), (100,), (50, 50)],
            'activation': ['relu', 'tanh'],
            'learning_rate_init': [0.001, 0.01]
        }
    }
}

# --- HELPER FUNCTIONS ---

# --- HELPER FUNCTIONS ---

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def process_signal_fast(sig, win_len, p_mask, v_start):
    # (No changes to signal processing)
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

def create_pipeline(model_type, params, use_scaler, pca_var):
    from sklearn.pipeline import Pipeline
    
    steps = []
    
    # 1. Scaling
    if use_scaler == 'StandardScaler':
        steps.append(('scaler', StandardScaler()))
        
    # 2. PCA
    if pca_var is not None:
        # Note: We rely on the valid float/int passing. 
        # If float < 1.0, it selects variance. If int, it selects components.
        # Pipeline handles this dynamically.
        steps.append(('pca', PCA(n_components=pca_var, random_state=RANDOM_STATE)))

    # 3. Model
    model_conf = PARAM_GRIDS[model_type]
    # We clone to avoid mutating the global definition
    from sklearn.base import clone
    clf = clone(model_conf['model'])
    clf.set_params(**params)
    steps.append(('model', clf))
    
    return Pipeline(steps)

def evaluate_configuration(X_train, Y_train, X_test, Y_test, model_type, params, use_scaler, pca_var):
    """
    Trains and evaluates a specific configuration using CV.
    """
    
    pipeline = create_pipeline(model_type, params, use_scaler, pca_var)
    
    # CV Evaluation
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    
    # We apply the pipeline to the WHOLE feature vector (X_train)
    # This might differ slightly from original manual split logic but is more standard.
    try:
        cv_scores = cross_val_score(pipeline, X_train, Y_train, cv=cv, scoring='f1_weighted', n_jobs=1)
        avg_cv_f1 = np.mean(cv_scores)
    except Exception as e:
        # Catch errors like PCA n_components > n_samples
        print(f"CV Error ({model_type}): {e}") 
        avg_cv_f1 = 0.0

    # Retrain on Full Train for Final Test Score (Reporting & debugging)
    try:
        pipeline.fit(X_train, Y_train)
        Y_pred_test = pipeline.predict(X_test)
        test_acc = accuracy_score(Y_test, Y_pred_test)
        
        # Check actual PCA components if applicable
        actual_components = 0
        if 'pca' in pipeline.named_steps:
            actual_components = pipeline.named_steps['pca'].n_components_
        elif 'model' in pipeline.named_steps:
             # If no PCA, features involved = input features
             pass
             
    except Exception as e:
        test_acc = 0.0
        Y_pred_test = np.zeros_like(Y_test)
        actual_components = 0
    
    return {
        'model_type': model_type,
        'params': params,
        'scaler': use_scaler,
        'pca_var': pca_var,
        'f1_score': avg_cv_f1, # OPTIMIZE ON CV SCORE
        'accuracy': test_acc,  # Report Test Acc
        'pca_components': actual_components,
        'y_true': Y_test,
        'y_pred': Y_pred_test
    }

def run_optimization():
    print("Loading Data...")
    X_all, Y_all = load_data_and_extract()
    print(f"Total Samples: {len(Y_all)}")
    print(f"Classes: {np.unique(Y_all)}")
    
    # Global Train/Test Split
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    
    le = LabelEncoder()
    Y_all = le.fit_transform(Y_all)
    print(f"Classes Encoded: {le.classes_}")
    
    X_train, X_test, Y_train, Y_test = train_test_split(
        X_all, Y_all, test_size=0.2, random_state=RANDOM_STATE, stratify=Y_all
    )
    
    all_results = []
    # ... (rest of loop is same) ...
    # [truncated for tool call, I will target the chunks separately]
    best_per_model = {}
    
    total_iterations = 0
    # Calculate total iterations for progress bar
    for m_name, m_conf in PARAM_GRIDS.items():
        n_params = len(list(ParameterGrid(m_conf['params'])))
        n_preproc = len(SCALER_OPTIONS) * len(PCA_OPTIONS)
        total_iterations += n_params * n_preproc
        
    print(f"\nStarting Optimization... ({total_iterations} total configurations)")
    
    idx = 0
    for model_name, config in PARAM_GRIDS.items():
        print(f"\nModel: {model_name.upper()}")
        
        best_f1_this_model = -1
        best_res_this_model = None
        
        param_list = list(ParameterGrid(config['params']))
        
        for params in param_list:
            for scaler_opt in SCALER_OPTIONS:
                for pca_opt in PCA_OPTIONS:
                    idx += 1
                    if idx % 10 == 0:
                        print(f"  Progress: {idx}/{total_iterations}...", end='\r')
                    
                    res = evaluate_configuration(
                        X_train, Y_train, X_test, Y_test,
                        model_name, params, 
                        scaler_opt, 
                        pca_opt
                    )
                    
                    if res['f1_score'] > best_f1_this_model:
                        best_f1_this_model = res['f1_score']
                        best_res_this_model = res
                        
                    all_results.append(res)
        
        if best_res_this_model:
            best_per_model[model_name] = best_res_this_model
            print(f"  Best {model_name.upper()}: F1={best_f1_this_model:.4f} | Scaler={best_res_this_model['scaler']} | PCA={best_res_this_model['pca_var']}")

    # --- REPORTING ---
    print("\n" + "="*60)
    print("OPTIMIZATION RESULTS (Weighted F1-Score)")
    print("="*60)
    
    RESULTS_DIR = os.path.join(BASE_PATH, 'optimization_results')
    MODELS_DIR = os.path.join(BASE_PATH, 'models') # Ensure this path matches train_model.py convention if possible
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    report_path = os.path.join(RESULTS_DIR, 'best_params.txt')
    with open(report_path, 'w') as f:
        f.write("OPTIMIZATION RESULTS\n")
        f.write("====================\n\n")
        
        for m_name, res in best_per_model.items():
            line1 = f"Model: {m_name.upper()}"
            line2 = f"  F1-Score: {res['f1_score']:.4f} (Accuracy: {res['accuracy']:.4f})"
            line3 = f"  Scaler: {res['scaler']}"
            line4 = f"  PCA Variance: {res['pca_var']} (Components used: {res['pca_components']})"
            line5 = f"  Hyperparameters: {res['params']}"
            
            print(line1)
            print(line2)
            print(line3)
            print(line4)
            print(line5)
            print("-" * 30)
            
            f.write(line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5 + "\n")
            f.write("-" * 30 + "\n")
            
            # --- SAVE MODEL ---
            # Retrain best configuration on X_train (or X_all if preferred, X_train is safer for validation consistency)
            print(f"  Saving best {m_name.upper()} model...")
            final_pipeline = create_pipeline(res['model_type'], res['params'], res['scaler'], res['pca_var'])
            final_pipeline.fit(X_train, Y_train)
            
            # Filename: sonar_model_{algo}_opt.pkl
            model_filename = f"sonar_model_{m_name}_opt.pkl"
            model_path = os.path.join(MODELS_DIR, model_filename)
            
            # Save extra metadata/artifacts 
            # We assume user loads it and knows it's a pipeline.
            # CRITICAL: Save classes so we can decode predictions later without guessing
            model_data = {
                'model': final_pipeline,
                'classes': le.classes_
            }
            joblib.dump(model_data, model_path)
            print(f"  Saved to: {model_path}")
            
            print("-" * 30)

    # --- VISUALIZATION ---
    # 1. Bar Chart Comparison
    plt.figure(figsize=(10, 6))
    models = list(best_per_model.keys())
    scores = [best_per_model[m]['f1_score'] for m in models]
    
    sns.barplot(x=models, y=scores, palette='viridis')
    plt.title("Best F1-Score by Model Type")
    plt.ylim(0, 1.0)
    plt.ylabel("Weighted F1 Score")
    
    for i, v in enumerate(scores):
        plt.text(i, v + 0.01, f"{v:.3f}", ha='center', fontweight='bold')
        
    plt.savefig(os.path.join(RESULTS_DIR, 'model_comparison.png'))
    plt.close()
    
    # 2. Confusion Matrices for Best Models
    for m_name, res in best_per_model.items():
        plt.figure(figsize=(6, 5))
        cm = confusion_matrix(res['y_true'], res['y_pred'])
        # Use encoded classes if available
        labels = le.classes_ if 'le' in locals() else sorted(np.unique(res['y_true']))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
        plt.title(f"Best {m_name.upper()} Matrix (F1: {res['f1_score']:.2f})")
        plt.ylabel('True')
        plt.xlabel('Predicted')
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, f'confusion_matrix_{m_name}.png'))
        plt.close()
        
    print(f"\nResults saved to: {RESULTS_DIR}")
    print(f"Optimized Models saved to: {MODELS_DIR}")

if __name__ == "__main__":
    run_optimization()