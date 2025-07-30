# Style Guide for Python Code

Hier wir beschreiben, wie in unserem Projekt Code geschrieben werden soll.

## 1. Allgemeiner Stil: PEP 8

Verwendet den offiziellen Python-Styleguide: [PEP 8](https://peps.python.org/pep-0008/). Schau hier mal rein. 

## 2. Benennungen (Naming)

| Art        | Konvention   | Beispiel         |
|------------|--------------|------------------|
| Variablen  | snake_case   | user_name        |
| Funktionen | snake_case() | calculate_sum()  |
| Klassen    | CamelCase    | DataProcessor    |
| Konstanten | ALL_CAPS     | PI = 3.14        |

## 3. Normale Kommentare 

- Inline-Kommentar
  
    ```python
    x = x + 1  # Zähler erhöhen
    ```

- Block-Kommentar
  
    ```python
    # Prüfe, ob das Signal stabil ist,
    # bevor mit der Messung begonnen wird.
    if signal_is_stable(signal):
        start_measurement()
    ```

- Sonderkommentare
  
    ```python
    # TODO: Sensor-Kalibrierung einbauen
    # FIXME: Übergangslösung – nicht robust
    ```

## 3. Docstring Kommentare (für Doku-Tools wie Sphinx)

Wir verwenden Google-Style Docstrings, da sie lesbar sind und mit Sphinx automatisch eine Dokumentation erzeugen können

- Funktion – Docstring (Google Style)
  
    ```python
    def add(a: int, b: int) -> int:
        """
        Gibt die Summe von a und b zurück.

        Args:
            a (int): Erste Zahl
            b (int): Zweite Zahl

        Returns:
            int: Summe der beiden Zahlen
        """
        return a + b
    ```

- Klasse – Docstring
 
    ```python
    class Sensor:
        """
        Repräsentiert einen Sonar-Sensor.

        Attributes:
            id (str): Sensor-ID
            status (str): Aktueller Status
        """

        def __init__(self, id: str):
            """
            Initialisiert einen neuen Sensor.

            Args:
                id (str): Eindeutige Sensor-ID
            """
            self.id = id
            self.status = "off"
    ```
