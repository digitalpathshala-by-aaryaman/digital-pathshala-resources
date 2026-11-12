#!/usr/bin/env python3
"""Single synthetic end-to-end test: real GAS POST -> Google Sheet receipt -> PDF.
Only runs on a specially tagged commit. Request ID fixed so re-runs are idempotent.
No real visitor details, no marketing opt-in, no credential output.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GAS="https://script.google.com/macros/s/AKfycbwldCtUXGeD3LqeyGqj8TjSUKdasREcXDvfIoMYrhXI3UaHBoM25i6Ypp60ctQu-Efd/exec"
BASE="https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/"
SLUG="let-ai-do-your-browser-work-while-you-watch-2026"
RESOURCE_ID="ebook-"+SLUG
REQUEST_ID="d010d000-2026-4aca-9200-000000000001"
PDF_SHA="85d56d8578f7e350b2b364c888bbcdec5018d1f5a0b54994bee0132c94d484bc"
payload={
 "request_id": REQUEST_ID, "action": "download",
 "video_id": RESOURCE_ID, "page_url": BASE+"ebooks/"+SLUG+"/",
 "full_name": "DIGITAL PATHSHALA AUTOMATED TEST - NOT A VISITOR",
 "email": "digital-pathshala-test@example.com",
 "phone": "", "privacy_consent": True, "marketing_opt_in": False,
 "website": "", "referrer": "", "utm_source": "automated-test",
 "utm_medium": "github-actions", "utm_campaign": "one-time-form-e2e"
}
headers={"User-Agent":"DigitalPathshalaOneTimeIntegrationTest/3.0","Accept":"application/json"}
try:
    raw=json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(GAS,method="POST",data=raw,
          headers={**headers,"Content-Type":"text/plain;charset=utf-8"})
    try:
        with urllib.request.urlopen(req,timeout=40) as r:
            doc=json.loads(r.read(10000).decode("utf-8"))
            print("POST response status:",doc.get("status"),"action:",doc.get("action"),
                  "code:",doc.get("code",""))
    except Exception as ex:
        # Google ContentService redirects to one-time URLs and can transiently
        # fail there even AFTER Apps Script has saved the record. Always check
        # receipt for this SAME request ID rather than issuing another POST.
        print("POST response not readable; checking exact receipt:",type(ex).__name__)
    receipt=None
    for n in range(12):
        time.sleep(1.5 if n==0 else 1)
        url=GAS+"?"+urllib.parse.urlencode({"action":"receipt","request_id":REQUEST_ID})
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=25) as r:
                answer=json.loads(r.read(10000).decode("utf-8"))
        except Exception as ex:
            print("Receipt GET transient failure, attempt",n+1,type(ex).__name__)
            continue
        print("Receipt attempt",n+1,answer.get("status"))
        if answer.get("status")=="ok":
            receipt=answer
            break
        if answer.get("status")=="error":
            raise AssertionError("Backend rejected synthetic submission: "+str(answer.get("code")))
        if answer.get("status")!="pending":
            raise AssertionError("Unexpected receipt response")
    if not receipt:
        raise AssertionError("The real Sheet receipt could not be verified")
    assert receipt.get("video_id")==RESOURCE_ID, "Incorrect resource ID in Sheet receipt"
    assert receipt.get("action")=="download", "Incorrect action in Sheet receipt"
    public_url=receipt.get("download_url","")
    expected=BASE+"downloads/ebooks/"+SLUG+"/Digital-Pathshala-AI-in-Your-Browser-2026.pdf"
    assert public_url==expected, "Incorrect published PDF URL"
    with urllib.request.urlopen(urllib.request.Request(public_url,headers=headers),timeout=25) as r:
        pdf=r.read(1_000_000)
    assert len(pdf)==648870, "Incorrect PDF size"
    assert hashlib.sha256(pdf).hexdigest()==PDF_SHA, "Original PDF checksum mismatch"
    print("FORM_E2E=PASS: synthetic Sheet write, receipt confirmation and exact original PDF download")
    print("Test record label: DIGITAL PATHSHALA AUTOMATED TEST - NOT A VISITOR")
except Exception as ex:
    print("FORM_E2E=FAIL:",type(ex).__name__,str(ex)[:230],file=sys.stderr)
    raise SystemExit(1)
