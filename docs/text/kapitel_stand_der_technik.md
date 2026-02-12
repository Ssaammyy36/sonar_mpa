\chapter{Stand der Technik und Einordnung der Arbeit}

\section{Ausgangspunkt der Arbeit}

Die vorliegende Arbeit baut auf einer spezifischen Infrastruktur auf, welche die Rahmenbedingungen sowohl für die Implementierung der Sensorkommunikation und die Validierung der Messdaten, als auch für die darauf aufbauende Entwicklung des Klassifizierungssystems definierte.

\subsection{Hardware- und Software-Voraussetzungen}
Als primäre Messkomponente stand der Sonarsensor \textit{EchoLogger ECT D052} zur Verfügung. Die Auswahl dieses Sensors begründet sich in dessen Verfügbarkeit am Institut sowie dem günstigen Kosten-Nutzen-Verhältnis für akademische Forschungszwecke. Trotz seiner kompakten Bauweise ermöglicht das Gerät durch den Dual-Frequenz-Betrieb (\SI{50}{\kilo\hertz} und \SI{200}{\kilo\hertz}) vergleichende Untersuchungen unterschiedlicher akustischer Bodenantworten.

Zu Beginn der Arbeit lag keine spezifische Softwarelösung für die automatisierte Ansteuerung des Sensors oder die systematische Erfassung von Trainingsdaten vor. Die Entwicklung einer entsprechenden Steuerungssoftware sowie die Implementierung der prozessinternen Signalverarbeitungs-Pipelines stellten somit einen integralen Bestandteil der Aufgabenstellung dar.

\subsection{Experimentelle Umgebung}
Für die Durchführung der experimentellen Validierung wurde ein stationäres Wasserbecken bereitgestellt. Dieses bot eine einfache und kontrollierbare Umgebung, um reproduzierbare Testbedingungen für verschiedene Messreihen zu schaffen.

Zu Beginn der Arbeit war dieses Becken lediglich mit Wasser gefüllt. Im weiteren Verlauf wurde der experimentelle Aufbau modular erweitert:
Innerhalb des großen Beckens wurden drei separate Behältnisse platziert, die als definierte Probenkörper dienten. Diese wurden jeweils mit einem homogenen Sedimenttyp (Sand, Kies, Steine) befüllt. Dieser Aufbau erlaubte einen schnellen Wechsel zwischen den Substraten und gewährleistete konstante Umgebungsbedingungen während der Messungen.

\section{Verwandte Arbeiten und Forschungsrelevanz}

Die akustische Klassifizierung von Gewässerböden hat sich in den letzten Jahrzehnten von einfachen echolotbasierten Verfahren zu komplexen multispektralen und lernbasierten Ansätzen entwickelt. Dieses Kapitel gibt einen Überblick über den aktuellen Stand der Technik hinsichtlich der verwendeten Sensorsysteme, Frequenzen, Merkmalsextraktion und Klassifikationsalgorithmen. Darauf aufbauend werden bestehende Limitierungen identifiziert und die Relevanz der vorliegenden Arbeit im Kontext kostengünstiger Dual-Frequenz-Systeme unter kontrollierten Bedingungen hergeleitet.

\subsection{Ansätze zur Untergrundklassifizierung}
In der Literatur lassen sich zwei Hauptströmungen zur akustischen Bodenklassifizierung identifizieren: bildgebende Verfahren mittels Side-Scan-Sonar (\ac{SSS}) und Multi-Beam-Echosoundern (\ac{MBES}) sowie signalbasierte Verfahren mittels Single-Beam-Echosoundern (\ac{SBES}).

Bildgebende Verfahren nutzen primär die räumliche Textur und die Rückstreustärke (Backscatter) des akustischen Bildes. Zhao et al. demonstrierten beispielsweise die Klassifizierung von Sedimenten (Fels, Sand, Schlamm) mittels \ac{SSS}-Bildern, indem sie Deep-Learning-Ansätze wie \ac{CNN} (Convolutional Neural Networks) einsetzten, welche traditionelle Merkmalsextraktionsmethoden übertrafen \cite{zhao_sediment_classification}. Auch Lubniewski et al. kombinierten bathymetrische Daten mit Grauwert-Statistiken und fraktalen Analysen aus \ac{MBES}-Bildern zur Sedimentcharakterisierung \cite{lubniewski_fractal}.

Im Gegensatz dazu fokussieren sich signalbasierte \ac{SBES}-Ansätze, die dem in dieser Arbeit verfolgten Ansatz näherstehen, auf die Analyse der Echohüllkurve (Echo Envelope). Historisch etabliert sind hierbei Methoden, die auf der Energie des ersten und zweiten Echos basieren. Hamilton beschreibt das weit verbreitete RoxAnn-System, welches den Roughness-Index E1 (Ausklang des ersten Echos) und den Hardness-Index E2 (zweites Echo) nutzt \cite{hamilton_roxann}. Hamuna et al. erweiterten diesen Ansatz kürzlich, indem sie zeigten, dass die Hinzunahme von Parametern des dritten Echos sowie detaillierte Phaseninformationen (Attack/Decay) die Klassifikationsgenauigkeit signifikant erhöhen können \cite{hamuna_echo_envelope}. Auch Snellen et al. bestätigten, dass modellbasierte Ansätze, die die volle Echohüllkurve (\enquote{Full Echo Envelope}) nutzen, gegenüber reinen Energie-Ansätzen überlegen sind, wenngleich sie rechenintensiver ausfallen \cite{snellen_model_based}.

Die Rolle der Feature Extraction ist dabei zentral. Während ältere Ansätze oft proprietäre Indizes verwendeten, zeigen aktuelle Studien den Trend zu physikalisch interpretierbaren Features (z.\,B. Echo-Länge, spektrale Momente) oder rein datengetriebenen Features, die direkt durch Machine Learning Algorithmen aus den Rohdaten gelernt werden, wie Brautaset et al. am Beispiel von Multifrequenz-Daten zeigten \cite{brautaset_multifrequency}.

\subsection{Technische Setups und Frequenzen}
Die Wahl der Frequenz ist entscheidend für die Interaktion des Schalls mit dem Sediment. In der Literatur sind Frequenzen im Bereich von \SI{30}{\kilo\hertz} bis \SI{400}{\kilo\hertz} üblich, wobei \SI{50}{\kilo\hertz} und \SI{200}{\kilo\hertz} als Standardfrequenzen für \ac{SBES} gelten.

Quintino et al. untersuchten die Eignung eines \SI{50}{\kilo\hertz}/\SI{200}{\kilo\hertz}-Systems (QTC VIEW) zur Vegetations- und Sedimentbestimmung. Sie stellten fest, dass \SI{200}{\kilo\hertz}-Signale besser zur Differenzierung von Biomasse geeignet waren, während beide Frequenzen Sedimentunterschiede in Flachwasserbereichen auflösen konnten \cite{quintino_qtc_view}. Die physikalische Notwendigkeit mehrerer Frequenzen wird auch von Hamilton betont: Unterschiedliche Frequenzen interagieren verschieden mit der Rauheit und Korngröße des Bodens, sodass ein Dual- oder Multifrequenz-Ansatz die Diskriminierungsfähigkeit erhöht.

Aktuelle Forschungen, wie die von Ntouskos et al. im Rahmen der \enquote{R2Sonic Multispectral Challenge}, heben den Vorteil multispektraler Daten (z.\,B. \SI{100}{\kilo\hertz}, \SI{200}{\kilo\hertz}, \SI{400}{\kilo\hertz}) hervor. Sie zeigten, dass die Kombination mehrerer Frequenzen oft ausreicht, um hohe Klassifikationsgüten zu erreichen, ohne zwingend auf bathymetrische Hilfsdaten angewiesen zu sein \cite{ntouskos_multispectral}. Dies stützt die Hypothese unserer Arbeit, dass die Fusion von \SI{50}{\kilo\hertz} und \SI{200}{\kilo\hertz} Signalen in einem kostengünstigen Setup signifikante Informationsgewinne liefert.

\subsection{Verwendete Algorithmen}
Hinsichtlich der Klassifikationsalgorithmen gilt Machine Learning (\ac{ML}) als \enquote{State of the Art}. Stephens und Diesing verglichen sechs verschiedene Algorithmen für \ac{MBES}-Daten und identifizierten Random Forest (\ac{RF}) sowie Support Vector Machines (\ac{SVM}) als leistungsfähige Methoden, wobei \ac{RF} oft robuster gegenüber Rauschen war \cite{stephens_diesing_comparison}.

Auch Hamuna et al. nutzten \ac{RF} und \ac{SVM} zur Klassifizierung von \ac{SBES}-Daten. In ihrer Studie erreichte der Random Forest Algorithmus mit einer Genauigkeit von \SI{79,33}{\percent} leicht bessere Ergebnisse als die \ac{SVM} mit \SI{78,67}{\percent}. Ntouskos et al. verglichen \ac{RF}, \ac{SVM} und Multilayer Perceptrons (\ac{MLP}) für multispektrale Daten und fanden, dass MLPs in ihrem Szenario die besten Ergebnisse lieferten, insbesondere hinsichtlich der räumlichen Kohärenz der Klassifizierung.

Neuere Ansätze setzen vermehrt auf Deep Learning. Zhao et al. nutzten ein Dimension-Invariant Residual Network (eine \ac{CNN}-Variante), um Sedimente auf Sonarbildern mit fast \SI{98}{\percent} Genauigkeit zu klassifizieren \cite{zhao_residual_network}. Ebenso verwendeten Zhou et al. Stacked Denoising Autoencoders (SDAE) in Kombination mit Extreme Learning Machines (ELM), um Robustheit gegenüber Bildrauschen zu erzielen \cite{zhou_sdae}. Dennoch bleibt der Random Forest aufgrund seiner Nachvollziehbarkeit und Effizienz bei tabellarischen Feature-Sets ein Goldstandard in der Literatur.

\subsection{Limitierungen bisheriger Arbeiten}
Trotz der technologischen Fortschritte bestehen signifikante Limitierungen in der bisherigen Forschung:

\begin{enumerate}
    \item \textbf{Kosten und Komplexität:} Viele Studien stützen sich auf teure \ac{MBES}- oder \ac{SSS}-Systeme (vgl. Schönrock et al., Danube Manual), die für kleine Gewässer oder Low-Budget-Projekte oft unzugänglich sind.
    \item \textbf{Mangelnde Validierung (Ground Truth):} Ein wiederkehrendes Problem ist die Qualität der Referenzdaten. Stephens und Diesing sowie Biffard weisen darauf hin, dass Greiferproben (Grab Samples) oft Positionsfehler aufweisen oder die akustische Variabilität nicht adäquat abbilden \cite{biffard_ground_truth}.
    \item \textbf{Fehlende Standardisierung bei SBES:} Während für marine \ac{MBES}-Anwendungen Standards existieren, fehlen diese oft für \ac{SBES} in Binnengewässern. Zudem sind viele kommerzielle Systeme (wie QTC oder RoxAnn) \enquote{Black Boxes}, deren interne Algorithmen nicht vollständig transparent sind, wie Hamilton kritisiert.
    \item \textbf{Einfluss von Störgrößen:} In Felddaten sind externe Einflüsse wie Bootsbewegungen, wechselnde Wassertiefen und Hangneigungen schwer zu isolieren, was die Entwicklung robuster physikalischer Modelle erschwert (Biffard, Schönrock et al.).
\end{enumerate}

\subsection{Einordnung unserer Arbeit (Forschungsrelevanz)}
Die vorliegende Masterarbeit adressiert diese Forschungslücken durch einen integrierten Ansatz. Während die Mehrheit der Studien teure Multi-Beam-Systeme oder komplexe Side-Scan-Sonare verwendet, untersuchen wir das Potenzial eines kostengünstigen Single-Beam-Sensors (\SI{50}{\kilo\hertz}/\SI{200}{\kilo\hertz}).

Die Relevanz unserer Arbeit begründet sich durch drei Kernaspekte:

\begin{enumerate}
    \item \textbf{Kosten-Effizienz:} Wir prüfen, ob moderne \ac{ML}-Algorithmen (\ac{RF}, \ac{MLP}) die hardwareseitigen Limitierungen günstiger Sensoren kompensieren können, um valide Ergebnisse für Anwendungen mit begrenztem Budget (z.\,B. Monitoring kleiner Binnengewässer) zu liefern.
    \item \textbf{Dual-Frequency-Fusion:} In Anlehnung an Ntouskos et al. und Quintino et al. nutzen wir explizit die Informationsdichte zweier Frequenzen (\SI{50}{\kilo\hertz} und \SI{200}{\kilo\hertz}), um die physikalischen Interaktionen (Eindringtiefe vs. Oberflächenstreuung) für die Klassifikation von Sand, Kies und Steinen nutzbar zu machen.
    \item \textbf{Kontrollierte Validierung:} Im Gegensatz zu Feldstudien mit unsicherer Ground Truth (vgl. Biffard), führen wir unsere Experimente in einer kontrollierten Laborumgebung durch. Dies eliminiert externe Störfaktoren und ermöglicht eine präzise Zuordnung von akustischen Signalen zu definierten Sedimentklassen, was eine essentielle Grundlage für das Training und die Validierung der \ac{ML}-Modelle darstellt.
\end{enumerate}

Damit leistet diese Arbeit einen Beitrag zur Entwicklung transparenter, kostengünstiger und robuster Methoden für die hydroakustische Bodenklassifizierung.
