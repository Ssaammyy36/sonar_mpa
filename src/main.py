"""
Hauptskript zum Starten der Sonar-Anwendung.
"""
from steuerung import Steuerung

def main():
    """
    Hauptfunktion: Erstellt das Steuerungsobjekt und startet die Anwendung.
    """
    # 1. Erstelle die Hauptsteuerung
    app_steuerung = Steuerung()
    
    # 2. Starte den Komponenten-Test
    app_steuerung.teste_komponenten()

if __name__ == "__main__":
    main()