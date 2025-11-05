from utils.logger import get_logger
from sonar import Sonar
from datenverarbeitung import Datenverarbeitung
from pathlib import Path
import sys


class Steuerung:
    """
    Steuert den gesamten Ablauf der Sonar-Messung und -Verarbeitung.
    Diese Klasse initialisiert alle notwendigen Komponenten und koordiniert deren Zusammenspiel.
    """

    def __init__(self):
        """Initialisiert die Steuerung und alle Kernkomponenten."""
        self.logger = get_logger(__name__)

        self.sonar = Sonar()
        self.datenverarbeitung = Datenverarbeitung()

        self.logger.debug("Steuerung und alle Komponenten initialisiert.")

    def starte_anwendung(self, test_modus: str | None = None):
        """Hauptmethode, die den Anwendungsablauf steuert."""
        self.logger.info("Sonar-Anwendung wird gestartet.")

        # Checkt TestModus
        if not test_modus:
            self.logger.info("Kein Testmodus angegeben !!! Bitte wähle einen Modus.")
            return

        # Verbinden 
        if self.sonar.verbinden():
            self.logger.info("Sonar erfolgreich verbunden.")

            # Ablauf Modi auswäheln 
            if test_modus.lower() in ('3', 'nmea'):
                self.fuehre_nmea_test_durch()
            elif test_modus.lower() in ('100', '8bit'):
                print(...)
            elif test_modus.lower() in ('101', '16bit'):
                self.fuehre_12_bit_binary_test_durch()
            else:
                self.logger.warning(f"Unbekannter Testmodus: '{test_modus}'!!!")
            
            # Verbindung Trennen
            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")

        self.logger.info("Sonar-Anwendung beendet.")

    def fuehre_nmea_test_durch(self):
        """Führt einen Test zur Aufnahme und Verarbeitung von NMEA-Daten durch."""
        self.logger.info("Starte NMEA-Daten-Test...")
        self.sonar.konfigurieren(output_mode="3", frequency="low", interval="1.0", sampl_freq="100000")
        
        # Lesen
        nmea_daten = self.sonar.daten_lesen(dauer=5.0, print_mode=True)

        # Aufbereiten
        if nmea_daten:
            tiefen = self.datenverarbeitung.parse_nmea_tiefe(nmea_daten)
            if tiefen:

                # Ausgeben
                formatierte_tiefen = ", ".join([f"{t:.2f}m" for t in tiefen])
                self.logger.info(f"{len(tiefen)} Tiefenwerte erfolgreich geparst: [{formatierte_tiefen}]")
            else:
                self.logger.info("NMEA-Daten empfangen, aber keine gültigen Tiefenwerte ($SDDBT) gefunden.")
        else:
            self.logger.warning("Keine NMEA-Daten vom Sonar empfangen.")

    def fuehre_12_bit_binary_test_durch(self):
        """Führt einen Test zur Aufnahme und Verarbeitung von Binärdaten durch."""
        self.logger.info("Starte 12-Bit Binärdaten-Test...")
        self.sonar.konfigurieren(output_mode="100", frequency="high", interval="0.2", sampl_freq="100000")
        
        # Scannen 
        binaer_daten = self.sonar.daten_lesen(dauer=2.0)

        # Verarbeiten
        if binaer_daten:
            amplituden = self.datenverarbeitung.parse_12_bit_binary_data(binaer_daten)
            self.logger.info(f"{len(amplituden)} Amplituden-Samples erfolgreich geparst.")
        else:
            self.logger.warning("Keine Binärdaten vom Sonar empfangen.")

if __name__ == "__main__":
    
    """
    Hauptfunktion: Erstellt das Steuerungsobjekt und startet die Anwendung.
    """
    try:
        # --- HIER DEN GEWÜNSCHTEN TESTMODUS EINGEBEN ---
        # '3' oder 'nmea':   für den NMEA-Tiefendaten-Test
        # '100': für 12-Bit  
        # '101': für den 8-Bit Binärdaten-Test mit Plot

        test_modus = "3"

        steuerung = Steuerung()
        steuerung.starte_anwendung(test_modus)
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)
