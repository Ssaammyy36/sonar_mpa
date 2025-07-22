# Git Workflow für sonar_mpa

Dieses Dokument beschreibt den standardisierten Git-Workflow für die Zusammenarbeit an diesem Repository.  
Ziel: sauberer, nachvollziehbarer und sicherer Entwicklungsprozess mit Feature-Branches.

## 🔀 Branch-Konzept

| Branch     | Zweck                                      |
|------------|--------------------------------------------|
| `main`     | Nur stabiler, getesteter Code (Produktionsstand) |
| `dev`      | Aktuelle Entwicklungsversion (Integration der Features) |
| `feature/*`| Einzelne neue Funktionen oder Aufgaben     |

## 🧱 Branch-Struktur (Beispiel)

```text
main
 └── dev
      ├── feature/sensor-daten
      ├── feature/login
      └── feature/api-anbindung
```

### 💡 Merktipp

origin = der Name deines "Online-Repos" (z. B. auf GitHub).
Du brauchst ihn immer, wenn du etwas mit dem entfernten Repository machst – also beim Holen, Pushen oder Löschen.

## Anleitung

### 🔧 Einmalig: `dev`-Branch erstellen

```bash
git checkout main                      # Wechsle auf den main-Branch
git checkout -b dev                    # Erstelle neuen Branch 'dev' und wechsle hinein
git push -u origin dev                 # Lade dev zum Remote und verknüpfe ihn
```

---

### 🛠 Feature-Branch erstellen (pro Aufgabe)

```bash
git checkout dev                       # Wechsel auf aktuellen Entwicklungsstand
git pull origin dev                    # dev-Branch aktualisieren
git checkout -b feature/<name>         # Neuen Feature-Branch lokal erstellen
git push -u origin feature/<name>      # Feature-Branch ins Remote laden
```

📝 Beispiel:
```bash
git checkout -b feature/sensor-api     # Branch für Sensor-API erstellen
```

### ✍️ Im Feature-Branch arbeiten

```bash
git add .                              # Alle Änderungen zur Staging-Area hinzufügen
git commit -m "feat: Sensor-API hinzugefügt"  # Mit sprechender Nachricht committen
git push                               # Änderungen ins Remote-Repo laden
```

### 🔁 Feature-Branch in `dev` mergen

Wenn die Funktion getestet ist:

```bash
git checkout dev                       # Zurück auf dev-Branch
git pull origin dev                    # dev aktualisieren
git merge feature/<name>               # Feature in dev integrieren
git push origin dev                    # dev hochladen
```

### 🧼 Feature-Branch löschen (optional)

Nach erfolgreichem Merge:

```bash
git branch -d feature/<name>           # Lokal löschen
git push origin --delete feature/<name>  # Remote löschen
```

---

### 🚀 dev → main mergen (Release)

Nur wenn der Code **stabil & getestet** ist:

```bash
git checkout main                      # Auf main wechseln
git pull origin main                   # Neuesten Stand holen
git merge dev                          # dev in main mergen
git push origin main                   # Änderungen hochladen
```

### 🧭 Commit-Regeln

- Verwende sprechende Nachrichten:
  - `feat:` Neues Feature
  - `fix:` Fehler behoben
  - `refactor:` Code umgebaut
  - `test:` Tests ergänzt
- Keine direkten Commits auf `main` oder `dev`
- Konflikte **vor dem Merge** lösen
- Optional: Pull-Request für Review


