"""Verify Digital Pathshala free e-books #4 and #5 without releasing unverified PDFs."""
import hashlib,json,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOOKS=[{"slug":"copy-text-from-anything-on-your-screen-2026","name":"Digital-Pathshala-Copy-Text-from-Anything.pdf","sha":"8963b4a77eee10fba5c4bd236f2c8ef7fc9815d88d8a28c9f9a64ef8267e5bc9","bytes":374421,"preview":[2,3,7]},{"slug":"pdf-tables-into-excel-the-honest-verified-guide-2026","name":"Digital-Pathshala-PDF-to-Excel-Verified-Guide.pdf","sha":"50760db7dca74e42e2706f9b729608e8df05b66815b14b911de5643f166b5a6c","bytes":409511,"preview":[2,4,6]}]
class NewEbooks(unittest.TestCase):
    def test_eight_unique_resources_including_previous_books(self):
        entries=json.loads((ROOT/"config/independent.json").read_text())["resources"]
        self.assertEqual(len(entries),8)
        self.assertEqual(len({x['slug'] for x in entries}),8)
        for b in BOOKS:
            rec=next(x for x in entries if x['slug']==b['slug'])
            self.assertEqual(rec['file_name'],b['name'])
            self.assertEqual(rec['sha256'],b['sha'])
            self.assertEqual(rec['preview_pages'],b['preview'])
            self.assertTrue(rec['approved'])
    def test_unchanged_pdf_when_uploaded(self):
        for b in BOOKS:
            with self.subTest(b=b['slug']):
                folder=ROOT/'independent_source'/'ebooks'/b['slug']
                self.assertTrue((folder/'README.md').exists())
                self.assertFalse((folder/(b['name']+'.pdf')).exists())
                file=folder/b['name']
                if not file.exists():continue
                data=file.read_bytes()
                self.assertTrue(data.startswith(b'%PDF-'))
                self.assertEqual(len(data),b['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),b['sha'])
    def test_reserved_pages_and_fallback_covers(self):
        for b in BOOKS:
            ET.parse(ROOT/'site'/'covers'/(b['slug']+'.svg'))
            p=(ROOT/'site'/'ebooks'/b['slug']/'index.html').read_text()
            self.assertIn('Download is being activated.',p)
            self.assertIn('/ebooks/'+b['slug']+'/',p)
if __name__=='__main__':unittest.main()
