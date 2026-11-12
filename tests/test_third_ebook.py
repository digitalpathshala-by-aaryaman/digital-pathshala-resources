"""Protect third free e-book PDF and permalink."""
import json,hashlib,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SLUG="let-ai-do-your-browser-work-while-you-watch-2026"
NAME="Digital-Pathshala-AI-in-Your-Browser-2026.pdf"
SHA="85d56d8578f7e350b2b364c888bbcdec5018d1f5a0b54994bee0132c94d484bc"
class ThirdEbookTests(unittest.TestCase):
    def test_unique_catalogue_entry(self):
        rows=json.loads((ROOT/"config/independent.json").read_text())["resources"]
        matches=[x for x in rows if x["kind"]=="ebook" and x["slug"]==SLUG]
        self.assertEqual(len(matches),1)
        self.assertEqual(matches[0]["sha256"],SHA)
        self.assertEqual(matches[0]["file_name"],NAME)
        self.assertEqual(matches[0]["preview_pages"],[2,11,16])
        self.assertTrue(matches[0]["approved"])
    def test_original_upload(self):
        folder=ROOT/"independent_source"/"ebooks"/SLUG
        p=folder/NAME
        self.assertFalse((folder/(NAME+".pdf")).exists(),"Remove duplicate .pdf extension")
        if not p.exists(): self.skipTest("Third original PDF awaits upload")
        data=p.read_bytes()
        self.assertTrue(data.startswith(b"%PDF-"))
        self.assertEqual(len(data),648870)
        self.assertEqual(hashlib.sha256(data).hexdigest(),SHA)
    def test_safe_reserved_page(self):
        ET.parse(ROOT/"site"/"covers"/(SLUG+".svg"))
        text=(ROOT/"site"/"ebooks"/SLUG/"index.html").read_text()
        self.assertIn("Download is being activated.",text)
        self.assertIn("/ebooks/"+SLUG+"/",text)
if __name__=="__main__":unittest.main()
