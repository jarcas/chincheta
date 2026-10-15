import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from chincheta import StickyNote
from storage import NoteStore


class ResizeHandleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_resize_handles_follow_note_edges(self):
        with tempfile.TemporaryDirectory() as folder:
            store = NoteStore(Path(folder) / "notes.db")
            app = type("NoteApp", (), {"is_wayland": False, "store": store, "t": lambda self, key: key})()
            note = StickyNote(app, store.create())
            note.resize(360, 260)
            self.qt.processEvents()

            handles = dict((position, handle) for handle, position in note.resize_handles)
            self.assertEqual(len(handles), 8)
            self.assertEqual(handles["top_left"].geometry().topLeft(), note.rect().topLeft())
            self.assertEqual(handles["bottom_right"].geometry().bottomRight(), note.rect().bottomRight())
            note.close()
            store.close()


if __name__ == "__main__":
    unittest.main()
