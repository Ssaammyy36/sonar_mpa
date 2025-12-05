import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from data_types import EchogramMeasurement

from logger import get_logger


class Visualisierung:
    """
    Erstellt Visualisierungen aus verarbeiteten Sonar-Daten.
    """

    def __init__(self, run_dir: str):
        """
        Initialisiert das Visualisierungs-Objekt.

        Args:
            run_dir (str): Das Verzeichnis, in dem Plots gespeichert werden.
        """
        self.logger = get_logger(__name__)
        self.run_dir = run_dir

    @staticmethod
    def calculate_db_from_raw(data_points: List[int], max_adc: int = 4095) -> np.ndarray:
        """
        Berechnet die dBFS-Werte für eine Liste von Rohdaten.
        
        Args:
            data_points: Die rohen Amplitudenwerte (0 bis max_adc).
            max_adc: Der maximale ADC-Wert (Referenz für 0 dB).
            
        Returns:
            np.ndarray: Die Amplituden in dBFS (geclippt bei -80 dB).
        """
        raw_amps = np.array(data_points)
        if len(raw_amps) == 0:
            return np.array([])
            
        # 1. Normalisierung auf 0..1 (Relativ zu Full Scale)
        amps_norm = raw_amps / float(max_adc)
        
        # 2. Logarithmierung (dB)
        # Epsilon addieren/clippen gegen log(0)
        epsilon = 1e-9
        amps_norm = np.clip(amps_norm, epsilon, 1.0)
        amps_db = 20 * np.log10(amps_norm)
        
        # 3. Noise Floor Clipping
        # Alles unter -80 dB wird abgeschnitten
        min_db = -80.0
        return np.clip(amps_db, min_db, 0.0)

    def create_plots_from_measurements(self, measurements: List[EchogramMeasurement], mode_name: str, settings: dict):
        """
        Public API: Erstellt Plots für eine Liste von Messungen (Batch-Verarbeitung).
        
        Args:
            measurements: Liste der Echogramm-Objekte.
            mode_name: Name des aktuellen Modus (für Titel).
            settings: Einstellungen (enthält u.a. Sampling Rate).
        """
        self.logger.info(f"Erstelle Plots für {len(measurements)} Messungen (Batch)...")
        
        # Sampling Frequenz ermitteln
        try:
            val = settings.get("freqIdSamplFreq", {})
            fs = float(val) if val else 100000.0
        except (ValueError, TypeError):
            fs = 100000.0
            
        for i, m in enumerate(measurements):
            # Titel generieren
            depth_info = ""
            if "Depth" in m.header:
                depth_info = f" (Tiefe: {m.header['Depth']})"
            title = f"Echogramm Mode '{mode_name}'{depth_info}"
            
            # Dateiname generieren
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"echogram_{ts_str}_block_{i+1}.png"
            
            # Plotten
            self._render_and_save_figure(m.data_points, fs, title, filename, block_index=i+1)


    def _render_and_save_figure(self, raw_data: List[int], fs: float, title: str, filename: str, block_index: int):
        """
        Interne Methode: Führt die Berechnung durch, erstellt den Plot und speichert ihn.
        """
        if not raw_data:
            self.logger.warning(f"Keine Daten für Plot '{filename}'.")
            return

        # 1. Daten berechnen
        amps_db = self.calculate_db_from_raw(raw_data)
        num_samples = len(amps_db)
        
        # 2. Zeitachse berechnen
        time_axis_s = np.arange(num_samples) / fs
        time_axis_ms = time_axis_s * 1000.0
        
        # 3. Plotten
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(time_axis_ms, amps_db, label=f'Block {block_index}')
        
        ax.set_title(title)
        ax.set_xlabel("Zeit [ms]")
        ax.set_ylabel("Amplitude [dBFS]")
        ax.set_ylim(-85, 5) # Fixer Bereich für bessere Vergleichbarkeit (+5 für Margin)
        ax.grid(True)
        
        # Sekundäre X-Achse (Entfernung)
        # v = 1500 m/s
        def ms_to_m(t_ms):
            return (t_ms / 1000.0) * 1500.0 / 2.0
        def m_to_ms(d_m):
            return (d_m * 2.0 / 1500.0) * 1000.0
            
        secax = ax.secondary_xaxis('top', functions=(ms_to_m, m_to_ms))
        secax.set_xlabel("Entfernung [m] (v=1500 m/s)")
        
        plt.tight_layout()
        
        # 4. Speichern
        save_path = os.path.join(self.run_dir, filename)
        try:
            plt.savefig(save_path)
            self.logger.debug(f"Plot gespeichert: {save_path}")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern von {save_path}: {e}")
        finally:
            plt.close(fig)
