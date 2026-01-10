# Setup ECT D052

## Setup

1. **USB am Laptop und Netzkabel einstecken** 

    -  Windows: Comport anzeigen lassen  `[System.IO.Ports.SerialPort]::GetPortNames()`
    -  Comport einstellungen chekcen `mode`
    -  Comport einstellen `mode COM5 baud=115200 parity=e data=7 stop=1`
    -  Im Code wird COM5 verwendet ❗
  
2. **Sensor-Kabel am Sensor befestigen**

    - Andere Reihenfolgen funktioniert nicht ❗

## Fehlerbehebung

### `Unable to open port` oder `AttributeError: module 'serial' has no attribute 'Serial'`

Dieses Problem tritt auf, wenn das falsche `serial` Paket installiert ist, welches mit dem benötigten `pyserial` Paket in Konflikt steht.

**Lösung für die globale Python-Installation:**

Führen Sie die folgenden Befehle in Ihrer Kommandozeile aus:

```shell
pip uninstall -y serial
pip install pyserial
```

**Lösung für das VS Code Virtual Environment (`.venv`):**

Wenn der Fehler beim Ausführen des Skripts mit dem Play-Button in VS Code auftritt, müssen die Pakete innerhalb der virtuellen Umgebung korrigiert werden.

```shell
# Zuerst das falsche Paket deinstallieren
.venv/Scripts/python.exe -m pip uninstall -y serial

# Dann das richtige Paket installieren
.venv/Scripts/python.exe -m pip install pyserial
```
