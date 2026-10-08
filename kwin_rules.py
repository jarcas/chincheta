"""KWin integration for Wayland window positions."""

from __future__ import annotations

import configparser
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


SCRIPT_NAME = "chincheta"


class KWinRules:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".config" / "kwinrulesrc"

    def ensure_position_rules(self, notes: list[dict]) -> bool:
        parser = self._read()
        changed = False
        rule_ids = self._rule_ids(parser)

        for note in notes:
            description = f"Chincheta: recordar posición de nota {note['id']}"
            if any(
                parser.get(section, "Description", fallback="") == description
                for section in parser.sections()
            ):
                continue
            numeric_ids = [int(item) for item in rule_ids if item.isdigit()]
            rule_id = str(max(numeric_ids, default=0) + 1)
            parser.add_section(rule_id)
            parser[rule_id].update(
                {
                    "Description": description,
                    "position": f"{note['x']},{note['y']}",
                    "positionrule": "4",
                    "title": rf"^Chincheta (note|pinned) {note['id']}$",
                    "titlematch": "3",
                    "wmclass": "chincheta",
                    "wmclassmatch": "1",
                }
            )
            rule_ids.append(rule_id)
            changed = True

        if changed:
            self._write(parser, rule_ids)
            self.reload()
        return changed

    def remove_position_rule(self, note_id: int) -> bool:
        parser = self._read()
        description = f"Chincheta: recordar posición de nota {note_id}"
        removed = [
            section
            for section in parser.sections()
            if parser.get(section, "Description", fallback="") == description
        ]
        if not removed:
            return False
        for section in removed:
            parser.remove_section(section)
        self._write(
            parser,
            [item for item in self._rule_ids(parser) if item not in removed],
        )
        self.reload()
        return True

    def reload(self) -> None:
        qdbus = shutil.which("qdbus")
        if qdbus:
            subprocess.run(
                [qdbus, "org.kde.KWin", "/KWin", "reconfigure"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def load_keep_above_script(self, script_path: Path) -> bool:
        qdbus = shutil.which("qdbus")
        if not qdbus or not script_path.exists():
            return False
        base = [qdbus, "org.kde.KWin", "/Scripting"]
        loaded = subprocess.run(
            base + ["org.kde.kwin.Scripting.isScriptLoaded", SCRIPT_NAME],
            check=False,
            capture_output=True,
            text=True,
        )
        if loaded.stdout.strip() == "true":
            subprocess.run(
                base + ["org.kde.kwin.Scripting.unloadScript", SCRIPT_NAME],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        result = subprocess.run(
            base
            + [
                "org.kde.kwin.Scripting.loadScript",
                str(script_path.resolve()),
                SCRIPT_NAME,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False
        subprocess.run(
            base + ["org.kde.kwin.Scripting.start"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True

    def _read(self) -> configparser.RawConfigParser:
        parser = configparser.RawConfigParser()
        parser.optionxform = str
        if self.path.exists():
            parser.read(self.path, encoding="utf-8")
        if not parser.has_section("General"):
            parser.add_section("General")
        return parser

    @staticmethod
    def _rule_ids(parser: configparser.RawConfigParser) -> list[str]:
        configured = parser.get("General", "rules", fallback="")
        rule_ids = [item for item in configured.split(",") if item]
        for section in parser.sections():
            if section not in ("$Version", "General") and section not in rule_ids:
                rule_ids.append(section)
        return rule_ids

    def _write(self, parser: configparser.RawConfigParser, rule_ids: list[str]) -> None:
        parser.set("General", "rules", ",".join(rule_ids))
        parser.set("General", "count", str(len(rule_ids)))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".kwinrulesrc.",
            text=True,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
                parser.write(temporary, space_around_delimiters=False)
            os.replace(temporary_name, self.path)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
