"""
Hauptskript zum Starten der Sonar-Anwendung.
"""
from steuerung import Steuerung
import sys

def main():
    """
    Hauptfunktion: Erstellt das Steuerungsobjekt und startet die Anwendung.
    """
    try:
        # --- HIER DEN GEWÜNSCHTEN TESTMODUS EINGEBEN ---
        # '1' oder 'ascii':  für den rohen ASCII-Daten-Test
        # '2' oder 'binaer': für den Binärdaten-Test mit Plot
        # '3' oder 'nmea':   für den NMEA-Tiefendaten-Test
        # '100' oder '12bit': für den 12-Bit Binärdaten-Test mit Plot

        test_modus = "100"
        
        steuerung = Steuerung()
        # Übergib den ausgewählten Modus an die Steuerungsklasse
        steuerung.starte_anwendung(test_modus)
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()