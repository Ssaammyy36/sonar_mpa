
# Python Umgebung 

Wir verwenden einen venv für einfaches Packet-Management 

## Setup

1. Virtuelle Umgebung erstellen: `python -m venv venv`
2. Virtuelle Umgebung aktivieren: `venv\Scripts\activate`
   
## Verwendung 

1. Pakete installieren z.B. sphinx und pdoc: `pip install sphinx pdoc`
2. Abhängigkeiten speichern in einer text Datei: `pip freeze > requirements.txt`
3. Bestimmte Abhänikgkeiten installiere: `pip install -r requirements.txt`

## Umgebung deaktivieren 

1. Deaktivieren: `deactivate`

