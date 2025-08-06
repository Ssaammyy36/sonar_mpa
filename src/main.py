"""
Hauptskript zum Starten der Sonar-Anwendung.

Dieses Skript initialisiert alle notwendigen Komponenten des Systems
(Sensor, Empfaenger, Datenverarbeitung, Steuerung) und startet den
Hauptprozess.
"""
from sensor import Sensor
from empfaenger import Empfaenger
from datenverarbeitung import Datenverarbeitung
from steuerung import Steuerung
import logging

def teste_klassen(
    sensor: Sensor,
    empfaenger: Empfaenger,
    daten: Datenverarbeitung,
    steuerung: Steuerung,
) -> None:
    """
    Führt einen einfachen Erreichbarkeitstest für alle Kernkomponenten aus.

    Args:
        sensor (Sensor): Das Sensor-Objekt.
        empfaenger (Empfaenger): Das Empfaenger-Objekt.
        daten (Datenverarbeitung): Das Datenverarbeitungs-Objekt.
        steuerung (Steuerung): Das Steuerungs-Objekt.
    """
    sensor.test()
    empfaenger.test()
    daten.test()
    steuerung.test()

def main() -> None:
    """
    Initialisiert die Systemkomponenten und führt den Test aus.
    """
    # Teste alle Klassen
    sensor = Sensor("S1")
    empfaenger = Empfaenger("E1")
    daten = Datenverarbeitung()
    steuerung = Steuerung()

    teste_klassen(sensor, empfaenger, daten, steuerung)

if __name__ == "__main__":
    main()
