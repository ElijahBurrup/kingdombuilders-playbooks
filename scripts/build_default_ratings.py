"""Parse the curated Playbook Full Review on S: and emit a slug→overall map.

Source: S:\\My Drive\\1. Projects\\KingdomBuilders.AI\\PlaybookFullReview.html
Output: scripts/default_ratings.json (slug → overall score on a 1-10 scale)

These act as seed ratings shown in the archive until each playbook
collects enough real reviewer feedback (≥ 10) to display the
crowd-sourced average instead.
"""
import html as htmllib
import json
import re
import sys

sys.path.insert(0, '.')
from playbook_registry import SLUG_TO_FILE

SRC = "S:/My Drive/1. Projects/KingdomBuilders.AI/PlaybookFullReview.html"
OUT = "scripts/default_ratings.json"


def fuzz(s: str) -> str:
    """Normalize a title so it compares cleanly to a slug-as-words."""
    s = htmllib.unescape(s).lower()
    # The review titles often append a subtitle like:
    #   "The Crow's Gambit. How Pot Odds Reveal..."
    #   "Dad Talks: The Flinch - Why Your Body Quits..."
    # Cut at the FIRST sentence/subtitle break so only the playbook name remains.
    s = re.split(r"[.!?]\s|\s[-–—]\s", s, maxsplit=1)[0]
    # Strip apostrophes in possessive 's so slug 'wolfs' matches 'wolf's'
    s = s.replace("’s", "s").replace("'s", "s")
    s = s.replace("kingdom builders ai", " ")
    s = s.replace("forest economy", "economy")  # squirrel forest economy → squirrel economy
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(the|main|series|a|of|to|for|and)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Hand-curated overrides for titles that are messy/ambiguous in the source
ALIASES = {
    "manna given": "given",
    "manna returning": "returning",
    "lay it down": "lay-it-down",
    "before garden returns": "before-the-garden-returns",
    "tending garden": "tending-the-garden",
    "roche limit": "the-roche-limit",
    "conductors playbook": "conductors-playbook",
    "kintsugi protocol": "the-kintsugi-bowl",  # source uses 'Protocol', slug uses 'Bowl'
    "kintsugi": "the-kintsugi-bowl",
}


def main() -> None:
    with open(SRC, encoding="utf-8") as f:
        raw = f.read()

    # slug -> fuzzed slug-as-words form
    slug_by_fuzz: dict[str, str] = {}
    for slug in SLUG_TO_FILE:
        slug_by_fuzz[fuzz(slug.replace("-", " "))] = slug

    # Extract each <tr> row that has rank + title + the Overall column
    # (Overall is identified by font-size:1.05rem on its <td>).
    row_pat = re.compile(
        r'<tr>\s*<td class="rank">\d+</td>\s*'
        r'<td class="title">([^<]+)</td>'
        r'.*?'
        r'<td style="[^"]*?font-size:1\.05rem[^"]*">\s*([0-9]+(?:\.[0-9]+)?)\s*</td>',
        re.DOTALL,
    )

    ratings: dict[str, float] = {}
    skipped: list[str] = []

    for m in row_pat.finditer(raw):
        title = m.group(1).strip()
        overall = float(m.group(2))
        # Some rows already use the slug as the title — pick it up directly
        slug_candidate = title.strip().lower()
        if slug_candidate in SLUG_TO_FILE:
            ratings[slug_candidate] = round(overall, 2)
            continue
        # Strip series prefix and try both
        candidates = [title]
        if ":" in title:
            candidates.append(title.split(":", 1)[1])
        chosen = None
        for cand in candidates:
            f = fuzz(cand)
            if f in slug_by_fuzz:
                chosen = slug_by_fuzz[f]
                break
            # Alias lookup: any alias key contained within fuzzed title
            for ak, slug in ALIASES.items():
                if ak in f:
                    chosen = slug
                    break
            if chosen:
                break

        if chosen:
            # Keep highest if a slug appears more than once
            if chosen in ratings:
                ratings[chosen] = round(max(ratings[chosen], overall), 2)
            else:
                ratings[chosen] = round(overall, 2)
        else:
            skipped.append(title)

    ratings = dict(sorted(ratings.items()))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ratings, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT}: {len(ratings)} playbooks rated")
    if skipped:
        print(f"\nSkipped {len(skipped)} unmatched rows:")
        for s in skipped:
            print(f"  {s!r}")

    missing = sorted(set(SLUG_TO_FILE) - set(ratings))
    if missing:
        print(f"\n{len(missing)} slugs in registry have no seed rating:")
        for s in missing:
            print(f"  {s}")


if __name__ == "__main__":
    main()
