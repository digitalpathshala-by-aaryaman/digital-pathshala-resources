"""Release registration safety tests for Digital Pathshala's first real e-book."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "10-hidden-ai-mistakes-nobody-warns-you-about-2026"
NAME = "Digital-Pathshala-10-Hidden-AI-Mistakes-2026.pdf"
SHA = "33f22832b61efde560ccedcf1ade92fc927145939b2d0905f98802144ed505d9"
BASE = "https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/"


class FirstEbookTests(unittest.TestCase):
    def test_registered_title_permanent_slug_and_release(self):
        catalogue = json.loads((ROOT/"config/independent.json").read_text())
        items = [x for x in catalogue["resources"] if x["kind"]=="ebook" and x["slug"]==SLUG]
        self.assertEqual(len(items),1)
        item=items[0]
        self.assertEqual(item["title"], "10 Hidden AI Mistakes Nobody Warns You About (2026)")
        self.assertEqual(item["file_name"], NAME)
        self.assertEqual(item["sha256"], SHA)
        self.assertEqual(item["preview_pages"], [2,13])
        self.assertTrue(item["approved"])
        self.assertEqual(item["cover_url"], BASE+"covers/"+SLUG+".svg")

    def test_original_pdf_exact_when_uploaded(self):
        path=ROOT/"independent_source"/"ebooks"/SLUG/NAME
        if not path.exists():
            self.skipTest("Original PDF awaits source upload: site correctly withholds download")
        self.assertEqual(path.stat().st_size,815170)
        self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),SHA)

    def test_cover_and_prelaunch_page_valid(self):
        ET.parse(ROOT/"site"/"covers"/(SLUG+".svg"))
        page=(ROOT/"site"/"ebooks"/SLUG/"index.html").read_text()
        self.assertIn(BASE+"ebooks/"+SLUG+"/",page)
        self.assertIn("10 Hidden AI Mistakes",page)
        self.assertIn("Download is being activated.",page)
        self.assertNotIn('href="'+BASE+'downloads/',page)


if __name__=="__main__":
    unittest.main()
