"""
Hauptskript zum Starten der Sonar-Anwendung.
"""
from steuerung import Steuerung

def main():
    """
    Hauptfunktion: Erstellt das Steuerungsobjekt und startet die Anwendung.
    """
    steuerung = Steuerung()
    steuerung.starte_anwendung()

if __name__ == "__main__":
    main()