"""Restructure the Free column:
- Remove the Free TH and the cell-free TD from each row
- Add a green 'Free' chip inline with category chips when row was free
- Switch row schema from data-category (single) to data-cats (space-list)
- Update filter JS so 'category' uniqueness reads from data-cats
"""
import re

PATH = 'static/archive.html'
with open(PATH, encoding='utf-8') as f:
    html = f.read()

# 1) Drop the Free TH
html = re.sub(
    r'\s*<th data-col="free" class="filterable">.*?</th>',
    '',
    html, count=1, flags=re.DOTALL,
)

# 2) Walk each row. For each row:
#    - read data-free + data-category + categories chips
#    - rewrite as data-cats="Cat1 Cat2 Free"
#    - drop the <td class="cell-free">...</td>
#    - inject a <span class="cat-chip free">Free</span> at the start of cell-cats
row_pat = re.compile(
    r'<tr data-pathway="([^"]*)" data-series="([^"]*)"(?:\s+data-series-order="[^"]*")? data-category="([^"]*)" data-free="(yes|no)" data-status="([^"]*)">'
    r'(?P<body>.*?)'
    r'</tr>',
    re.DOTALL,
)

def rewrite_row(m):
    pathway, series, primary_cat, free, status = m.groups()[:5]
    body = m.group('body')

    # Extract chip labels from the cell-cats cell
    chips_m = re.search(
        r'<td class="cell-cats">(.*?)</td>',
        body, flags=re.DOTALL,
    )
    chip_labels = []
    if chips_m:
        for c in re.findall(r'<span class="cat-chip[^"]*">([^<]+)</span>', chips_m.group(1)):
            label = c.strip()
            if label and label not in chip_labels:
                chip_labels.append(label)

    # Prepend Free if applicable
    if free == 'yes' and 'Free' not in chip_labels:
        chip_labels.insert(0, 'Free')

    # Build new chips HTML
    chips_html = ' '.join(
        f'<span class="cat-chip{" free" if c == "Free" else ""}">{c}</span>'
        for c in chip_labels
    )
    new_cats_td = f'<td class="cell-cats">{chips_html}</td>'

    # Strip the old cell-cats + cell-free TDs
    body = re.sub(
        r'<td class="cell-cats">.*?</td>\s*<td class="cell-free">.*?</td>',
        new_cats_td,
        body, flags=re.DOTALL,
    )

    # Build data-cats attribute (space-separated)
    data_cats = ' '.join(chip_labels)

    return (
        f'<tr data-pathway="{pathway}" data-series="{series}" '
        f'data-cats="{data_cats}" data-status="{status}">'
        f'{body}</tr>'
    )

new_html, n_rows = row_pat.subn(rewrite_row, html)
html = new_html

# 3) Drop the Free-specific CSS (cell-free, free-yes, free-no)
html = re.sub(
    r'\n\.cell-free\{[^}]*\}',
    '',
    html,
)
html = re.sub(
    r"\n\.free-yes\{[^}]*\}",
    '',
    html,
)
html = re.sub(
    r"\n\.free-no\{[^}]*\}",
    '',
    html,
)

# 4) Add green free chip style (only if not present)
if '.cat-chip.free{' not in html:
    extra_css = (
        "\n.cat-chip.free{"
        "background:rgba(45,138,78,0.14);color:#1E7E34;"
        "border:1px solid rgba(45,138,78,0.28);"
        "font-weight:800;letter-spacing:1.3px"
        "}"
    )
    html = html.replace('</style>', extra_css + '\n</style>', 1)

# 5) Update getUniqueValues + refresh filter to handle category as multi-valued
old_unique = (
    "  function getUniqueValues(col){\n"
    "    const m = new Map();\n"
    "    allRows.forEach(r => {\n"
    "      const v = r.dataset[col] || '—';\n"
    "      m.set(v, (m.get(v) || 0) + 1);\n"
    "    });\n"
    "    return Array.from(m.entries()).sort((a,b) => a[0].localeCompare(b[0]));\n"
    "  }"
)
new_unique = (
    "  function getUniqueValues(col){\n"
    "    const m = new Map();\n"
    "    if(col === 'category'){\n"
    "      allRows.forEach(r => {\n"
    "        const cats = (r.dataset.cats || '').split(/\\s+/).filter(Boolean);\n"
    "        if(cats.length === 0){ m.set('—', (m.get('—') || 0) + 1); }\n"
    "        else { cats.forEach(c => m.set(c, (m.get(c) || 0) + 1)); }\n"
    "      });\n"
    "    } else {\n"
    "      allRows.forEach(r => {\n"
    "        const v = r.dataset[col] || '—';\n"
    "        m.set(v, (m.get(v) || 0) + 1);\n"
    "      });\n"
    "    }\n"
    "    return Array.from(m.entries()).sort((a,b) => {\n"
    "      if(a[0] === 'Free') return -1;\n"
    "      if(b[0] === 'Free') return 1;\n"
    "      return a[0].localeCompare(b[0]);\n"
    "    });\n"
    "  }"
)
html = html.replace(old_unique, new_unique)

# Update refresh() to match any data-cats value for the category filter
old_refresh = (
    "    allRows.forEach(r => {\n"
    "      let show = true;\n"
    "      for(const col in activeFilters){\n"
    "        const v = r.dataset[col] || '—';\n"
    "        if(!activeFilters[col].has(v)){ show = false; break; }\n"
    "      }"
)
new_refresh = (
    "    allRows.forEach(r => {\n"
    "      let show = true;\n"
    "      for(const col in activeFilters){\n"
    "        let match = false;\n"
    "        if(col === 'category'){\n"
    "          const cats = (r.dataset.cats || '').split(/\\s+/).filter(Boolean);\n"
    "          if(cats.length === 0) cats.push('—');\n"
    "          match = cats.some(c => activeFilters[col].has(c));\n"
    "        } else {\n"
    "          const v = r.dataset[col] || '—';\n"
    "          match = activeFilters[col].has(v);\n"
    "        }\n"
    "        if(!match){ show = false; break; }\n"
    "      }"
)
html = html.replace(old_refresh, new_refresh)

# Sort by category should sort by data-cats lexically — fine as-is since cells
# render alphabetically; nothing extra needed.

# 6) Remove 'yes'/'no' Free entries from PRETTY map (no longer used)
html = html.replace(
    "    'yes':'Free','no':'Not Free',\n",
    "",
)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Restructured {n_rows} rows.")
print("Free column removed, Free chip added inline, filter is multi-value for category.")
