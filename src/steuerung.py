from typing import List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

from logger import get_logger, setup_logging
from sonar import Sonar
from datenverarbeitung import Datenverarbeitung
from visualisierung import Visualisierung
from data_types import TestSzenario, Measurement
from classifier import SonarClassifier
import config


class Steuerung:
    """
    Steuert den gesamten Ablauf von Sonar-Messungen.
    """

    def __init__(self, geplante_sessions: List['MeasurementSession']):
        """
        Initialisiert die Steuerung und alle Kernkomponenten.

        Args:
            geplante_sessions (List[MeasurementSession]): Eine Liste von Session-Objekten.
        """
        # Logger Verzeichnis
        self.run_dir = Path('logs') / datetime.now().strftime('%Y%m%d_%H%M%S')
        Path(self.run_dir).mkdir(parents=True, exist_ok=True)
        setup_logging(self.run_dir)

        # Initialisierung
        self.geplante_sessions = geplante_sessions
        self.logger = get_logger(__name__)
        self.sonar = Sonar()
        self.datenverarbeitung = Datenverarbeitung(run_dir=self.run_dir)
        self.visualisierung = Visualisierung(run_dir=self.run_dir)
        self.classifier = SonarClassifier()
        self.logger.debug("Steuerung und alle Komponenten initialisiert.")

        # Schrittkette starten
        self.run_tests()

    def run_single_test(self, mode_id: str, frequency: str, class_name: str, test_number: int, save_result: bool = True) -> Tuple[List[Measurement], Dict]:
        """
        Führt einen einzelnen, klar definierten Test basierend auf der Konfiguration durch.

        Args:
            mode_id: Die ID des Testmodus (z.B. "3", "4", "100").
            frequency: Die zu verwendende Frequenz ("low" oder "high").
            class_name: Die Klasse des Tests (z.B. "Test" oder "Gravel").
            save_result: Ob das Ergebnis sofort in die CSV geschrieben werden soll.
        
        Returns:
            Tuple[List[Measurement], Dict]: Die gemessenen Daten und die verwendeten Einstellungen.
        """
        # 1. Konfiguration laden
        mode_config = config.MODES.get(mode_id)
        mode_name = mode_config["name"]
        output_mode_id = mode_config["output_mode_id"]
        data_type = mode_config["data_type"]

        # Lade die spezifischen Einstellungen für den Modus
        mode_settings = mode_config.get("settings", {}).get(frequency, {}).copy()
        mode_settings["class_name"] = class_name
        mode_settings["frequency"] = frequency

        # 2. Sonar konfigurieren
        self.logger.info(f"--- Starte Test: Modus '{mode_name}' ({mode_id}) mit Frequenz '{frequency}' ---")
        self.sonar.konfigurieren(
            output_mode=output_mode_id,
            frequency=frequency,
            settings=mode_settings
        )

        # 3. Daten lesen (mit Timeout aus der Konfiguration)
        read_timeout = mode_settings.get("read_timeout", 2.0)
        sensor_daten = self.sonar.daten_lesen(dauer=read_timeout)
        
        if not sensor_daten:
            self.logger.error(f"Keine Daten für Test {mode_name} empfangen!")
            return [], mode_settings

        # 4. Daten verarbeiten
        data_packages = self.datenverarbeitung.verarbeite_daten(
            data_type=data_type,
            sensor_daten=sensor_daten,
            mode_name=mode_name,
            settings=mode_settings,
        )

        self.logger.info(f"Test '{mode_name}' beendet")

        # 5. Visualisieren (immer sofort, gutes Feedback)
        if config.LOGGING_CONFIG["plot_echograms"] and data_packages:
            self.visualisierung.create_plots_from_measurements([data_packages[0]], mode_name, mode_settings, test_number)

        # 6. Daten in CSV schreiben (Optional, falls später mit Prediction gespeichert werden soll)
        if save_result:
            self.datenverarbeitung.append_ping_to_csv(data_packages=data_packages, settings=mode_settings)

        return data_packages, mode_settings

    def run_tests(self):
        """
        Führt die geplanten Sessions und deren Wiederholungen aus.
        """
        self.logger.info(f"Starte {len(self.geplante_sessions)} Session(s).")
        if self.sonar.verbinden():
            self.logger.debug("Sonar erfolgreich verbunden.")
            global_test_counter = 0

            for session_idx, session in enumerate(self.geplante_sessions):
                self.logger.info(f"=== Starte Session {session_idx + 1} ({len(session.tasks)} Tasks, {session.repetitions} Wiederholungen) ===")
                
                for rep in range(session.repetitions):
                    self.logger.info(f"Wiederholung {rep + 1}/{session.repetitions}")
                    self.run_session_iteration(session, global_test_counter)
                    global_test_counter += 1

            self.logger.info("Alle geplanten Tests abgeschlossen.")
            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")

    def run_session_iteration(self, session: 'MeasurementSession', session_id: int):
        """
        Führt einen einzelnen Durchlauf einer Session aus.
        """
        collected_data = [] # List of tuple (data, settings)

        # 1. Alle Tasks der Session ausführen
        for i, task in enumerate(session.tasks):
            # Test-ID generieren für eindeutige Plots/Logs
            test_number = session_id * 100 + i 
            
            # Ergebnis erst speichern, wenn wir wissen ob Prediction kommt oder nicht
            data, settings = self.run_single_test(
                task.mode_id, task.frequency, task.class_name, 
                test_number, save_result=False
            )
            
            if data:
                collected_data.append((data, settings))
            else:
                self.logger.error(f"Task {i} in Session fehlgeschlagen. Session wird unvollständig gespeichert.")

        # 2. KI-Analyse (nur wenn analyze=True und wir Daten haben)
        prediction = None
        if session.analyze and config.ANALYSIS_CONFIG["enable_classification"]:
            data_low = None
            data_high = None

            # Versuche Low und High aus den gesammelten Daten zu finden
            # (Nimmt aktuell einfach das erste gefundene Low und High)
            for data, settings in collected_data:
                freq = settings.get("frequency")
                if freq == "low" and data_low is None:
                    data_low = data
                elif freq == "high" and data_high is None:
                    data_high = data
            
            if data_low and data_high:
                self.logger.info("--- Starte KI-Klassifizierung für Session---")
                prediction = self.classifier.predict_paired(data_low, data_high)
                if prediction:
                    self.logger.info(f"Klassifizierungsergebnis: {prediction}")
            else:
                if session.analyze: # Nur warnen, wenn Analyse erwartet war
                    self.logger.warning("Konnte keine Low/High Paarung für Analyse finden (Daten fehlen).")

        # 3. Ergebnisse final speichern (mit Prediction falls vorhanden)
        for data, settings in collected_data:
            if prediction:
                settings["ml_prediction"] = prediction
            self.datenverarbeitung.append_ping_to_csv(data, settings)

