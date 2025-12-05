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

    def plotte_datenpunkte(self, t_ms: np.ndarray, amps_norm: np.ndarray, titel: str, block_index: int):
        """
        Erstellt ein Liniendiagramm für einen einzelnen Echogramm-Datenblock und speichert es.

        Args:
            t_ms (np.ndarray): Zeitachse in Millisekunden.
            amps_norm (np.ndarray): Normierte Amplitudenwerte.
            titel (str): Der Titel für den Plot.
            block_index (int): Der Index des Datenblocks (für den Dateinamen).
        """
        if len(amps_norm) == 0:
            self.logger.warning(
                f"Datenblock {block_index + 1} enthält keine Amplituden zum Plotten.")
            return

        # --- PLOT VORBEREITEN ---
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(t_ms, amps_norm, label=f'Normierte Amplituden (Block {block_index + 1})')

        # Achsenbeschriftungen
        ax.set_title(f"{titel} - Block {block_index + 1}")
        ax.set_xlabel("Zeit [ms]")
        ax.set_ylabel("Normierte Intensität")
        ax.grid(True)

        # Ticks
        tick_spacing_ms = 0.5
        max_ms = t_ms[-1] if t_ms.size > 0 else 0
        ticks_ms = np.arange(0, max_ms + tick_spacing_ms, tick_spacing_ms)
        ax.set_xticks(ticks_ms)
        ax.set_xticklabels([f"{t:.1f}" for t in ticks_ms])

        # Zweite X-Achse für die Entfernung
        def ms_to_m(val_ms):
            return (val_ms / 1000.0) * 1500.0 / 2.0

        def m_to_ms(val_m):
            return (val_m * 2.0 / 1500.0) * 1000.0

        secax = ax.secondary_xaxis('top', functions=(ms_to_m, m_to_ms))
        secax.set_xlabel("Entfernung [m] (v=1500m/s)")

        plt.tight_layout()

        # SPEICHERUNG
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"echogram_{timestamp}_block_{block_index + 1}.png"
        save_path = os.path.join(self.run_dir, filename)

        try:
            plt.savefig(save_path)
            self.logger.info(
                f"Plot für Block {block_index + 1} erfolgreich gespeichert: {save_path}")
        except Exception as e:
            self.logger.error(
                f"Fehler beim Speichern des Plots für Block {block_index + 1}: {e}")
        finally:
            plt.close(fig)
    def plotte_measurements(self, measurements: List[EchogramMeasurement], mode_name: str, settings: dict):
        """
        Iteriert über eine Liste von Messungen und erstellt Plots.
        """
        self.logger.info(f"Erstelle Plots für {len(measurements)} Messungen...")
        current_settings = settings if settings else {}
        for i, measurement in enumerate(measurements):
            t_s, _, amps_norm = self.berechne_metadaten(measurement.data_points, current_settings)
            t_ms = t_s * 1000
            
            titel_suffix = ""
            if "Depth" in measurement.header:
                titel_suffix = f" (Tiefe: {measurement.header['Depth']})"
            
            self.plotte_datenpunkte(
                t_ms,
                amps_norm,
                titel=f"Echogramm für Modus '{mode_name}'{titel_suffix}",
                block_index=i
            )

    def berechne_metadaten(self, amplituden_block: List[int], settings: dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Berechnet Zeit- und Entfernungsachsen sowie normierte Amplituden.
        """
        raw_amps = np.array(amplituden_block)
        num_samples = len(raw_amps)

        if num_samples == 0:
            return np.array([]), np.array([]), np.array([])

        try:
            fs_val = settings.get("freqIdSamplFreq", {}) # Check key name in config? Usually IdSamplFreq
            # Fallback check for IdSamplFreq directly if not found
            if not fs_val:
                 fs_val = settings.get("IdSamplFreq")
            
            fs = float(fs_val) if fs_val else 100000.0
        except (ValueError, TypeError):
            fs = 100000.0

        time_axis_s = np.arange(num_samples) / fs
        sound_speed = 1500.0
        dist_axis_m = (time_axis_s * sound_speed) / 2

        min_val = raw_amps.min()
        max_val = raw_amps.max()

        if max_val > min_val:
            amps_norm = (raw_amps - min_val) / (max_val - min_val)
        else:
            amps_norm = np.zeros_like(raw_amps, dtype=float)

        return time_axis_s, dist_axis_m, amps_norm
