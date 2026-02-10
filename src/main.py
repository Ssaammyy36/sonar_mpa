import sys
from steuerung import Steuerung
from data_types import TestSzenario, MeasurementSession


if __name__ == "__main__":
    """
    Hauptfunktion: Definiert die auszuführenden Tests und startet die Anwendung.
    """
    try:
        # Tests definieren
        geplante_sessions = [
            MeasurementSession(
                tasks=[
                    TestSzenario(class_name="Stones", mode_id="4", frequency="low"),
                    TestSzenario(class_name="Stones", mode_id="4", frequency="high")
                ],
                repetitions=1, 
                analyze=True
            ),
        ]

        # Starte die Hauptanwendung
        steuerung = Steuerung(geplante_sessions=geplante_sessions)

    except Exception as e:
        print(f"Ein unerwarteter, kritischer Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)

