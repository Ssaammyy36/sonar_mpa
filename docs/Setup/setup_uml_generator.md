# UML Diagramm generieren

## Variante 1 Instalation

**Instalation**

```shell
# Für Ubuntu

sudo apt update
sudo apt install graphviz
pip install pylint
```

```shell
# Für Windows

#...
```

**Anwendung**

`pyreverse -o png -p MeinProjekt src/`

## Variante 2

**Instalation**

`pip install py2puml`

**Anwendung**

`py2puml src/ mein_modul > docs/uml/classes.puml`
