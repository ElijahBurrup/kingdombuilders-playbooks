#!/usr/bin/env python3
"""
Kingdom Builders AI — PDF Generator

Uses Playwright (Chromium) to render playbook HTML files as high-quality PDFs
with smart page breaks, decorative transitions, and preserved visual design.

Generates two formats per playbook:
  1. Standard PDF (8.5" x 11" portrait) — assets/pdf/{stem}.pdf
  2. Book-cut PDF (11" x 8.5" landscape, two 5.5" x 8.5" book pages per sheet)
     — assets/pdf-bookcut/{stem}_bookcut.pdf
     Print, cut each sheet in half vertically, stack right halves under left
     halves to create a 5.5x8.5 booklet.

Usage:
  python -m scripts.generate_pdfs                                   # All playbooks
  python -m scripts.generate_pdfs Dad_Talks_The_Dopamine_Drought.html  # Single
  python -m scripts.generate_pdfs --force                           # Regenerate all
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
PDF_DIR = ASSETS_DIR / "pdf"
BOOKCUT_DIR = ASSETS_DIR / "pdf-bookcut"

PDF_DIR.mkdir(exist_ok=True)
BOOKCUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# PDF-SPECIFIC CSS (applied unconditionally, not behind @media print)
# Playwright's page.pdf() uses print media by default.
# ---------------------------------------------------------------------------
PDF_CSS = """
<style id="pdf-gen-css">
@media print {
  @page {
    margin: 16mm 14mm 20mm 14mm;
  }

  /* --- Hide interactive / overlay elements --- */
  .pb-back, .chain-panel, .email-slidein, .rating-popup,
  .pb-print-trigger, nav, .cookie-banner,
  script, .spark, .ghost-noise { display: none !important; }

  /* --- Base resets --- */
  html { font-size: 16px; }
  body { background: white !important; color: #1A1A1A !important;
         -webkit-print-color-adjust: exact !important;
         print-color-adjust: exact !important; }

  /* --- Cover: full first page --- */
  .cover { min-height: auto; padding: 60px 30px; break-after: page;
           -webkit-print-color-adjust: exact !important;
           print-color-adjust: exact !important; }
  .cover-art svg { filter: none !important; }

  /* --- Page layout --- */
  .page { max-width: 100%; padding: 0 8px; }
  .section { padding: 20px 0; }

  /* --- Prevent visual blocks from splitting across pages --- */
  .scene, .memory, .wisdom, .dad-voice, .viz, .adventure,
  .taste-recipe, .reflect, .compare-table, .final-test,
  .prompt, .think, .insight, .mission, .root-ck, .root-check,
  .gear, .meter, .cut, .ba-pair, .invert-pair, .gq,
  .tl-item, .rm-item, .dd, .deep-dive, .inst, .id-card,
  .ribbon, .flow, .char-card { break-inside: avoid; }

  /* --- Chapter headers start new page --- */
  .ch-head { break-before: page; }

  /* --- Finale: own page --- */
  .finale { break-before: page; padding: 60px 20px;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important; }

  /* --- Footer --- */
  footer { break-before: avoid; margin-top: 20px; }

  /* --- Kill all animations --- */
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
  }

  /* --- Preserve dark backgrounds --- */
  .memory, .memory-inner { -webkit-print-color-adjust: exact !important;
                            print-color-adjust: exact !important; }
  .viz { -webkit-print-color-adjust: exact !important;
         print-color-adjust: exact !important; }
  .viz-glow, .memory-glow { display: none !important; }

  .scene { box-shadow: none; }
  .wisdom { box-shadow: none; }
  .dad-voice { box-shadow: none;
               -webkit-print-color-adjust: exact !important;
               print-color-adjust: exact !important; }
  .compare-table { box-shadow: none; }
  .compare-header { -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important; }
  .prompt { -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important; }
  .reflect { box-shadow: none; }
  .ribbon { -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important; }

  /* --- Decorative transition borders on visual blocks --- */
  .memory, .viz, .scene, .wisdom, .dad-voice, .compare-table,
  .prompt, .reflect, .adventure, .insight, .mission, .gear,
  .think, .taste-recipe, .root-ck, .id-card, .ba-pair {
    padding-bottom: 16px;
    margin-bottom: 16px;
  }

  /* --- Prose: orphans/widows control --- */
  .prose p { orphans: 3; widows: 3; }

  /* --- Links: no underline --- */
  a { text-decoration: none !important; }

  /* --- Hide the "save as PDF" footer tip --- */
  body > div:last-child { display: none !important; }
}
</style>
"""


def generate_standard_pdf(page, html: str, output_path: Path):
    """Generate 8.5x11 portrait PDF."""
    injected = html.replace("</head>", PDF_CSS + "</head>")
    page.set_content(injected, wait_until="networkidle")
    page.wait_for_timeout(1000)  # let fonts render

    # Relax break-inside for blocks taller than 80% of page height
    page.evaluate("""
        const blocks = document.querySelectorAll('.viz, .memory, .scene, .wisdom, .dad-voice, .reflect, .compare-table');
        const pageH = 9.5 * 96;  // ~9.5 inches usable at 96dpi
        blocks.forEach(el => {
            if (el.offsetHeight > pageH * 0.8) {
                el.style.breakInside = 'auto';
            }
        });
    """)

    page.pdf(
        path=str(output_path),
        format="Letter",
        print_background=True,
        prefer_css_page_size=False,
    )


def generate_bookcut_pdf(standard_pdf_path: Path, output_path: Path):
    """
    Take a standard 8.5x11 PDF and create a book-cut version.

    Actually, we generate a HALF-LETTER (5.5x8.5) PDF first,
    then impose two pages side-by-side on landscape letter sheets.
    But since the standard PDF content might reflow differently at
    half-letter size, we take the simpler approach: scale the standard
    letter pages down to fit two per landscape sheet.

    For a true book-cut, we re-render at 5.5x8.5 and impose.
    """
    # We'll use a different approach: render the standard pages
    # scaled to fit two per landscape letter sheet.
    reader = PdfReader(str(standard_pdf_path))
    writer = PdfWriter()

    pages = list(reader.pages)
    n = len(pages)

    # Pad to even count
    if n % 2 != 0:
        blank = PageObject.create_blank_page(
            width=float(pages[0].mediabox.width),
            height=float(pages[0].mediabox.height),
        )
        pages.append(blank)

    # Letter dimensions in points: 8.5" x 11" = 612 x 792 pts
    # Landscape letter: 11" x 8.5" = 792 x 612 pts
    # Each half-page: 5.5" x 8.5" = 396 x 612 pts
    letter_w = 612.0
    letter_h = 792.0
    half_w = 396.0
    target_h = 612.0

    # Scale factor to fit a letter-sized page into half-width landscape
    scale_x = half_w / letter_w
    scale_y = target_h / letter_h
    scale = min(scale_x, scale_y)

    for i in range(0, len(pages), 2):
        # Create landscape letter sheet
        sheet = PageObject.create_blank_page(width=792, height=612)

        # Left page
        left = pages[i]
        left_transform = Transformation().scale(scale, scale)
        # Center vertically
        y_offset = (target_h - letter_h * scale) / 2
        left_transform = left_transform.translate(0, y_offset)
        sheet.merge_transformed_page(left, left_transform)

        # Right page
        right = pages[i + 1]
        right_transform = Transformation().scale(scale, scale).translate(half_w, y_offset)
        sheet.merge_transformed_page(right, right_transform)

        writer.add_page(sheet)

    with open(str(output_path), "wb") as f:
        writer.write(f)


def generate_instructions_pdf(page, output_path: Path):
    """Generate the book-cut instruction cover page as a half-letter PDF."""
    instructions_html = BOOKCUT_DIR / "cover_instructions.html"
    if not instructions_html.is_file():
        return None
    html = instructions_html.read_text(encoding="utf-8")
    page.set_content(html, wait_until="networkidle")
    page.wait_for_timeout(800)
    page.pdf(
        path=str(output_path),
        width="5.5in",
        height="8.5in",
        margin={"top": "8mm", "right": "6mm", "bottom": "8mm", "left": "6mm"},
        print_background=True,
        prefer_css_page_size=False,
    )
    return output_path


def generate_bookcut_native(page, html: str, output_path: Path):
    """
    Generate book-cut PDF by rendering at half-letter size (5.5x8.5),
    then imposing two pages per landscape letter sheet.
    Prepends a cover instruction page explaining how to cut and bind.
    """
    # Generate instruction cover page first
    instr_path = output_path.with_suffix(".instr.pdf")
    generate_instructions_pdf(page, instr_path)

    # Render playbook at half-letter size
    injected = html.replace("</head>", PDF_CSS + "</head>")
    page.set_content(injected, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Relax tall blocks
    page.evaluate("""
        const blocks = document.querySelectorAll('.viz, .memory, .scene, .wisdom, .dad-voice, .reflect, .compare-table');
        const pageH = 7.5 * 96;
        blocks.forEach(el => {
            if (el.offsetHeight > pageH * 0.8) {
                el.style.breakInside = 'auto';
            }
        });
    """)

    temp_path = output_path.with_suffix(".tmp.pdf")
    page.pdf(
        path=str(temp_path),
        width="5.5in",
        height="8.5in",
        margin={"top": "12mm", "right": "10mm", "bottom": "14mm", "left": "10mm"},
        print_background=True,
        prefer_css_page_size=False,
    )

    # Collect all half-letter pages: instructions first, then content
    all_pages = []

    if instr_path.is_file():
        instr_reader = PdfReader(str(instr_path))
        all_pages.extend(list(instr_reader.pages))

    content_reader = PdfReader(str(temp_path))
    all_pages.extend(list(content_reader.pages))

    # Pad to even count
    if len(all_pages) % 2 != 0:
        blank = PageObject.create_blank_page(width=396, height=612)
        all_pages.append(blank)

    # Impose two pages per landscape letter sheet
    writer = PdfWriter()
    for i in range(0, len(all_pages), 2):
        sheet = PageObject.create_blank_page(width=792, height=612)

        # Left page (already 396x612)
        sheet.merge_page(all_pages[i])

        # Right page — shift right by 396 points
        right = all_pages[i + 1]
        right_transform = Transformation().translate(396, 0)
        sheet.merge_transformed_page(right, right_transform)

        writer.add_page(sheet)

    with open(str(output_path), "wb") as f:
        writer.write(f)

    # Clean up temp files
    temp_path.unlink(missing_ok=True)
    instr_path.unlink(missing_ok=True)


def main():
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # Determine which files to process
    if args:
        html_files = []
        for a in args:
            p = ASSETS_DIR / a
            if p.is_file():
                html_files.append(p)
            else:
                print(f"  NOT FOUND: {p}")
    else:
        html_files = sorted(ASSETS_DIR.glob("*.html"))

    if not html_files:
        print("No HTML files found.")
        return

    print(f"Processing {len(html_files)} playbook(s)...\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()

        for html_path in html_files:
            stem = html_path.stem
            std_pdf = PDF_DIR / f"{stem}.pdf"
            bk_pdf = BOOKCUT_DIR / f"{stem}_bookcut.pdf"

            # Skip if up-to-date
            html_mtime = html_path.stat().st_mtime
            if not force:
                if std_pdf.exists() and std_pdf.stat().st_mtime >= html_mtime:
                    if bk_pdf.exists() and bk_pdf.stat().st_mtime >= html_mtime:
                        print(f"  SKIP {stem} (up to date)")
                        continue

            print(f"  Generating {stem}...")
            html = html_path.read_text(encoding="utf-8")
            start = time.time()

            page = context.new_page()

            # Standard PDF
            generate_standard_pdf(page, html, std_pdf)
            print(f"    Standard: {std_pdf.name} ({std_pdf.stat().st_size // 1024}KB)")

            # Book-cut PDF (native half-letter rendering)
            generate_bookcut_native(page, html, bk_pdf)
            print(f"    Book-cut: {bk_pdf.name} ({bk_pdf.stat().st_size // 1024}KB)")

            page.close()
            elapsed = time.time() - start
            print(f"    Done in {elapsed:.1f}s")

        browser.close()

    print(f"\nComplete. PDFs in:\n  Standard: {PDF_DIR}\n  Book-cut: {BOOKCUT_DIR}")


if __name__ == "__main__":
    main()
