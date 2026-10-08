# Chincheta

Chincheta es una aplicación ligera de notas adhesivas para Linux, escrita en
Python y PySide6.

## Idiomas

- [English](README.md)
- [Español](README.es.md)
- [Deutsch](README.de.md)

## Funciones

- Notas de escritorio editables con texto, color, tamaño y posición
  persistentes
- Títulos de nota en negrita
- Colores personalizados, incluido un rojo de urgencia y una opción verde
- Entrada de color hexadecimal
- Notas siempre encima con estado fijado visible
- Integración con la bandeja del sistema
- Acciones para mostrar y ocultar todas las notas
- Interfaz en español, inglés y alemán, configurable desde Preferencias
- Inicio automático opcional con la sesión de escritorio
- Almacenamiento SQLite bajo el directorio de datos XDG estándar
- Integración con KDE Plasma y XWayland

## Requisitos

- Linux
- Python 3.12 o una versión compatible de Python 3 con `venv`
- `pip`
- Una sesión de escritorio X11, o una sesión Wayland con XWayland disponible

## Compatibilidad de escritorio

El entorno validado es KDE Plasma 5.27 en una sesión Wayland con KWin y
XWayland disponibles.

Chincheta establece `QT_QPA_PLATFORM=xcb` por defecto, salvo que el usuario ya
haya definido esa variable. En sesiones Wayland esto hace que Qt se ejecute a
través de XWayland. Es intencionado: con Qt 6.11 en el entorno Plasma objetivo,
las superficies raster nativas de Wayland mostraban artefactos de renderizado
durante el primer frame, y XWayland también expone las coordenadas globales de
ventana necesarias para persistir la posición de las notas.

Otros escritorios compatibles con X11 o XWayland pueden funcionar, pero KDE
Plasma 5.27 en Wayland es el entorno probado.

## Ejecución

```bash
chmod +x run_chincheta.sh
./run_chincheta.sh
```

El lanzador crea `.venv` e instala las dependencias fijadas cuando hace falta.
Al elegir **Salir** en el menú de la bandeja se elimina el entorno virtual. Una
terminación externa, un fallo o el cierre de sesión lo conservan.

## Lanzador de escritorio

Crea `~/.local/share/applications/chincheta.desktop` con las rutas ajustadas a
tu copia:

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

Después actualiza la base de datos de aplicaciones:

```bash
desktop-file-validate ~/.local/share/applications/chincheta.desktop
update-desktop-database ~/.local/share/applications
```

El inicio automático se puede activar desde **Preferencias**.

## Datos

Las notas se guardan en:

```text
$XDG_DATA_HOME/chincheta/notes.db
```

Si `XDG_DATA_HOME` no está definido, Chincheta usa:

```text
~/.local/share/chincheta/notes.db
```

## Pruebas

Con el entorno virtual disponible:

```bash
python3 -m py_compile chincheta.py storage.py kwin_rules.py
.venv/bin/python -m unittest discover -s tests -v
```

## Estructura del proyecto

- `chincheta.py` - interfaz de usuario y comportamiento de la aplicación
- `storage.py` - persistencia SQLite
- `kwin_rules.py` - integración con reglas de KWin para el modo Wayland nativo
- `kwin_keep_above.js` - ayudante de KWin para mantener notas encima
- `kwin-script/` - paquete instalable del script de KWin
- `run_chincheta.sh` - preparación del entorno y lanzador de la aplicación
- `tests/` - pruebas automatizadas
