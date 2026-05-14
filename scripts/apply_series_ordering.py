"""Show series position "X of N" in the Series cell and reorder rows so
each series appears in narrative reading order. Non-series rows sort
alphabetically by title and are placed AFTER all series rows.
"""
import re
import sys

sys.path.insert(0, '.')
from series_definitions import (
    SERIES_SEQUENCE,
    SERIES_DISPLAY_NAME,
    SERIES_DESCRIPTION,
    get_series_position,
)

PATH = 'static/archive.html'
with open(PATH, encoding='utf-8') as f:
    html = f.read()

# Extract the tbody block
m = re.search(r'(<tbody id="table-body">)(.*?)(</tbody>)', html, flags=re.DOTALL)
if not m:
    print("ERROR: tbody not found")
    sys.exit(1)
open_tag, body, close_tag = m.groups()

# Parse each row
row_pat = re.compile(r'<tr [^>]*>.*?</tr>', re.DOTALL)
rows = row_pat.findall(body)
print(f"Parsed {len(rows)} rows")

def rewrite(row: str) -> tuple[str, str | None, int, str]:
    slug_m = re.search(r'href="read/([^"]+)"', row)
    title_m = re.search(r'<a href="read/[^"]+">([^<]+)', row)
    slug = slug_m.group(1) if slug_m else ''
    title = (title_m.group(1) if title_m else '').lower()
    pos_info = get_series_position(slug)

    # Normalize: strip any existing data-series-order so re-runs are idempotent.
    row = re.sub(r'\s*data-series-order="[^"]*"', '', row)

    if pos_info:
        series_slug, pos, total = pos_info
        series_name = SERIES_DISPLAY_NAME.get(series_slug, series_slug)
        desc = SERIES_DESCRIPTION.get(series_slug, "")
        desc_html = (
            f'<span class="series-desc">{desc}</span>' if desc else ""
        )
        new_series_cell = (
            f'<td class="cell-series" data-series-slug="{series_slug}" title="{desc}">'
            f'<span class="series-name">{series_name}</span>'
            f'{desc_html}'
            f'<span class="series-pos">{pos} of {total}</span>'
            f'</td>'
        )
        order_key = f"{series_slug}:{pos:03d}"
        row_with_attr = re.sub(
            r'data-series="[^"]*"',
            f'data-series="{series_name}" data-series-order="{order_key}"',
            row, count=1,
        )
        # Replace either an old plain <td>...</td> or a previous <td class="cell-series">
        row_with_attr = re.sub(
            r'<td(?:\s+class="cell-series"[^>]*>.*?|[^>]*>(?:<em>—</em>|—|[^<]*))</td>(?=\s*<td class="cell-cats")',
            new_series_cell,
            row_with_attr, count=1, flags=re.DOTALL,
        )
        return row_with_attr, series_slug, pos, title

    row_with_attr = re.sub(
        r'data-series="[^"]*"',
        'data-series="—" data-series-order="zzz"',
        row, count=1,
    )
    return row_with_attr, None, 0, title

processed = [rewrite(r) for r in rows]

# Sort: series rows first by (series_slug, pos), then non-series rows by title
def key(item):
    _row, series_slug, pos, title = item
    if series_slug is None:
        return (1, '', 0, title)
    return (0, series_slug, pos, title)

processed.sort(key=key)
new_rows = [item[0] for item in processed]

new_body = '\n      ' + '\n      '.join(new_rows) + '\n    '
html = html[:m.start()] + open_tag + new_body + close_tag + html[m.end():]

# Add CSS for series cell layout — strip any previous version first for idempotency
html = re.sub(
    r'\n\.cell-series\{[^}]*\}(?:\n\.cell-series\s[^}]*\{[^}]*\})*',
    '',
    html,
)
EXTRA_CSS = '''
.cell-series{min-width:180px;max-width:260px}
.cell-series .series-name{display:block;font-family:'Poppins',sans-serif;font-size:0.78rem;font-weight:700;color:var(--dawn);line-height:1.2}
.cell-series .series-desc{display:block;margin-top:3px;font-family:'Lora',serif;font-style:italic;font-size:0.72rem;color:var(--text-light);line-height:1.35}
.cell-series .series-pos{display:inline-block;margin-top:6px;padding:2px 8px;border-radius:30px;background:rgba(212,168,67,0.14);color:#8a6a1c;font-family:'Poppins',sans-serif;font-size:0.58rem;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;border:1px solid rgba(212,168,67,0.32)}
'''
html = html.replace('</style>', EXTRA_CSS + '\n</style>', 1)

# Default sort indicator: bring Series column up as primary sort key in the JS.
# The grid already lets users re-sort by clicking columns; we just changed the
# initial DOM order so the default view is series order. Highlight the Series
# column as sorted-asc so the arrow reflects the actual order.
html = re.sub(
    r'<th data-col="series" class="filterable"><div class="th-head">Series',
    '<th data-col="series" class="filterable sorted sorted-asc"><div class="th-head">Series',
    html, count=1,
)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(html)

n_series = sum(1 for _, s, _, _ in processed if s is not None)
n_solo = len(processed) - n_series
print(f"Updated: {n_series} series rows ordered, {n_solo} standalone rows tail-sorted.")
