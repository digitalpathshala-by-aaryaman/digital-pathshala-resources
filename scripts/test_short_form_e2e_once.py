#!/usr/bin/env python3
"""One-time synthetic SHORT download -> Google Sheet -> receipt -> original ZIP test.

This uses a fixed request ID and a clearly marked synthetic visitor, never a
real visitor's personal information. A retry uses the same ID, not a second lead.
"""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request

GAS=("https://script.google.com/macros/s/"
     "AKfycbwldCtUXGeD3LqeyGqj8TjSUKdasREcXDvfIoMYrhXI3UaHBoM25i6Ypp60ctQu-Efd/exec")
BASE="https://digitalpathshala-by-aaryaman.github.io/digital-pathshala-resources/"
VIDEO_ID="short-s01"
REQUEST_ID="d010d001-2026-4aca-9200-000000000001"
ZIP_SHA="c509323fb770fe316b48403928445c6317ba5f853c161855c662dff4053a1e3c"
payload={
 "request_id":REQUEST_ID, "action":"download",
 "video_id":VIDEO_ID,"page_url":BASE+"?v="+VIDEO_ID,
 "full_name":"DIGITAL PATHSHALA SHORT TEST - NOT A VISITOR",
 "email":"digital-pathshala-test@example.com",
 "phone":"","privacy_consent":True,"marketing_opt_in":False,
 "website":"","referrer":"","utm_source":"automated-test",
 "utm_medium":"github-actions","utm_campaign":"short-first-release-e2e"
}
headers={"User-Agent":"DigitalPathshalaOneTimeShortTest/3.0","Accept":"application/json"}
try:
  request=urllib.request.Request(GAS,method="POST",data=json.dumps(payload).encode(),
        headers={**headers,"Content-Type":"text/plain;charset=utf-8"})
  try:
    with urllib.request.urlopen(request,timeout=40) as response:
      doc=json.loads(response.read(10000).decode())
    print("POST result:",doc.get("status"),"code:",doc.get("code",""))
  except Exception as ex:
    print("POST response not readable; checking same request ID:",type(ex).__name__)
  receipt=None
  for i in range(15):
    time.sleep(1.5 if i==0 else 1)
    url=GAS+"?"+urllib.parse.urlencode({"action":"receipt","request_id":REQUEST_ID})
    try:
      with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=25) as response:
        doc=json.loads(response.read(10000).decode())
    except Exception as ex:
      print("Temporary receipt connection issue:",type(ex).__name__)
      continue
    print("Receipt attempt",i+1,doc.get("status"))
    if doc.get("status")=="ok":
      receipt=doc
      break
    if doc.get("status")=="error":
      raise AssertionError("Submission rejected: "+str(doc.get("code","unknown")))
    if doc.get("status")!="pending":
      raise AssertionError("Unexpected receipt response")
  if receipt is None:
    raise AssertionError("Cannot verify Sheet receipt")
  assert receipt.get("video_id")==VIDEO_ID,"Wrong video"
  assert receipt.get("action")=="download","Wrong action"
  url=receipt.get("download_url","")
  assert url==BASE+"resources/"+VIDEO_ID+".zip","Incorrect ZIP link in Sheet receipt"
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response:
    blob=response.read(200000)
  assert len(blob)==152617,"ZIP byte length incorrect"
  assert hashlib.sha256(blob).hexdigest()==ZIP_SHA,"Original ZIP checksum mismatch"
  print("SHORT_FORM_E2E=PASS: live Sheet write, receipt and original short-s01.zip download")
  print("Synthetic label: DIGITAL PATHSHALA SHORT TEST - NOT A VISITOR")
except Exception as ex:
  print("SHORT_FORM_E2E=FAIL:",type(ex).__name__,str(ex)[:220],file=sys.stderr)
  raise SystemExit(1)
