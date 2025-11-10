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

    def starte_anwendung(self, test_modus: str | None = None, frequency: str ="low"):
        """Hauptmethode, die den Anwendungsablauf steuert."""

        self.logger.info("Sonar-Anwendung wird gestartet.")

        # Checkt TestModus
        if not test_modus:
            self.logger.warning("Kein Testmodus angegeben !!! Bitte wähle einen Modus.")
            return

        # Verbinden 
        if self.sonar.verbinden():
            self.logger.info("Sonar erfolgreich verbunden.")

            # Ablauf Modi auswäheln 
            if test_modus.lower() in ('3', 'nmea'):
                self.fuehre_nmea_test_durch()

            elif test_modus.lower() in ('2', '10bit-Echogram'):
                self.fuehre_10_bit_echogram_test_durch()
            elif test_modus.lower() in ('4', '12bit-Echogram'):
                self.fuehre_12_bit_echogram_test_durch()
                
            elif test_modus.lower() in ('100', '12bit-Binary'):
                self.fuehre_12_bit_binary_test_durch()        
            elif test_modus.lower() in ('101', '8bit-Binary'):
                self.fuehre_8_bit_binary_test_durch()
            else:
                self.logger.warning(f"Unbekannter Testmodus: '{test_modus}'!!!")
            
            # Verbindung Trennen
            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")

        self.logger.info("Sonar-Anwendung beendet.")

    def fuehre_nmea_test_durch(self, frequency="low"):
        """Führt einen Test zur Aufnahme und Verarbeitung von NMEA-Daten durch."""

        self.logger.info("Starte NMEA-Daten-Test...")
        self.sonar.konfigurieren(output_mode="3", frequency=frequency)
        
        # Lesen
        nmea_daten = self.sonar.daten_lesen()

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

    def fuehre_10_bit_echogram_test_durch(self, frequency="low"):
        """Führt einen Test zur Aufnahme und Verarbeitung von String durch."""

        self.logger.info("Starte 10-Bit String-Test...")
        self.sonar.konfigurieren(output_mode="2", frequency=frequency)
        
        # Daten Lesen 
        echogram_daten = self.sonar.daten_lesen()
        echogram_str = echogram_daten.decode("latin_1")

        # Verarbeiten
        if echogram_daten:
            # loggen
            #self.logger.debug(f"Darstellung des Echogramms: {echogram_str}")

            # Parsen
            measurements = self.datenverarbeitung.pars_data_form_echogram(echogram_str)
            print(f"Anzahl der Datenpunkte: {len(measurements)}")
            print(f"Ersten 10 Punkte: {measurements[:10]}...")
        else:
            self.logger.warning("Keine Echogramm vom Sonar empfangen.")

    def fuehre_12_bit_echogram_test_durch(self, frequency="low"):
        """Führt einen Test zur Aufnahme und Verarbeitung von String durch."""

        self.logger.info("Starte 12-Bit String-Test...")
        self.sonar.konfigurieren(output_mode="4", frequency=frequency)
        
        # Scannen 
        echogram_daten = self.sonar.daten_lesen()
        echogram_str = echogram_daten.decode("latin_1")

        # Verarbeiten
        if echogram_daten:
            # loggen
            #self.logger.debug(f"Darstellung des Echogramms: {echogram_str}")

            # Parsen
            measurements = self.datenverarbeitung.pars_data_form_echogram(echogram_str)
            print(f"Anzahl der Datenpunkte: {len(measurements)}")
            print(f"Beispiel-Datenpunkte: {measurements[:10]}...")

            # Dastellen
            self.datenverarbeitung.plotte_datenpunkte(measurements, titel="Test-Messung vom Sonar")
        else:
            self.logger.warning("Keine Echogramm vom Sonar empfangen.")

    def fuehre_8_bit_binary_test_durch(self, frequency="low"):
        """Führt einen Test zur Aufnahme und Verarbeitung von Binärdaten durch."""

        self.logger.info("Starte 12-Bit Binärdaten-Test...")
        self.sonar.konfigurieren(output_mode="101", frequency=frequency)
        
        # Scannen 
        binaer_daten = self.sonar.daten_lesen()

        # Verarbeiten
        if binaer_daten:
            # Hex loggen
            hex_repr = binaer_daten.hex(' ')
            self.logger.debug(f"Hex-Darstellung: {hex_repr}")

            # Parsen
            # ...
        else:
            self.logger.warning("Keine Binärdaten vom Sonar empfangen.")

    def fuehre_12_bit_binary_test_durch(self, frequency="low"):
        """Führt einen Test zur Aufnahme und Verarbeitung von Binärdaten durch."""

        self.logger.info("Starte 12-Bit Binärdaten-Test...")
        self.sonar.konfigurieren(output_mode="100", frequency=frequency)
        
        # Scannen 
        binaer_daten = self.sonar.daten_lesen()

        # Verarbeiten
        if binaer_daten:
            # Hex loggen
            hex_repr = binaer_daten.hex(' ')
            self.logger.debug(f"Hex-Darstellung: {hex_repr}")

            # Parsen
            # ...
        else:
            self.logger.warning("Keine Binärdaten vom Sonar empfangen.")

if __name__ == "__main__":
    
    """
    Hauptfunktion: Erstellt das Steuerungsobjekt und startet die Anwendung.
    """
    try:
        # --- HIER DEN GEWÜNSCHTEN TESTMODUS EINGEBEN ---
        # 2: für 10-Bit Echogram
        # 3: für NMEA
        # 4: für 12-Bit Echogramm
        # 100: für 12-Bit-Binary
        # 101: für 8-Bit-Binary

        test_modus = "4"

        steuerung = Steuerung()
        steuerung.starte_anwendung(test_modus, frequency="low")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)
