from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from logger import get_logger, setup_logging
from sonar import Sonar
from datenverarbeitung import Datenverarbeitung
from visualisierung import Visualisierung
from data_types import TestSzenario
import config


class Steuerung:
    """
    Steuert den gesamten Ablauf von Sonar-Messungen.
    """

    def __init__(self, geplante_tests: List[TestSzenario]):
        """
        Initialisiert die Steuerung und alle Kernkomponenten.

        Args:
            geplante_tests (List[TestSzenario]): Eine Liste von TestSzenario-Objekten.
        """
        self.run_dir = Path('logs') / datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Verzeichnis erstellen und Logging konfigurieren
        Path(self.run_dir).mkdir(parents=True, exist_ok=True)
        setup_logging(self.run_dir)

        self.geplante_tests = geplante_tests

        self.logger = get_logger(__name__)
        self.sonar = Sonar()
        self.datenverarbeitung = Datenverarbeitung(run_dir=self.run_dir)
        self.visualisierung = Visualisierung(run_dir=self.run_dir)
        self.logger.debug("Steuerung und alle Komponenten initialisiert.")

        self.run_tests()

    def run_single_test(self, mode_id: str, frequency: str, class_name: str):
        """
        Führt einen einzelnen, klar definierten Test basierend auf der Konfiguration durch.

        Args:
            mode_id: Die ID des Testmodus (z.B. "3", "4", "100").
            frequency: Die zu verwendende Frequenz ("low" oder "high").
            class_name: Die Klasse des Tests (z.B. "Test" oder "Gravel").
        """
        # 1. Konfiguration laden
        if class_name and class_name not in config.CLASSES:
            self.logger.error(f"Warnung: Unbekannte Klasse '{class_name}'. Erlaubt sind: {config.CLASSES}")
            return

        mode_config = config.MODES.get(mode_id)  # 2,3,4,100,101
        if not mode_config:
            self.logger.error(f"Testmodus '{mode_id}' ist in config.py nicht definiert!")
            return

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
            settings=mode_settings  # Übergibt die spezifischen Einstellungen
        )

        # 3. Daten lesen (mit Timeout aus der Konfiguration)
        read_timeout = mode_settings.get("read_timeout", 2.0)
        sensor_daten = self.sonar.daten_lesen(dauer=read_timeout)
        
        if not sensor_daten:
            self.logger.error(f"Keine Daten für Test {mode_name} empfangen!")
            return

        # 4. Daten verarbeiten
        data_packages = self.datenverarbeitung.verarbeite_daten(
            data_type=data_type,
            sensor_daten=sensor_daten,
            mode_name=mode_name,
            settings=mode_settings,
        )
        self.logger.info(f"Test '{mode_name}' beendet")

        # 5. Visualisieren
        if config.LOGGING_CONFIG["plot_echograms"] and data_packages:
            self.visualisierung.plotte_measurements(data_packages, mode_name, mode_settings)

        # 6. Daten in CSV schreiben
        self.datenverarbeitung.append_ping_to_csv(data_packages=data_packages, settings=mode_settings)

    def run_tests(self):
        """
        Führt eine Liste von Tests nacheinander aus.
        """
        self.logger.info(f"--- Sonar-Anwendung wird gestartet, {len(self.geplante_tests)} Test(s) geplant. ---")

        if not self.geplante_tests:
            self.logger.warning("Keine Tests zur Ausführung angegeben.")
            return

        if self.sonar.verbinden():
            self.logger.info("Sonar erfolgreich verbunden.")

            for test in self.geplante_tests:

                # Aktueller Test i
                self.run_single_test(mode_id=test.mode_id, frequency=test.frequency, class_name=test.class_name)

            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")

        self.logger.info("Alle geplanten Tests abgeschlossen. Sonar-Anwendung beendet.")
