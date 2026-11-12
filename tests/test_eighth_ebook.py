"""E-book 8: original uploaded file must be identical and page must be stable."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SLUG="chatgpt-images-2-6-gifs-and-the-same-character-every-time-2026"
NAME="Digital-Pathshala-ChatGPT-Images-2.6-GIFs-References.pdf"
SHA="d6b9a7f21246ee1eef1a051dbddf311a7d120fb8f4b194a20d4b6fc1f3ddab86"
SIZE=396841
class EighthEbookTests(unittest.TestCase):
    def test_unique_registered_eighth_book(self):
        records=json.loads((ROOT/"config/independent.json").read_text())["resources"]
        self.assertEqual(len(records),8)
        self.assertEqual(len({r["slug"] for r in records}),8)
        entries=[r for r in records if r["kind"]=="ebook" and r["slug"]==SLUG]
        self.assertEqual(len(entries),1)
        item=entries[0]
        self.assertEqual(item["title"],"ChatGPT Images 2.6 — GIFs and the Same Character, Every Time (2026)")
        self.assertEqual(item["file_name"],NAME)
        self.assertEqual(item["sha256"],SHA)
        self.assertEqual(item["preview_pages"],[3,6,9])
        self.assertTrue(item["approved"])
    def test_unchanged_pdf_when_uploaded(self):
        folder=ROOT/"independent_source"/"ebooks"/SLUG
        self.assertTrue((folder/"README.md").exists())
        self.assertFalse((folder/(NAME+".pdf")).exists(),"Remove extra .pdf suffix")
        pdf=folder/NAME
        if not pdf.exists():
            self.skipTest("Original 11-page PDF awaiting upload; resource withheld")
        content=pdf.read_bytes()
        self.assertTrue(content.startswith(b"%PDF-"))
        self.assertEqual(len(content),SIZE)
        self.assertEqual(hashlib.sha256(content).hexdigest(),SHA)
    def test_safe_pending_permalink_and_svg(self):
        ET.parse(ROOT/"site"/"covers"/(SLUG+".svg"))
        page=(ROOT/"site"/"ebooks"/SLUG/"index.html").read_text()
        self.assertIn("Download is being activated.",page)
        self.assertIn("/ebooks/"+SLUG+"/",page)
        self.assertNotIn("href=\"https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/downloads/",page)
if __name__=="__main__": unittest.main()
