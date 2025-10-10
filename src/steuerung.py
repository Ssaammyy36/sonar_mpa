from utils.logger import get_logger
from sonar import Sonar
from datenverarbeitung import Datenverarbeitung

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

    def starte_anwendung(self):
        """Hauptmethode, die den Anwendungsablauf steuert."""
        self.logger.info("Sonar-Anwendung wird gestartet.")
        
        if self.sonar.verbinden():
            self.logger.info("Sonar erfolgreich verbunden.")
            
            # Führe einen Testlauf durch (z.B. den Binär-Test)
            self.fuehre_nmea_test_durch()
            
            # Hier könnten weitere Abläufe folgen
            # self.fuehre_nmea_test_durch()

            self.sonar.trennen()
            self.logger.info("Sonarverbindung getrennt.")
        else:
            self.logger.error("Anwendung konnte nicht gestartet werden, da das Sonar nicht verbunden werden konnte.")
            
        self.logger.info("Sonar-Anwendung beendet.")

    def fuehre_binaer_test_durch(self):
        """Führt einen Test zur Aufnahme und Verarbeitung von Binärdaten durch."""
        self.logger.info("Starte Binärdaten-Test...")
        self.sonar.konfigurieren(output_mode="2", frequency="high", interval="0.2", sampl_freq="100000")
        binaer_daten = self.sonar.daten_lesen(dauer=2.0)
        
        if binaer_daten:
            amplituden = self.datenverarbeitung.parse_binaer_daten(binaer_daten)
            self.logger.info(f"{len(amplituden)} Amplituden-Samples erfolgreich geparst.")
            self.datenverarbeitung.plotte_echogramm(amplituden, titel="Sonar Echo Amplitude (Binär-Modus)")
        else:
            self.logger.warning("Keine Binärdaten vom Sonar empfangen.")
    
    def fuehre_nmea_test_durch(self):
        """Führt einen Test zur Aufnahme und Verarbeitung von NMEA-Daten durch."""
        self.logger.info("Starte NMEA-Daten-Test...")
        self.sonar.konfigurieren(output_mode="3", frequency="low", interval="1.0", sampl_freq="100000")
        nmea_daten = self.sonar.daten_lesen(dauer=5.0)
        
        if nmea_daten:
            tiefen = self.datenverarbeitung.parse_nmea_tiefe(nmea_daten)
            if tiefen:
                # Formatiert die Liste der Tiefen für eine bessere Lesbarkeit im Log
                formatierte_tiefen = ", ".join([f"{t:.2f}m" for t in tiefen])
                self.logger.info(f"{len(tiefen)} Tiefenwerte erfolgreich geparst: [{formatierte_tiefen}]")
            else:
                self.logger.info("NMEA-Daten empfangen, aber keine gültigen Tiefenwerte ($SDDBT) gefunden.")
        else:
            self.logger.warning("Keine NMEA-Daten vom Sonar empfangen.")
