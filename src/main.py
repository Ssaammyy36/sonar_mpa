from sensor import Sensor
from empfaenger import Empfaenger
from datenverarbeitung import Datenverarbeitung
from steuerung import Steuerung
import logging

def teste_klassen( sensor, empfaenger, daten, steuerung):
    sensor.test()
    empfaenger.test()
    daten.test()
    steuerung.test()

def main():
    # Teste alle Klassen
    sensor = Sensor("S1")
    empfaenger = Empfaenger("E1")
    daten = Datenverarbeitung()
    steuerung = Steuerung()

    teste_klassen(sensor, empfaenger, daten, steuerung) 

if __name__ == "__main__":
    main()
