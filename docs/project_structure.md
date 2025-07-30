# Projektstruktur

Im Folgenden wird die Struktur des Projekts und die Funktion der wichtigsten Dateien und Ordner beschrieben:

```
sonar_mpa/
│
├── README.md                # Projektübersicht und Einstieg
├── config.py                # Zentrale Konfigurationsdatei für das Projekt
├── src/                     # Quellcode des Projekts (z.B. Module, Skripte)
│   └── utils.py             # Hilfsfunktionen, die mehrfach im Projekt verwendet werden
├── tests/                   # (Optional) Unit- und Integrationstests
├── docs/                    # Dokumentation und Anleitungen
│   ├── developer_guidelines.md   # Styleguide und Entwicklerhinweise
│   ├── klassendiagramme.drawio.svg # Klassendiagramm als SVG
│   ├── project_structure.md       # Diese Übersicht zur Projektstruktur
│   ├── setup_environment.md       # Anleitung zur Python-Umgebung
│   └── setup_git_repo.md          # Anleitung zum Einrichten des Git-Repos
├── venv/                    # Virtuelle Python-Umgebung (automatisch erstellt)
└── .gitignore               # Dateien und Ordner, die nicht ins Git sollen
```

**Hinweise:**
- Der Quellcode kommt in den Ordner `src/` (z.B. main.py, utils.py).
- Tests sollten im Ordner `tests/` abgelegt werden.
- Die gesamte Projektdokumentation liegt im Ordner `docs/`.
- Die virtuelle Umgebung `venv/` wird von Python erstellt und enthält alle installierten Pakete.
