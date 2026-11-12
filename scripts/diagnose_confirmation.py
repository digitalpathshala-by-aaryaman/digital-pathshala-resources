#!/usr/bin/env python3
"""Non-mutating diagnostics for the exact browser JSONP confirmation path.
No personal data is requested or submitted.
"""
import json, urllib.parse, urllib.request, uuid

SCRIPT = ("https://script.google.com/macros/s/"
          "AKfycbwldCtUXGeD3LqeyGqj8TjSUKdasREcXDvfIoMYrhXI3UaHBoM25i6Ypp60ctQu-Efd/exec")
cases=[
 ("health_plain",{"action":"health"}),
 ("health_jsonp",{"action":"health","callback":"dpCallbackProbe"}),
 ("receipt_jsonp",{"action":"receipt","request_id":str(uuid.uuid4()),"callback":"dpCallbackProbe"})
]
for label,params in cases:
    url=SCRIPT+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Digital Pathshala diagnostics)","Accept":"*/*"})
    try:
        with urllib.request.urlopen(req,timeout=22) as response:
            raw=response.read(1400).decode("utf-8","replace")
            headers=response.info()
            print(json.dumps({"test":label,"status":response.status,
                 "redirect_host":urllib.parse.urlparse(response.url).hostname,
                 "content_type":headers.get("Content-Type"),
                 "x_content_type_options":headers.get("X-Content-Type-Options"),
                 "content_disposition":headers.get("Content-Disposition"),
                 "csp":headers.get("Content-Security-Policy"),
                 "starts_callback":raw.startswith("dpCallbackProbe("),
                 "response_excerpt":raw[:170]}))
    except Exception as e:
        print(json.dumps({"test":label,"failure_type":type(e).__name__,
                          "message":str(e)[:160]}))
