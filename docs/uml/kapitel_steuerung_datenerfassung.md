# Steuerung des Sensors und Datenerfassung

## Einleitung

Dieses Kapitel beschreibt die technische Umsetzung der Sensorkommunikation und der anschließenden Datenverarbeitung. Das entwickelte System folgt einem modularen Ansatz, bei dem die Hardware-Steuerung (`Sonar`) strikt von der Dateninterpretation (`Datenverarbeitung`) getrennt ist. Dies ermöglicht eine flexible Erweiterung auf verschiedene Datenformate und Sensor-Modi.

## Anbindung der Hardware-Schnittstelle

Die Kommunikation mit dem Echolot erfolgt über eine serielle Schnittstelle (COM-Port). Die Klasse `Sonar` fungiert hierbei als Hardware-Abstraktionsschicht (HAL), die die direkten Zugriffe auf die Treiber-Bibliothek (`echosounderapi`) kapselt.

### Initialisierung und Verbindungsaufbau

Der Verbindungsaufbau wird in der Methode `verbinden()` initiiert. Das System nutzt die `DualEchosounder`-Klasse der API, um eine Verbindung über den konfigurierten seriellen Port (Standard: COM5) mit einer Baudrate von 115200 herzustellen. Nach erfolgreicher Instanziierung prüft die Methode mittels `Detect()`, ob das physikalische Gerät antwortet, und synchronisiert anschließend die interne Zeitbasis des Sensors (`SetCurrentTime()`).

### Konfiguration der Messparameter

Die Konfiguration des Sensors erfolgt dynamisch vor jeder Messreihe durch die Methode `konfigurieren()`. Hierbei werden zwei Kategorien von Parametern unterschieden:

1.  **Hardware-Befehle**: Frequenzumschaltung (z.B. 50 kHz vs. 200 kHz) und Ausgabemodus (z.B. Echogramm-Daten vs. NMEA-Strings). Diese werden als direkte Kommandos an den Sensor gesendet.
2. Signalverarbeitungsparameter:
Einstellungen wie Sendeleistung (`IdTxPower`), Pulslänge (`IdTxLengthL` bzw. `IdTxLengthH`) und
Empfindlichkeit (`IdGain`). Diese Werte werden über `SetValue()` in die Register des Sensors geschrieben.

Dieser Ansatz erlaubt es, zwischen verschiedenen Messszenarien (z.B. Flachwasser vs. Tiefsee) zu wechseln, ohne die Software neu starten zu müssen.

## Datenerfassung und Rohdaten-Handling
Der eigentliche Messvorgang wird durch die Methode `daten_lesen()` gesteuert. Da der Sensor
kontinuierlich Daten sendet, sobald er aktiviert ist (`Start()`), puffert der Treiber den Datenstrom
während der definierten Messdauer.
Der Lesevorgang ruft anschließend die gepufferten Daten ab, wobei standardmäßig eine Blockgröße 
von 4096 Bytes verwendet wird. Dies entspricht der typischen Paketgröße des Sensors im 12-Bit-
Echogramm-Modus. Die empfangenen Rohdaten (Bytes) werden zunächst ungefiltert zwischenge-
speichert, um die Integrität der Messung nicht durch synchrone Verarbeitungsschritte zu gefährden.

## Parsing und Datenaufbereitung

Nach der Erfassung werden die Rohdaten an das Modul `Datenverarbeitung` übergeben. Um die unterschiedlichen Ausgabeformate des Sensors (NMEA, ASCII-Echogramm, Binär) effizient zu handhaben, kommt das **Strategy Pattern** zum Einsatz.

### Architektur der Verarbeitung

Die abstrakte Basisklasse `DataProcessor` definiert die Schnittstelle `process()`, die von spezifischen Implementierungen realisiert wird:

*   **NMEAProcessor**: Extrahiert Tiefeninformationen aus standardisierten NMEA-0183-Sätzen (z.B. `$SDDBT`). Hierbei wird der String dekodiert und auf Validität geprüft.
*   **EchogramProcessor**: Verantwortlich für die komplexere Verarbeitung der Echogramm-Daten. Der Sensor sendet diese in einem proprietären ASCII-Format, das durch Marker wie `#DeviceID` (Start) und `##DataEnd` (Ende) strukturiert ist.

### Parsing-Algorithmus für Echogramme

Der `EchogramProcessor` implementiert einen robusten Parsing-Algorithmus, der den kontinuierlichen Byte-Strom in diskrete Messpakete („Pings“) zerlegt:

1.  **Segmentierung**: Der Datenstrom wird anhand der Start- und End-Marker in einzelne Pakete isoliert. Unvollständige Fragmente am Anfang oder Ende des Streams werden verworfen.
2.  **Header-Extraktion**: Metadaten wie die aktuelle Tiefe, Zeitstempel und Hardware-Status werden aus dem Header-Bereich (zwischen `#DeviceID` und `##DataStart`) in ein Key-Value-Dictionary geparst.
3.  **Signal-Extraktion**: Die eigentlichen Amplitudenwerte des Rückstreusignals befinden sich im Body des Pakets. Diese werden aus dem ASCII-Format in numerische Integer-Arrays konvertiert.

### Datenstrukturierung

Das Ergebnis des Parsing-Prozesses ist eine Liste von typisierten `Measurement`-Objekten (bzw. `EchogramMeasurement`). Diese Datenklasse aggregiert alle relevanten Informationen einer Einzelmessung:

*   **Zeitstempel**: Präziser Zeitpunkt der Erfassung.
*   **Header-Daten**: Metadaten zur Reproduzierbarkeit (z.B. genutzte Frequenz, Gain).
*   **Signalvektor**: Das digitalisierte Echosignal als Array.

Diese objektorientierte Kapselung erleichtert die nachgelagerte Weiterverarbeitung, wie etwa die Feature-Extraktion für die KI-Klassifizierung oder die Visualisierung der Echogramme.
