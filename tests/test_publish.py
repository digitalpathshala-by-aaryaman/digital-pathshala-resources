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
        self.assertEqual(sum(v["approved"] is True for v in plan), 50)
        self.assertEqual(sum(v["approved"] is False for v in plan), 40)

    def test_50_shorts_daily_and_40_long_held(self):
        plan = json.loads((ROOT / "config/videos.json").read_text())["videos"]
        shorts = sorted((v for v in plan if v["type"] == "short"), key=lambda v: int(v["id"].split("s")[-1]))
        self.assertEqual(len(shorts), 50)
        start = dt.datetime(2026, 11, 16, 0, 0)
        for i, v in enumerate(shorts):
            self.assertEqual(v["id"], "short-s%02d" % (i + 1))
            self.assertEqual(v["release_at_ist"], (start + dt.timedelta(days=i)).strftime("%Y-%m-%d %H:%M"))
            self.assertTrue(v["approved"])
        longs = [v for v in plan if v["type"] == "long"]
        self.assertEqual(len(longs), 40)
        self.assertTrue(all(v["release_at_ist"] == "" and v["approved"] is False for v in longs))

    def test_shorts_without_youtube_ids_remain_unpublished(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "site"
            result = builder.build(output=out, now=dt.datetime(2027, 1, 5, tzinfo=ZoneInfo("Asia/Kolkata")), public_ids=set())
            self.assertEqual(result, [])
            self.assertFalse(list((out / "resources").glob("*.zip")))

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
