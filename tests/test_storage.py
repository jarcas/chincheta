import tempfile
import unittest
from pathlib import Path

from storage import NoteStore


class NoteStoreTest(unittest.TestCase):
    def test_note_persists(self):
        with tempfile.TemporaryDirectory() as folder:
            store = NoteStore(Path(folder) / "notes.db")
            note = store.create()
            self.assertEqual((note["x"], note["y"]), (0, 0))
            store.update(note["id"], title="Comprar", body="Pan", x=42, pinned=1)
            saved = store.get(note["id"])
            self.assertEqual((saved["title"], saved["body"], saved["x"], saved["pinned"]), ("Comprar", "Pan", 42, 1))
            store.delete(note["id"])
            self.assertEqual(store.all_visible(), [])


if __name__ == "__main__":
    unittest.main()
