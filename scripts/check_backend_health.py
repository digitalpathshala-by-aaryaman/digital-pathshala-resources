#!/usr/bin/env python3
"""Read-only health check for the published Digital Pathshala Apps Script.

Never creates leads, feedback or videos. Safe to run on scheduled builds.
"""
import json
import sys
import urllib.parse
import urllib.request

APP_URL = ("https://script.google.com/macros/s/"
           "AKfycbwldCtUXGeD3LqeyGqj8TjSUKdasREcXDvfIoMYrhXI3UaHBoM25i6Ypp60ctQu-Efd/exec")

def main():
    url = APP_URL + "?" + urllib.parse.urlencode({"action": "health"})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DigitalPathshalaHealth/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            value = json.loads(response.read(15000).decode("utf-8"))
        if value.get("status") != "ok" or value.get("service") != "Digital Pathshala Resources":
            print("APP_SCRIPT_HEALTH=FAIL: unexpected service status", file=sys.stderr)
            return 2
        if value.get("configured") is not True:
            print("APP_SCRIPT_HEALTH=PARTIAL: service is online but PUBLISHED_MANIFEST_URL is not configured", file=sys.stderr)
            return 3
        print("APP_SCRIPT_HEALTH=PASS: service online; manifest property configured")
        return 0
    except Exception as exc:
        print("APP_SCRIPT_HEALTH=UNVERIFIED:", type(exc).__name__, str(exc)[:160], file=sys.stderr)
        return 4

if __name__ == "__main__":
    raise SystemExit(main())
