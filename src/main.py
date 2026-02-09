import sys
from steuerung import Steuerung
from data_types import TestSzenario


if __name__ == "__main__":
    """
    Hauptfunktion: Definiert die auszuführenden Tests und startet die Anwendung.
    """
    try:
        # --- HIER DIE GEWÜNSCHTEN TESTS DEFINIEREN ---
        geplante_tests = [
            TestSzenario(class_name="Stones", mode_id="4", frequency="low"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="high"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="low"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="high"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="low"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="high"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="low"),
            TestSzenario(class_name="Stones", mode_id="4", frequency="high")
        ]

        # Starte die Hauptanwendung
        steuerung = Steuerung(geplante_tests=geplante_tests)

    except Exception as e:
        print(f"Ein unerwarteter, kritischer Fehler ist aufgetreten: {e}", file=sys.stderr)

        sys.exit(1)
