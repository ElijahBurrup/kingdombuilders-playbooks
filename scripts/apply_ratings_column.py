"""Add a Rating column to the archive table.

- Inserts a 'Rating' <th> after Series (filterable + sortable)
- Adds an empty <td class="cell-rating" data-slug="..."> on every row
- Injects CSS for the star widget + a 'pending' state when there are
  fewer than RATING_MIN_VOTES reviewers
- Injects JS that fetches /api/v1/feedback-summary on page load,
  computes the star markup, and writes it into each cell. Rows with
  count < threshold display a muted "—" so unproven playbooks aren't
  marked low or high by a thin sample.

Re-runnable: removes any prior Rating column / styles / script before
re-injecting so the archive build chain can repeat cleanly.
"""
import re

PATH = "static/archive.html"
RATING_MIN_VOTES = 10  # only show a star score once we have ≥ 10 reviewers


def main() -> None:
    with open(PATH, encoding="utf-8") as f:
        html = f.read()

    # ---- Strip any previous rating injections so this script is idempotent
    html = re.sub(
        r'\s*<th data-col="rating"[^>]*>.*?</th>',
        "",
        html, flags=re.DOTALL,
    )
    html = re.sub(
        r'\s*<td class="cell-rating"[^>]*>.*?</td>',
        "",
        html, flags=re.DOTALL,
    )
    html = re.sub(r"\n\.cell-rating\{[^}]*\}", "", html)
    html = re.sub(r"\n\.cell-rating[^}{]*\{[^}]*\}", "", html)
    html = re.sub(
        r'\s*<script data-archive-ratings="v1">.*?</script>',
        "",
        html, flags=re.DOTALL,
    )

    # ---- Inject the <th> after the Series column header
    thead_m = re.search(
        r'(<th data-col="series" class="[^"]*"><div class="th-head">Series'
        r'.*?</button></div></th>)',
        html, flags=re.DOTALL,
    )
    if not thead_m:
        raise SystemExit("Could not find Series <th> to anchor Rating header")

    rating_th = (
        '\n      <th data-col="rating">'
        '<div class="th-head th-static">Rating</div></th>'
    )
    html = html[: thead_m.end()] + rating_th + html[thead_m.end():]

    # ---- Inject a placeholder <td> on every row, anchored before the Status cell
    def _row_with_cell(match: re.Match) -> str:
        row = match.group(0)
        slug_m = re.search(r'href="read/([\w-]+)"', row)
        slug = slug_m.group(1) if slug_m else ""
        cell = (
            f'<td class="cell-rating" data-slug="{slug}" data-rating="0">'
            f'<span class="rating-pending">&mdash;</span></td>'
        )
        # Insert before the status <td>
        return re.sub(
            r'(?=<td><span class="status-chip)',
            cell,
            row, count=1,
        )

    html = re.sub(
        r'<tr [^>]*data-status="[^"]*"[^>]*>.*?</tr>',
        _row_with_cell,
        html, flags=re.DOTALL,
    )

    # ---- Inject CSS for stars
    css = """
.th-static{cursor:default}
.th-static:hover{color:inherit !important;background:transparent !important}
.cell-rating{white-space:nowrap;min-width:120px}
.cell-rating .stars{display:inline-flex;gap:1px;font-family:Arial,sans-serif;font-size:0.95rem;letter-spacing:0;line-height:1}
.cell-rating .stars .s-full{color:#D4A843}
.cell-rating .stars .s-half{color:#D4A843;position:relative;display:inline-block;width:1ch;overflow:hidden}
.cell-rating .stars .s-empty{color:rgba(60,60,80,0.18)}
.cell-rating .rating-num{margin-left:7px;font-family:'Poppins',sans-serif;font-size:0.72rem;font-weight:700;color:var(--dawn)}
.cell-rating .rating-count{margin-left:5px;font-family:'Poppins',sans-serif;font-size:0.6rem;font-weight:600;color:var(--text-muted);letter-spacing:0.4px}
.cell-rating .rating-pending{font-family:'Poppins',sans-serif;font-size:0.62rem;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:var(--text-muted);opacity:0.55}
"""
    html = html.replace("</style>", css + "\n</style>", 1)

    # ---- Inject JS loader
    js = """
<script data-archive-ratings="v1">
(function(){
  var MIN = """ + str(RATING_MIN_VOTES) + """;
  function starsHtml(avg5){
    var rounded = Math.round(avg5 * 2) / 2;  // nearest 0.5
    var html = '<span class="stars" aria-label="' + avg5.toFixed(1) + ' out of 5">';
    for (var i = 1; i <= 5; i++){
      if (rounded >= i) html += '<span class="s-full">&#9733;</span>';
      else if (rounded >= i - 0.5) html += '<span class="s-half">&#9733;</span>';
      else html += '<span class="s-empty">&#9733;</span>';
    }
    html += '</span>';
    return html;
  }
  fetch('/playbooks/api/v1/feedback-summary', {credentials:'same-origin'})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if(!d || !d.ratings) return;
      document.querySelectorAll('td.cell-rating').forEach(function(td){
        var slug = td.dataset.slug;
        var info = d.ratings[slug];
        if (!info || !info.count || info.count < MIN){
          // leave the &mdash; placeholder + zero data-rating
          return;
        }
        var avg5 = Number(info.avg) || 0;
        td.dataset.rating = String(avg5);
        td.innerHTML = starsHtml(avg5)
          + '<span class="rating-num">' + avg5.toFixed(1) + '</span>'
          + '<span class="rating-count">(' + info.count + ')</span>';
      });
    })
    .catch(function(){});
})();
</script>
"""
    html = html.replace("</body>", js + "\n</body>", 1)

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Added Rating column to {PATH}")


if __name__ == "__main__":
    main()
