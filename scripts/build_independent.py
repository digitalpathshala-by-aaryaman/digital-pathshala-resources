"""Build SEO-ready permanent pages for approved independent free resources."""
import datetime as dt
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo

KINDS={'ebook':'ebooks','template':'templates','guide':'guides','tool':'tools','resource':'resources'}
EXTENSIONS={'.pdf':'PDF','.xlsx':'Excel','.xlsm':'Excel macro-enabled','.zip':'ZIP'}
SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def slugify(title):
    slug=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
    if not slug or len(slug)>70: raise ValueError('Title cannot produce safe, short URL')
    return slug

def publish(root, output, now, base_url):
    root,output=Path(root),Path(output)
    source=json.loads((root/'config/independent.json').read_text(encoding='utf-8'))
    if source.get('schema_version')!=1 or not isinstance(source.get('resources'),list):
        raise ValueError('Invalid independent resource catalogue')
    items=[]; used=set()
    for resource in source['resources']:
        kind=resource.get('kind')
        slug=resource.get('slug') or slugify(resource.get('title',''))
        if kind not in KINDS or not SLUG.fullmatch(slug) or len(slug)>70:
            raise ValueError('Unsafe resource category or URL slug')
        rid=kind+'-'+slug; route=KINDS[kind]+'/'+slug
        if rid in used: raise ValueError('Duplicate permanent resource URL')
        used.add(rid)
        if resource.get('approved') is not True: continue
        try:
            when=dt.datetime.strptime(resource['published_at_ist'],'%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('Asia/Kolkata'))
        except (KeyError,ValueError,TypeError):
            raise ValueError('Invalid publish date: '+rid)
        if now<when: continue
        name=resource.get('file_name','')
        if not name or name!=Path(name).name or '/' in name or '\\' in name or Path(name).suffix.lower() not in EXTENSIONS:
            raise ValueError('Unsupported independent resource file: '+rid)
        file=root/'independent_source'/KINDS[kind]/slug/name
        if not file.is_file():
            print('Independent resource file not ready; holding',rid)
            continue
        checksum=hashlib.sha256(file.read_bytes()).hexdigest()
        if checksum!=resource.get('sha256'):
            raise ValueError('Resource SHA256 mismatch: '+rid)
        folder=output/'downloads'/route
        folder.mkdir(parents=True,exist_ok=True)
        shutil.copy2(file,folder/name)
        canonical=base_url+route+'/'
        cover=resource.get('cover_url','')
        if cover and not cover.startswith(base_url+'covers/'):
            raise ValueError('Cover must be hosted under the site covers folder')
        previews=resource.get('preview_images',[])[:4]
        if not isinstance(previews,list) or any(not isinstance(p,str) or not p.startswith(base_url+'covers/') for p in previews):
            raise ValueError('Preview images must be hosted in the site covers folder')
        item={
            'preview_images':previews,
            'id':rid,'kind':kind,'slug':slug,'title':resource['title'],
            'category':resource.get('category','General'),
            'description':resource.get('description',''),
            'highlights':resource.get('highlights',[])[:8],
            'cover_url':cover,'file_name':name,
            'file_type':EXTENSIONS[Path(name).suffix.lower()],
            'file_bytes':file.stat().st_size,
            'published_at_ist':resource['published_at_ist'],
            'release_at_ist':resource['published_at_ist'],
            'resource_url':base_url+'downloads/'+route+'/'+name,
            'page_url':canonical,'status':'live'
        }
        items.append(item)
        page=(root/'site/index.html').read_text(encoding='utf-8')
        page=page.replace('<head>','<head><base href="'+html.escape(base_url,quote=True)+'">',1)
        title=html.escape(item['title'],quote=True)
        description=html.escape(item['description'][:230],quote=True)
        page=page.replace('<title>Digital Pathshala · Free Learning Resources</title>','<title>'+title+' | Free Download | Digital Pathshala</title>',1)
        page=page.replace('Official free learning resource library for Digital Pathshala by Aaryaman Goenka. Download companion templates, guides and ZIP files for published YouTube videos.',description,1)
        meta='<meta property="og:type" content="article"><meta property="og:title" content="'+title+'"><meta property="og:description" content="'+description+'"><meta property="og:url" content="'+html.escape(canonical,quote=True)+'">'
        if cover:meta+='<meta property="og:image" content="'+html.escape(cover,quote=True)+'">'
        meta+='<link rel="canonical" href="'+html.escape(canonical,quote=True)+'">'
        page=page.replace('</head>',meta+'</head>',1)
        page_path=output/route/'index.html'
        page_path.parent.mkdir(parents=True,exist_ok=True)
        page_path.write_text(page,encoding='utf-8')
    items.sort(key=lambda v:(v['published_at_ist'],v['id']),reverse=True)
    (output/'independent.json').write_text(json.dumps({'resources':items},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Published independent resources:',len(items))
    return items
