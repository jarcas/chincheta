#!/usr/bin/env python3
"""Chincheta: lightweight desktop sticky notes for Linux."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Qt 6 raster surfaces show corrupted initial buffers under KWin 5.27
# Wayland on the target desktop. XWayland is stable and also exposes the
# global window coordinates needed to persist note positions.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PySide6.QtCore import QEvent, QPoint, Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QSystemTrayIcon, QTextEdit, QVBoxLayout, QWidget,
)

from storage import NoteStore
from kwin_rules import KWinRules

APP_NAME = "Chincheta"
APP_ICON = Path(__file__).with_name("icon.svg")
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "chincheta"
VENV_DELETE_MARKER = DATA_DIR / ".delete-venv-on-exit"
DESKTOP_FILE = Path.home() / ".local" / "share" / "applications" / "chincheta.desktop"
AUTOSTART_FILE = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart" / "chincheta.desktop"
KWIN_SCRIPT = Path(__file__).with_name("kwin_keep_above.js")
COLOURS = ["#FFF59D", "#EF5350", "#C8E6C9", "#B2DFDB", "#BBDEFB", "#E1BEE7"]
HOVER_HINT_STYLE = (
    "QLabel#hoverHint {"
    " background-color: #fffbe6;"
    " color: #202020;"
    " border: 1px solid #767676;"
    " border-radius: 3px;"
    " padding: 4px 6px;"
    "}"
)
TEXT = {
    "es": {"new": "Nueva nota", "show": "Mostrar todas", "hide": "Ocultar todas", "prefs": "Preferencias", "quit": "Salir", "title": "Título", "body": "Escribe aquí…", "delete": "Eliminar", "colour": "Color", "pin": "Siempre encima", "unpin": "Quitar siempre encima", "language": "Idioma", "autostart": "Iniciar con la sesión", "settings": "Preferencias", "confirm": "¿Eliminar esta nota?", "yes": "Eliminar", "no": "Cancelar", "save": "Guardar", "cancel": "Cancelar", "choose_colour": "Color de la nota", "hex_colour": "Color hexadecimal", "apply": "Aplicar", "drag": "Arrastrar nota"},
    "en": {"new": "New note", "show": "Show all", "hide": "Hide all", "prefs": "Preferences", "quit": "Quit", "title": "Title", "body": "Write here…", "delete": "Delete", "colour": "Colour", "pin": "Always on top", "unpin": "Stop staying on top", "language": "Language", "autostart": "Start with the session", "settings": "Preferences", "confirm": "Delete this note?", "yes": "Delete", "no": "Cancel", "save": "Save", "cancel": "Cancel", "choose_colour": "Note colour", "hex_colour": "Hex colour", "apply": "Apply", "drag": "Drag note"},
    "de": {"new": "Neue Notiz", "show": "Alle anzeigen", "hide": "Alle ausblenden", "prefs": "Einstellungen", "quit": "Beenden", "title": "Titel", "body": "Hier schreiben…", "delete": "Löschen", "colour": "Farbe", "pin": "Immer im Vordergrund", "unpin": "Nicht mehr im Vordergrund", "language": "Sprache", "autostart": "Mit der Sitzung starten", "settings": "Einstellungen", "confirm": "Diese Notiz löschen?", "yes": "Löschen", "no": "Abbrechen", "save": "Speichern", "cancel": "Abbrechen", "choose_colour": "Notizfarbe", "hex_colour": "Hex-Farbe", "apply": "Anwenden", "drag": "Notiz verschieben"},
}


def note_window_flags() -> Qt.WindowType:
    return Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint


def action_icon(action: str) -> QIcon:
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if action == "accept":
        painter.setPen(QPen(QColor("#238636"), 2.5))
        painter.drawLine(3, 8, 7, 12)
        painter.drawLine(7, 12, 14, 4)
    elif action == "delete":
        painter.setPen(QPen(QColor("#c62828"), 2))
        painter.drawLine(4, 5, 12, 5)
        painter.drawLine(6, 3, 10, 3)
        painter.drawRect(5, 6, 6, 7)
    else:
        painter.setPen(QPen(QColor("#555555"), 2.5))
        painter.drawLine(4, 4, 12, 12)
        painter.drawLine(12, 4, 4, 12)
    painter.end()
    return QIcon(pixmap)


class ColourPicker(QDialog):
    """Opaque, toolkit-only selector that avoids Plasma's native colour dialog."""
    def __init__(self, app: "ChinchetaApp", current: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.app, self.colour = app, current
        self.setWindowTitle(app.t("choose_colour"))
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "QDialog { background-color: #f7f7f7; color: #202020; }"
            "QLabel { color: #202020; background: transparent; }"
            "QLineEdit { background-color: #ffffff; color: #202020; border: 1px solid #999999; padding: 5px; }"
            "QPushButton { background-color: #ffffff; color: #202020; border: 1px solid #999999; border-radius: 4px; padding: 6px 12px; }"
        )
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(app.t("choose_colour")))
        palette = QGridLayout()
        for index, colour in enumerate(COLOURS):
            button = QPushButton(colour)
            button.setStyleSheet(f"QPushButton {{ background-color: {colour}; color: #202020; border: 1px solid #777777; min-height: 28px; }}")
            button.clicked.connect(lambda checked=False, c=colour: self.select(c))
            palette.addWidget(button, index // 2, index % 2)
        layout.addLayout(palette)
        layout.addWidget(QLabel(app.t("hex_colour")))
        self.hex_input = QLineEdit(current); layout.addWidget(self.hex_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(app.t("apply"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(app.t("cancel"))
        buttons.button(QDialogButtonBox.StandardButton.Ok).setIcon(action_icon("accept"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setIcon(action_icon("cancel"))
        buttons.accepted.connect(self.select_custom); buttons.rejected.connect(self.reject); layout.addWidget(buttons)

    def select(self, colour: str) -> None:
        self.colour = colour; self.accept()

    def select_custom(self) -> None:
        colour = QColor(self.hex_input.text().strip())
        if colour.isValid():
            self.colour = colour.name(); self.accept()
        else:
            self.hex_input.setStyleSheet("background-color: #fee2e2; color: #202020; border: 1px solid #c53030; padding: 5px;")


class DragHandle(QLabel):
    def __init__(self, note: "StickyNote") -> None:
        super().__init__("⠿", note)
        self.note = note
        self.setObjectName("dragHandle")
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setFixedWidth(18)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event) -> None:
        self.note.begin_drag(event)

    def mouseMoveEvent(self, event) -> None:
        self.note.continue_drag(event)

    def mouseReleaseEvent(self, event) -> None:
        self.note.end_drag(event)


class StickyNote(QWidget):
    def __init__(self, app: "ChinchetaApp", note: dict) -> None:
        # Plasma Wayland needs a KWin skip-taskbar rule (installed separately)
        # for persistent editable desktop surfaces.
        super().__init__(None, note_window_flags())
        self.app, self.note, self.drag_offset = app, note, None
        self.setObjectName("stickyNote")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        if not app.is_wayland:
            self.setAttribute(Qt.WidgetAttribute.WA_X11NetWmWindowTypeUtility, True)
        self.update_window_title(bool(note["pinned"]))
        self.setMinimumSize(180, 140)
        self.resize(note["width"], note["height"])
        self.move(note["x"], note["y"])
        self._build()
        self._apply_note()

    def _build(self) -> None:
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 8, 10, 10); layout.setSpacing(6)
        header = QHBoxLayout(); header.setSpacing(4)
        self.drag_handle = DragHandle(self)
        self.title = QLineEdit(); self.title.setObjectName("noteTitle"); self.title.setPlaceholderText(self.app.t("title")); self.title.setFrame(False)
        self.title.textChanged.connect(self.save)
        self.colour_button = QPushButton("●"); self.colour_button.clicked.connect(self.choose_colour)
        self.pin_button = QPushButton("📌"); self.pin_button.setCheckable(True); self.pin_button.toggled.connect(self.set_pinned)
        self.delete_button = QPushButton("×"); self.delete_button.clicked.connect(self.delete)
        header.addWidget(self.drag_handle); header.addWidget(self.title); header.addWidget(self.colour_button); header.addWidget(self.pin_button); header.addWidget(self.delete_button)
        self.hover_hint = QLabel(self)
        self.hover_hint.setObjectName("hoverHint")
        self.hover_hint.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.hover_hint.hide()
        self._set_hover_hint(self.drag_handle, self.app.t("drag"))
        self._set_hover_hint(self.colour_button, self.app.t("colour"))
        self._set_hover_hint(self.pin_button, self.app.t("pin"))
        self._set_hover_hint(self.delete_button, self.app.t("delete"))
        self.body = QTextEdit(); self.body.setPlaceholderText(self.app.t("body")); self.body.setFrameStyle(0); self.body.textChanged.connect(self.save)
        layout.addLayout(header); layout.addWidget(self.body)

    def _set_hover_hint(self, widget: QWidget, text: str) -> None:
        widget.setProperty("hover_hint", text)
        widget.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if watched.property("hover_hint"):
            if event.type() == QEvent.Type.Enter:
                self.show_hover_hint(watched, watched.property("hover_hint"))
            elif event.type() in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress, QEvent.Type.Hide):
                self.hover_hint.hide()
        return super().eventFilter(watched, event)

    def show_hover_hint(self, widget: QWidget, text: str) -> None:
        self.hover_hint.setText(text)
        self.hover_hint.adjustSize()
        position = widget.mapTo(self, QPoint(0, widget.height() + 4))
        x = max(6, min(position.x(), self.width() - self.hover_hint.width() - 6))
        y = max(6, min(position.y(), self.height() - self.hover_hint.height() - 6))
        self.hover_hint.move(x, y)
        self.hover_hint.raise_()
        self.hover_hint.show()

    def _apply_note(self) -> None:
        self.title.setText(self.note["title"]); self.body.setPlainText(self.note["body"])
        self.pin_button.setChecked(bool(self.note["pinned"])); self.set_colour(self.note["colour"])
        self.show()
        QTimer.singleShot(0, self.repaint_note)
        QTimer.singleShot(100, self.repaint_note)

    def update_window_title(self, pinned: bool) -> None:
        state = "pinned" if pinned else "note"
        self.setWindowTitle(f"{APP_NAME} {state} {self.note['id']}")

    def update_pin_button(self, pinned: bool) -> None:
        self.pin_button.setText("📍" if pinned else "📌")
        self.pin_button.setProperty("hover_hint", self.app.t("unpin" if pinned else "pin"))

    def set_colour(self, colour: str) -> None:
        self.note["colour"] = colour
        note_colour = QColor(colour)
        text_colour = QColor("#2b2924")
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, note_colour)
        palette.setColor(QPalette.ColorRole.WindowText, text_colour)
        palette.setColor(QPalette.ColorRole.Base, note_colour)
        palette.setColor(QPalette.ColorRole.Text, text_colour)
        self.setPalette(palette)
        self.title.setPalette(palette)
        self.body.setPalette(palette)
        self.body.viewport().setPalette(palette)
        self.setAutoFillBackground(True)
        self.title.setAutoFillBackground(True)
        self.body.setAutoFillBackground(True)
        self.body.viewport().setAutoFillBackground(True)
        self.setStyleSheet(
            f"QWidget#stickyNote {{ background-color: {colour}; color: #2b2924; border: 1px solid #c6bc73; }}"
            f"QLineEdit, QTextEdit, QTextEdit QWidget {{ background-color: {colour}; color: #2b2924; }}"
            "QLineEdit#noteTitle { font-weight: 700; }"
            "QLineEdit, QTextEdit { border: none; }"
            "QLabel#dragHandle { background: transparent; color: #2b2924; }"
            "QPushButton { border: none; background: transparent; color: #2b2924; min-width: 22px; }"
            f"{HOVER_HINT_STYLE}"
        )
        self.repaint_note()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.note["colour"]))
        painter.end()
        super().paintEvent(event)

    def repaint_note(self) -> None:
        self.repaint()
        self.title.repaint()
        self.body.repaint()
        self.body.viewport().repaint()

    def choose_colour(self) -> None:
        picker = ColourPicker(self.app, self.note["colour"], self)
        if picker.exec(): self.change_colour(picker.colour)

    def change_colour(self, colour: str) -> None:
        self.set_colour(colour); self.save()

    def set_pinned(self, checked: bool) -> None:
        self.note["pinned"] = int(checked)
        self.update_window_title(checked)
        self.update_pin_button(checked)
        if not self.app.is_wayland:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
            self.show()
        if checked:
            self.raise_()
            self.activateWindow()
        self.save()

    def save(self) -> None:
        if not hasattr(self, "body"): return
        self.app.store.update(self.note["id"], title=self.title.text(), body=self.body.toPlainText(), colour=self.note["colour"], pinned=int(self.pin_button.isChecked()))

    def delete(self) -> None:
        prompt = QDialog()
        prompt.setWindowModality(Qt.WindowModality.ApplicationModal)
        prompt.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        prompt.setAutoFillBackground(True)
        prompt.setStyleSheet(
            "QDialog { background-color: #f7f7f7; color: #202020; }"
            "QLabel { background-color: #f7f7f7; color: #202020; }"
            "QPushButton { background-color: #ffffff; color: #202020; border: 1px solid #999999; border-radius: 4px; padding: 6px 14px; min-width: 72px; }"
        )
        layout = QVBoxLayout(prompt)
        layout.addWidget(QLabel(self.app.t("confirm")))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes
            | QDialogButtonBox.StandardButton.No
        )
        buttons.button(QDialogButtonBox.StandardButton.Yes).setText(self.app.t("yes"))
        buttons.button(QDialogButtonBox.StandardButton.No).setText(self.app.t("no"))
        buttons.button(QDialogButtonBox.StandardButton.Yes).setIcon(action_icon("delete"))
        buttons.button(QDialogButtonBox.StandardButton.No).setIcon(action_icon("cancel"))
        buttons.accepted.connect(prompt.accept)
        buttons.rejected.connect(prompt.reject)
        layout.addWidget(buttons)
        if prompt.exec() == QDialog.DialogCode.Accepted:
            self.close()
            self.app.store.delete(self.note["id"])
            self.app.kwin_rules.remove_position_rule(self.note["id"])
            self.app.notes.pop(self.note["id"], None)

    def begin_drag(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton: return
        handle = self.windowHandle()
        if handle and handle.startSystemMove():
            self.drag_offset = None
        else:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def continue_drag(self, event) -> None:
        if self.drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def end_drag(self, event=None) -> None:
        self.drag_offset = None
        self.save_geometry()

    def moveEvent(self, event) -> None:
        QTimer.singleShot(150, self.save_geometry)
        super().moveEvent(event)

    def resizeEvent(self, event) -> None:
        QTimer.singleShot(150, self.save_geometry); super().resizeEvent(event)

    def save_geometry(self) -> None:
        if self.isVisible():
            values = {"width": self.width(), "height": self.height()}
            if not self.app.is_wayland:
                values.update(x=self.x(), y=self.y())
            self.app.store.update(self.note["id"], **values)


class ChinchetaApp:
    def __init__(self) -> None:
        self.qt = QApplication(sys.argv); self.qt.setApplicationName(APP_NAME); self.qt.setDesktopFileName("chincheta"); self.qt.setQuitOnLastWindowClosed(False)
        self.qt.setWindowIcon(QIcon(str(APP_ICON)))
        self.is_wayland = self.qt.platformName() == "wayland"
        self.store = NoteStore(DATA_DIR / "notes.db"); self.notes: dict[int, StickyNote] = {}
        self.kwin_rules = KWinRules()
        self.settings = QSettings("Chincheta", "Chincheta")
        self.language = self.settings.value("language", "es")
        if self.is_wayland:
            self.kwin_rules.load_keep_above_script(KWIN_SCRIPT)
            self.kwin_rules.ensure_position_rules(self.store.all_visible())
        self.create_tray(); self.restore_notes()

    def t(self, key: str) -> str: return TEXT.get(self.language, TEXT["es"])[key]

    def create_tray(self) -> None:
        self.tray = QSystemTrayIcon(QIcon(str(APP_ICON)), self.qt); self.menu = QMenu()
        self.new_action = self.menu.addAction(self.t("new")); self.new_action.triggered.connect(self.new_note)
        self.show_action = self.menu.addAction(self.t("show")); self.show_action.triggered.connect(self.show_all)
        self.hide_action = self.menu.addAction(self.t("hide")); self.hide_action.triggered.connect(self.hide_all)
        self.menu.addSeparator(); self.preferences_action = self.menu.addAction(self.t("prefs")); self.preferences_action.triggered.connect(self.preferences)
        self.menu.addSeparator(); self.quit_action = self.menu.addAction(self.t("quit")); self.quit_action.triggered.connect(self.quit)
        self.tray.setContextMenu(self.menu); self.tray.activated.connect(lambda reason: self.new_note() if reason == QSystemTrayIcon.ActivationReason.Trigger else None); self.tray.show()

    def restore_notes(self) -> None:
        for note in self.store.all_visible(): self.open_note(note)

    def open_note(self, note: dict) -> None: self.notes[note["id"]] = StickyNote(self, note)
    def new_note(self) -> None:
        note = self.store.create()
        screen = self.qt.screenAt(QCursor.pos()) or self.qt.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            note["x"] = area.x() + (area.width() - note["width"]) // 2
            note["y"] = area.y() + (area.height() - note["height"]) // 2
            self.store.update(note["id"], x=note["x"], y=note["y"])
        if self.is_wayland:
            self.kwin_rules.ensure_position_rules([note])
        self.open_note(note)
    def show_all(self) -> None:
        for note in self.notes.values():
            note.show()
            note.raise_()
        if self.notes:
            next(reversed(self.notes.values())).activateWindow()
    def hide_all(self) -> None:
        for note in self.notes.values(): note.hide()

    def set_autostart(self, enabled: bool) -> None:
        if enabled:
            AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
            if DESKTOP_FILE.exists():
                shutil.copy2(DESKTOP_FILE, AUTOSTART_FILE)
            else:
                AUTOSTART_FILE.write_text(
                    "[Desktop Entry]\n"
                    "Version=1.0\n"
                    "Type=Application\n"
                    "Name=Chincheta\n"
                    f"Exec={sys.executable} {Path(__file__).resolve()}\n"
                    f"Icon={Path(__file__).with_name('icon.svg').resolve()}\n"
                    "Terminal=false\n"
                    "StartupNotify=false\n",
                    encoding="utf-8",
                )
        else:
            AUTOSTART_FILE.unlink(missing_ok=True)

    def preferences(self) -> None:
        dialog = QDialog()
        dialog.setWindowTitle(self.t("settings"))
        dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dialog.setStyleSheet(
            "QDialog { background-color: #f7f7f7; color: #202020; }"
            "QLabel { color: #202020; background: transparent; }"
            "QComboBox { background: #ffffff; color: #202020; border: 1px solid #999999; padding: 4px; }"
            "QComboBox QAbstractItemView { background-color: #ffffff; color: #202020; selection-background-color: #dbeafe; selection-color: #202020; border: 1px solid #999999; outline: none; }"
            "QCheckBox { color: #202020; background: transparent; spacing: 6px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; background-color: #ffffff; border: 1px solid #777777; border-radius: 3px; }"
            "QCheckBox::indicator:checked { background-color: #238636; border-color: #1b6e2a; }"
            "QPushButton { background: #ffffff; color: #202020; border: 1px solid #999999; border-radius: 4px; padding: 6px 14px; }"
        )
        form = QFormLayout(dialog)
        language = QComboBox()
        language.addItem("Español", "es"); language.addItem("English", "en"); language.addItem("Deutsch", "de")
        language.setCurrentIndex(language.findData(self.language)); form.addRow(self.t("language"), language)
        autostart = QCheckBox(self.t("autostart"))
        autostart.setChecked(AUTOSTART_FILE.exists())
        form.addRow(autostart)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel); form.addRow(buttons)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.t("save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.t("cancel"))
        buttons.button(QDialogButtonBox.StandardButton.Save).setIcon(action_icon("accept"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setIcon(action_icon("cancel"))
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        if dialog.exec():
            self.set_autostart(autostart.isChecked())
            selected = language.currentData()
            if selected in TEXT:
                self.language = selected
                self.settings.setValue("language", selected)
                self.new_action.setText(self.t("new")); self.show_action.setText(self.t("show")); self.hide_action.setText(self.t("hide"))
                self.preferences_action.setText(self.t("prefs")); self.quit_action.setText(self.t("quit"))

    def quit(self) -> None:
        for note in self.notes.values(): note.save_geometry(); note.save()
        VENV_DELETE_MARKER.write_text("", encoding="utf-8")
        self.store.close(); self.qt.quit()

    def run(self) -> int: return self.qt.exec()


if __name__ == "__main__":
    raise SystemExit(ChinchetaApp().run())
