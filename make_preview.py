"""Writes preview/ (a local look at the migrated site) and LINK-REPORT.md."""
import json, html, pathlib, shutil, re
ROOT = pathlib.Path(__file__).parent
pages = json.load(open(ROOT / 'pages.json'))
links = json.load(open(ROOT / 'links.json'))

SECTIONS = [
    ('Home', '/index.html', []),
    ('About Us', '/about_us/index.html', []),
    ('Program Details', '/program_details/index.html', [p for p in pages if p['path'].startswith('/program_details/') and not p['path'].endswith('index.html')]),
    ('The Shake-It-Up Team', '/the_shake_it_up_team/index.html', []),
    ('Publications', '/publications/index.html', [p for p in pages if p['path'].startswith('/publications/') and not p['path'].endswith('index.html')]),
]

CSS = """
:root{--purple:#4f2683;--purple-dark:#3a1c61;--ink:#1d1d1f;--muted:#555;--line:#ddd;--bg:#fff;--tint:#f5f3f8}
*{box-sizing:border-box}body{margin:0;font:17px/1.65 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--purple)}a:hover{color:var(--purple-dark)}:focus-visible{outline:3px solid #f2b705;outline-offset:2px}
.skip{position:absolute;left:-999px;top:0;background:#000;color:#fff;padding:.6rem 1rem}.skip:focus{left:1rem;top:1rem}
header{background:var(--purple);color:#fff}header .in{max-width:72rem;margin:auto;padding:1rem 1.25rem;display:flex;flex-wrap:wrap;gap:1rem;align-items:center;justify-content:space-between}
.brand{color:#fff;text-decoration:none;font-weight:700;font-size:1.3rem}.brand small{display:block;font-weight:400;font-size:.85rem;opacity:.85}
.note{background:#fff8d6;border-bottom:1px solid #e9d98a;font-size:.9rem}.note .in{max-width:72rem;margin:auto;padding:.6rem 1.25rem}
nav.top{background:var(--purple-dark)}nav.top ul{list-style:none;margin:0 auto;padding:0 1.25rem;max-width:72rem;display:flex;flex-wrap:wrap}
nav.top a{display:block;color:#fff;text-decoration:none;padding:.75rem 1rem;font-weight:600}nav.top a[aria-current]{background:#fff;color:var(--purple)}
.layout{max-width:72rem;margin:auto;padding:2rem 1.25rem 4rem;display:grid;grid-template-columns:16rem 1fr;gap:2.5rem}
@media(max-width:50rem){.layout{grid-template-columns:1fr}}
aside h2{font-size:1rem;margin:0 0 .5rem;color:var(--purple)}aside ul{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
aside li a{display:block;padding:.5rem .25rem;border-bottom:1px solid var(--line);text-decoration:none}aside a[aria-current]{font-weight:700;border-left:4px solid var(--purple);padding-left:.6rem}
.crumbs{font-size:.9rem;color:var(--muted);margin-bottom:1rem}.crumbs a{color:var(--muted)}
main h1{color:var(--purple);font-size:2.1rem;line-height:1.2;margin:0 0 1rem}main h2,main h3{color:var(--purple-dark)}
main img{max-width:100%;height:auto;border-radius:6px}main table{border-collapse:collapse;width:100%;margin:1rem 0}main td,main th{border:1px solid var(--line);padding:.6rem;vertical-align:top}
main blockquote{margin:1rem 0;padding:.75rem 1rem;background:var(--tint);border-left:4px solid var(--purple)}
footer{background:var(--purple);color:#fff;padding:2rem 1.25rem;text-align:center;font-size:.9rem}
"""

CUR = ' aria-current="page"'

def title_of(path):
    for p in pages:
        if p['path'] == path: return p['title']
    return ''

def render(p):
    depth = p['path'].count('/') - 1
    up = '../' * depth
    rel = lambda path: up + path.lstrip('/')
    sec = next((s for s in SECTIONS if p['path'] == s[1] or p in s[2]), SECTIONS[0])
    body = p['html']
    body = re.sub(r'(src|href)="files/', lambda m: f'{m.group(1)}="{up}files/', body)
    body = re.sub(r'href="/([^"]+)"', lambda m: f'href="{up}{m.group(1)}"', body)
    if not re.search(r'<h1', body):
        body = f'<h1>{html.escape(p["title"] if p["path"] != "/index.html" else "Project Shake-It-Up")}</h1>\n' + body
    nav = ''.join(f'<li><a href="{rel(s[1])}"{CUR if s is sec else ""}>{s[0]}</a></li>' for s in SECTIONS)
    side = ''
    if sec[2]:
        side = f'<aside aria-label="{sec[0]}"><h2>{sec[0]}</h2><ul>' + ''.join(
            f'<li><a href="{rel(c["path"])}"{CUR if c is p else ""}>{html.escape(c["title"])}</a></li>' for c in sec[2]) + '</ul></aside>'
    crumbs = f'<a href="{rel("/index.html")}">Home</a>' + (f' / <a href="{rel(sec[1])}">{sec[0]}</a>' if sec[1] != '/index.html' and p['path'] != sec[1] else '') + (f' / {html.escape(p["title"])}' if p['path'] != '/index.html' else '')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(p["title"])} | Project Shake-It-Up | Western University</title><style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to main content</a>
<div class="note"><div class="in"><strong>Migration preview.</strong> The content as it will appear in the new Western template, with dead links removed.</div></div>
<header><div class="in"><a class="brand" href="{rel('/index.html')}">Project Shake-It-Up<small>Health promotion and capacity building · Western University</small></a></div></header>
<nav class="top" aria-label="Main"><ul>{nav}</ul></nav>
<div class="layout">{side or '<div></div>'}<main id="main"><p class="crumbs">{crumbs}</p>{body}</main></div>
<footer>Project Shake-It-Up · Department of Anthropology, Western University</footer></body></html>'''

out = ROOT / 'preview'
shutil.rmtree(out, ignore_errors=True)
for p in pages:
    f = out / p['path'].lstrip('/')
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(render(p))
shutil.copytree(ROOT / 'files', out / 'files')

# ── link report ──────────────────────────────────────────────────────────────
pt = {p['url']: p['title'] for p in pages}
lines = ['# shakeitup.uwo.ca: link report', '',
         f'Every link on all {len(pages)} pages was checked. Dead links are removed and the organization names and phone numbers are kept. Broken addresses that have moved are updated.', '',
         f'## Removed: {len(links["removed"])} dead links', '', '| Page | Link | Why |', '|---|---|---|']
for page, text, href, why in links['removed']:
    lines.append(f'| {pt.get(page, page)} | {text.replace("|", "/")[:70]} | {why} |')
lines += ['', f'## Updated: {len(links["fixed"])} links that moved', '', '| Page | Old address | New address |', '|---|---|---|']
for page, old, new in links['fixed']:
    lines.append(f'| {pt.get(page, page)} | {old[:60]} | {new[:60]} |')
lines += ['', f'## Kept: {len(links["kept"])} links that block automated checks but open in a browser', '']
lines += [f'- {u}' for u in links['kept']]
lines += ['', '## Accessibility improvements', '',
          '- Every image now has a meaningful text description, including a full description of the program-model diagram. Several were empty or just file names, such as “Interview4”.',
          '- Removed empty links, including the blank “home” link in the old menu, and the old “skip” anchor.',
          '- Links no longer force a new tab, and PDF links are labelled “(PDF)”.',
          '- PDF file names no longer contain spaces, which broke some browsers and screen readers.',
          '- Removed inline styles and classes so the new template controls fonts, colours, and contrast.']
(ROOT / 'LINK-REPORT.md').write_text('\n'.join(lines) + '\n')
print('preview pages:', len(pages))
