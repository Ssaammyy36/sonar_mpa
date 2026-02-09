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
            TestSzenario(mode_id="4", frequency="low", class_name="Stones"),
            TestSzenario(mode_id="4", frequency="high", class_name="Stones")
        ]

        # Starte die Hauptanwendung
        steuerung = Steuerung(geplante_tests=geplante_tests)

    except Exception as e:
        print(f"Ein unerwarteter, kritischer Fehler ist aufgetreten: {e}", file=sys.stderr)

        sys.exit(1)
