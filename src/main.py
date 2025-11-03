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
        # '3' oder 'nmea':   für den NMEA-Tiefendaten-Test
        # '100': für 12-Bit  
        # '101': für den 8-Bit Binärdaten-Test mit Plot

        test_modus = "3"

        steuerung = Steuerung()
        steuerung.starte_anwendung(test_modus)
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
