#!/usr/bin/env python3
"""Safe release diagnostics. Only public metadata and readiness booleans are logged."""
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'config/site.json').read_text())
PLAN=json.loads((ROOT/'config/videos.json').read_text())['videos']
DISCOVERED=json.loads((ROOT/'config/discovered.json').read_text())['shorts']
IST=ZoneInfo('Asia/Kolkata')
now=dt.datetime.now(IST)
channel_id=CONFIG['youtube_channel_id']
print('CHECK: local time:',now.strftime('%Y-%m-%d %H:%M %Z'))
print('CHECK: approved Shorts:',sum(s.get('type')=='short' and s.get('approved') is True for s in PLAN))
print('CHECK: due Shorts:',','.join(s['id'] for s in PLAN if s.get('type')=='short' and s.get('approved') is True and s.get('release_at_ist') and now>=dt.datetime.strptime(s['release_at_ist'],'%Y-%m-%d %H:%M').replace(tzinfo=IST)) or 'none')
print('CHECK: public YouTube links discovered:',len(DISCOVERED))
print('CHECK: encrypted vault archives:',len(list((ROOT/'vault').glob('*.zip.enc'))))
print('CHECK: vault passphrase configured:',bool(os.environ.get('DP_VAULT_PASSPHRASE')))
for purpose,url in [
    ('official_handle',CONFIG['channel_url']),
    ('rss_feed','https://www.youtube.com/feeds/videos.xml?channel_id='+channel_id),
    ('shorts_tab',CONFIG['channel_url'].rstrip('/')+'/shorts')
]:
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Digital Pathshala public channel diagnostics)'})
        with urllib.request.urlopen(request,timeout=15) as res:
            doc=res.read(2800000).decode('utf-8','replace')
            print('CHECK:',purpose,'HTTP',res.status,'content_type',res.headers.get('Content-Type','')[:90])
        if purpose=='rss_feed':
            ns={'yt':'http://www.youtube.com/xml/schemas/2015',
                'a':'http://www.w3.org/2005/Atom'}
            root=ET.fromstring(doc)
            raw=root.findtext('yt:channelId',default='',namespaces=ns)
            feed_id=root.findtext('a:id',default='',namespaces=ns)
            title=root.findtext('a:title',default='',namespaces=ns)
            print('CHECK: RSS root channel ID:',repr(raw))
            print('CHECK: RSS feed identity:',repr(feed_id))
            print('CHECK: RSS title:',repr(title))
            print('CHECK: RSS matches configured channel:',raw==channel_id)
            for e in root.findall('a:entry',ns)[:5]:
                print('CHECK: RSS entry',repr(e.findtext('yt:videoId',default='',namespaces=ns)),
                      repr(e.findtext('a:published',default='',namespaces=ns)),
                      repr(e.findtext('a:title',default='',namespaces=ns))[:150])
        else:
            import re
            matches=re.findall(r'(?:"externalId"|"channelId")\s*:\s*"(UC[A-Za-z0-9_-]{22})"',doc)
            print('CHECK:',purpose,'public identity candidates:',sorted(set(matches))[:3])
            if purpose=='shorts_tab':
                print('CHECK: shorts-tab has video ID markers:',bool(re.search(r'"videoId"\s*:',doc)))
    except Exception as ex:
        print('CHECK:',purpose,'unavailable:',type(ex).__name__,str(ex)[:100])
