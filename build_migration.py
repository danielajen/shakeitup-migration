"""Builds the shakeitup.uwo.ca migration package for Western's Cascade template.

Pulls every page's main content from the live site, removes dead links (keeping
the organization names and phone numbers), fixes accessibility issues, downloads
images and PDFs, and writes:
  content/<section>/<page>.html  paste-ready content for each Cascade page
  files/                         images and PDFs to upload to Cascade
  preview/                       a local preview of the migrated site
  LINK-REPORT.md                 every link removed, fixed, or flagged
"""
import json, re, ssl, sys, html, urllib.request, os, pathlib
from urllib.parse import urljoin, urlparse, unquote

ROOT = pathlib.Path(__file__).parent
SITE = 'https://shakeitup.uwo.ca/'
ctx = ssl._create_unverified_context()
UA = {'User-Agent': 'Mozilla/5.0'}
crawl = json.load(open(sys.argv[1]))
recheck = json.load(open(sys.argv[2]))

def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u.replace(' ', '%20'), headers=UA), context=ctx, timeout=30).read()

# ── classify every external link ────────────────────────────────────────────
DEAD, KEEP, FIX = {}, {}, {}
for u, v in recheck.items():
    if v == 'ok' or v.startswith('file'):
        continue
    code, _, final = v.partition(' -> ')
    if code in ('403', '401', '999') and 'linkedin' in u or code in ('403',) and any(k in u for k in ('cheapoair', 'umassmed', 'zocdoc')):
        KEEP[u] = f'{code}: site blocks automated checks — opens in a browser'
    elif code == '200' and final and final != u:
        FIX[u] = final
    elif 'safelinks.protection.outlook.com' in u:
        FIX[u] = 'https://www.als.org/als-care/resources'
    else:
        reason = {'404': 'page no longer exists', '000': 'website no longer exists'}.get(code, f'returns {code}')
        if 'reddragonbrewery' in final: reason = 'domain now belongs to an unrelated business'
        if 'lost-and-found' in final: reason = 'redirects to a “page not found” page'
        if 'homeadvisor' in u: reason = 'redirects to an advertising page'
        if 'wheelchairnet' in u or 'craighospital' in u: reason = 'redirect loop — page does not load'
        if 'ncpad.org' in u: reason = 'old NCPAD site, now login-only (successor: nchpad.org)'
        DEAD[u] = reason


# Image descriptions written for the migration (the old site's were empty or just file names).
ALT = {
    'diagram.gif': 'Project Shake-It-Up program model. At the centre: peer support, capacity building, and social networks. Around it, four linked areas: recreation and physical activity (fitness and leisure; nutrition and skin care), independent living and case coordination (setting goals; strength and conditioning; problem solving; developing life skills; self-advocacy), and health promotion (adaptive equipment; talking to medical professionals; alcohol and substance use reduction). Arrows connect them as healthy living, independent living, and individualized, self-directed programs.',
    'training.jpg': 'Participants, several using power wheelchairs, sit in a semicircle outdoors following a seated exercise led by an instructor.',
    'recreation.jpg': 'A group of participants, some in wheelchairs, gather in a parking lot by a lawn before an outdoor activity.',
    'kayaking.jpg': 'A participant paddles a yellow kayak on a harbour, with sailboats and motorboats in the background.',
    'kayak3.jpg': 'A smiling participant in a life jacket and sunglasses sits in a blue kayak holding a paddle.',
    'sailing.jpg': 'An adaptive sailboat with a Shake-A-Leg sail carries several people across a bay.',
    'handcycling2.jpg': 'A smiling woman in a wheelchair tries an arm-powered exercise cycle outdoors while a young man stands beside her.',
    'handcycling3.jpg': 'A participant rides a low, three-wheeled hand cycle around an indoor running track.',
    'wheelchairbasketball.jpg': 'Players in sports wheelchairs move across an indoor court during a wheelchair basketball game.',
    'interview1.jpg': 'Portrait of interview participant 1.',
    'interview2.jpg': 'Portrait of interview participant 2.',
    'interview3.jpg': 'Portrait of interview participant 3.',
    'interview4.jpg': 'Portrait of interview participant 4.',
}

# Same organization, new address (each checked and loading in October 2026).
SUCCESSORS = {
    'http://www.mdausa.org/': 'https://www.mda.org/',
    'http://www.ncpad.org/': 'https://www.nchpad.org/',
    'http://familydoctor.org/familydoctor/en/diseases-conditions/multiple-sclerosis.html': 'https://familydoctor.org/condition/multiple-sclerosis/',
}
for old, new in SUCCESSORS.items():
    DEAD.pop(old, None)
    FIX[old] = new

URLISH = re.compile(r'^(https?://|www\.)|\.(org|com|net|edu|gov|info)(/|$)', re.I)

def clean(content, page_url, removed, fixed):
    # dead links: drop the link; drop link text too when it is just the address
    def link(m):
        attrs, text = m.group(1), m.group(2)
        hm = re.search(r'href="([^"]*)"', attrs)
        if not hm: return text
        href = urljoin(page_url, html.unescape(hm.group(1)))
        plain = re.sub('<[^>]+>', '', text).strip()
        if href in DEAD:
            removed.append((page_url, plain or href, href, DEAD[href]))
            return '' if (not plain or URLISH.search(plain)) else text
        if href in FIX:
            fixed.append((page_url, href, FIX[href]))
            href = FIX[href]
            if URLISH.search(plain): text = re.sub(r'https?://', '', href).rstrip('/')
        if not plain and '<img' not in text:
            return ''  # empty link: invisible to everyone, confusing for screen readers
        p = urlparse(href)
        if p.netloc == 'shakeitup.uwo.ca' and not re.search(r'\.(pdf|jpg|png)$', p.path, re.I):
            href = '/' + p.path.lstrip('/')
        elif p.netloc == 'shakeitup.uwo.ca':
            href = 'files/' + unquote(os.path.basename(p.path)).replace(' ', '-')
        label = ' (PDF)' if href.lower().endswith('.pdf') and 'pdf' not in plain.lower() else ''
        return f'<a href="{html.escape(href, quote=True)}">{text}{label}</a>'
    content = re.sub(r'<a\b([^>]*)>(.*?)</a>', link, content, flags=re.S)
    content = re.sub(r'<a name="[^"]*"></a>', '', content)
    # images → local files, keep alt
    def img(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        alt = re.search(r'alt="([^"]*)"', tag)
        name = unquote(os.path.basename(urlparse(urljoin(page_url, src)).path)).replace(' ', '-')
        text = ALT.get(name, alt.group(1) if alt else '')
        return f'<img src="files/{name}" alt="{html.escape(text, quote=True)}">'
    content = re.sub(r'<img\b[^>]*>', img, content)
    content = re.sub(r'\s(class|style|target|rel)="[^"]*"', '', content)
    content = content.replace('<span>&#160;</span>', ' ').replace('&#160;', ' ')
    content = re.sub(r'<p>\s*</p>', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()

pages, removed, fixed = [], [], []
assets = set()
for url in crawl['pages']:
    if url.rstrip('/') == SITE.rstrip('/') and url != SITE: continue
    if url.endswith('/index.html') and url[:-10] in crawl['pages'] and url != SITE + 'index.html': pass
    if url == SITE + 'index.html': continue
    raw = fetch(url).decode('utf-8', 'ignore')
    m = re.search(r'<div class="grid_9">\s*(.*?)<!--10 extra', raw, re.S) or re.search(r'<div class="grid_9">\s*(.*?)</div>\s*<!--end div grid_9', raw, re.S)
    body = m.group(1) if m else ''
    for a in re.findall(r'(?:src|href)="([^"]+\.(?:jpe?g|png|gif|pdf))"', body, re.I):
        full = urljoin(url, html.unescape(a))
        if urlparse(full).netloc == 'shakeitup.uwo.ca':
            assets.add(full)
    title = re.sub('<[^>]+>', '', (re.search(r'<h1>(.*?)</h1>', body, re.S) or re.search(r'<h2>(.*?)</h2>', body, re.S) or [None, 'Home'])[1]).strip()
    path = urlparse(url).path or '/'
    if path.endswith('/'): path += 'index.html'
    pages.append({'url': url, 'path': path, 'title': html.unescape(title) or 'Shake It Up!', 'html': clean(body, url, removed, fixed)})

(ROOT / 'files').mkdir(exist_ok=True)
for a in sorted(assets):
    name = unquote(os.path.basename(urlparse(a).path)).replace(' ', '-')
    try: (ROOT / 'files' / name).write_bytes(fetch(a))
    except Exception as e: print('could not download', a, e)

for p in pages:
    out = ROOT / 'content' / p['path'].lstrip('/')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(p['html'] + '\n')

json.dump([{k: v for k, v in p.items()} for p in pages], open(ROOT / 'pages.json', 'w'), indent=1)
json.dump({'removed': removed, 'fixed': fixed, 'kept': KEEP}, open(ROOT / 'links.json', 'w'), indent=1)
print(len(pages), 'pages,', len(assets), 'files,', len(removed), 'dead links removed,', len(fixed), 'links fixed,', len(KEEP), 'kept (bot-blocked)')
