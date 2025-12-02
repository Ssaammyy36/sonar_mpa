from typing import List, Dict, Any

from logger import get_logger, setup_logging
from sonar import Sonar
from datenverarbeitung import Datenverarbeitung
import config


class Steuerung:
    """
    Steuert den gesamten Ablauf von Sonar-Messungen.
    Diese Klasse agiert als flexible Engine, die verschiedene, in der Konfiguration
    definierte Test-Szenarien ausführen kann.
    """

    def __init__(self, run_dir: str, geplante_tests: List[Dict[str, Any]]):
        """
        Initialisiert die Steuerung und alle Kernkomponenten.

        Args:
            run_dir (str): Das Verzeichnis für diesen Programmlauf, in dem Logs und Plots gespeichert werden.
            geplante_tests (List[Dict[str, Any]]): Eine Liste von Dictionaries, wobei jedes Dict einen Test definiert.
        """
        self.run_dir = run_dir
        self.geplante_tests = geplante_tests

        self.logger = get_logger(__name__)
        self.sonar = Sonar()
        self.datenverarbeitung = Datenverarbeitung(run_dir=self.run_dir)
        self.logger.debug("Steuerung und alle Komponenten initialisiert.")

        self.run_tests()

    def fuehre_test_durch(self, mode_id: str, frequency: str, class_name: str):
        """
        Führt einen einzelnen, klar definierten Test basierend auf der Konfiguration durch.

        Args:
            mode_id: Die ID des Testmodus (z.B. "3", "4", "100").
            frequency: Die zu verwendende Frequenz ("low" oder "high").
        """
        # 1. Konfiguration laden
        if class_name and class_name not in config.CLASSES:
            self.logger.warning(f"Warnung: Unbekannte Klasse '{class_name}'. Erlaubt sind: {config.CLASSES}")

        mode_config = config.MODES.get(mode_id)  # 2,3,4,100,101
        if not mode_config:
            self.logger.error(f"Testmodus '{mode_id}' ist in config.py nicht definiert!")
            return

        mode_name = mode_config["name"]
        output_mode_id = mode_config["output_mode_id"]
        data_type = mode_config["data_type"]

        # Lade die spezifischen Einstellungen für den Modus und die angegebene Frequenz
        # Wir erstellen eine Kopie, um die globalen Config-Daten nicht zu verändern
        mode_settings = mode_config.get("settings", {}).get(frequency, {}).copy()
        
        # Metadaten hinzufügen
        mode_settings["class_name"] = class_name
        mode_settings["frequency"] = frequency

        self.logger.info(f"--- Starte Test: Modus '{mode_name}' ({mode_id}) mit Frequenz '{frequency}' ---")

        # 2. Sonar konfigurieren
        self.sonar.konfigurieren(
            output_mode=output_mode_id,
            frequency=frequency,
            settings=mode_settings  # Übergibt die spezifischen Einstellungen
        )

        # 3. Daten lesen (mit Timeout aus der Konfiguration)
        read_timeout = mode_settings.get("read_timeout", 2.0)
        sensor_daten = self.sonar.daten_lesen(dauer=read_timeout)
        self.logger.debug(f"Nachricht: {sensor_daten.decode('latin_1')}")

        # 4. Daten verarbeiten
        daten_bloecke = self.datenverarbeitung.verarbeite_daten(
            data_type=data_type,
            sensor_daten=sensor_daten,
            mode_name=mode_name,
            settings=mode_settings,
        )
        self.logger.info(f"--- Test '{mode_name}' beendet ---")

        # 5. Daten in CSV schreiben
        self.datenverarbeitung.append_ping_to_csv(daten_bloecke=daten_bloecke, settings=mode_settings)

    def run_tests(self):
        """
        Führt eine Liste von Tests nacheinander aus.
        """
        self.logger.info(f"Sonar-Anwendung wird gestartet, {len(self.geplante_tests)} Test(s) geplant.")

        if not self.geplante_tests:
            self.logger.warning("Keine Tests zur Ausführung angegeben.")
            return

        if self.sonar.verbinden():
            self.logger.info("Sonar erfolgreich verbunden.")

            for test_config in self.geplante_tests:
                mode_id = test_config.get("mode_id")
                frequency = test_config.get("frequency", "low")  # Default auf "low"
                class_name = test_config.get("class")

                if not mode_id:
                    self.logger.error(f"Ungültiger Test in der Liste, 'mode_id' fehlt: {test_config}")
                    continue

                self.fuehre_test_durch(mode_id=mode_id, frequency=frequency, class_name=class_name)

            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")

        self.logger.info("Alle geplanten Tests abgeschlossen. Sonar-Anwendung beendet.")
