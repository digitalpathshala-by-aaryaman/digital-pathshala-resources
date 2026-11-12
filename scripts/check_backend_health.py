#!/usr/bin/env python3
"""Read-only live smoke test for Digital Pathshala GitHub Pages and Apps Script v3.

No actual visitor names, test submissions, or private data are created.
"""
import json
import sys
import urllib.parse
import urllib.request
import uuid

SITE = "https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/"
SCRIPT = ("https://script.google.com/macros/s/"
          "AKfycbwldCtUXGeD3LqeyGqj8TjSUKdasREcXDvfIoMYrhXI3UaHBoM25i6Ypp60ctQu-Efd/exec")


def get(url, as_json=True):
    req = urllib.request.Request(url, headers={
        "User-Agent": "DigitalPathshalaLiveSmokeTest/3.0", "Accept": "application/json,text/html"
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read(200000).decode("utf-8", "replace")
        if response.status != 200:
            raise ValueError("Non-200 HTTP response")
    return json.loads(body) if as_json else body


def endpoint(**params):
    return get(SCRIPT + "?" + urllib.parse.urlencode(params))


def expect(condition, label):
    if not condition:
        raise AssertionError(label)
    print("PASS:", label)


def main():
    failures = []
    checks = [
        ("Apps Script health: version 3.0 and configured", lambda: (
            lambda v: expect(v.get("status") == "ok" and v.get("version") == "3.0"
                             and v.get("configured") is True, "Apps Script v3.0 live with manifest configured")
        )(endpoint(action="health"))),
        ("GitHub Pages home", lambda: expect(
            "Digital Pathshala" in get(SITE, False) and
            "assets/site.js" in get(SITE, False), "public GitHub Pages homepage responds")),
        ("Live video manifest", lambda: (
            lambda j: expect(isinstance(j.get("videos"), list), "videos.json valid public catalogue")
        )(get(SITE + "videos.json"))),
        ("Live independent manifest", lambda: (
            lambda j: expect(isinstance(j.get("resources"), list), "independent.json valid public catalogue")
        )(get(SITE + "independent.json"))),
        ("Future video cannot be downloaded", lambda: (
            lambda v: expect(v.get("status") == "not_released", "unknown video safely held")
        )(endpoint(action="video", v="short-nonexistent-check-123"))),
        ("Future independent item cannot be downloaded", lambda: (
            lambda v: expect(v.get("status") == "not_released", "unknown independent resource safely held")
        )(endpoint(action="resource", v="ebook-nonexistent-check-123"))),
        ("Receipt lookup and Sheets connectivity", lambda: (
            lambda v: expect(v.get("status") == "pending", "nonexistent receipt is pending, Sheet accessible")
        )(endpoint(action="receipt", request_id=str(uuid.uuid4())))),
    ]
    for label, check in checks:
        try:
            check()
        except Exception as exc:
            failures.append(label)
            print("FAIL:", label, "|", type(exc).__name__, str(exc)[:160], file=sys.stderr)
    if failures:
        print("LIVE_SMOKE=FAIL: ", len(failures), "of", len(checks), "checks failed", file=sys.stderr)
        return 1
    print("LIVE_SMOKE=PASS:", len(checks), "read-only checks; no lead created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
