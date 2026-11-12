#!/usr/bin/env python3
"""Keyless Shorts discovery: public YouTube Atom feed + public Shorts listing.
Ambiguous or unavailable matches stay on hold; no API key is required.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
IST = ZoneInfo('Asia/Kolkata')
YOUTUBE_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
CHANNEL_ID = re.compile(r'^UC[A-Za-z0-9_-]{22}$')
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; DigitalPathshalaResourcePublisher/2.0)'}


def get_text(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError('External endpoint did not return 200')
        return response.read(3_000_001).decode('utf-8', 'replace')


def discover_channel_id(home_html):
    patterns = [
        r'"externalId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
        r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
        r'https?://www\.youtube\.com/feeds/videos\.xml\?channel_id=(UC[A-Za-z0-9_-]{22})',
        r'https?://www\.youtube\.com/channel/(UC[A-Za-z0-9_-]{22})',
    ]
    for pattern in patterns:
        match = re.search(pattern, home_html)
        if match and CHANNEL_ID.fullmatch(match.group(1)):
            return match.group(1)
    return ''


def parse_feed(feed_xml, expected_channel_id):
    ns = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
    root = ET.fromstring(feed_xml)
    channel_id = (root.findtext('yt:channelId', default='', namespaces=ns) or '').strip()
    if channel_id != expected_channel_id:
        raise ValueError('YouTube channel identity mismatch')
    results = []
    for entry in root.findall('a:entry', ns):
        video_id = (entry.findtext('yt:videoId', default='', namespaces=ns) or '').strip()
        published = (entry.findtext('a:published', default='', namespaces=ns) or '').strip()
        title = (entry.findtext('a:title', default='', namespaces=ns) or '').strip()
        if not YOUTUBE_ID.fullmatch(video_id):
            continue
        try:
            when = dt.datetime.fromisoformat(published.replace('Z', '+00:00'))
            if when.tzinfo is None:
                continue
        except ValueError:
            continue
        results.append({'id': video_id, 'title': title,
                        'published_utc': when.astimezone(dt.timezone.utc).isoformat(),
                        'when': when.astimezone(IST)})
    return results


def shorts_page_ids(page_html):
    ids = set()
    for marker in ('reelItemRenderer', 'shortsLockupViewModel'):
        for match in re.finditer(r'"' + marker + r'"\s*:\s*\{', page_html):
            vicinity = page_html[match.end():match.end()+1400]
            for expression in (r'"videoId"\s*:\s*"([A-Za-z0-9_-]{11})"',
                               r'"entityId"\s*:\s*"shorts-shelf-item-([A-Za-z0-9_-]{11})"',
                               r'"contentId"\s*:\s*"([A-Za-z0-9_-]{11})"'):
                found = re.search(expression, vicinity)
                if found:
                    ids.add(found.group(1))
                    break
    return ids


def normalized(text):
    return ' '.join(re.findall(r'[a-z0-9]+', (text or '').casefold()))


def title_score(a, b):
    a, b = normalized(a), normalized(b)
    if not a or not b:
        return 0.0
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    aa, bb = set(a.split()), set(b.split())
    common = len(aa & bb)
    overlap = common / max(1, min(len(aa), len(bb)))
    return max(ratio, overlap if common >= 3 else 0.0)


def choose_candidate(video, feed_entries, shorts_ids, used_ids, now):
    """Match a video on its release date after 11 AM IST; ambiguous cases hold."""
    earliest = dt.datetime.strptime(video['release_at_ist'], '%Y-%m-%d %H:%M').replace(tzinfo=IST)
    if now < earliest or not video.get('approved') or video.get('type') != 'short':
        return None
    target_day = earliest.date()
    contenders = [e for e in feed_entries if e['id'] not in used_ids
                  and e['when'].date() == target_day and e['when'].hour >= 11]
    if not contenders:
        return None
    verified_shorts = [e for e in contenders if e['id'] in shorts_ids]
    if len(verified_shorts) == 1:
        return verified_shorts[0]
    if len(verified_shorts) > 1:
        contenders = verified_shorts
    ranked = sorted(((title_score(video['title'], e['title']), e) for e in contenders),
                    key=lambda x: x[0], reverse=True)
    score, candidate = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0
    if score >= 0.76 and score - runner_up >= 0.16:
        return candidate
    return None


def run(root=ROOT, now=None, getter=get_text):
    root = Path(root)
    now = now or dt.datetime.now(IST)
    site = json.loads((root / 'config/site.json').read_text())
    plan = json.loads((root / 'config/videos.json').read_text())['videos']
    dest = root / 'config/discovered.json'
    found = json.loads(dest.read_text()) if dest.exists() else {'schema_version': 1, 'shorts': {}}
    already = found.setdefault('shorts', {})
    if not isinstance(already, dict):
        raise ValueError('Invalid discovery registry')
    known_ids = {v['youtube_id'] for v in already.values()}
    home_url = site.get('channel_url', '').rstrip('/')
    if not home_url.startswith('https://www.youtube.com/@'):
        raise ValueError('Unexpected configured YouTube channel handle')
    channel_id = site.get('youtube_channel_id', '')
    if not CHANNEL_ID.fullmatch(channel_id):
        channel_id = discover_channel_id(getter(home_url))
    if not channel_id:
        raise RuntimeError('Cannot identify channel from the public YouTube page')
    feed = getter('https://www.youtube.com/feeds/videos.xml?channel_id=' + channel_id)
    entries = parse_feed(feed, channel_id)
    try:
        short_ids = shorts_page_ids(getter(home_url + '/shorts'))
    except Exception as ex:
        print('Shorts tab unavailable; requiring strong title evidence:', type(ex).__name__)
        short_ids = set()
    additions = []
    for item in sorted(plan, key=lambda v: v.get('release_at_ist', '')):
        if item['id'] in already or item.get('type') != 'short' or not item.get('release_at_ist'):
            continue
        match = choose_candidate(item, entries, short_ids, known_ids, now)
        if match:
            already[item['id']] = {
                'youtube_id': match['id'],
                'published_at_utc': match['published_utc'],
                'discovered_at_utc': now.astimezone(dt.timezone.utc).isoformat(),
                'feed_title': match['title'], 'channel_id': channel_id,
                'proof': 'public-channel-feed' + ('-and-shorts-tab' if match['id'] in short_ids else '-title-match')
            }
            known_ids.add(match['id'])
            additions.append(item['id'])
    if additions:
        dest.write_text(json.dumps(found, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Keyless YouTube discovery:', len(additions), 'new Shorts; total', len(already))
    return additions


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Public feed unavailable; keeping existing mapping:', type(exc).__name__, str(exc), file=sys.stderr)
        # Website can still deploy; no unverified resources are published.
