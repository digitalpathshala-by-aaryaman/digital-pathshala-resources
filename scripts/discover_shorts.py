#!/usr/bin/env python3
"""Keyless Shorts discovery: public YouTube Atom feed + public Shorts listing.
Ambiguous or unavailable matches stay on hold; no API key is required.
"""
from __future__ import annotations

import datetime as dt
import difflib
import html
import json
import re
import sys
import urllib.request
import urllib.parse
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



def verified_shorts_entries(page_html, expected_channel_id, getter, max_checks=20):
    """Fallback: require official Shorts listing AND the video's own channel/date/title metadata."""
    ids = []
    for match in re.finditer(r'shorts-shelf-item-([A-Za-z0-9_-]{11})', page_html):
        if match.group(1) not in ids:
            ids.append(match.group(1))
    if not ids:
        ids = list(shorts_page_ids(page_html))
    result = []
    for video_id in ids[:max_checks]:
        try:
            page = getter('https://www.youtube.com/shorts/' + video_id)
            channel = re.search(r'"externalChannelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"', page)
            stamp = re.search(r'"publishDate"\s*:\s*"([^"]+)"', page)
            title = re.search(r'<meta\s+[^>]*property="og:title"[^>]*content="([^"]+)"', page)
            if not channel or channel.group(1) != expected_channel_id or not stamp or not title:
                continue
            when = dt.datetime.fromisoformat(stamp.group(1).replace('Z', '+00:00'))
            if when.tzinfo is None:
                continue
            result.append({'id': video_id, 'title': html.unescape(title.group(1)),
                           'published_utc': when.astimezone(dt.timezone.utc).isoformat(),
                           'when': when.astimezone(IST)})
        except (OSError, ValueError, TimeoutError) as exc:
            print('Short metadata temporarily unavailable:', video_id, type(exc).__name__)
    return result, set(ids)


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
        try:
            channel_id = discover_channel_id(getter(home_url))
        except Exception as ex:
            print('Channel handle fetch failed; trying the public trailer:', type(ex).__name__)
            channel_id = ''
    # Fallback to the channel trailer's YouTube oEmbed author_url.
    # This is public metadata; no Google or YouTube API key is involved.
    if not channel_id:
        trailer = site.get('channel_trailer_video_id', '')
        if YOUTUBE_ID.fullmatch(trailer):
            try:
                url = 'https://www.youtube.com/oembed?url=' + urllib.parse.quote(
                    'https://www.youtube.com/watch?v=' + trailer, safe=''
                ) + '&format=json'
                meta = json.loads(getter(url))
                author = meta.get('author_name', '').casefold()
                author_url = meta.get('author_url', '')
                if 'digital pathshala' in author and 'aaryaman' in author and author_url.startswith('https://www.youtube.com/'):
                    match = re.search(r'/channel/(UC[A-Za-z0-9_-]{22})', author_url)
                    if match:
                        channel_id = match.group(1)
                    else:
                        home_url = author_url.rstrip('/')
                        channel_id = discover_channel_id(getter(home_url))
            except Exception as ex:
                print('Public trailer fallback unavailable:', type(ex).__name__)
    if not CHANNEL_ID.fullmatch(channel_id):
        raise RuntimeError('Cannot identify the official channel from public YouTube metadata')
    # Avoid external requests until an approved Short is due and still unmapped.
    pending_due = []
    for item in plan:
        if item.get('type') != 'short' or item.get('approved') is not True or item['id'] in already:
            continue
        try:
            when = dt.datetime.strptime(item['release_at_ist'], '%Y-%m-%d %H:%M').replace(tzinfo=IST)
            if now >= when:
                pending_due.append(item)
        except (TypeError, ValueError, KeyError):
            continue
    if not pending_due:
        print('Keyless discovery: no due unmapped Shorts; total', len(already))
        return []
    try:
        public_page = getter(home_url + '/shorts')
    except Exception as ex:
        print('Official Shorts tab unavailable:', type(ex).__name__)
        public_page = ''
    short_ids = shorts_page_ids(public_page)
    fallback = False
    try:
        feed = getter('https://www.youtube.com/feeds/videos.xml?channel_id=' + channel_id)
        entries = parse_feed(feed, channel_id)
    except Exception as ex:
        fallback = True
        print('RSS unavailable; using verified public Shorts video metadata:', type(ex).__name__)
        if not public_page:
            return []
        entries, short_ids = verified_shorts_entries(public_page, channel_id, getter)
        print('Verified', len(entries), 'official Short video pages from', len(short_ids), 'listing IDs')
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
                'proof': ('verified-shorts-page-channel-and-timestamp' if fallback else
                          'public-channel-feed' + ('-and-shorts-tab' if match['id'] in short_ids else '-title-match'))
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
