"""Homepage discovery layout and counts: protect published video URL contracts."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/"site/assets/site.js").read_text()
HTML=(ROOT/"site/index.html").read_text()
CSS=(ROOT/"site/assets/site.css").read_text()
class HomeLayoutTests(unittest.TestCase):
    def test_ebooks_first_and_shared_search_above_both(self):
        home=JS.split("function home(){",1)[1].split("function cards(){",1)[0]
        self.assertLess(home.index("id=\"searchVideos\""),home.index('id=\"independent\"'))
        self.assertLess(home.index('id=\"independent\"'),home.index('id=\"resources\"'))
        self.assertEqual(home.count('id=\"searchVideos\"'),1)
        self.assertIn('cards();independentCards()',home)
    def test_hero_counts_total_published_resources(self):
        stat=JS.split("function stat(){",1)[1].split("function card(",1)[0]
        self.assertIn("published.length+independent.length",stat)
        self.assertIn("Total free resources",JS)
        self.assertNotIn("Free video resource packs",JS)
        self.assertIn("Video resources coming soon",JS)
        self.assertIn("independentHeaderCount",stat)
    def test_preserve_video_links_and_safe_publication(self):
        self.assertIn('href="?v=',JS)
        self.assertIn("validRelease(v)",JS)
        self.assertIn("publishedOnly(videoData.videos)",JS)
        self.assertIn("visibleIndependent(resourceData.resources)",JS)
    def test_search_styling_and_navigation(self):
        self.assertIn(".library-search-wrap",CSS)
        self.assertLess(HTML.index('href="?#independent"'),HTML.index('href="?#resources"'))
if __name__=="__main__":unittest.main()
