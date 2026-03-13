#!/usr/bin/env python3
"""
PDF Quality Test — Validates generated PDFs for whitespace waste and page breaks.

Uses Playwright to measure block positions relative to page boundaries and
reports wasted space from break-inside-avoid pushing blocks to new pages.

Usage:
  python -m scripts.pdf_quality_test                                    # All
  python -m scripts.pdf_quality_test Dad_Talks_The_Dopamine_Drought.html  # Single

Exit code 0 = pass, 1 = failures found.
"""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

# PDF-specific CSS (same as generate_pdfs.py)
PDF_CSS = """
<style>
@media print {
  @page { margin: 16mm 14mm 20mm 14mm; }
  .spark, .ghost-noise, .viz-glow, .memory-glow { display: none !important; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
  html { font-size: 16px; }
  .page { max-width: 100%; padding: 0 8px; }
  .section { padding: 20px 0; }
  .cover { min-height: auto; padding: 60px 30px; break-after: page; }
  .scene, .memory, .wisdom, .dad-voice, .viz, .adventure,
  .taste-recipe, .reflect, .compare-table, .final-test,
  .prompt, .think, .insight, .mission, .root-ck, .root-check,
  .gear, .meter, .cut, .ba-pair, .invert-pair, .gq,
  .ribbon, .flow, .char-card { break-inside: avoid; }
  .ch-head { break-before: page; }
  .finale { break-before: page; padding: 60px 20px; }
  body > div:last-child { display: none !important; }
}
</style>
"""

WASTE_THRESHOLD = 0.20  # 20% max total whitespace waste
PAGE_HEIGHT_PX = 9.5 * 96  # ~9.5 inches usable at 96dpi


def analyze_playbook(page, html_path: Path) -> dict:
    """Analyze a playbook for page break quality."""
    html = html_path.read_text(encoding="utf-8")
    injected = html.replace("</head>", PDF_CSS + "</head>")

    page.set_viewport_size({"width": 816, "height": 100000})  # letter width at 96dpi
    page.set_content(injected, wait_until="networkidle")
    page.wait_for_timeout(800)

    # Emulate print media
    page.emulate_media(media="print")
    page.wait_for_timeout(500)

    # Measure block positions
    data = page.evaluate("""() => {
        const PAGE_H = 9.5 * 96;
        const selectors = '.memory, .viz, .scene, .wisdom, .dad-voice, .reflect, .compare-table, .prompt, .root-ck, .final-test, .char-grid, .ribbon';
        const blocks = document.querySelectorAll(selectors);
        const results = [];
        let totalHeight = document.documentElement.scrollHeight;

        for (const el of blocks) {
            const rect = el.getBoundingClientRect();
            const top = rect.top + window.scrollY;
            const pageNum = Math.floor(top / PAGE_H) + 1;
            const posOnPage = top % PAGE_H;
            const remainingOnPage = PAGE_H - posOnPage;
            const wouldSplit = rect.height > remainingOnPage && rect.height < PAGE_H;
            const wastedIfMoved = wouldSplit ? remainingOnPage : 0;

            results.push({
                cls: el.className.split(' ')[0],
                height: Math.round(rect.height),
                pageNum: pageNum,
                posOnPage: Math.round(posOnPage),
                remainingOnPage: Math.round(remainingOnPage),
                wouldSplit: wouldSplit,
                wastedPx: Math.round(wastedIfMoved)
            });
        }

        return {
            totalHeight: totalHeight,
            totalPages: Math.ceil(totalHeight / PAGE_H),
            blocks: results
        };
    }""")

    return data


def report(html_path: Path, data: dict) -> bool:
    """Print report for a single playbook. Returns True if passed."""
    stem = html_path.stem
    total_pages = data["totalPages"]
    total_waste_px = sum(b["wastedPx"] for b in data["blocks"] if b["wouldSplit"])
    total_page_area = total_pages * PAGE_HEIGHT_PX
    waste_pct = (total_waste_px / total_page_area) * 100 if total_page_area > 0 else 0

    passed = waste_pct <= WASTE_THRESHOLD * 100

    print(f"\n  {stem}")
    print(f"    Pages: ~{total_pages}")
    print(f"    Total whitespace waste: {waste_pct:.1f}% ({'PASS' if passed else 'FAIL > 20%'})")

    split_blocks = [b for b in data["blocks"] if b["wouldSplit"]]
    if split_blocks:
        for b in split_blocks:
            pct = (b["wastedPx"] / PAGE_HEIGHT_PX) * 100
            print(f"    Page {b['pageNum']}: .{b['cls']} ({b['height']}px) pushed to next page, wasting {b['wastedPx']}px ({pct:.0f}% of page)")
    else:
        print(f"    Page breaks: All clean")

    return passed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        html_files = [ASSETS_DIR / a for a in args if (ASSETS_DIR / a).is_file()]
    else:
        html_files = sorted(ASSETS_DIR.glob("*.html"))

    if not html_files:
        print("No HTML files found.")
        return

    print(f"=== PDF Quality Report ({len(html_files)} playbooks) ===")

    all_passed = True

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        for html_path in html_files:
            data = analyze_playbook(page, html_path)
            if not report(html_path, data):
                all_passed = False

        browser.close()

    print(f"\n--- {'ALL PASSED' if all_passed else 'SOME FAILED'} ---")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
