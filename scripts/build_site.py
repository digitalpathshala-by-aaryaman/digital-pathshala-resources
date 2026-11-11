#!/usr/bin/env python3
"""Fail-closed GitHub Pages builder: never publish an unreleased ZIP."""
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
IST = ZoneInfo("Asia/Kolkata")
ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,71}$")
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def due(value, now):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d", value):
        return False
    try:
        return now >= dt.datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    except ValueError:
        return False

def youtube_public(ids):
    key = os.getenv("YOUTUBE_API_KEY", "")
    if not ids or not key:
        return set()
    found = set()
    for start in range(0, len(ids), 50):
        url = "https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode({
            "part": "status", "id": ",".join(ids[start:start + 50]), "key": key
        })
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DigitalPathshalaResources/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                items = json.load(response).get("items", [])
        except Exception as exc:
            print("YouTube verification failed; withholding unverified releases:", type(exc).__name__, file=sys.stderr)
            return set()
        for item in items:
            status = item.get("status", {})
            if status.get("privacyStatus") == "public" and status.get("uploadStatus", "processed") == "processed":
                found.add(item.get("id", ""))
    return found

def open_batches(root, temp):
    if not os.getenv("DP_VAULT_PASSPHRASE", ""):
        return []
    archives = []
    for i, path in enumerate(sorted((root / "vault").glob("*.zip.enc"))):
        output = temp / ("batch-%04d.zip" % i)
        proc = subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
             "-in", str(path), "-out", str(output), "-pass", "env:DP_VAULT_PASSPHRASE"],
            env=os.environ, capture_output=True
        )
        if proc.returncode:
            raise RuntimeError("Encrypted batch could not be decrypted: " + path.name)
        archives.append(zipfile.ZipFile(output))
    return archives

def find_zip(archives, video_id):
    matches = []
    for archive in archives:
        for member in archive.namelist():
            name = member.replace("\\", "/")
            if name == video_id + ".zip" or name.endswith("/" + video_id + ".zip"):
                matches.append((archive, member))
    if len(matches) > 1:
        raise ValueError("Duplicate resource pack: " + video_id)
    return matches[0] if matches else None

def build(root=ROOT, output=None, now=None, public_ids=None):
    root = Path(root)
    output = Path(output) if output else root / "_site"
    site = load(root / "config/site.json")
    plan = load(root / "config/videos.json")["videos"]
    base = site["base_url"].rstrip("/") + "/"
    if not base.startswith("https://"):
        raise ValueError("Site URL must use HTTPS.")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(root / "site", output)
    (output / "resources").mkdir(exist_ok=True)
    now = now or dt.datetime.now(IST)
    ids = set()
    due_videos = []
    for v in plan:
        vid = v.get("id", "")
        if not ID.fullmatch(vid) or vid in ids:
            raise ValueError("Invalid/duplicate ID: " + repr(vid))
        ids.add(vid)
        if v.get("approved") is True and due(v.get("release_at_ist"), now) and YOUTUBE_ID.fullmatch(v.get("youtube_id", "")):
            due_videos.append(v)
    if not site.get("privacy_contact_email") or "@" not in site["privacy_contact_email"]:
        print("Privacy contact missing; holding all releases.", file=sys.stderr)
        due_videos = []
    if public_ids is None:
        public_ids = youtube_public([v["youtube_id"] for v in due_videos])
    ready = [v for v in due_videos if v["youtube_id"] in public_ids]
    published = []
    with tempfile.TemporaryDirectory() as temp:
        archives = open_batches(root, Path(temp)) if ready else []
        for v in ready:
            match = find_zip(archives, v["id"])
            if not match:
                print("Encrypted resource pack missing; holding", v["id"], file=sys.stderr)
                continue
            archive, member = match
            blob = archive.read(member)
            if hashlib.sha256(blob).hexdigest().lower() != v["sha256"].lower():
                raise ValueError("Resource SHA mismatch: " + v["id"])
            if not zipfile.is_zipfile(io.BytesIO(blob)):
                raise ValueError("Invalid ZIP: " + v["id"])
            (output / "resources" / (v["id"] + ".zip")).write_bytes(blob)
            published.append({
                "id": v["id"], "title": v["title"], "type": v["type"],
                "description": v.get("description", ""),
                "release_at_ist": v["release_at_ist"], "status": "live",
                "youtube_url": "https://www.youtube.com/watch?v=" + v["youtube_id"],
                "resource_url": base + "resources/" + v["id"] + ".zip",
                "resources": v.get("resources", [])
            })
        for archive in archives:
            archive.close()
    published.sort(key=lambda v: (v["release_at_ist"], v["id"]), reverse=True)
    (output / "videos.json").write_text(json.dumps({"videos": published}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / ".nojekyll").touch()
    print("Published resource count:", len(published), "out of", len(plan), "prepared video IDs.")
    return published

if __name__ == "__main__":
    build()
