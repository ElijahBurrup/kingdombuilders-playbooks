"""Update archive grid:
- Remove Length and Price columns
- Add Free column (Yes/No)
- Show multiple category chips per row
- Fix Clear all filters readability
"""
import re
import sys
sys.path.insert(0, '.')
from playbook_registry import SLUG_TO_FILE
from pathway_definitions import NEAREST_PATHWAY, get_playbook_position_in_pathway

PATH_SHORT = {
    'work-reset': 'Work Reset', 'identity-walk': 'Identity Walk', 'ai-age': 'AI Age',
    'money-architecture': 'Money', 'resilience-stack': 'Resilience',
    'inner-battle': 'Inner Battle', 'family-foundation': 'Family',
    'strategist-toolkit': 'Strategist', 'process-model': 'Process Model',
}
SERIES_NAMES = {
    'how-ai-works': 'How AI Works', 'ai-economy': 'AI Economy',
    'a-process-model': 'A Process Model', 'eden-pattern': 'Eden Pattern',
    'the-attending': 'Stay Series', 'manna': 'Manna',
    'lay-it-down': 'Lay It Down', 'dad-talks': 'Dad Talks',
    'the-shield-series': 'Shield Series', 'the-mirror-series': 'Mirror Series',
}
PILLAR_LABEL = {
    'faith': 'Faith', 'health': 'Health', 'wealth': 'Wealth',
    'spiritual': 'Spiritual', 'identity': 'Identity',
    'relationships': 'Relationships', 'mental': 'Mental',
    'systems': 'Systems', 'money': 'Money', 'productivity': 'Productivity',
}

with open('static/archive-original.html.bak', encoding='utf-8') as f:
    cat = f.read()

card_pat = re.compile(
    r'<a href="read/(?P<slug>[\w-]+)" class="card"(?P<attrs>[^>]*)>(?P<inner>.*?)</a>',
    re.DOTALL,
)
playbooks = {}
for m in card_pat.finditer(cat):
    slug = m.group('slug')
    inner, attrs = m.group('inner'), m.group('attrs')
    title_m = re.search(r'class="card-title">([^<]+)</div>', inner)
    sub_m = re.search(r'class="card-subtitle">([^<]+)</div>', inner)
    tag_m = re.search(r'class="card-tag[\s\w-]*">([^<]+)</span>', inner)
    series_m = re.search(r'data-series="([^"]+)"', attrs)
    pillar_m = re.search(r'data-pillar="([^"]+)"', attrs)
    sub_attr_m = re.search(r'data-sub="([^"]+)"', attrs)
    free = 'data-free="true"' in attrs

    primary_cat = tag_m.group(1).strip() if tag_m else '—'
    pillars = pillar_m.group(1).split() if pillar_m else []
    subs = sub_attr_m.group(1).split() if sub_attr_m else []
    categories = [primary_cat]
    for p in pillars + subs:
        label = PILLAR_LABEL.get(p, p.title())
        if label not in categories and label != '—':
            categories.append(label)

    playbooks[slug] = dict(
        title=title_m.group(1).strip() if title_m else slug,
        sub=sub_m.group(1).strip() if sub_m else '',
        categories=categories,
        series=series_m.group(1) if series_m else '',
        free=free,
    )

with open('static/archive.html', encoding='utf-8') as f:
    html = f.read()

# Replace THEAD
old_thead_m = re.search(r'<thead><tr>.*?</tr></thead>', html, flags=re.DOTALL)
new_thead = '''<thead><tr>
      <th data-col="title"><div class="th-head">Title <span class="sort-arrow">&#9650;</span></div></th>
      <th data-col="pathway" class="filterable"><div class="th-head">Pathway <span class="sort-arrow">&#9650;</span><button class="filter-btn" aria-label="Filter pathway"><svg viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg></button></div></th>
      <th data-col="series" class="filterable"><div class="th-head">Series <span class="sort-arrow">&#9650;</span><button class="filter-btn" aria-label="Filter series"><svg viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg></button></div></th>
      <th data-col="category" class="filterable"><div class="th-head">Category <span class="sort-arrow">&#9650;</span><button class="filter-btn" aria-label="Filter category"><svg viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg></button></div></th>
      <th data-col="free" class="filterable"><div class="th-head">Free <span class="sort-arrow">&#9650;</span><button class="filter-btn" aria-label="Filter free"><svg viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg></button></div></th>
      <th data-col="status" class="filterable"><div class="th-head">Status <span class="sort-arrow">&#9650;</span><button class="filter-btn" aria-label="Filter status"><svg viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg></button></div></th>
    </tr></thead>'''
html = html.replace(old_thead_m.group(0), new_thead)

# Regenerate rows
rows = []
for slug in sorted(SLUG_TO_FILE.keys()):
    pb = playbooks.get(slug)
    if not pb:
        continue
    pathway = NEAREST_PATHWAY.get(slug, '')
    if pathway:
        pos = get_playbook_position_in_pathway(slug, pathway)
        step_label = (
            f"{PATH_SHORT.get(pathway, '')} · {pos[0]}"
            if pos
            else f"{PATH_SHORT.get(pathway, '')} · Rel"
        )
        pathway_cell = f'<span class="pa-chip {pathway}">{step_label}</span>'
    else:
        pathway_cell = '<span class="pa-chip" style="background:#eee;color:#888">&mdash;</span>'

    series_name = SERIES_NAMES.get(
        pb['series'], '—' if not pb['series'] else pb['series']
    )
    free_data = 'yes' if pb['free'] else 'no'
    free_html = (
        '<span class="free-yes">&#10003; Free</span>'
        if pb['free']
        else '<span class="free-no">&mdash;</span>'
    )

    cat_chips = ' '.join(
        f'<span class="cat-chip">{c}</span>' for c in pb['categories']
    )

    title_html = pb['title']
    sub_html = f'<em>{pb["sub"]}</em>' if pb['sub'] else ''

    row = (
        f'<tr data-pathway="{pathway}" data-series="{series_name}" '
        f'data-category="{pb["categories"][0]}" data-free="{free_data}" '
        f'data-status="not-started">'
        f'<td class="cell-title"><a href="read/{slug}">{title_html}{sub_html}</a></td>'
        f'<td>{pathway_cell}</td>'
        f'<td>{series_name}</td>'
        f'<td class="cell-cats">{cat_chips}</td>'
        f'<td class="cell-free">{free_html}</td>'
        f'<td><span class="status-chip status-not-started">Not Started</span></td>'
        f'</tr>'
    )
    rows.append(row)

new_body = '\n      '.join(rows)
html = re.sub(
    r'<tbody id="table-body">.*?</tbody>',
    f'<tbody id="table-body">\n      {new_body}\n    </tbody>',
    html, flags=re.DOTALL,
)

# Update clear-filters CSS
old_clear = (
    '.clear-filters{font-family:\'Poppins\',sans-serif;font-size:0.66rem;'
    'font-weight:700;letter-spacing:1px;text-transform:uppercase;'
    'color:var(--rose);background:transparent;border:none;cursor:pointer;'
    'padding:6px 10px;transition:color 0.2s}'
)
new_clear = (
    '.clear-filters{font-family:\'Poppins\',sans-serif;font-size:0.7rem;'
    'font-weight:700;letter-spacing:1.2px;text-transform:uppercase;'
    'color:var(--dawn);background:var(--cream);border:1px solid var(--cream-deep);'
    'border-radius:50px;cursor:pointer;padding:7px 14px;transition:all 0.2s}'
)
html = html.replace(old_clear, new_clear)
html = html.replace(
    '.clear-filters:hover{color:var(--text)}',
    '.clear-filters:hover{background:var(--rose);color:var(--white);border-color:var(--rose)}',
)
html = html.replace(
    '.clear-filters:disabled{opacity:0.35;cursor:not-allowed}',
    '.clear-filters:disabled{opacity:0.4;cursor:not-allowed;background:transparent;'
    'color:var(--text-muted);border-color:var(--cream-deep)}',
)

# Add CSS for new column styles
new_css = (
    '\n.cell-cats{min-width:160px}'
    '\n.cell-cats .cat-chip{margin-right:5px;margin-bottom:4px;display:inline-block}'
    '\n.cell-free{text-align:center;white-space:nowrap}'
    '\n.free-yes{display:inline-block;padding:4px 12px;border-radius:30px;'
    'background:rgba(45,138,78,0.12);color:#1E7E34;'
    'font-family:\'Poppins\',sans-serif;font-size:0.62rem;font-weight:800;'
    'letter-spacing:1.2px;text-transform:uppercase;'
    'border:1px solid rgba(45,138,78,0.2)}'
    '\n.free-no{color:var(--text-muted);font-family:\'Poppins\',sans-serif;'
    'font-size:1rem;font-weight:500}'
)
if '.cell-cats{' not in html:
    html = html.replace('</style>', new_css + '\n</style>', 1)

# Update PRETTY map in JS for free=yes/no values
html = html.replace(
    "'free':'Free','paid':'Paid',",
    "'yes':'Free','no':'Not Free',",
)

# Auto-update the global playbook count wherever it appears.
# Without this, the archive shows N rows but the counter still says N-1
# from the previous build, and the catalog feels out of sync after
# every new playbook ships.
total = len(rows)
html = re.sub(
    r'(Showing <strong id="row-count">)\d+(</strong> of <strong>)\d+(</strong>)',
    rf'\g<1>{total}\g<2>{total}\g<3>',
    html,
)
with open('static/archive.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Sync the homepage "library has N playbooks" copy.
try:
    with open('static/index.html', encoding='utf-8') as f:
        idx = f.read()
    new_idx = re.sub(
        r'(The library has )\d+( playbooks)',
        rf'\g<1>{total}\g<2>',
        idx,
    )
    if new_idx != idx:
        with open('static/index.html', 'w', encoding='utf-8') as f:
            f.write(new_idx)
        print(f"Homepage counter synced to {total}")
except FileNotFoundError:
    pass

print(f"Archive updated: {total} rows")
print("Columns: Title | Pathway | Series | Category | Free | Status")
