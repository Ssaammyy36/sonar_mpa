import os
import re
import glob
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Sklearn Imports
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

# Modelle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier

import matplotlib
matplotlib.use('Agg')  # Verhindert GUI-Fenster, speichert nur PDF

# --- 1. CONFIGURATION & STYLE ---

# Plotting Style
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'font.family': 'sans-serif',
    'figure.autolayout': True,
})

# Farben für Modelle
MODEL_COLORS = {
    'RF': '#2c3e50',   # Dark Blue
    'GB': '#27ae60',   # Green
    'SVM': '#34495e',  # Desaturated Blue
    'MLP': '#8e44ad',  # Purple
    'KNN': '#16a085'   # Teal
}

# GEWÜNSCHTE REIHENFOLGE DER MODELLE
MODEL_ORDER = ['RF', 'GB', 'SVM', 'MLP', 'KNN']

# Pfade & Parameter
WINDOW_LEN = 155
RANDOM_STATE = 42
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_PATH, '../../data')
OUTPUT_DIR = os.path.join(BASE_PATH, 'thesis_plots_final')
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_DIRS = [
    'messung_08_01_26', 'messung_15_12_25', 'messung_09_02_26', 'messung_10_02_26'
]

EXPECTED_COLS = ['Timestamp', 'class_name', 'Frequency', 'NMEA_Depth_m',
                 'PulseLength_us', 'Sampling_Freq_Hz', 'Prediction'] + \
    [f'S_{i}' for i in range(400)]

# --- 2. DEFINITION DER BESTEN MODELLE ---
BEST_MODELS = {
    'RF': {
        'pipeline': [('model', RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_split=2, random_state=RANDOM_STATE))]
    },
    'GB': {
        'pipeline': [('model', GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=3, random_state=RANDOM_STATE))]
    },
    'SVM': {
        'pipeline': [('scaler', StandardScaler()), ('pca', PCA(n_components=0.99, random_state=RANDOM_STATE)), ('model', SVC(C=1, kernel='rbf', gamma='scale', random_state=RANDOM_STATE))]
    },
    'MLP': {
        'pipeline': [('scaler', StandardScaler()), ('model', MLPClassifier(hidden_layer_sizes=(100,), activation='tanh', learning_rate_init=0.01, max_iter=1000, random_state=RANDOM_STATE))]
    },
    'KNN': {
        'pipeline': [('scaler', StandardScaler()), ('model', KNeighborsClassifier(n_neighbors=11, weights='distance', metric='manhattan'))]
    }
}

# --- 3. HELPER FUNCTIONS (Signal Processing & Loading) ---


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def _sniff_csv_separator(filepath):
    with open(filepath, 'r', errors='ignore') as f:
        line = f.readline()
    return ';' if line.count(';') > line.count(',') else ','


def process_signal_fast(sig, win_len, p_mask, v_start):
    """
    Identische Signalverarbeitung wie zuvor.
    """
    sig_len = len(sig)
    roi_start = min(sig_len, p_mask)
    if roi_start >= sig_len:
        peak_idx = 0
    else:
        peak_idx = roi_start + np.argmax(sig[roi_start:])
    peak_val_raw = sig[peak_idx] if peak_idx < sig_len else 0

    v_s = min(sig_len, v_start)
    v_e = peak_idx
    if v_s >= v_e:
        valley_idx = v_s
    else:
        valley_idx = v_s + np.argmin(sig[v_s:v_e])
    valley_val = sig[valley_idx] if valley_idx < sig_len else 0

    threshold = valley_val + (peak_val_raw - valley_val) * 0.10
    rise_segment = sig[valley_idx:peak_idx] if valley_idx < peak_idx else np.array([
    ])

    if len(rise_segment) == 0:
        onset_abs = valley_idx
    else:
        below_idxs = np.where(rise_segment < threshold)[0]
        if len(below_idxs) > 0:
            onset_abs = valley_idx + below_idxs[-1]
        else:
            onset_abs = valley_idx

    start_idx = onset_abs
    end_idx = start_idx + win_len
    aligned_window = np.zeros(win_len)

    read_start = max(0, start_idx)
    read_end = min(sig_len, end_idx)
    write_start = read_start - start_idx

    length = read_end - read_start
    if length > 0 and write_start < win_len:
        write_end = min(write_start + length, win_len)
        aligned_window[write_start:write_end] = sig[read_start:read_start +
                                                    (write_end - write_start)]

    s_val = np.std(aligned_window)
    m_val = np.mean(aligned_window)
    if s_val > 1e-9:
        aligned_window_norm = (aligned_window - m_val) / s_val
    else:
        aligned_window_norm = aligned_window - m_val

    raw_energy = np.sum(aligned_window**2)

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


def load_data_with_filenames():
    data_frames = []
    print(f"Suche Daten in {DATA_ROOT}...")

    for d in DATA_DIRS:
        files = glob.glob(os.path.join(
            DATA_ROOT, d, '**', '*.csv'), recursive=True)
        for f in files:
            try:
                sep = _sniff_csv_separator(f)
                df = pd.read_csv(f, sep=sep, decimal='.', names=EXPECTED_COLS,
                                 header=None, skiprows=1, on_bad_lines='skip', engine='python')
                if len(df.columns) < 5:
                    df = pd.read_csv(f, sep=sep, decimal=',', names=EXPECTED_COLS,
                                     header=None, skiprows=1, on_bad_lines='skip', engine='python')

                path_parts = os.path.normpath(f).split(os.sep)
                dataset_name = next(
                    (p for p in path_parts if 'messung' in p.lower()), 'unknown')

                df['dataset_source'] = dataset_name
                df['source_file'] = f
                data_frames.append(df)
            except Exception:
                pass

    if not data_frames:
        raise RuntimeError("Keine gültigen Datendateien gefunden.")
    full_df = pd.concat(data_frames, ignore_index=True).fillna(0)

    unique_files = full_df['source_file'].unique()
    X_list, Y_list, Dataset_list = [], [], []

    print(f"Verarbeite {len(unique_files)} Dateien...")

    for f in unique_files:
        df_file = full_df[full_df['source_file'] == f]
        df_high = df_file[df_file['Frequency'].str.lower() ==
                          'high'].sort_values('Timestamp')
        df_low = df_file[df_file['Frequency'].str.lower() ==
                         'low'].sort_values('Timestamp')

        n = min(len(df_high), len(df_low))
        if n == 0:
            continue

        df_high, df_low = df_high.iloc[:n], df_low.iloc[:n]
        hf_cols = sorted(
            [c for c in EXPECTED_COLS if c.startswith('S_')], key=natural_sort_key)
        lf_cols = sorted(
            [c for c in EXPECTED_COLS if c.startswith('S_')], key=natural_sort_key)

        if any(c not in df_high.columns for c in hf_cols):
            continue

        data_hf, data_lf = df_high[hf_cols].values, df_low[lf_cols].values
        labels = df_high['class_name'].values
        datasets = df_high['dataset_source'].values

        for i in range(n):
            stats_hf, win_hf = process_signal_fast(
                data_hf[i], WINDOW_LEN, 30, 20)
            stats_lf, win_lf = process_signal_fast(
                data_lf[i], WINDOW_LEN, 78, 55)
            X_list.append(np.concatenate([stats_hf, stats_lf, win_hf, win_lf]))
            Y_list.append(labels[i])
            Dataset_list.append(datasets[i])

    return np.array(X_list), np.array(Y_list), np.array(Dataset_list)

# --- 4. PLOTTING FUNCTIONS ---


def plot_feature_importance_advanced(pipeline, feature_names, model_name='RF'):
    """
    Plottet die Feature Importance für Tree-based Models (RF, GB).
    Update: 
    - Layout geändert auf HORIZONTAL (Breitbild).
    - Features auf der X-Achse (Säulen statt Balken).
    - X-Achsen-Labels rotiert für Lesbarkeit.
    """
    # 1. Modell extrahieren
    if 'model' in pipeline.named_steps:
        model = pipeline.named_steps['model']
    else:
        print(f"Kein Modellschritt in Pipeline {model_name} gefunden.")
        return

    if not hasattr(model, 'feature_importances_'):
        return

    importances = model.feature_importances_

    if len(importances) != len(feature_names):
        print("Warnung: Anzahl Features und Importances stimmen nicht überein.")
        return

    df_imp = pd.DataFrame(
        {'Feature': feature_names, 'Importance': importances})
    df_imp = df_imp.sort_values(by='Importance', ascending=False)

    # --- PLOT 1: TOP 20 FEATURES (Säulendiagramm / Vertical Bars) ---
    # Breites Format für horizontale Anordnung
    plt.figure(figsize=(15, 7))

    # ACHTUNG: x und y getauscht -> Features auf X-Achse
    ax = sns.barplot(x='Feature', y='Importance',
                     data=df_imp.head(20), palette='viridis')

    plt.ylabel('Relative Wichtigkeit', fontsize=14)
    plt.xlabel('Merkmal', fontsize=14)

    # X-Achsen Labels (Features) rotieren, damit sie lesbar sind
    ax.tick_params(axis='x', labelsize=12, rotation=45)
    ax.tick_params(axis='y', labelsize=12)

    # Labels sauber ausrichten (Rechtsbündig nach Rotation)
    plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")

    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(
        OUTPUT_DIR, f'feature_importance_top20_{model_name}.pdf'), bbox_inches='tight')
    plt.close()

    # --- PLOT 2: AGGREGIERTE GRUPPEN (Überblick) ---
    def assign_group(name):
        if 'HF' in name:
            if 'S_' in name:
                return 'HF Waveform (Form)'
            else:
                return 'HF Heuristics (Energie)'
        elif 'LF' in name:
            if 'S_' in name:
                return 'LF Waveform (Form)'
            else:
                return 'LF Heuristics (Energie)'
        return 'Other'

    df_imp['Group'] = df_imp['Feature'].apply(assign_group)
    df_grouped = df_imp.groupby('Group')['Importance'].sum(
    ).reset_index().sort_values(by='Importance', ascending=False)

    # Auch hier das Format etwas breiter machen, damit es einheitlich wirkt
    plt.figure(figsize=(10, 6))

    # Auch hier tauschen wir x und y für Konsistenz (Säulen)
    sns.barplot(x='Group', y='Importance', data=df_grouped, palette='mako')

    plt.ylabel('Summierte Wichtigkeit', fontsize=12)
    plt.xlabel('Feature Gruppe', fontsize=12)

    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(
        OUTPUT_DIR, f'feature_importance_grouped_{model_name}.pdf'), bbox_inches='tight')
    plt.close()

    print(f"Feature Importance Plots für {model_name} gespeichert.")


def plot_overfitting_analysis(train_scores, test_scores, model_order):
    """
    Vergleicht Training vs Test F1-Score (Overfitting Check).
    Sortiert nach model_order.
    """
    models = model_order
    # Werte in korrekter Reihenfolge extrahieren
    t_scores = [train_scores[m] for m in models]
    v_scores = [test_scores[m] for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    color_train = '#95a5a6'  # Grau
    color_test = '#2c3e50'   # Dunkelblau

    rects1 = ax.bar(x - width/2, t_scores, width,
                    label='Training', color=color_train)
    rects2 = ax.bar(x + width/2, v_scores, width,
                    label='Test (Blind)', color=color_test)

    ax.set_ylabel('Weighted F1-Score')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.15)

    ax.legend(loc='lower right', framealpha=0.95, fancybox=True)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.savefig(os.path.join(
        OUTPUT_DIR, 'overfitting_analysis.pdf'), bbox_inches='tight')
    plt.close()


def plot_dataset_relative_error(results_store, all_datasets_test, model_order):
    """
    Plottet die relative Fehlerrate pro Datensatz.
    Sortiert die Modelle in der Legende und die Balken gruppiert nach model_order.
    """
    unique_datasets = sorted(np.unique(all_datasets_test))

    dataset_counts = {d: np.sum(all_datasets_test == d)
                      for d in unique_datasets}

    plot_data = []
    # Iteriere über die gewünschte Reihenfolge der Modelle
    for m in model_order:
        errors_mask = results_store[m]['y_true'] != results_store[m]['y_pred']
        error_datasets = results_store[m]['datasets'][errors_mask]

        for d in unique_datasets:
            n_errors = np.sum(error_datasets == d)
            n_total = dataset_counts[d]
            error_rate_pct = (n_errors / n_total * 100) if n_total > 0 else 0

            plot_data.append({
                'Modell': m,
                'Datensatz': d,
                'Fehlerrate (%)': error_rate_pct
            })

    df_plot = pd.DataFrame(plot_data)

    plt.figure(figsize=(10, 6))

    ax = sns.barplot(
        data=df_plot,
        x='Datensatz',
        y='Fehlerrate (%)',
        hue='Modell',
        hue_order=model_order,  # Erzwingt die Reihenfolge in Legende und Plot
        palette=MODEL_COLORS,
        edgecolor='white'
    )

    plt.ylabel('Anteil falsch klassifizierter Messungen [%]')
    plt.xlabel('Messkampagne')
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.legend(title='Modell', loc='upper right',
               framealpha=0.95, fancybox=True)

    ax.yaxis.set_major_formatter(ticker.PercentFormatter())

    plt.tight_layout()
    plt.savefig(os.path.join(
        OUTPUT_DIR, 'relative_error_by_dataset.pdf'), bbox_inches='tight')
    plt.close()


def plot_confusion_matrix_clean(y_true, y_pred, classes, model_name, f1):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(5, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=classes, yticklabels=classes,
                annot_kws={"size": 12, "weight": "bold"})
    plt.ylabel('Tatsächliche Klasse')
    plt.xlabel('Vorhergesagte Klasse')
    plt.tight_layout()
    plt.savefig(os.path.join(
        OUTPUT_DIR, f'cm_{model_name}.pdf'), bbox_inches='tight')
    plt.close()


def export_results_table(model_order, test_scores, pipelines):
    """
    Erstellt eine Textdatei mit der Tabelle für LaTeX.
    Extrahiert automatisch Parameter aus den Pipelines.
    """
    filepath = os.path.join(OUTPUT_DIR, 'final_results_table.txt')

    with open(filepath, 'w') as f:
        f.write("MODElL | F1 (Test) | SCALER | PCA | PARAMETER\n")
        f.write("-" * 80 + "\n")

        for name in model_order:
            pipe = pipelines[name]
            f1 = test_scores[name]

            # 1. Scaler Check
            has_scaler = 'scaler' in pipe.named_steps
            scaler_str = "Std." if has_scaler else "-"

            # 2. PCA Check
            has_pca = 'pca' in pipe.named_steps
            pca_str = str(
                pipe.named_steps['pca'].n_components) if has_pca else "-"

            # 3. Parameters Extraction (Modell ist immer der letzte Schritt 'model')
            model_step = pipe.named_steps['model']
            params = model_step.get_params()

            # Relevante Parameter filtern (hardcoded logic für saubere Ausgabe)
            param_str_list = []
            if name == 'RF':
                param_str_list.append(
                    f"n_estimators: {params['n_estimators']}")
                param_str_list.append(f"max_depth: {params['max_depth']}")
                param_str_list.append(
                    f"min_samples_split: {params['min_samples_split']}")
            elif name == 'GB':
                param_str_list.append(
                    f"n_estimators: {params['n_estimators']}")
                param_str_list.append(
                    f"learning_rate: {params['learning_rate']}")
                param_str_list.append(f"max_depth: {params['max_depth']}")
            elif name == 'SVM':
                param_str_list.append(f"C: {params['C']}")
                param_str_list.append(f"kernel: {params['kernel']}")
                param_str_list.append(f"gamma: {params['gamma']}")
            elif name == 'MLP':
                param_str_list.append(
                    f"hidden_layer_sizes: {params['hidden_layer_sizes']}")
                param_str_list.append(f"activation: {params['activation']}")
                param_str_list.append(
                    f"learning_rate_init: {params['learning_rate_init']}")
            elif name == 'KNN':
                param_str_list.append(f"n_neighbors: {params['n_neighbors']}")
                param_str_list.append(f"weights: {params['weights']}")
                param_str_list.append(f"metric: {params['metric']}")

            # Formatierung für LaTeX Tabelle (bullet points)
            latex_params = "\\begin{tabular}{@{\\textbullet~}l@{}} " + \
                " \\\\ ".join(param_str_list) + " \\end{tabular}"

            # Ausgabe in Datei
            f.write(
                f"{name:<6} | {f1:.4f}    | {scaler_str:<6} | {pca_str:<4} | {latex_params}\n")
            f.write("-" * 80 + "\n")

    print(f"\nTabellen-Daten exportiert nach: {filepath}")

# --- 5. MAIN EXECUTION ---


if __name__ == "__main__":
    try:
        X, Y, Datasets = load_data_with_filenames()
    except Exception as e:
        print(f"Fehler beim Laden der Daten: {e}")
        exit()

    print(
        f"\nDaten geladen: {len(Y)} Samples aus {len(np.unique(Datasets))} Datensätzen.")

    le = LabelEncoder()
    Y_enc = le.fit_transform(Y)
    classes = le.classes_
    print(f"Klassen: {classes}")

    X_train, X_test, Y_train, Y_test, D_train, D_test = train_test_split(
        X, Y_enc, Datasets, test_size=0.2, random_state=RANDOM_STATE, stratify=Y_enc
    )

    train_scores = {}
    test_scores = {}
    results_store = {}
    pipelines_store = {}  # Speichert trainierte Pipelines für Export

    # FEATURE NAMEN DEFINIEREN
    # Reihenfolge muss exakt der in load_data_with_filenames entsprechen:
    # [stats_hf, stats_lf, win_hf, win_lf]
    feat_names = ['HF_Energy', 'HF_PeakRaw', 'HF_PeakNorm', 'HF_Width',
                  'LF_Energy', 'LF_PeakRaw', 'LF_PeakNorm', 'LF_Width'] + \
        [f'HF_S_{i}' for i in range(155)] + \
        [f'LF_S_{i}' for i in range(155)]

    print(f"\nStarte Evaluation (Reihenfolge: {', '.join(MODEL_ORDER)})...")

    # WICHTIG: Iteration nun über die definierte MODEL_ORDER
    for name in MODEL_ORDER:
        config = BEST_MODELS[name]
        print(f"  Modell: {name}...")
        pipe = Pipeline(config['pipeline'])

        pipe.fit(X_train, Y_train)
        pipelines_store[name] = pipe

        y_train_pred = pipe.predict(X_train)
        f1_train = f1_score(Y_train, y_train_pred, average='weighted')
        train_scores[name] = f1_train

        y_test_pred = pipe.predict(X_test)
        f1_test = f1_score(Y_test, y_test_pred, average='weighted')
        test_scores[name] = f1_test

        print(f"    -> Train F1: {f1_train:.3f} | Test F1: {f1_test:.3f}")

        results_store[name] = {
            'y_true': Y_test,
            'y_pred': y_test_pred,
            'datasets': D_test
        }

        plot_confusion_matrix_clean(
            Y_test, y_test_pred, classes, name, f1_test)

        # FEATURE IMPORTANCE PLOTTEN
        if name in ['RF', 'GB']:
            plot_feature_importance_advanced(
                pipelines_store[name], feat_names, model_name=name)

    # Plots mit erzwungener Reihenfolge
    plot_overfitting_analysis(train_scores, test_scores, MODEL_ORDER)
    plot_dataset_relative_error(results_store, D_test, MODEL_ORDER)

    # Export der Tabelle
    export_results_table(MODEL_ORDER, test_scores, pipelines_store)

    print(
        f"\nFertig! Alle Plots und die Tabelle wurden gespeichert in: {OUTPUT_DIR}")
