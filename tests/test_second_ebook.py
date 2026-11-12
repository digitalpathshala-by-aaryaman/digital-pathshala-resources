"""Protect original PDF and URL of Digital Pathshala's second independent e-book."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SLUG="the-hidden-switches-inside-chatgpt-gemini-claude-2026"
NAME="Digital-Pathshala-Hidden-AI-Settings-2026.pdf"
SHA="f6d65036d58ed61eb70f92ec272ba4fb054a90605085dd928595b3e4dd0deafe"
BASE="https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/"


class SecondEbookTests(unittest.TestCase):
    def test_registered_resource_is_unique_and_title_based(self):
        catalogue=json.loads((ROOT/"config/independent.json").read_text())
        matches=[r for r in catalogue["resources"] if r["kind"]=="ebook" and r["slug"]==SLUG]
        self.assertEqual(len(matches),1)
        entry=matches[0]
        self.assertEqual(entry["title"],"The Hidden Switches Inside ChatGPT, Gemini & Claude (2026)")
        self.assertEqual(entry["file_name"],NAME)
        self.assertEqual(entry["sha256"],SHA)
        self.assertEqual(entry["preview_pages"],[2,13])
        self.assertTrue(entry["approved"])

    def test_original_uploaded_pdf_is_identical(self):
        folder=ROOT/"independent_source"/"ebooks"/SLUG
        pdf=folder/NAME
        if not pdf.exists():
            self.assertFalse((folder/(NAME+".pdf")).exists(),"PDF was uploaded with an extra .pdf extension")
            self.skipTest("Original second PDF awaiting upload; builder must withhold download")
        blob=pdf.read_bytes()
        self.assertEqual(len(blob),499431)
        self.assertTrue(blob.startswith(b"%PDF-"))
        self.assertEqual(hashlib.sha256(blob).hexdigest(),SHA)

    def test_permanent_page_and_fallback_cover(self):
        ET.parse(ROOT/"site"/"covers"/(SLUG+".svg"))
        page=(ROOT/"site"/"ebooks"/SLUG/"index.html").read_text()
        self.assertIn(BASE+"ebooks/"+SLUG+"/",page)
        self.assertIn("The Hidden Switches Inside ChatGPT",page)
        self.assertIn("Download is being activated.",page)
        self.assertNotIn('href="'+BASE+"downloads/",page)

if __name__=="__main__":
    unittest.main()
