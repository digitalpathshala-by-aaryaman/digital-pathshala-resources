import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dpdiscovery', ROOT/'scripts/discover_shorts.py')
disc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(disc)
IST = ZoneInfo('Asia/Kolkata')
CID = 'UC' + 'Q'*22
VID = 'abc12345678'
FEED = f'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
 <yt:channelId>{CID}</yt:channelId>
 <entry><yt:videoId>{VID}</yt:videoId><title>Completely rewritten title!</title><published>2026-11-16T05:45:00+00:00</published></entry></feed>'''

class DiscoveryTests(unittest.TestCase):
    def test_validate_feed_identity(self):
        self.assertEqual(disc.parse_feed(FEED, CID)[0]['id'], VID)
        with self.assertRaises(ValueError):
            disc.parse_feed(FEED, 'UC' + 'Z'*22)

    def test_find_channel(self):
        self.assertEqual(disc.discover_channel_id('"externalId":"' + CID + '"'), CID)

    def test_accept_verified_short_on_exact_day_after_11(self):
        v = {'id':'short-s01','title':'Strong prompt tips','type':'short','approved':True,'release_at_ist':'2026-11-16 11:00'}
        feed = disc.parse_feed(FEED, CID)
        self.assertIsNone(disc.choose_candidate(v, feed, {VID}, set(), dt.datetime(2026,11,16,10,59,tzinfo=IST)))
        self.assertEqual(disc.choose_candidate(v, feed, {VID}, set(), dt.datetime(2026,11,16,11,46,tzinfo=IST))['id'], VID)
        self.assertIsNone(disc.choose_candidate(v, feed, set(), set(), dt.datetime(2026,11,16,12,tzinfo=IST)))

    def test_feed_discovery_keeps_existing_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'config').mkdir()
            (root/'config/site.json').write_text(json.dumps({'channel_url':'https://www.youtube.com/@DigitalPathshalabyAaryaman'}))
            (root/'config/videos.json').write_text(json.dumps({'videos':[{'id':'short-s01','title':'Strong prompt tips','type':'short','approved':True,'release_at_ist':'2026-11-16 11:00'}]}))
            def mock_get(url):
                if url.endswith('/shorts'):
                    return '"reelItemRenderer":{"videoId":"' + VID + '"}'
                if 'videos.xml' in url:
                    return FEED
                return '"externalId":"' + CID + '"'
            now = dt.datetime(2026,11,16,12,tzinfo=IST)
            self.assertEqual(disc.run(root, now, mock_get), ['short-s01'])
            self.assertEqual(disc.run(root, now, mock_get), [])
            data = json.loads((root/'config/discovered.json').read_text())
            self.assertEqual(data['shorts']['short-s01']['youtube_id'], VID)

    def test_no_unapproved_release(self):
        v = {'id':'short-s01','title':'Strong prompt tips','type':'short','approved':False,'release_at_ist':'2026-11-16 11:00'}
        self.assertIsNone(disc.choose_candidate(v, disc.parse_feed(FEED, CID), {VID}, set(), dt.datetime(2026,11,16,12,tzinfo=IST)))

if __name__ == '__main__':
    unittest.main()
