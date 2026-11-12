#!/usr/bin/env python3
"""Register an approved PUBLIC independent resource; the build creates its page."""
import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo
from build_independent import KINDS, EXTENSIONS, slugify

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description='Publish one approved free Digital Pathshala resource')
    parser.add_argument('--kind',required=True,choices=list(KINDS))
    parser.add_argument('--title',required=True)
    parser.add_argument('--file',type=Path,required=True)
    parser.add_argument('--description',default='')
    parser.add_argument('--category',default='General')
    parser.add_argument('--highlight',action='append',default=[])
    parser.add_argument('--cover-url',default='')
    parser.add_argument('--slug',default='')
    parser.add_argument('--publish',action='store_true',help='Required: confirms immediate PUBLIC publication')
    args=parser.parse_args()
    if not args.publish:parser.error('--publish is required. Never stage private, future or draft files in this public repository.')
    if not args.file.is_file():parser.error('Resource file missing')
    if args.file.suffix.lower() not in EXTENSIONS:parser.error('Supported: PDF, XLSX, XLSM, ZIP. Package HTML tools inside ZIP.')
    slug=args.slug or slugify(args.title)
    if slugify(slug)!=slug:parser.error('Invalid URL slug')
    config_path=ROOT/'config/independent.json'
    data=json.loads(config_path.read_text(encoding='utf-8'))
    if any(v['kind']==args.kind and v['slug']==slug for v in data['resources']):
        parser.error('Duplicate permanent resource URL; existing slugs must remain stable')
    destination=ROOT/'independent_source'/KINDS[args.kind]/slug/args.file.name
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(args.file,destination)
    stamp=dt.datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M')
    data['resources'].append({
        'kind':args.kind,'slug':slug,'title':args.title,'description':args.description,
        'category':args.category,'highlights':args.highlight[:8],
        'cover_url':args.cover_url,'approved':True,'published_at_ist':stamp,
        'file_name':args.file.name,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()
    })
    config_path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    base=json.loads((ROOT/'config/site.json').read_text())['base_url'].rstrip('/')+'/'
    print('Permanent public page:',base+KINDS[args.kind]+'/'+slug+'/')
    print('Download file staged:',destination.relative_to(ROOT))
    print('Commit both source file and config/independent.json to publish this resource.')
if __name__=='__main__':main()
