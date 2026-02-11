```mermaid
flowchart TD
    A([Start: Empfangene Rohdaten (Bytes)]) --> B{Daten vorhanden?};
    B -- Nein --> Z([Ende: Leere Liste]);
    B -- Ja --> C[Konvertierung zu ASCII-String (latin_1)];
    C --> D[Segmentierung: Suche #DeviceID & ##DataEnd];
    D --> E[Liste von Roh-Paketen];
    
    E --> F{Interation über Pakete};
    F -- Nächstes Paket --> G[Extrahiere Header];
    G --> H[Parse Key-Value Paare (z.B. Tiefe, Gain)];
    H --> I[Extrahiere Signal-Daten];
    I --> J[Konvertiere String-Werte zu Integer-Array];
    J --> K[Erstelle EchogramMeasurement Objekt];
    K --> L[Füge zu Ergebnisliste hinzu];
    L --> F;
    
    F -- Keine Pakete mehr --> M([Ende: Liste von Measurements]);
```
