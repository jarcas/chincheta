"""Persistent local storage for Chincheta."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_COLOUR = "#FFF59D"


class NoteStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                colour TEXT NOT NULL DEFAULT '#FFF59D',
                x INTEGER NOT NULL DEFAULT 0,
                y INTEGER NOT NULL DEFAULT 0,
                width INTEGER NOT NULL DEFAULT 280,
                height INTEGER NOT NULL DEFAULT 240,
                pinned INTEGER NOT NULL DEFAULT 0,
                visible INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()

    def create(self) -> dict:
        # Specify the origin explicitly so existing databases created with the
        # former 120,120 defaults also place new notes at the top-left.
        cursor = self.connection.execute("INSERT INTO notes (x, y) VALUES (0, 0)")
        self.connection.commit()
        return self.get(cursor.lastrowid)

    def get(self, note_id: int) -> dict:
        row = self.connection.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            raise KeyError(note_id)
        return dict(row)

    def all_visible(self) -> list[dict]:
        return [dict(row) for row in self.connection.execute("SELECT * FROM notes WHERE visible = 1 ORDER BY id")]

    def update(self, note_id: int, **values: object) -> None:
        allowed = {"title", "body", "colour", "x", "y", "width", "height", "pinned", "visible"}
        values = {key: value for key, value in values.items() if key in allowed}
        if not values:
            return
        fields = ", ".join(f"{key} = ?" for key in values)
        self.connection.execute(
            f"UPDATE notes SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (*values.values(), note_id),
        )
        self.connection.commit()

    def set_all_visible(self, visible: bool) -> None:
        self.connection.execute("UPDATE notes SET visible = ?", (int(visible),))
        self.connection.commit()

    def delete(self, note_id: int) -> None:
        self.connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
