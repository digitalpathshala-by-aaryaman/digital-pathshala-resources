#!/usr/bin/env python3
"""Read-only live smoke test for Digital Pathshala GitHub Pages and Apps Script v3.

No actual visitor names, test submissions, or private data are created.
"""
import json
import hashlib
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


def verify_first_ebook():
    slug = '10-hidden-ai-mistakes-nobody-warns-you-about-2026'
    url = SITE + 'ebooks/' + slug + '/'
    page = get(url, False)
    expect('10 Hidden AI Mistakes' in page, 'first e-book permanent page responds')
    manifest = get(SITE + 'independent.json')
    rows = [v for v in manifest.get('resources', [])
            if v.get('id') == 'ebook-' + slug]
    if rows:
        item = rows[0]
        expect(item['page_url'] == url and item.get('status') == 'live',
               'first e-book publicly listed with permanent URL')
        request = urllib.request.Request(item['resource_url'],
                   headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            blob = response.read(1_200_000)
        expect(hashlib.sha256(blob).hexdigest() ==
               '33f22832b61efde560ccedcf1ade92fc927145939b2d0905f98802144ed505d9',
               'public original PDF bytes match registered checksum')
    else:
        expect('Download is being activated.' in page,
               'ebook prelaunch page honestly holds pending download')



def verify_second_ebook():
    slug = 'the-hidden-switches-inside-chatgpt-gemini-claude-2026'
    url = SITE + 'ebooks/' + slug + '/'
    page = get(url, False)
    expect('The Hidden Switches Inside ChatGPT' in page,
           'second e-book permanent page responds')
    rows = [v for v in get(SITE+'independent.json').get('resources', [])
            if v.get('id') == 'ebook-' + slug]
    if rows:
        item = rows[0]
        expect(item['page_url'] == url and item.get('status') == 'live',
               'second e-book publicly listed with permanent URL')
        req = urllib.request.Request(item['resource_url'],
                   headers={'User-Agent': 'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            blob = response.read(1_200_000)
        expect(len(blob) == 499431 and
               hashlib.sha256(blob).hexdigest() ==
               'f6d65036d58ed61eb70f92ec272ba4fb054a90605085dd928595b3e4dd0deafe',
               'public second original PDF bytes match registered checksum')
    else:
        expect('Download is being activated.' in page,
               'second e-book prelaunch page safely holds pending PDF')



def verify_third_ebook():
    slug = 'let-ai-do-your-browser-work-while-you-watch-2026'
    url = SITE + 'ebooks/' + slug + '/'
    page = get(url, False)
    expect('Let AI Do Your Browser Work' in page, 'third ebook permanent page loads')
    rows = [v for v in get(SITE + 'independent.json').get('resources', [])
            if v.get('id') == 'ebook-' + slug]
    if rows:
        item = rows[0]
        expect(item.get('page_url') == url and item.get('status') == 'live',
               'third ebook appears in public catalogue')
        req = urllib.request.Request(item['resource_url'],
                   headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            blob = response.read(1_200_000)
        expect(len(blob)==648870 and hashlib.sha256(blob).hexdigest()=='85d56d8578f7e350b2b364c888bbcdec5018d1f5a0b54994bee0132c94d484bc',
               'public third original PDF checksum matches uploaded document')
    else:
        expect('Download is being activated.' in page,
               'third ebook safely withheld until exact PDF upload')

def verify_new_ebook_4():
    slug='copy-text-from-anything-on-your-screen-2026'
    url=SITE+'ebooks/'+slug+'/'
    page=get(url,False)
    expect('Copy Text from Anything' in page,'ebook 4 permanent landing page')
    rows=[r for r in get(SITE+'independent.json').get('resources',[]) if r.get('id')=='ebook-'+slug]
    if rows:
        item=rows[0]
        expect(item.get('page_url')==url and item.get('status')=='live','ebook 4 listed in public catalogue')
        req=urllib.request.Request(item['resource_url'],headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(req,timeout=25) as response: blob=response.read(1000000)
        expect(len(blob)==374421 and hashlib.sha256(blob).hexdigest()=='8963b4a77eee10fba5c4bd236f2c8ef7fc9815d88d8a28c9f9a64ef8267e5bc9','ebook 4 PDF exact original checksum')
    else:
        expect('Download is being activated.' in page,'ebook 4 safely withheld until uploaded')


def verify_new_ebook_5():
    slug='pdf-tables-into-excel-the-honest-verified-guide-2026'
    url=SITE+'ebooks/'+slug+'/'
    page=get(url,False)
    expect('PDF Tables into Excel' in page,'ebook 5 permanent landing page')
    rows=[r for r in get(SITE+'independent.json').get('resources',[]) if r.get('id')=='ebook-'+slug]
    if rows:
        item=rows[0]
        expect(item.get('page_url')==url and item.get('status')=='live','ebook 5 listed in public catalogue')
        req=urllib.request.Request(item['resource_url'],headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(req,timeout=25) as response: blob=response.read(1000000)
        expect(len(blob)==409511 and hashlib.sha256(blob).hexdigest()=='50760db7dca74e42e2706f9b729608e8df05b66815b14b911de5643f166b5a6c','ebook 5 PDF exact original checksum')
    else:
        expect('Download is being activated.' in page,'ebook 5 safely withheld until uploaded')

def verify_ebook_6():
    slug='ask-chatgpt-for-a-tool-not-an-answer-2026'
    url=SITE+'ebooks/'+slug+'/'
    page=get(url,False)
    expect('Ask ChatGPT for a Tool' in page,'ebook 6 permanent landing page')
    items=[r for r in get(SITE+'independent.json').get('resources',[]) if r.get('id')=='ebook-'+slug]
    if items:
        item=items[0]
        expect(item.get('page_url')==url and item.get('status')=='live','ebook 6 is published in the catalogue')
        request=urllib.request.Request(item['resource_url'],headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(request,timeout=25) as response: pdf=response.read(1000000)
        expect(len(pdf)==343252 and hashlib.sha256(pdf).hexdigest()=='d4a3e0486293b8d799c54a1535a5902d69524fc94a9ccdad34671453a937ff4a','ebook 6 original PDF checksum verified')
    else:
        expect('Download is being activated.' in page,'ebook 6 is withheld safely until publication')

def verify_ebook_7():
    slug='claude-sheets-whiteboards-the-first-guide-2026'
    url=SITE+'ebooks/'+slug+'/'
    page=get(url,False)
    expect('Claude Sheets' in page,'ebook 7 permanent landing page')
    items=[r for r in get(SITE+'independent.json').get('resources',[]) if r.get('id')=='ebook-'+slug]
    if items:
        item=items[0]
        expect(item.get('page_url')==url and item.get('status')=='live','ebook 7 is published in the catalogue')
        request=urllib.request.Request(item['resource_url'],headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(request,timeout=25) as response: pdf=response.read(1000000)
        expect(len(pdf)==399857 and hashlib.sha256(pdf).hexdigest()=='8f3efd8e74d6a99d827c49f229120eaa1a4b825e912ddcd25ad4cdfe40193b75','ebook 7 original PDF checksum verified')
    else:
        expect('Download is being activated.' in page,'ebook 7 is withheld safely until publication')

SIZE_EBOOK_8 = 396841

def verify_ebook_8():
    slug='chatgpt-images-2-6-gifs-and-the-same-character-every-time-2026'
    url=SITE+'ebooks/'+slug+'/'
    page=get(url,False)
    expect('GIFs and the Same Character' in page,'ebook 8 permanent landing page responds')
    rows=[r for r in get(SITE+'independent.json').get('resources',[]) if r.get('id')=='ebook-'+slug]
    if rows:
        item=rows[0]
        expect(item.get('page_url')==url and item.get('status')=='live','ebook 8 publicly listed with correct permanent URL')
        req=urllib.request.Request(item['resource_url'],headers={'User-Agent':'DigitalPathshalaLiveSmokeTest/3.0'})
        with urllib.request.urlopen(req,timeout=25) as response:
            data=response.read(1000000)
        expect(len(data)==SIZE_EBOOK_8 and hashlib.sha256(data).hexdigest()=='d6b9a7f21246ee1eef1a051dbddf311a7d120fb8f4b194a20d4b6fc1f3ddab86',
               'ebook 8 original PDF checksum verified from public download')
    else:
        expect('Download is being activated.' in page,
               'ebook 8 correctly withholds download until original PDF upload')

def main():
    failures = []
    checks = [
        ("Apps Script health: version 3.0 and configured", lambda: (
            lambda v: expect(v.get("status") == "ok" and v.get("version") == "3.0"
                             and v.get("configured") is True, "Apps Script v3.0 live with manifest configured")
        )(endpoint(action="health"))),
        ("First e-book permanent link and PDF state", verify_first_ebook),
        ("Second e-book permanent link and PDF state", verify_second_ebook),
        ("Third e-book permanent link and PDF state", verify_third_ebook),
        ("Fourth e-book URL and PDF state", verify_new_ebook_4),
        ("Fifth e-book URL and PDF state", verify_new_ebook_5),
        ("Sixth e-book permanent URL and PDF", verify_ebook_6),
        ("Seventh e-book permanent URL and PDF", verify_ebook_7),
        ("Eighth e-book permanent URL and PDF", verify_ebook_8),
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
