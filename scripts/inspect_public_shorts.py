#!/usr/bin/env python3
"""Temporary public Shorts listing probe for safe keyless discovery implementation."""
import json
import re
import urllib.request
from urllib.parse import quote
BASE='https://www.youtube.com/@DigitalPathshalabyAaryaman'
HEAD={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}
def get(url):
  with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=20) as x:
    return x.read(3000000).decode('utf-8','replace')
doc=get(BASE+'/shorts')
for marker in ['shortsLockupViewModel','reelItemRenderer','"ytInitialData"','var ytInitialData','"videoId"','"entityId"']:
  print('MARKER',marker,'COUNT',doc.count(marker),'FIRST',doc.find(marker))
for marker in ['shortsLockupViewModel','reelItemRenderer']:
  pos=doc.find(marker)
  if pos>=0:
    print('EXCERPT',marker,doc[pos:pos+1450][:1450])
# Extract valid official shorts lockup IDs, not arbitrary YouTube suggestions.
found=[]
for m in re.finditer(r'shorts-shelf-item-([A-Za-z0-9_-]{11})',doc):
  if m.group(1) not in found:found.append(m.group(1))
for m in re.finditer(r'"shortsLockupViewModel"\s*:\s*\{',doc):
  blob=doc[m.end():m.end()+2200]
  x=re.search(r'"videoId"\s*:\s*"([A-Za-z0-9_-]{11})"',blob) or re.search(r'"shorts-shelf-item-([A-Za-z0-9_-]{11})',blob)
  if x and x.group(1) not in found:found.append(x.group(1))
print('PUBLIC SHORTS IDS',found[:16])
for vid in found[:5]:
  try:
    html=get('https://www.youtube.com/shorts/'+vid)
    ids=re.findall(r'"publishDate"\s*:\s*"([^"]+)"',html)[:3]
    date=re.findall(r'"uploadDate"\s*:\s*"([^"]+)"',html)[:3]
    titles=re.findall(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',html)[:2]
    channel=re.findall(r'"externalChannelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',html)[:2]
    print('SHORT DETAILS',vid,'date',ids,'upload',date,'title',titles,'channel',channel)
  except Exception as e:print('SHORT UNAVAILABLE',vid,type(e).__name__,str(e)[:70])
