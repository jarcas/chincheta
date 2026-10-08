import configparser
import tempfile
import unittest
from pathlib import Path

from kwin_rules import KWinRules


class TestKWinRules(KWinRules):
    def reload(self) -> None:
        pass


class KWinRulesTest(unittest.TestCase):
    def test_adds_and_removes_note_rule_without_losing_existing_rules(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "kwinrulesrc"
            path.write_text(
                "[1]\nDescription=Existing\nwmclass=other\n\n"
                "[General]\ncount=1\nrules=1\n",
                encoding="utf-8",
            )
            rules = TestKWinRules(path)
            note = {"id": 7, "x": 120, "y": 130}

            self.assertTrue(rules.ensure_position_rules([note]))
            self.assertFalse(rules.ensure_position_rules([note]))

            parser = configparser.RawConfigParser()
            parser.optionxform = str
            parser.read(path, encoding="utf-8")
            self.assertEqual(parser["1"]["Description"], "Existing")
            self.assertEqual(parser["2"]["position"], "120,130")
            self.assertEqual(parser["2"]["positionrule"], "4")
            self.assertEqual(parser["General"]["rules"], "1,2")

            self.assertTrue(rules.remove_position_rule(7))
            parser = configparser.RawConfigParser()
            parser.optionxform = str
            parser.read(path, encoding="utf-8")
            self.assertFalse(parser.has_section("2"))
            self.assertEqual(parser["General"]["rules"], "1")


if __name__ == "__main__":
    unittest.main()
