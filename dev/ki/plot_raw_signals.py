import os
import re
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import matplotlib
matplotlib.use('Agg')  # Verhindert GUI-Fenster, speichert nur PDF

# --- 1. CONFIGURATION & STYLE ---

# Plotting Style (wie bei der Fensterung: clean und professionell)
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 13,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'font.family': 'sans-serif',
    'figure.autolayout': True,
})

# Farben für die Sedimentklassen
CLASS_COLORS = {
    'Sand': '#F1C40F',   # Gelb/Gold
    'Gravel': '#E67E22',  # Orange/Rötlich
    'Stones': '#7F8C8D'  # Grau
}

# --- 2. HIER DIE GEWÜNSCHTEN SAMPLES EINSTELLEN ---
# Index der Zeile für die jeweilige Klasse im Datensatz
SELECTED_INDICES = {
    'HF': {
        'Sand': 20,
        'Gravel': 20,
        'Stones': 20
    },
    'LF': {
        'Sand': 20,
        'Gravel': 20,
        'Stones': 20
    }
}

# Pfade
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

# --- 3. DATEN LADEN (Nur Rohdaten) ---


def _sniff_csv_separator(filepath):
    with open(filepath, 'r', errors='ignore') as f:
        line = f.readline()
    return ';' if line.count(';') > line.count(',') else ','


def load_raw_data():
    data_frames = []
    print(f"Lade Rohdaten aus {DATA_ROOT}...")

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
                data_frames.append(df)
            except Exception:
                pass

    if not data_frames:
        raise RuntimeError("Keine gültigen Datendateien gefunden.")

    return pd.concat(data_frames, ignore_index=True).fillna(0)

# --- 4. PLOTTING FUNKTION ---


def plot_raw_frequencies(df):
    """
    Erstellt je einen sauberen Plot für HF und LF ohne Titel.
    X-Achse unten: Zeit [ms]. X-Achse oben: Distanz in Wasser [cm].
    """
    f_s = 100000.0  # 100 kHz Abtastrate

    # Zeitachse (0 bis 4 ms)
    time_ms = np.arange(400) * (1.0 / f_s) * 1000.0

    for freq_key, freq_name in [('HF', 'high'), ('LF', 'low')]:
        df_freq = df[df['Frequency'].str.lower() == freq_name]

        # Breite etwas kompakter für schönen "Line-Plot" Look in LaTeX
        plt.figure(figsize=(8, 4.5))
        ax1 = plt.gca()

        classes = ['Sand', 'Gravel', 'Stones']

        for cls in classes:
            df_cls = df_freq[df_freq['class_name'] == cls]
            if df_cls.empty:
                continue

            target_idx = SELECTED_INDICES[freq_key][cls]
            target_idx = min(target_idx, len(df_cls) - 1)

            raw_signal = df_cls.iloc[target_idx][[
                f'S_{i}' for i in range(400)]].values.astype(float)

            ax1.plot(time_ms, raw_signal, label=cls,
                     color=CLASS_COLORS[cls], linewidth=1.5, alpha=0.9)

        # Beschriftung Primärachse (Clean)
        ax1.set_xlabel('Zeit [ms]')
        ax1.set_ylabel('Amplitude [a.u.]')

        ax1.grid(True, linestyle='--', alpha=0.5)
        ax1.legend(loc='upper right', framealpha=0.95)
        ax1.set_xlim(0, max(time_ms))

        # Sekundärachse (Distanz)
        # 1 ms = 75 cm (bei 1500 m/s und 2-Wege-Laufzeit)
        ax2 = ax1.twiny()
        ax1_xlims = ax1.get_xlim()
        ax2.set_xlim(ax1_xlims[0] * 75.0, ax1_xlims[1] * 75.0)
        ax2.set_xlabel('Distanz [cm]', labelpad=10)

        # Speichern ohne Titel
        out_name = os.path.join(
            OUTPUT_DIR, f'raw_signals_overlay_{freq_key}.pdf')
        plt.savefig(out_name, bbox_inches='tight')
        plt.close()

        print(f"Plot gespeichert: {out_name}")


# --- 5. MAIN EXECUTION ---
if __name__ == "__main__":
    try:
        df_raw = load_raw_data()
        plot_raw_frequencies(df_raw)
        print(f"\nFertig! Die Rohdaten-Plots liegen in: {OUTPUT_DIR}")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
