"""Already-released local ZIP source is safe ONLY after approved YouTube publication."""
import datetime as dt
import hashlib
import importlib.util
import json
import unittest
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dp_release',ROOT/'scripts/build_site.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
IST=ZoneInfo('Asia/Kolkata')
class ReleasedShortSourceTests(unittest.TestCase):
    def test_pack_is_original_sha_and_contains_expected_files(self):
        v=next(x for x in json.loads((ROOT/'config/videos.json').read_text())['videos'] if x['id']=='short-s01')
        pack=ROOT/'released_source'/'short-s01.zip'
        self.assertTrue(pack.is_file())
        self.assertEqual(hashlib.sha256(pack.read_bytes()).hexdigest(),v['sha256'])
        import zipfile
        with zipfile.ZipFile(pack) as z:
            self.assertEqual(sorted(z.namelist()),sorted(['20-Everyday-ChatGPT-Tasks.pdf','Sample-Sales-Data.xlsx']))
    def test_first_pack_is_withheld_before_schedule(self):
        with tempfile.TemporaryDirectory() as temp:
            result=b.build(output=Path(temp)/'site',now=dt.datetime(2026,11,16,10,59,tzinfo=IST))
            self.assertFalse(result)
    def test_first_pack_published_only_on_verified_channel(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'site'
            releases=b.build(output=out,now=dt.datetime(2026,11,16,12,0,tzinfo=IST))
            self.assertEqual([x['id'] for x in releases],['short-s01'])
            self.assertEqual(releases[0]['youtube_url'],'https://www.youtube.com/watch?v=lvq3r6yHAxQ')
            self.assertEqual(hashlib.sha256((out/'resources/short-s01.zip').read_bytes()).hexdigest(),'c509323fb770fe316b48403928445c6317ba5f853c161855c662dff4053a1e3c')
    def test_first_pack_not_published_without_verified_id(self):
        with tempfile.TemporaryDirectory() as temp:
            result=b.build(output=Path(temp)/'site',now=dt.datetime(2026,11,16,12,tzinfo=IST),public_ids=set())
            self.assertEqual(result,[])
if __name__=='__main__':unittest.main()
