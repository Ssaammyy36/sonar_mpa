import csv
import argparse
import os
import sys
from visualisierung import Visualisierung
from logger import setup_logging

def plot_from_csv(csv_path: str):
    """
    Liest eine CSV-Datei und erstellt Plots für jeden Eintrag.
    
    Args:
        csv_path: Pfad zur CSV-Datei.
    """
    if not os.path.exists(csv_path):
        print(f"Fehler: Datei '{csv_path}' nicht gefunden.")
        return

    # Logging setup (nutzt das Verzeichnis der CSV-Datei für Logs/Plots)
    run_dir = os.path.dirname(csv_path)
    if not run_dir:
        run_dir = "."
    
    # Optional: Neues Unterverzeichnis für Replay-Plots
    plot_dir = os.path.join(run_dir, "replay_plots")
    os.makedirs(plot_dir, exist_ok=True)
    
    visualisierung = Visualisierung(plot_dir)
    
    print(f"Lese Daten aus '{csv_path}'...")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader, None)
            
            if not header:
                print("Fehler: Leere CSV-Datei.")
                return
            
            # Indizes finden
            try:
                idx_freq = header.index("Sampling_Freq_Hz")
                # Daten-Spalten fangen mit S_0 an
                idx_s0 = header.index("S_0")
            except ValueError:
                print("Fehler: CSV-Format ungültig. 'Sampling_Freq_Hz' oder 'S_0' nicht gefunden.")
                return

            count = 0
            for row in reader:
                if not row: continue
                
                try:
                    sampling_freq = float(row[idx_freq])
                    
                    # Alle Spalten ab S_0 sind Datenpunkte
                    # Leere Strings filtern
                    raw_data = []
                    for val in row[idx_s0:]:
                        if val.strip():
                            raw_data.append(int(val))
                    
                    timestamp_str = row[0] # Annahme: Timestamp ist erste Spalte
                    
                    visualisierung.prepare_and_plot(
                        raw_data, 
                        sampling_freq, 
                        title=f"Replay", 
                        block_index=count
                    )
                    count += 1
                    
                except (ValueError, IndexError) as e:
                    print(f"Fehler beim Parsen von Zeile {count+2}: {e}")
            
            print(f"Fertig! {count} Plots in '{plot_dir}' erstellt.")

    except Exception as e:
        print(f"Kritischer Fehler: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Sonar Data from CSV")
    parser.add_argument("file", help="Path to the CSV file")
    args = parser.parse_args()
    
    plot_from_csv(args.file)
