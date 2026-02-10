```mermaid
flowchart TD
    Start([Start: Main]) --> Init[Initialisiere Steuerung\n(Logger, Sonar, Datenverarbeitung, Classifier)]
    Init --> ExecuteCampaign[execute_campaign()]
    
    ExecuteCampaign --> ConnectSonar{Sonar verbinden?}
    ConnectSonar -- Fehlgeschlagen --> LogError[Log Error & Exit]
    LogError --> End([Ende])
    
    ConnectSonar -- Erfolg --> LoopSessions{Weitere Sessions\ngeplant?}
    
    LoopSessions -- Nein (Alle fertig) --> Disconnect[Sonar trennen]
    Disconnect --> End
    
    LoopSessions -- Ja (Nächste Session) --> ExecuteSession[execute_session(session)]
    ExecuteSession --> LoopTasks{Weitere Tasks\nin Session?}
    
    LoopTasks -- Nein (Session fertig) --> CheckAnalysis{Analyse aktiviert & \nLow+High Daten vorhanden?}
    
    %% Analyse Zweig
    CheckAnalysis -- Ja --> RunClassifier[Klassifizierung: classifier.predict_paired()]
    RunClassifier --> SaveResult[Ergebnis in Settings speichern]
    CheckAnalysis -- Nein --> LogWarning[Warnung: Daten unvollständig\noder Analyse deaktiviert]
    
    SaveResult --> PersistSession[Alle Session-Daten in CSV speichern]
    LogWarning --> PersistSession
    
    PersistSession --> LoopSessions
    
    %% Messung Zweig (Inner Loop)
    LoopTasks -- Ja (Nächster Task) --> ExecuteMeasurement[execute_measurement()]
    ExecuteMeasurement --> ConfigSonar[Sonar konfigurieren\n(Mode, Freq, Settings)]
    ConfigSonar --> ReadData[Daten lesen (mit Timeout)]
    
    ReadData --> CheckData{Daten empfangen?}
    CheckData -- Nein (Timeout) --> LogDataError[Fehler: Keine Daten]
    LogDataError --> ReturnEmpty[Return: Leeres Ergebnis]
    
    CheckData -- Ja --> ProcessData[Verarbeite Daten\n(Datenverarbeitung)]
    ProcessData --> Visualize{Visualisierung an?}
    Visualize -- Ja --> CreatePlot[Erstelle Plot]
    Visualize -- Nein --> SkipPlot[Weiter]
    
    CreatePlot --> ReturnData[Return: Daten & Settings]
    SkipPlot --> ReturnData
    
    ReturnData --> CollectData[Daten für Session sammeln]
    ReturnEmpty --> CollectData
    
    CollectData --> LoopTasks
```
