"""Sealed video resource archive integrity, without ever reading the key."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHUNKS=ROOT/"vault"/"chunks"
class EncryptedVaultTests(unittest.TestCase):
    def test_all_encrypted_archive_bytes_are_in_public_git_only_in_sealed_form(self):
        meta=json.loads((CHUNKS/"manifest.json").read_text())
        self.assertEqual(meta["chunks"],44)
        self.assertEqual(meta["encrypted_file_bytes"],11504144)
        self.assertEqual(meta["chunk_bytes"],262144)
        sha=hashlib.sha256()
        total=0
        for n in range(1,45):
            p=CHUNKS/("encpart-%03d.bin"%n)
            self.assertTrue(p.is_file(),p)
            data=p.read_bytes()
            self.assertEqual(len(data),min(262144,meta["encrypted_file_bytes"]-(n-1)*262144))
            sha.update(data)
            total+=len(data)
        self.assertEqual(total,meta["encrypted_file_bytes"])
        self.assertEqual(sha.hexdigest(),meta["encrypted_file_sha256"])
    def test_only_verified_published_shorts_have_plaintext_packs(self):
        released=sorted((ROOT/"released_source").glob("short-s*.zip"))
        plan={v["id"]:v for v in json.loads((ROOT/"config/videos.json").read_text())["videos"]}
        discovered=json.loads((ROOT/"config/discovered.json").read_text())["shorts"]
        self.assertTrue(released)
        for path in released:
            rid=path.stem
            self.assertIn(rid,discovered,"Never stage an unverified future video ZIP")
            self.assertIn(rid,plan)
            self.assertTrue(plan[rid]["approved"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                plan[rid]["sha256"],
                "Only the original verified release ZIP can be staged")
    def test_never_stage_vault_key_in_repository(self):
        self.assertFalse((ROOT/"vault"/"passphrase.txt").exists())
        self.assertFalse((ROOT/"vault"/"DP_VAULT_PASSPHRASE").exists())
        self.assertFalse((ROOT/"vault"/"batch-001.zip").exists())
if __name__=="__main__":
    unittest.main()
