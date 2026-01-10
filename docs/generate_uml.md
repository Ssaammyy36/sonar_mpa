# UML Diagramm generieren 

## Instalation 

sudo apt update

sudo apt install graphviz

pip install pylint

## Anwendung

pyreverse -o png -p MeinProjekt src/


## Variante 2

pip install py2puml


py2puml src/ mein_modul > classes.puml
