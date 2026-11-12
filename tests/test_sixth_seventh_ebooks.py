"""Check free e-books #6 and #7 and unchanged original PDFs."""
import hashlib,json,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOOKS=[{"slug":"ask-chatgpt-for-a-tool-not-an-answer-2026","name":"Digital-Pathshala-ChatGPT-Intelligent-UI.pdf","pages":8,"bytes":343252,"sha":"d4a3e0486293b8d799c54a1535a5902d69524fc94a9ccdad34671453a937ff4a","previews":[2,3,6]},{"slug":"claude-sheets-whiteboards-the-first-guide-2026","name":"Digital-Pathshala-Claude-Sheets-Whiteboards.pdf","pages":11,"bytes":399857,"sha":"8f3efd8e74d6a99d827c49f229120eaa1a4b825e912ddcd25ad4cdfe40193b75","previews":[2,4,7]}]
class SixthSeventhEbookTests(unittest.TestCase):
    def test_existing_sixth_and_seventh_among_eight_ebooks(self):
        items=json.loads((ROOT/'config/independent.json').read_text())['resources']
        self.assertEqual(len(items),8)
        self.assertEqual(len({x['slug'] for x in items}),8)
        for v in BOOKS:
            entry=next(x for x in items if x['slug']==v['slug'])
            self.assertEqual(entry['file_name'],v['name'])
            self.assertEqual(entry['sha256'],v['sha'])
            self.assertEqual(entry['preview_pages'],v['previews'])
            self.assertTrue(entry['approved'])
    def test_original_pdf_bytes(self):
        for v in BOOKS:
            with self.subTest(slug=v['slug']):
                folder=ROOT/'independent_source'/'ebooks'/v['slug']
                self.assertTrue((folder/'README.md').exists())
                self.assertFalse((folder/(v['name']+'.pdf')).exists())
                pdf=folder/v['name']
                if not pdf.exists():continue
                data=pdf.read_bytes()
                self.assertTrue(data.startswith(b'%PDF-'))
                self.assertEqual(len(data),v['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),v['sha'])
    def test_prepared_cover_and_permalink(self):
        for v in BOOKS:
            ET.parse(ROOT/'site'/'covers'/(v['slug']+'.svg'))
            p=(ROOT/'site'/'ebooks'/v['slug']/'index.html').read_text()
            self.assertIn('Download is being activated.',p)
            self.assertIn('/ebooks/'+v['slug']+'/',p)
if __name__=='__main__':unittest.main()
