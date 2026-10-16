"""Builds cascade/pages.json: the 13-page structure for the 2025 Cascade site.

Each page lists its Cascade sections (Columns = one WYSIWYG block, Accordion =
titled items). Images and PDFs are written as {{IMG:name}} / {{FILE:name}}
placeholders, swapped for real Cascade paths once the files are uploaded.
Every outside link is re-checked; list items whose link no longer works (or
that never had one after the first clean-up) are dropped, per Dr. Block's
"exclude any dead links".
"""
import json, re, html, subprocess, pathlib
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).parent
C = ROOT / 'content'
read = lambda p: (C / p).read_text()

def strip_h1(s):
    return re.sub(r'^\s*<h1>.*?</h1>', '', s, flags=re.S).strip()

def assets(s):
    s = re.sub(r'src="files/([^"]+)"', r'src="{{IMG:\1}}"', s)
    s = re.sub(r'href="files/([^"]+)"', r'href="{{FILE:\1}}"', s)
    return s

def tidy(s):
    s = re.sub(r'<p>\s*</p>|<li>\s*</li>', '', s)
    s = re.sub(r'<hr[^>]*>', '', s)
    s = s.replace('https://na01.safelinks.protection.outlook.com/?url=https%3A%2F%2Fwww.recreation.ucla.edu%2Fadaptiveprograms', 'https://recreation.ucla.edu/rec-programs/adaptive-recreation')
    s = re.sub(r'href="https://na01\.safelinks[^"]*"', 'href="https://recreation.ucla.edu/rec-programs/adaptive-recreation"', s)
    # Bold pseudo-headings become real headings (screen readers can navigate them)
    s = re.sub(r'<p><strong>([^<]{2,60}?):?</strong></p>', r'<h3>\1</h3>', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

# ── Program activities ──────────────────────────────────────────────────────
WORKSHOPS = ['team_building', 'self_advocacy__goal_setting', 'speaking_to_medical_professionals', 'assistive_technology',
             'sexuality__relationships', 'medication_management__substances_interactions', 'nutrition_and_skin_care',
             'bowel__bladder_maintenance']
ACTIVITIES = ['strength_and_conditioning', 'self_defense', 'meditation_tai_chi_yoga', 'sailing', 'kite_flying', 'handcycling',
              'kayaking', 'scuba', 'waterskiing', 'fishing', 'sled_hockey', 'court_sports']

def activity(slug):
    s = read(f'program_details/{slug}.html')
    title = html.unescape(re.search(r'<h1>(.*?)</h1>', s).group(1)).strip()
    return {'title': title, 'html': tidy(assets(strip_h1(s)))}

# ── Program Details overview ────────────────────────────────────────────────
pd = read('program_details/index.html')
seminars = re.search(r'<p><strong>Training Seminars</strong></p>(.*?)<p>Click on one', pd, re.S).group(1)
rec = re.search(r'<p><strong>Recreational Activities</strong><br/>(.*?)<p>Click on one', pd, re.S | re.M)
rec_html = '<p>' + rec.group(1)
interviews = ''
for n, vid in zip(range(1, 5), ['NS7YQLjEHns', 'fHvvLm5WJYA', 'qe-34a_vMZA', '_AqgVgwvLfQ']):
    interviews += (f'<tr><td><img src="{{{{IMG:interview{n}.jpg}}}}" alt="Portrait of interview participant {n}." width="100" height="100"></td>'
                   f'<th scope="row">Interview {n}</th>'
                   f'<td><a href="https://www.youtube.com/watch?v={vid}">Watch on YouTube</a></td>'
                   f'<td><a href="{{{{FILE:Interview-{n}.pdf}}}}">Read the transcript (PDF)</a></td></tr>')
program_overview = tidy(assets(
    '<p>Project Shake-It-Up ran ten day-long sessions. Mornings were spent in health promotion and independent living '
    'training seminars, and afternoons in adaptive physical and recreational activities, all designed and led by people '
    'with disabilities using a peer-mentoring model.</p>'
    '<h2>Training seminars</h2>' + seminars +
    '<p><a href="/program-details/workshops">Explore the eight training seminars</a></p>'
    '<h2>Recreational activities</h2>' + rec_html +
    '<p><a href="/program-details/physical-and-recreational-activities">Explore the twelve physical and recreational activities</a></p>'
    '<h2>Participant interviews</h2>'
    '<p>Four participants shared their experiences of the program. Each interview is available as a video and as a written transcript.</p>'
    '<table><caption>Participant interviews</caption><thead><tr><th scope="col">Photo</th><th scope="col">Interview</th>'
    '<th scope="col">Video</th><th scope="col">Transcript</th></tr></thead><tbody>' + interviews + '</tbody></table>'))
program_overview = re.sub(r'<a href="https://healthtechnology[^"]*">(<img[^>]*>)</a>', r'\1', program_overview)

# ── Home, findings, resources ───────────────────────────────────────────────
home_src = read('index.html')
intro_end = home_src.find('<p><strong>Demographics</strong></p>')
links_start = home_src.find('<p><strong>Useful links and phone numbers</strong></p>')
home_intro = tidy(assets(home_src[:intro_end]))
home_intro = re.sub(r'<p><img src="\{\{IMG:diagram.gif\}\}"[^>]*></p>', '', home_intro)
findings = tidy(assets(
    '<p>Results from Project Shake-It-Up, a non-randomized clinical trial of a health promotion and capacity-building '
    'program for people with spinal cord injuries and related neurological disabilities.</p>'
    + home_src[intro_end:links_start]))
diagram = re.search(r'<img src="files/diagram.gif" alt="([^"]*)"', home_src).group(1)
model = (f'<h2>Program model</h2><p><img src="{{{{IMG:diagram.gif}}}}" alt="{html.escape(diagram, quote=True)}" width="372" height="390"></p>'
         f'<p>{html.escape(diagram)}</p>')

# Resources: re-check each link, group the lists by topic
links_html = home_src[links_start:]
lists = re.findall(r'<ul>(.*?)</ul>', links_html, re.S)
groups = ['Health, disability and rehabilitation', 'Women’s health', 'Government and rural services',
          'Self-defence', 'Travel, sports and recreation', 'Rehabilitation centres and resource guides',
          'Employment, education and adaptive programs', 'Rhode Island contacts (phone)']
urls = set(re.findall(r'href="(https?://[^"]+)"', links_html))

def check(u):
    out = subprocess.run(['curl', '-s', '-o', '/dev/null', '-L', '-m', '20', '-A',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36',
                          '-w', '%{http_code}', u], capture_output=True, text=True).stdout
    return u, out

with ThreadPoolExecutor(12) as ex:
    status = dict(ex.map(check, urls))
alive = lambda u: status.get(u, '0')[:1] in '23' or status.get(u) in ('403', '999', '429')

resource_items, removed = [], []
for title, ul in zip(groups, lists):
    items = []
    for li in re.findall(r'<li>(.*?)</li>', ul, re.S):
        m = re.search(r'href="([^"]+)"', li)
        if m:
            if alive(m.group(1)):
                items.append(li)
            else:
                removed.append((re.sub('<[^>]+>', '', li), m.group(1), status.get(m.group(1))))
        elif re.search(r'\d{3}-\d{4}', li):  # phone numbers are content, not links
            items.append(li)
        else:
            removed.append((li, '(link already removed as dead)', ''))
    if items:
        resource_items.append({'title': title, 'html': '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'})
resources_intro = ('<p>Organizations and information for people with spinal cord injuries, multiple sclerosis and related '
                   'neurological disabilities, gathered during Project Shake-It-Up (2002–2005). This is an archival list: '
                   'every link was checked in October 2026, and links that no longer work have been removed.</p>')

# ── About, team, publications ───────────────────────────────────────────────
about = ('<p>This website is owned by:</p>'
         '<p><strong>Pamela Block, Ph.D.</strong><br>Professor, Department of Anthropology<br>Western University<br>'
         'Social Science Centre, Room 3425<br>London, ON, Canada<br>519-661-2111 ext. 85077<br>'
         'Email: <a href="mailto:pblock@uwo.ca">pblock@uwo.ca</a></p>'
         '<p>Fellow of the Society for Applied Anthropology<br>2009–2010 President, Society for Disability Studies (ex officio in 2010–2011)</p>'
         '<h2>About this archive</h2>'
         '<p><strong>This is an archival website, made available to share resources and disseminate the products and results of '
         'the NIDRR grant entitled “Project Shake It Up! Health Promotion and Capacity Building for persons with Traumatic '
         'Spinal Cord Injury and other Neuromuscular Disability” (2002–2005).</strong> We will not be adding new resource '
         'links; however, please <a href="mailto:pblock@uwo.ca">contact us</a> if any of the links do not work.</p>')

team_raw = [('Pamela Block, PhD', 'Co-Principal Investigator', None),
            ('Sarah Everhart Skeels, MPH', 'Co-Principal Investigator', 'https://ase.tufts.edu/occupationalTherapy/people/skeels.htm'),
            ('James H. Rimmer, PhD', 'Co-Principal Investigator', None),
            ('Chris Keys, PhD', 'Senior Consultant', None),
            ('Erin Bean, CTRS', 'Data Collector, Activities Facilitator', 'https://www.linkedin.com/in/erin-bean-a20336b'),
            ('Jennifer Catrambone, CTRS', 'Activities Facilitator', 'https://www.linkedin.com/in/jenny-catrambone-663a6b1a'),
            ('Kristy Hart, BSPT', 'Physical Therapist, Activities Facilitator', None),
            ('Paul Choquette, MA', '', 'https://www.linkedin.com/in/paul-choquette-2ab3877'),
            ('Matt Sullivan', 'Data Collector, Case Coordinator', 'https://www.facebook.com/matt.sullivan.1401'),
            ('Elizabeth Vanner, MS', '', None),
            ('Francis Sparadeo, PhD', 'Workshop Facilitator', 'https://www.psychologytoday.com/us/therapists/frank-r-sparadeo-west-warwick-ri/61170')]
volunteers = [('Lisa Colaco Valentine', 'https://www.bcm.edu/people/view/lisa-valentine-m-d/b16aae27-ffed-11e2-be68-080027880ca6'),
              ('Belinda Marshall', 'https://www.facebook.com/belinda.r.marshall'), ('Molly Hostetler', None),
              ('Leslie Koren', 'https://www.instagram.com/ljkoren/'), ('Johanna Chang', 'https://www.rchsd.org/doctors/johanna-chang-md/')]
with ThreadPoolExecutor(8) as ex:
    status.update(dict(ex.map(check, [u for _, _, u in team_raw if u] + [u for _, u in volunteers if u])))
name = lambda n, u: f'<a href="{u}">{n}</a>' if u and alive(u) else n
team = ('<h2>Research team</h2><ul>' + ''.join(f'<li><strong>{name(n, u)}</strong>{" — " + r if r else ""}</li>' for n, r, u in team_raw)
        + '</ul><h2>Student volunteers</h2><ul>' + ''.join(f'<li>{name(n, u)}</li>' for n, u in volunteers) + '</ul>')

pub_index = tidy(assets(strip_h1(read('publications/index.html'))))
pub_index = (pub_index.replace('/publications/project_abstract.html', '/publications/project-abstract')
             .replace('/publications/health_promotion_and_capacity_building.html', '/publications/health-promotion-and-capacity-building')
             .replace('/publications/participatory_intervention_research.html', '/publications/participatory-intervention-research')
             .replace('/publications/research_paper.html', '/publications/research-paper'))
pub = lambda f: tidy(assets(strip_h1(read(f'publications/{f}.html'))))

pages = [
    {'key': 'home', 'existing': 'index', 'title': 'Project Shake-It-Up', 'sections': [
        {'type': 'Columns', 'html': home_intro},
        {'type': 'Columns', 'html': model}]},
    {'key': 'about', 'folder': 'about-us', 'title': 'About Us', 'sections': [{'type': 'Columns', 'html': about}]},
    {'key': 'program', 'folder': 'program-details', 'title': 'Program Details', 'sections': [{'type': 'Columns', 'html': program_overview}]},
    {'key': 'workshops', 'parent': 'program-details', 'name': 'workshops', 'title': 'Training Seminars', 'sections': [
        {'type': 'Columns', 'html': '<p>Training seminars provided educational information, skills training and peer support in independent living and health promotion. Select a seminar to read its objectives, plan, staffing, site criteria and resources.</p>'},
        {'type': 'Accordion', 'items': [activity(s) for s in WORKSHOPS]}]},
    {'key': 'activities', 'parent': 'program-details', 'name': 'physical-and-recreational-activities', 'title': 'Physical and Recreational Activities', 'sections': [
        {'type': 'Columns', 'html': '<p>Participants took part in adaptive indoor and outdoor physical and recreational activities. Select an activity to read its objectives, plan, staffing, site criteria, equipment and resources.</p>'},
        {'type': 'Accordion', 'items': [activity(s) for s in ACTIVITIES]}]},
    {'key': 'findings', 'folder': 'research-findings', 'title': 'Research Findings', 'sections': [{'type': 'Columns', 'html': findings}]},
    {'key': 'publications', 'folder': 'publications', 'title': 'Publications', 'sections': [{'type': 'Columns', 'html': pub_index}]},
    {'key': 'pub-abstract', 'parent': 'publications', 'name': 'project-abstract', 'title': 'Project Abstract', 'sections': [{'type': 'Columns', 'html': pub('project_abstract')}]},
    {'key': 'pub-health', 'parent': 'publications', 'name': 'health-promotion-and-capacity-building', 'title': 'Health Promotion and Capacity Building', 'sections': [{'type': 'Columns', 'html': pub('health_promotion_and_capacity_building')}]},
    {'key': 'pub-par', 'parent': 'publications', 'name': 'participatory-intervention-research', 'title': 'Participatory Intervention Research', 'sections': [{'type': 'Columns', 'html': pub('participatory_intervention_research')}]},
    {'key': 'pub-paper', 'parent': 'publications', 'name': 'research-paper', 'title': 'Research Paper', 'sections': [{'type': 'Columns', 'html': pub('research_paper')}]},
    {'key': 'resources', 'folder': 'resources', 'title': 'Resources', 'sections': [
        {'type': 'Columns', 'html': resources_intro}, {'type': 'Accordion', 'items': resource_items}]},
    {'key': 'team', 'folder': 'the-team', 'title': 'The Shake-It-Up Team', 'sections': [{'type': 'Columns', 'html': team}]},
]

out = ROOT / 'cascade'
out.mkdir(exist_ok=True)
(out / 'pages.json').write_text(json.dumps(pages, indent=1, ensure_ascii=False))
used = sorted(set(re.findall(r'\{\{(?:IMG|FILE):([^}]+)\}\}', json.dumps(pages))))
(out / 'files.json').write_text(json.dumps(used, indent=1))
(out / 'removed.json').write_text(json.dumps(removed, indent=1, ensure_ascii=False))
words = sum(len(re.sub('<[^>]+>', ' ', json.dumps(p)).split()) for p in pages)
print(f'{len(pages)} pages, {len(used)} files used, {len(resource_items)} resource groups, {len(removed)} resource entries dropped, ~{words} words')
for r in removed: print('  dropped:', r)
