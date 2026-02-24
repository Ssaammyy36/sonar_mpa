import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import seaborn as sns

# --- KONFIGURATION ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_PATH, '../../data')
FOLDER_NAME = 'messung_10_02_26'
INPUT_FILE = 'sand_training_data.csv'
CSV_PATH = os.path.join(DATA_ROOT, FOLDER_NAME, INPUT_FILE)

# Parameter
WINDOW_LEN = 155
SAMPLE_IDX = 9
HF_MASK = 30
HF_START = 20

# --- STYLING FÜR WISSENSCHAFTLICHE PUBLIKATION (SANS-SERIF) ---
sns.set_theme(style="whitegrid", rc={"axes.grid": True, "grid.linestyle": ":"})

plt.rcParams.update({
    # Schriftart: Serifenlos (Arial/Helvetica Stil)
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],

    # Auch Mathe-Formeln serifenlos machen
    'mathtext.fontset': 'custom',
    'mathtext.rm': 'Arial',
    'mathtext.it': 'Arial:italic',
    'mathtext.bf': 'Arial:bold',

    # Schriftgrößen (angepasst für A4 Breite ~16cm)
    'font.size': 11,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,

    # Figure Größe: 6.4 Zoll ist ca. Textbreite in Standard LaTeX
    'figure.figsize': (6.4, 4.0),
    'figure.dpi': 300
})


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]


def load_hf_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Datei nicht gefunden: {filepath}")
    try:
        df = pd.read_csv(filepath, sep=';')
        if df.shape[1] < 5:
            df = pd.read_csv(filepath, sep=',')
    except:
        df = pd.read_csv(filepath, sep=',')
    df.columns = df.columns.str.strip()
    freq_col = next((c for c in df.columns if c.lower() == 'frequency'), None)
    df_high = df[df[freq_col].str.lower() == 'high'].sort_values('Timestamp')
    sig_cols = sorted(
        [c for c in df.columns if c.startswith('S_')], key=natural_sort_key)
    return df_high[sig_cols].values.astype(float), df_high['class_name'].values


def calculate_points(sig, p_mask, v_start):
    sig_len = len(sig)

    # 1. Peak
    roi_start = min(sig_len, p_mask)
    peak_idx = roi_start + np.argmax(sig[roi_start:])
    peak_val = sig[peak_idx]

    # 2. Valley
    v_s = min(sig_len, v_start)
    valley_idx = v_s + np.argmin(sig[v_s:peak_idx])
    valley_val = sig[valley_idx]

    # 3. Onset
    threshold = valley_val + 0.10 * (peak_val - valley_val)
    subset = sig[valley_idx:peak_idx]
    below = np.where(subset < threshold)[0]
    onset_idx = valley_idx + (below[-1] if len(below) > 0 else 0)

    return peak_idx, peak_val, valley_idx, valley_val, onset_idx, threshold


def plot_thesis_figure(ax, sig, win_len, p_mask, v_start, label_class):
    peak_idx, peak_val, valley_idx, valley_val, onset_idx, threshold = calculate_points(
        sig, p_mask, v_start)

    # --- PLOTTING ---
    # Linienstärke etwas feiner für wissenschaftliche Plots
    ax.plot(sig, color='#5D6D7E', linewidth=1.0,
            alpha=0.9, label='Gemessenes Signal', zorder=1)

    # Maskierter Bereich
    ax.axvspan(0, p_mask, color='#95a5a6', alpha=0.2,
               label='Maske (Sendepuls)', zorder=0)

    # Threshold Linie
    ax.hlines(y=threshold, xmin=valley_idx-2, xmax=peak_idx-3, color='#e67e22',
              linestyle='--', linewidth=1.2, label='10% Schwelle', zorder=2)

    # Marker (zorder hochsetzen, damit sie über der Linie liegen)
    ax.scatter(peak_idx, peak_val, color='r', marker='x', s=60,
               linewidth=2, label=r'Peak ($A_{max}$)', zorder=3)
    ax.scatter(valley_idx, valley_val, color='b', marker='v',
               s=50, label=r'Valley ($A_{min}$)', zorder=3)
    ax.scatter(onset_idx, sig[onset_idx], color='g',
               marker='o', s=40, label='Onset', zorder=3)

    # Fenster
    ax.axvspan(onset_idx, onset_idx + win_len, color='#2ecc71',
               alpha=0.15, label=f'Fenster ({win_len} Samples)', zorder=0)

    # --- LAYOUT ---
    # ax.set_title(
    #    f'Signalausrichtung und Fensterung (Klasse: {label_class})', fontweight='bold', pad=10)
    ax.set_ylabel('Amplitude [a.u.]')
    ax.set_xlabel('Sample Index')

    # Zoom
    plot_start = max(0, p_mask - 10)
    plot_end = min(len(sig), onset_idx + win_len + 20)
    ax.set_xlim(plot_start, plot_end)
    ax.set_ylim(-100, max(sig) * 1.1)

    # Legende optimieren
    # framealpha=1 macht den Hintergrund undurchsichtig, damit man Linien darunter nicht sieht
    ax.legend(loc='upper right', frameon=True, framealpha=0.95,
              edgecolor='#cccccc', fontsize=9, fancybox=False)


# --- MAIN ---
if __name__ == "__main__":
    print(f"Lade Daten: {CSV_PATH}")
    try:
        raw_hf, labels = load_hf_data(CSV_PATH)
        if SAMPLE_IDX >= len(raw_hf):
            SAMPLE_IDX = 0
        lbl = labels[SAMPLE_IDX]

        # Figure erstellen
        fig, ax = plt.subplots()

        plot_thesis_figure(ax, raw_hf[SAMPLE_IDX],
                           WINDOW_LEN, HF_MASK, HF_START, lbl)

        # WICHTIG für LaTeX: Ränder entfernen
        plt.tight_layout()

        # Export als PDF (Vektorgrafik)
        output_filename = 'sonar_feature_extraction.pdf'
        plt.savefig(output_filename, format='pdf', bbox_inches='tight')
        print(f"Grafik gespeichert als: {output_filename}")

        plt.show()

    except Exception as e:
        print(f"Fehler: {e}")
