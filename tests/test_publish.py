import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dp_builder", ROOT / "scripts/build_site.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class PublishSafetyTests(unittest.TestCase):
    def test_90_entries_all_initially_hold(self):
        plan = json.loads((ROOT / "config/videos.json").read_text())["videos"]
        self.assertEqual(len(plan), 90)
        self.assertEqual(len({v["id"] for v in plan}), 90)
        self.assertTrue(all(v["approved"] is False for v in plan))

    def test_release_date(self):
        ist = ZoneInfo("Asia/Kolkata")
        self.assertFalse(builder.due("2026-11-16 19:00", dt.datetime(2026,11,11,19,tzinfo=ist)))
        self.assertTrue(builder.due("2026-11-16 19:00", dt.datetime(2026,11,16,19,tzinfo=ist)))
        self.assertFalse(builder.due("invalid", dt.datetime.now(ist)))

    def test_empty_public_catalogue_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "site"
            result = builder.build(output=output, now=dt.datetime(2026,11,11,tzinfo=ZoneInfo("Asia/Kolkata")))
            self.assertEqual(result, [])
            self.assertEqual(json.loads((output / "videos.json").read_text())["videos"], [])
            self.assertFalse(list((output / "resources").glob("*.zip")))

if __name__ == "__main__":
    unittest.main()
