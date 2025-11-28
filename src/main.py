import os
import sys
from datetime import datetime

from steuerung import Steuerung
from logger import get_logger, setup_logging


if __name__ == "__main__":
    """
    Hauptfunktion: Definiert die auszuführenden Tests und startet die Anwendung.
    """
    try:
        # --- HIER DIE GEWÜNSCHTEN TESTS DEFINIEREN ---
        geplante_tests = [
            {"mode_id": "4", "frequency": "low"}
        ]

        # Erstelle ein einzigartiges Verzeichnis für diesen Programmlauf
        run_dir = os.path.join(
            'logs', datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(run_dir, exist_ok=True)

        # Konfiguriere das Logging, um in das neue Verzeichnis zu schreiben
        setup_logging(run_dir)

        # Starte die Hauptanwendung und übergebe das Laufzeit-Verzeichnis
        steuerung = Steuerung(run_dir=run_dir)
        steuerung.starte_anwendung(geplante_tests)

    except Exception as e:
        print(
            f"Ein unerwarteter, kritischer Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)
