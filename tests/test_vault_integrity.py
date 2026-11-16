"""Secure vault content must be encrypted and checksum intact on every run."""
import hashlib
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CHUNKS=ROOT/'vault'/'chunks'
class EncryptedArchiveTests(unittest.TestCase):
    def test_all_ciphertext_parts_match_original_sealed_archive(self):
        manifest=json.loads((CHUNKS/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['encryption'],'openssl aes-256-cbc pbkdf2 sha256 200000 iterations')
        self.assertEqual(manifest['chunks'],44)
        expected_size=manifest['encrypted_file_bytes']
        chunk_size=manifest['chunk_bytes']
        sha=hashlib.sha256()
        total=0
        for i in range(1,manifest['chunks']+1):
            path=CHUNKS/('encpart-%03d.bin' % i)
            self.assertTrue(path.is_file(),f'Encrypted part {i} missing')
            data=path.read_bytes()
            self.assertEqual(len(data),min(chunk_size,expected_size-(i-1)*chunk_size))
            total+=len(data)
            sha.update(data)
        self.assertEqual(total,expected_size)
        self.assertEqual(sha.hexdigest(),manifest['encrypted_file_sha256'])
    def test_no_unreleased_plaintext_zip_in_public_source(self):
        published=ROOT/'released_source'
        names=sorted(p.name for p in published.glob('*.zip')) if published.exists() else []
        self.assertEqual(names,['short-s01.zip'])
        self.assertFalse(list((ROOT/'vault').rglob('*.zip')),'Future video ZIP found under vault')
        self.assertFalse(list((ROOT/'vault').rglob('*PASSPHRASE*')),'Private passphrase file must not be committed')
if __name__=='__main__':unittest.main()
