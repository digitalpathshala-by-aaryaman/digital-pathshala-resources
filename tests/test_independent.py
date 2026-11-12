import datetime as dt
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('independent_builder',ROOT/'scripts/build_independent.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
BASE='https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/'

class IndependentTests(unittest.TestCase):
    def test_empty_registry_is_safe(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'config').mkdir()
            (root/'config/independent.json').write_text('{"schema_version":1,"resources":[]}')
            out=root/'out';out.mkdir()
            self.assertEqual(builder.publish(root,out,dt.datetime(2026,11,12,tzinfo=ZoneInfo('Asia/Kolkata')),BASE),[])
            self.assertEqual(json.loads((out/'independent.json').read_text())['resources'],[])

    def test_title_page_appears_only_after_approved_release(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'config').mkdir();(root/'site').mkdir()
            (root/'site/index.html').write_text('<html><head><title>Digital Pathshala · Free Learning Resources</title></head></html>')
            filename='guide.pdf';folder=root/'independent_source/ebooks/my-ai-guide';folder.mkdir(parents=True)
            file=folder/filename;file.write_bytes(b'%PDF-1.4 test sample')
            item={'kind':'ebook','slug':'my-ai-guide','title':'My AI Guide','file_name':filename,
                  'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                  'approved':True,'published_at_ist':'2026-11-16 12:00'}
            (root/'config/independent.json').write_text(json.dumps({'schema_version':1,'resources':[item]}))
            out=root/'out';out.mkdir()
            self.assertEqual(builder.publish(root,out,dt.datetime(2026,11,15,tzinfo=ZoneInfo('Asia/Kolkata')),BASE),[])
            self.assertFalse((out/'ebooks/my-ai-guide/index.html').exists())
            found=builder.publish(root,out,dt.datetime(2026,11,17,tzinfo=ZoneInfo('Asia/Kolkata')),BASE)
            self.assertEqual(found[0]['page_url'],BASE+'ebooks/my-ai-guide/')
            self.assertTrue((out/'ebooks/my-ai-guide/index.html').exists())
            self.assertEqual((out/'downloads/ebooks/my-ai-guide/guide.pdf').read_bytes(),file.read_bytes())
            item['sha256']='0'*64
            (root/'config/independent.json').write_text(json.dumps({'schema_version':1,'resources':[item]}))
            with self.assertRaises(ValueError):builder.publish(root,out,dt.datetime(2026,11,17,tzinfo=ZoneInfo('Asia/Kolkata')),BASE)

    def test_slug_and_formats(self):
        self.assertEqual(builder.slugify('ChatGPT & Excel Guide!'),'chatgpt-excel-guide')
        self.assertNotIn('.html',builder.EXTENSIONS)

if __name__=='__main__':unittest.main()
