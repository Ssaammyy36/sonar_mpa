import sys
from datetime import datetime
from pathlib import Path
from steuerung import Steuerung
from logger import setup_logging


if __name__ == "__main__":
    """
    Hauptfunktion: Definiert die auszuführenden Tests und startet die Anwendung.
    """
    try:
        # --- HIER DIE GEWÜNSCHTEN TESTS DEFINIEREN ---
        geplante_tests = [
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"},
            {"mode_id": "4", "frequency": "low"}
        ]

        # 1. Log-Verzeichnis
        run_dir = Path('logs') / datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir.mkdir(parents=True, exist_ok=True)

        # Konfiguriere das Logging, um in das neue Verzeichnis zu schreiben
        setup_logging(run_dir)

        # Starte die Hauptanwendung und übergebe das Laufzeit-Verzeichnis
        steuerung = Steuerung(
            run_dir=run_dir, tests=geplante_tests)
        steuerung.starte_anwendung()

    except Exception as e:
        print(
            f"Ein unerwarteter, kritischer Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)
