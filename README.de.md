# Chincheta

Chincheta ist eine schlanke Notizzettel-Anwendung für Linux, entwickelt mit
Python und PySide6.

## Sprachen

- [English](README.md)
- [Español](README.es.md)
- [Deutsch](README.de.md)

## Funktionen

- Bearbeitbare Desktop-Notizen mit dauerhaft gespeichertem Text, Farbe,
  Größe und Position
- Fette Notiztitel
- Eigene Notizfarben, einschließlich eines dringenden Rottons und einer
  grünen Option
- Eingabe von Farben als Hexadezimalwert
- Notizen, die sichtbar als immer im Vordergrund markiert werden können
- Integration in die Systemleiste
- Aktionen zum Anzeigen und Ausblenden aller Notizen
- Oberfläche auf Spanisch, Englisch und Deutsch, einstellbar in den
  Einstellungen
- Optionaler automatischer Start mit der Desktop-Sitzung
- SQLite-Speicherung im Standard-XDG-Datenverzeichnis
- Integration mit KDE Plasma und XWayland

## Voraussetzungen

- Linux
- Python 3.12 oder eine kompatible Python-3-Version mit `venv`
- `pip`
- Eine X11-Desktop-Sitzung oder eine Wayland-Sitzung mit verfügbarem XWayland

## Desktop-Kompatibilität

Die validierte Zielumgebung ist KDE Plasma 5.27 in einer Wayland-Sitzung mit
KWin und verfügbarem XWayland.

Chincheta setzt `QT_QPA_PLATFORM=xcb` standardmäßig, sofern der Benutzer diese
Variable nicht bereits definiert hat. In Wayland-Sitzungen läuft Qt dadurch über
XWayland. Das ist beabsichtigt: Mit Qt 6.11 zeigten native
Wayland-Rasterflächen in der Plasma-Zielumgebung Darstellungsfehler während des
ersten Frames, und XWayland stellt außerdem die globalen Fensterkoordinaten
bereit, die zum Speichern der Notizpositionen benötigt werden.

Andere X11- oder XWayland-kompatible Desktops können funktionieren, aber KDE
Plasma 5.27 auf Wayland ist die getestete Umgebung.

## Ausführung

```bash
chmod +x run_chincheta.sh
./run_chincheta.sh
```

Der Starter erstellt `.venv` und installiert die festgelegten Abhängigkeiten,
wenn sie benötigt werden. Wenn im Menü der Systemleiste **Beenden** gewählt
wird, entfernt Chincheta die virtuelle Umgebung. Externes Beenden, Abstürze
und das Herunterfahren der Sitzung erhalten sie.

## Desktop-Starter

Erstelle `~/.local/share/applications/chincheta.desktop` und passe die Pfade an
deinen Clone an:

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Chincheta
Comment=Sticky notes for the desktop
Exec=/absolute/path/to/chincheta/run_chincheta.sh
Icon=/absolute/path/to/chincheta/icon.svg
Terminal=false
StartupNotify=true
Categories=Office;
StartupWMClass=chincheta
```

Aktualisiere danach die Anwendungsdatenbank:

```bash
desktop-file-validate ~/.local/share/applications/chincheta.desktop
update-desktop-database ~/.local/share/applications
```

Der automatische Start kann in den **Einstellungen** aktiviert werden.

## Daten

Notizen werden gespeichert unter:

```text
$XDG_DATA_HOME/chincheta/notes.db
```

Wenn `XDG_DATA_HOME` nicht gesetzt ist, verwendet Chincheta:

```text
~/.local/share/chincheta/notes.db
```

## Tests

Mit vorhandener virtueller Umgebung:

```bash
python3 -m py_compile chincheta.py storage.py kwin_rules.py
.venv/bin/python -m unittest discover -s tests -v
```

## Projektstruktur

- `chincheta.py` - Benutzeroberfläche und Anwendungsverhalten
- `storage.py` - SQLite-Persistenz
- `kwin_rules.py` - KWin-Regelintegration für die native Wayland-Ausweichlösung
- `kwin_keep_above.js` - KWin-Helfer für "immer im Vordergrund"
- `kwin-script/` - installierbares KWin-Skriptpaket
- `run_chincheta.sh` - Einrichtung der Umgebung und Anwendungsstarter
- `tests/` - automatisierte Tests
