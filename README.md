# Chincheta

Chincheta is a lightweight sticky-notes application for Linux, built with
Python and PySide6.

## Languages

- [English](README.md)
- [Español](README.es.md)
- [Deutsch](README.de.md)

## Features

- Editable desktop notes with persistent text, color, size, and position
- Bold note titles
- Custom note colors, including an urgent red and a green option
- Hexadecimal color input
- Always-on-top notes with a visible pinned state
- System tray integration
- Show-all and hide-all actions
- Spanish, English, and German interfaces, configurable from Preferences
- Optional automatic startup with the desktop session
- SQLite storage under the standard XDG data directory
- KDE Plasma and XWayland integration

## Requirements

- Linux
- Python 3.12 or a compatible Python 3 version with `venv`
- `pip`
- An X11 desktop session, or a Wayland session with XWayland available

## Desktop Compatibility

The validated target environment is KDE Plasma 5.27 running a Wayland session
with KWin and XWayland available.

Chincheta sets `QT_QPA_PLATFORM=xcb` by default, unless the user has already
defined that variable. On Wayland sessions this makes Qt run through XWayland.
This is intentional: with Qt 6.11 on the target Plasma environment, native
Wayland raster surfaces showed rendering artifacts during the first frame, and
XWayland also exposes the global window coordinates used to persist note
positions.

Other X11 or XWayland-compatible desktops may work, but KDE Plasma 5.27 on
Wayland is the tested setup.

## Running

```bash
chmod +x run_chincheta.sh
./run_chincheta.sh
```

The launcher creates `.venv` and installs the pinned dependencies when needed.
Choosing **Quit** from the tray menu removes the virtual environment. External
termination, crashes, and session shutdowns preserve it.

## Desktop launcher

Create `~/.local/share/applications/chincheta.desktop` with paths adjusted to
your clone:

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

Then refresh the application database:

```bash
desktop-file-validate ~/.local/share/applications/chincheta.desktop
update-desktop-database ~/.local/share/applications
```

Automatic startup can be enabled from **Preferences**.

## Data

Notes are stored in:

```text
$XDG_DATA_HOME/chincheta/notes.db
```

If `XDG_DATA_HOME` is not set, Chincheta uses:

```text
~/.local/share/chincheta/notes.db
```

## Tests

With the virtual environment available:

```bash
python3 -m py_compile chincheta.py storage.py kwin_rules.py
.venv/bin/python -m unittest discover -s tests -v
```

## Project structure

- `chincheta.py` — user interface and application behavior
- `storage.py` — SQLite persistence
- `kwin_rules.py` — KWin rule integration for native Wayland fallback
- `kwin_keep_above.js` — KWin always-on-top helper
- `kwin-script/` — installable KWin script package
- `run_chincheta.sh` — environment bootstrap and application launcher
- `tests/` — automated tests
