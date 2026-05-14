"""Add a Rating column to the archive table.

- Inserts a 'Rating' <th> after Series
- Adds a <td class="cell-rating" data-slug="..."> on every row, placed
  immediately before the Category cell so the column visually aligns
  with the THEAD position
- Injects CSS for the star widget + a 'pending' state when no rating
  is available
- Embeds the curated seed ratings (1-10) from scripts/default_ratings.json
  as a JSON blob the JS can read
- Injects JS that fetches /api/v1/feedback-summary on page load, computes
  the star markup, and writes it into each cell:
    * count >= RATING_MIN_VOTES → crowd-sourced average + (count) chip
    * else if seed rating exists → seed rating styled identically
    * else → muted dash

Re-runnable: removes any prior Rating column / styles / script before
re-injecting so the archive build chain can repeat cleanly.
"""
import json
import re

PATH = "static/archive.html"
DEFAULTS_PATH = "scripts/default_ratings.json"
RATING_MIN_VOTES = 10  # only switch to crowd-sourced average once we have ≥ 10 reviewers


def main() -> None:
    with open(PATH, encoding="utf-8") as f:
        html = f.read()

    try:
        with open(DEFAULTS_PATH, encoding="utf-8") as f:
            defaults = json.load(f)
    except FileNotFoundError:
        defaults = {}

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
    html = re.sub(r"\n\.th-static[^}{]*\{[^}]*\}", "", html)
    html = re.sub(
        r'\s*<script id="archive-default-ratings"[^>]*>.*?</script>',
        "",
        html, flags=re.DOTALL,
    )
    html = re.sub(
        r'\s*<script data-archive-ratings="v[0-9]+">.*?</script>',
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

    # ---- Inject a placeholder <td> on every row. Rating column lives BETWEEN
    # Series and Category in the THEAD, so the TD must be placed immediately
    # before the cell-cats td (not before status, which would put it on the
    # wrong side of Category and read as if the columns were swapped).
    def _row_with_cell(match: re.Match) -> str:
        row = match.group(0)
        slug_m = re.search(r'href="read/([\w-]+)"', row)
        slug = slug_m.group(1) if slug_m else ""
        cell = (
            f'<td class="cell-rating" data-slug="{slug}" data-rating="0">'
            f'<span class="rating-pending">&mdash;</span></td>'
        )
        return re.sub(
            r'(?=<td class="cell-cats")',
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
.cell-rating .rating-seed-tag{margin-left:6px;padding:2px 7px;border-radius:30px;background:rgba(212,168,67,0.10);color:var(--text-muted);font-family:'Poppins',sans-serif;font-size:0.52rem;font-weight:800;letter-spacing:1.3px;text-transform:uppercase;border:1px solid rgba(212,168,67,0.22)}
"""
    html = html.replace("</style>", css + "\n</style>", 1)

    # ---- Embed the seed defaults as a JSON island
    defaults_block = (
        '<script id="archive-default-ratings" type="application/json">'
        + json.dumps(defaults).replace("</", "<\\/")
        + "</script>"
    )

    # ---- Inject JS loader
    js = """
<script data-archive-ratings="v2">
(function(){
  var MIN = """ + str(RATING_MIN_VOTES) + """;
  var defaults = {};
  try {
    var node = document.getElementById('archive-default-ratings');
    if (node) defaults = JSON.parse(node.textContent) || {};
  } catch(e) {}

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

  function render(td, avg5, count, isSeed){
    td.dataset.rating = String(avg5);
    var html = starsHtml(avg5) + '<span class="rating-num">' + avg5.toFixed(1) + '</span>';
    if (count != null && !isSeed) {
      html += '<span class="rating-count">(' + count + ')</span>';
    } else if (isSeed) {
      html += '<span class="rating-seed-tag" title="Editorial seed rating shown until 10+ reader reviews come in">seed</span>';
    }
    td.innerHTML = html;
  }

  function paintFromDefaults(){
    document.querySelectorAll('td.cell-rating').forEach(function(td){
      var slug = td.dataset.slug;
      var seedTen = defaults[slug];
      if (typeof seedTen === 'number'){
        // Curated catalog uses 1-10 scale; convert to 1-5 for star display.
        render(td, seedTen / 2, null, true);
      }
    });
  }
  // Paint seeds immediately so cells aren't blank during the network fetch.
  paintFromDefaults();

  fetch('/playbooks/api/v1/feedback-summary', {credentials:'same-origin'})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if(!d || !d.ratings) return;
      document.querySelectorAll('td.cell-rating').forEach(function(td){
        var slug = td.dataset.slug;
        var info = d.ratings[slug];
        if (info && info.count && info.count >= MIN){
          var avg5 = Number(info.avg) || 0;  // already 1-5 from the API
          render(td, avg5, info.count, false);
        }
        // else: keep the seed already painted above
      });
    })
    .catch(function(){});
})();
</script>
"""
    html = html.replace("</body>", defaults_block + "\n" + js + "\n</body>", 1)

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Added Rating column to {PATH}")


if __name__ == "__main__":
    main()
