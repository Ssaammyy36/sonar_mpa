\chapter{Konzeption und Implementierung}

\section{Technische Spezifikation des Sonarsensors}

%% SensorTyp
Als zentrales Messinstrumentarium dieser Arbeit kommt das Modell \textit{ECT D052} des Herstellers EchoLogger zum Einsatz. Konzipiert als Dual-Frequency Single Beam Echosounder, ermöglicht das System den operativen Betrieb bei Frequenzen von \SI{200}{\kilo\hertz} oder \SI{50}{\kilo\hertz}. Die datentechnische Anbindung an das Host-System wird über eine RS-232/RS-485-Schnittstelle realisiert, welche mittels Adapter auf den USB-Standard umgesetzt wird \cite{eofe_ultrasonics_co_ltd_user_nodate}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\linewidth]{content/images/sonar_ect_d052.jpg}
    \caption{\centering Sonarsensor EchoLogger ECT D052 \cite{eofe_ultrasonics_co_ltd_user_nodate}}
    \label{fig:sonar_ect_d052}
\end{figure}

%% Funktion
Die hochfrequente Signalkomponente (\SI{200}{\kilo\hertz}) weist aufgrund ihrer kurzen Wellenlänge eine hohe Sensitivität gegenüber der Oberflächenbeschaffenheit des Sediments auf, besitzt jedoch eine geringe Penetrationstiefe. Folglich werden primär Informationen über die Topographie der Sedimentoberfläche erfasst.

Im Gegensatz dazu dringt das niederfrequente Signal (\SI{50}{\kilo\hertz}) signifikant tiefer in das Substrat ein. Da es an der Grenzschicht weniger stark gestreut wird, liefert es detaillierte Informationen über die innere Beschaffenheit und Dichte des Sediments.

\subsubsection*{Signalverarbeitung und Auflösung}

Der Sensor operiert im 12-Bit-Modus, wodurch die analoge Signalstärke in einen digitalen Wertebereich von 0 bis 4095 ($2^{12}$ Intensitätsstufen) quantisiert wird.

Die Digitalisierung des analogen Echosignals erfolgt mittels eines Analog-Digital-Wandlers (ADC) mit einer maximalen Abtastrate von \SI{100}{\kilo\hertz}. Unter der Prämisse einer Schallgeschwindigkeit von $c \approx \SI{1500}{\meter\per\second}$ resultiert aus dem Abtastintervall zwischen zwei Samples ($\Delta t = \SI{10}{\micro\second}$) eine theoretische vertikale Auflösung $\Delta z$ der Wassersäule von:

\begin{equation}
\Delta z = \frac{c \cdot \Delta t}{2} \approx \SI{7.5}{\milli\meter}
\end{equation}

\subsection{Versuchsaufbau und Datengrundlage}

Der experimentelle Aufbau wurde konzipiert, um reproduzierbare akustische Messungen an definierten Sedimentproben unter kontrollierten Laborbedingungen durchzuführen. Abbildung \ref{fig:foto_versuchsaufbau} zeigt den physischen Aufbau der Messstrecke.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{content/images/versuchsaufbau.jpg}
    \caption{\centering Versuchsaufbau zur Datenerfassung im Wassertank}
    \label{fig:foto_versuchsaufbau}
\end{figure}

Die Versuche fanden in einem Wassertank mit den Dimensionen \SI{120}{\centi\meter} $\times$ \SI{50}{\centi\meter} $\times$ \SI{80}{\centi\meter} ($L \times B \times H$) statt. Um eine hinreichende Signalpropagationsstrecke im Fernfeld des Sensors zu gewährleisten, wurde eine konstante Wassertiefe von \SI{70}{\centi\meter} gewählt. 

Zur Aufnahme der Sedimentproben wurden drei separate Behälter mit den Abmessungen \SI{45}{\centi\meter} $\times$ \SI{30}{\centi\meter} $\times$ \SI{30}{\centi\meter} ($L \times B \times H$) verwendet, die am Boden des Tanks positioniert wurden. Der Sonarsensor wurde mittels einer speziell angefertigten Halterung fixiert. Diese Konstruktion stellt sicher, dass der Sensor mechanisch entkoppelt ist und exakt vertikal über den Probenzentren ausgerichtet werden kann, was für die Vergleichbarkeit der Echogramme essenziell ist.

Die Untersuchung umfasst drei distinkte Sedimentklassen, die aufgrund ihrer unterschiedlichen akustischen Impedanzen und Streueigenschaften ausgewählt wurden. Die Materialien und ihre physikalischen Eigenschaften sind in Tabelle \ref{tab:untergrundklassen} zusammengefasst.

\begin{table}[H]
    \centering
    \caption{\centering Charakterisierung der Untergrundklassen}
    \label{tab:untergrundklassen}
    \begin{tabular}{|l|c|l|}
        \hline
        \textbf{Klasse} & \textbf{Korngröße (ca.)} & \textbf{Akustische Erwartung} \\
        \hline
        Sand & $\le \SI{2}{\milli\meter}$ & Homogene Oberfläche, geringe Streuung, hohe Dämpfung \\
        \hline
        Kies & $\approx \SI{2}{\milli\meter} - \SI{60}{\milli\meter}$ & Erhöhte Oberflächenrauigkeit, moderates Volume Scattering \\
        \hline
        Steine & $> \SI{60}{\milli\meter}$ & Starke diffuse Streuung, hohe Reflexionsenergie \\
        \hline
    \end{tabular}
\end{table}

\section{Sensoransteuerung und Kommunikation}

Die Software-Architektur folgt einem streng modularen Ansatz, um die Hardware-Steuerung (\ac{HAL}) von der Verarbeitungslogik zu entkoppeln. Dies gewährleistet Wartbarkeit und die einfache Integration neuer Sensormodelle.

\subsection{Hardware Abstraction Layer (HAL)} 

Die Klasse \texttt{Sonar} dient als \ac{HAL} und kapselt die proprietäre Treiber-Logik der Bibliothek \texttt{echosounderapi}. Durch diese Kapselung wird die Komplexität der asynchronen seriellen Kommunikation vor den höherliegenden Anwendungsschichten verborgen.

\subsubsection*{Dynamische Konfiguration} 
Die Methode \texttt{konfigurieren()} erlaubt eine Laufzeit-Anpassung der Sensorparameter. Dies ist essenziell für Multi-Frequenz-Untersuchungen, da so zwischen \SI{50}{\kilo\hertz} und \SI{200}{\kilo\hertz} umgeschaltet werden kann, ohne die Verbindung neu zu initialisieren. 
Wichtige Signalparameter wie die Pulslänge (\texttt{IdTxLength}) und die Verstärkung (\texttt{IdGain}) werden direkt in die Hardware-Register geschrieben, um das Signal-Rausch-Verhältnis (\ac{SNR}) an die jeweilige Umgebung (z.\,B. Wassertiefe) anzupassen.

\subsubsection*{Asynchrone Datenerfassung} 
Da die serielle Übertragung nicht deterministisch ist, implementiert die Methode \texttt{daten\_lesen()} einen Puffer-Mechanismus. Der Sensor sendet kontinuierlich Datenpakete, sobald der Befehl \texttt{Start()} empfangen wird. Die Software wartet für ein definiertes Zeitfenster (Blocking I/O), während der Treiber im Hintergrund den eingehenden Byte-Strom akkumuliert. Anschließend wird der Puffer (\SI{4096}{\byte}) als atomarer Block ausgelesen. Strategien zur Behandlung von Paketfragmentierung (Zerstückelung von Datenpaketen) werden in der nachfolgenden Verarbeitungsschicht implementiert.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\linewidth]{content/images/Sonar Kommunikation-2026-02-11-132123.png}
    \caption{\centering Sequenzdiagramm der Sensorkommunikation}
    \label{fig:seq_sonar_comm}
\end{figure}

\subsection{Parsing-Strategien und Design Patterns}
Die Interpretation der Rohdaten erfolgt im Modul \texttt{Datenverarbeitung}. Um die Variabilität der Sensor-Ausgabeformate (NMEA-Text, Binärdaten, ASCII-Echogramme) architektonisch sauber abzubilden, wurde das **Strategy Pattern** implementiert.

\subsubsection*{Architektur der Datenverarbeitung}
Die abstrakte Klasse \texttt{DataProcessor} definiert den Vertrag für alle Verarbeitungsalgorithmen. Dies erfüllt das Open-Closed Principle: Soll der Sensor zukünftig Binärdaten statt ASCII senden, muss lediglich eine neue \texttt{BinaryProcessor}-Klasse hinzugefügt werden, ohne die bestehende Steuerungslogik zu modifizieren.

\begin{figure}[ht]
    \centering
    \includegraphics[width=0.8\linewidth]{content/images/Data Processor-2026-02-11-143000.png}
    \caption{\centering Implementierung des Strategy Patterns}
    \label{fig:class_data_proc}
\end{figure}

\subsubsection*{Robustes Parsing von Datenströmen}
Besondere Herausforderung stellt das proprietäre ASCII-Format des Sensors dar. Da serielle Streams keine garantierten Paketgrenzen besitzen, implementiert der \texttt{EchogramProcessor} einen robusten State-Machine-Algorithmus:

\begin{enumerate}
    \item \textbf{Resynchronisation:} Der Parser sucht aktiv nach dem Start-Marker \texttt{\#DeviceID}, um sich nach Übertragungsfehlern neu auf den Datenstrom zu synchronisieren.
    \item \textbf{Integritätsprüfung:} Ein Paket wird nur akzeptiert, wenn sowohl Header als auch der Abschluss-Marker \texttt{\#\#DataEnd} vollständig empfangen wurden.
    \item \textbf{Typisierung:} Die extrahierten Amplitudenwerte werden von ASCII-Strings in numerische Ganzzahl-Vektoren überführt und in \texttt{EchogramMeasurement}-Objekten gekapselt.
\end{enumerate}

\begin{lstlisting}[basicstyle=\footnotesize\ttfamily, caption={Exemplarischer Datenstrom des Echosounders (ASCII-Format)}, label={lst:echosounder_stream}]
#DeviceID  D24 Type RS232
...
#Tx_Frequency,Hz 200000
#Range,m  50.0
#Pitch,deg  4.900
##DataStart
142
216
...
##DataEnd
\end{lstlisting}

\section{Feature Engineering und Signalverarbeitung}

Rohdaten von Echosoundern sind hochdimensional und rauschbehaftet. Für eine effiziente Klassifizierung ist daher eine Reduktion auf diskriminative Merkmale (Feature Extraction) notwendig. Dieser Prozess findet in der Klasse \texttt{FeatureBasedModel} statt.

\subsection{Zeitliche Ausrichtung (Alignment)}
Da der Abstand zwischen Sensor und Boden variieren kann, ist eine zeitliche Synchronisation der Signale erforderlich. Hierzu wird mittels einer Peak-Detektion das erste starke Echo (Bodenreflexion) ermittelt. Um auch den Anstieg des Signals ("Onset") zu erfassen, wird ein Fenster von $N=155$ Samples definiert, das relativ zum Peak positioniert wird. Dies macht die Features robust gegenüber Schwankungen der Wassertiefe.

\subsection{Merkmalsextraktion}
Aus dem gefensterten Signal werden physikalisch interpretierbare Kennzahlen abgeleitet:

\begin{itemize}
    \item \textbf{Energiemaß (E):} Die Summe der quadrierten Amplituden korreliert mit der akustischen Härte des Bodens (Reflexionskoeffizient). Harte Substrate wie Steine reflektieren mehr Energie als weicher Sand.
    \item \textbf{Pulsbreite (Width):} Die zeitliche Ausdehnung des Echos bei halber Maximalamplitude gibt Aufschluss über die Rauigkeit. Eine raue Oberfläche (Kies) streut das Signal zeitlich stärker als eine glatte Oberfläche (Sand).
    \item \textbf{Signalform:} Zusätzlich zu skalaren Metriken wird der gesamte normalisierte Signalverlauf als Vektor genutzt, um subtile Formunterschiede zu erfassen.
\end{itemize}

\section{Klassifikationsproblem und Evaluationskonzept}

Das Kernstück der Analyse bildet ein überwachtes Lernverfahren (\textit{Supervised Learning}), welches den Zusammenhang zwischen extrahierten Merkmalen und Sedimentklassen modelliert.

\subsection{Modellarchitektur}
Als primärer Klassifikator wird ein \textbf{Random Forest} eingesetzt. Diese Wahl begründet sich durch:
\begin{enumerate}
    \item \textbf{Robustheit:} Entscheidungsbäume sind unempfindlich gegenüber nicht-skalierten Daten und Ausreißern.
    \item \textbf{Relevanzanalyse:} Der Algorithmus erlaubt eine Bewertung der Feature-Wichtigkeit (Feature Importance), was physikalische Rückschlüsse auf die unterscheidenden Merkmale zulässt.
\end{enumerate}
Alternativ steht ein \acl{MLP} (\ac{MLP}) zur Verfügung, um nicht-lineare Zusammenhänge höherer Ordnung abzubilden.

\subsection{Evaluationsstrategie und Limitationen}
Die Bewertung der Modelle erfolgt primär über den \textbf{F1-Score}, da dieser (im Gegensatz zur Accuracy) auch bei unbalancierten Datensätzen ein verlässliches Gütemaß darstellt. Zur Validierung der Generalisierungsfähigkeit wird eine \textit{Cross-Validation} durchgeführt.

\textit{Kritische Reflexion:} Es ist zu beachten, dass die Trainingsdaten in einer kontrollierten Laborumgebung (Wassertank) erhoben wurden. Reale maritime Umgebungen führen zusätzliche Störgrößen wie Schwebstoffe, Strömungen oder variierende Einfallswinkel durch Schiffsbewegungen (Roll/Pitch) ein. Die Übertragbarkeit der Ergebnisse auf Feldmessungen stellt somit eine Limitation dar, die in der Diskussion weiter beleuchtet wird.
