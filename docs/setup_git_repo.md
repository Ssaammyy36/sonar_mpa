# Setup Git-Repository

## 1. Git-Bash aufsetzen

1. Download Git von hir: https://git-scm.com/downloads<br>
2. Installiere Git<br>
3. Öffne die Git-Bash<br>

## 2. SSH-Key generieren

1. Key generieren: ``ssh-keygen -t ed25519 -C "deine-email@beispiel.de"``<br>
2. Key kopieren Kopiere die Ausgabe: ``cat ~/.ssh/id_ed25519.pub``<br>
3. Gehe im Browser zu https://github.com/settings/keys<br>
4. Klicke auf „New SSH key“<br>
5. Gib einen Namen ein<br>
6. Füge den kopierten Public Key ins Feld „Key“ ein<br>
6. Klicke „Add SSH key“<br>

## 3. Repo klonen
   
1. Klonen mit SSH: ``git clone git@github.com:Ssaammyy36/sonar_mpa.git``
2. VS-Code Git Einstellungen: 
    ```sh
    git config --global user.name "Dein Name"
    git config --global user.email "deine@email.de"
    ```


