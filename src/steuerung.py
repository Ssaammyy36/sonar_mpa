import sys
from typing import List, Dict, Any

from utils.logger import get_logger
from sonar import Sonar
from datenverarbeitung import Datenverarbeitung
import config


class Steuerung:
    """
    Steuert den gesamten Ablauf von Sonar-Messungen.
    Diese Klasse agiert als flexible Engine, die verschiedene, in der Konfiguration
    definierte Test-Szenarien ausführen kann.
    """

    def __init__(self):
        """Initialisiert die Steuerung und alle Kernkomponenten."""
        self.logger = get_logger(__name__)
        self.sonar = Sonar()
        self.datenverarbeitung = Datenverarbeitung()
        self.logger.debug("Steuerung und alle Komponenten initialisiert.")

    def fuehre_test_durch(self, mode_id: str, frequency: str):
        """
        Führt einen einzelnen, klar definierten Test basierend auf der Konfiguration durch.

        Args:
            mode_id: Die ID des Testmodus (z.B. "3", "4", "100").
            frequency: Die zu verwendende Frequenz ("low" oder "high").
        """
        # 1. Konfiguration laden
        mode_config = config.MODES.get(mode_id)
        if not mode_config:
            self.logger.error(f"Testmodus '{mode_id}' ist in config.py nicht definiert!")
            return

        mode_name = mode_config["name"]
        output_mode_id = mode_config["output_mode_id"]
        data_type = mode_config["data_type"]

        self.logger.info(f"--- Starte Test: Modus '{mode_name}' ({mode_id}) mit Frequenz '{frequency}' ---")

        # 2. Sonar konfigurieren
        self.sonar.konfigurieren(output_mode=output_mode_id, frequency=frequency)

        # 3. Daten lesen
        sensor_daten = self.sonar.daten_lesen(dauer=2.0)

        # 4. Daten verarbeiten
        self.datenverarbeitung.verarbeite_daten(
            data_type=data_type,
            sensor_daten=sensor_daten,
            mode_name=mode_name
        )
        self.logger.info(f"--- Test '{mode_name}' beendet ---")

    def starte_anwendung(self, tests: List[Dict[str, Any]]):
        """
        Hauptmethode, die eine Liste von Tests nacheinander ausführt.

        Args:
            tests: Eine Liste von Dictionaries, wobei jedes Dict einen Test definiert.
                   Beispiel: [{"mode_id": "4", "frequency": "low"}, {"mode_id": "4", "frequency": "high"}]
        """
        self.logger.info(f"Sonar-Anwendung wird gestartet, {len(tests)} Test(s) geplant.")

        if not tests:
            self.logger.warning("Keine Tests zur Ausführung angegeben.")
            return

        if self.sonar.verbinden():
            self.logger.info("Sonar erfolgreich verbunden.")

            for test_config in tests:
                mode_id = test_config.get("mode_id")
                frequency = test_config.get("frequency", "low") # Default auf "low"
                if not mode_id:
                    self.logger.warning(f"Ungültiger Test in der Liste, 'mode_id' fehlt: {test_config}")
                    continue
                
                self.fuehre_test_durch(mode_id=mode_id, frequency=frequency)

            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")

        self.logger.info("Alle geplanten Tests abgeschlossen. Sonar-Anwendung beendet.")


if __name__ == "__main__":
    """
    Hauptfunktion: Definiert die auszuführenden Tests und startet die Anwendung.
    """
    try:
        # --- HIER DIE GEWÜNSCHTEN TESTS DEFINIEREN ---

        # Beispiel 1: Einen einzelnen Test ausführen
        geplante_tests = [
            {"mode_id": "4", "frequency": "low"}
        ]

        # Beispiel 2: Modus 4 mit beiden Frequenzen testen
        # geplante_tests = [
        #     {"mode_id": "4", "frequency": "low"},
        #     {"mode_id": "4", "frequency": "high"}
        # ]

        # Beispiel 3: Alle Modi mit niedriger Frequenz testen
        # geplante_tests = [
        #     {"mode_id": mode, "frequency": "low"} for mode in config.MODES
        # ]
        
        # Beispiel 4: Alle Modi mit ALLEN Frequenzen testen
        # geplante_tests = [
        #     {"mode_id": mode, "frequency": freq} 
        #     for mode in config.MODES 
        #     for freq in config.FREQUENCIES
        # ]

        steuerung = Steuerung()
        steuerung.starte_anwendung(geplante_tests)

    except Exception as e:
        # Ein globales Exception-Handling für unerwartete Fehler
        print(f"Ein unerwarteter, kritischer Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)
