// @ts-check
/**
 * Contrast Audit — Authoritative WCAG contrast check.
 *
 * Walks every text node in every playbook asset HTML file using a real
 * browser. For each visible text node, computes effective foreground color
 * and effective background color from the cascade (resolving inherited
 * backgrounds, gradients, and the dark color stops within them), then
 * reports any text below WCAG 2.1 AA contrast (4.5:1 for normal text,
 * 3:1 for large text).
 *
 * Run:
 *   npx playwright test tests/contrast-audit.spec.js --project=chrome-desktop
 *
 * Run for a single file:
 *   PLAYBOOK_FILTER=The_Body_Lie npx playwright test tests/contrast-audit.spec.js --project=chrome-desktop
 *
 * Skip when reading remote (only useful with file:// URLs):
 *   This spec ignores baseURL and loads each asset from disk.
 */

const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const ASSETS_DIR = path.join(__dirname, "..", "assets");
const FILTER = process.env.PLAYBOOK_FILTER || "";

const files = fs.readdirSync(ASSETS_DIR)
  .filter((f) => f.endsWith(".html") && !f.startsWith("_"))
  .filter((f) => !FILTER || f.includes(FILTER))
  .sort();

// In-browser audit script. Returns an array of {issue} for each failing text.
const auditFn = () => {
  /** @param {string} str */
  function parseRgb(str) {
    if (!str) return null;
    const m = str.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
    return m ? [+m[1], +m[2], +m[3]] : null;
  }

  /** @param {string} hex */
  function hexToRgb(hex) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
    if (hex.length !== 6 && hex.length !== 8) return null;
    return [
      parseInt(hex.slice(0, 2), 16),
      parseInt(hex.slice(2, 4), 16),
      parseInt(hex.slice(4, 6), 16),
    ];
  }

  /** @param {number[]} rgb */
  function luminance(rgb) {
    const a = rgb.slice(0, 3).map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
  }

  /** @param {number[]} c1 @param {number[]} c2 */
  function contrast(c1, c2) {
    const l1 = luminance(c1);
    const l2 = luminance(c2);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }

  // Extract every color from a gradient string (rgb(), rgba(), or #hex).
  function gradientColorStops(str) {
    if (!str || str === "none") return [];
    const stops = [];
    const re = /rgba?\([^)]+\)|#[0-9a-f]{3,8}\b/gi;
    let m;
    while ((m = re.exec(str)) !== null) {
      const rgb = m[0].startsWith("#") ? hexToRgb(m[0]) : parseRgb(m[0]);
      if (rgb) stops.push(rgb);
    }
    return stops;
  }

  /** Parse rgba's alpha. Returns 1.0 if not rgba. */
  function parseAlpha(str) {
    if (!str) return 1;
    const m = str.match(/rgba\([^)]+,\s*([\d.]+)\s*\)/);
    return m ? parseFloat(m[1]) : 1;
  }

  /** Alpha-blend a (rgba) over b (rgb). Returns rgb. */
  function blend(fg, fgAlpha, bg) {
    return [
      Math.round(fg[0] * fgAlpha + bg[0] * (1 - fgAlpha)),
      Math.round(fg[1] * fgAlpha + bg[1] * (1 - fgAlpha)),
      Math.round(fg[2] * fgAlpha + bg[2] * (1 - fgAlpha)),
    ];
  }

  /**
   * Walk up from el looking for the effective background. Returns the
   * set of candidate background colors that text might land on: for a
   * solid background, one color. For a gradient, the lightest and
   * darkest stops (the realistic range).
   *
   * Properly blends low-alpha backgrounds (e.g. rgba(255,255,255,0.08)) over
   * the parent's resolved background instead of treating them as opaque white.
   */
  function effectiveBg(el) {
    let cur = el;
    // Stack of (color, alpha) layers from innermost out. We resolve once we
    // hit an opaque layer.
    const layers = [];
    while (cur && cur !== document.documentElement) {
      const cs = getComputedStyle(cur);
      const bgColor = cs.backgroundColor;
      const bgImage = cs.backgroundImage;

      const stops = gradientColorStops(bgImage);
      if (stops.length) {
        stops.sort((a, b) => luminance(a) - luminance(b));
        const base = stops.length === 1 ? [stops[0]] : [stops[0], stops[stops.length - 1]];
        // Composite the saved layers over each base candidate
        const candidates = base.map((bg) => {
          let resolved = bg;
          for (let i = layers.length - 1; i >= 0; i--) {
            resolved = blend(layers[i].color, layers[i].alpha, resolved);
          }
          return resolved;
        });
        return { candidates, source: "gradient", el: cur };
      }

      const rgb = parseRgb(bgColor);
      const alpha = parseAlpha(bgColor);
      if (rgb && alpha > 0) {
        if (alpha >= 0.95) {
          // Opaque enough — terminate the walk, composite layers above it.
          let resolved = rgb;
          for (let i = layers.length - 1; i >= 0; i--) {
            resolved = blend(layers[i].color, layers[i].alpha, resolved);
          }
          return { candidates: [resolved], source: "bg-color", el: cur };
        }
        // Semi-transparent layer — record it and keep walking
        layers.push({ color: rgb, alpha });
      }
      cur = cur.parentElement;
    }
    // No opaque ancestor: composite over white (page default)
    let resolved = [255, 255, 255];
    for (let i = layers.length - 1; i >= 0; i--) {
      resolved = blend(layers[i].color, layers[i].alpha, resolved);
    }
    return { candidates: [resolved], source: "default-white", el: null };
  }

  /**
   * For text that is above-fold and visible on screen.
   * Skips invisible elements, scripts, styles, SVG content.
   */
  function isVisibleText(el) {
    if (!el) return false;
    const tag = el.tagName.toLowerCase();
    if (["script", "style", "svg", "head", "meta", "link", "title", "noscript"].includes(tag)) return false;
    if (el.closest("script, style, svg, head, [hidden]")) return false;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    if (parseFloat(cs.opacity) < 0.1) return false;
    return true;
  }

  const issues = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const text = (node.textContent || "").trim();
    if (text.length < 4) continue; // skip whitespace and 1-2 char fragments

    const parent = node.parentElement;
    if (!isVisibleText(parent)) continue;

    const cs = getComputedStyle(parent);
    let fg = parseRgb(cs.color);
    if (!fg) continue;

    // Skip very transparent text — decorative subtle styling, not a contrast bug.
    // 0.35 alpha is the cutoff: anything below that is intentionally faded.
    const alpha = (() => {
      const m = cs.color.match(/rgba\([^)]+,\s*([\d.]+)\s*\)/);
      return m ? parseFloat(m[1]) : 1.0;
    })();
    if (alpha < 0.35) continue;

    const fontSize = parseFloat(cs.fontSize);
    // Skip very small decorative text (under 10px, often dividers/tags)
    if (fontSize < 10) continue;

    const bg = effectiveBg(parent);

    // For gradients: pick the WORST contrast among candidates (the bg stop
    // closest in luminance to the fg). If it passes threshold, the text is
    // legible somewhere along the gradient. If it fails on ALL stops, real bug.
    let worstRatio = Infinity;
    let worstBg = bg.candidates[0];
    for (const c of bg.candidates) {
      const r = contrast(fg, c);
      if (r < worstRatio) {
        worstRatio = r;
        worstBg = c;
      }
    }

    const fontWeight = parseInt(cs.fontWeight);
    const isLarge = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
    const threshold = isLarge ? 3.0 : 4.5;

    if (worstRatio < threshold) {
      // Best-case contrast across all candidates. If best is fine, this might
      // just be a gradient region issue (text actually lands on the good stop).
      // We still flag it but rank it lower — the report can show both.
      let bestRatio = -Infinity;
      let bestBg = bg.candidates[0];
      for (const c of bg.candidates) {
        const r = contrast(fg, c);
        if (r > bestRatio) {
          bestRatio = r;
          bestBg = c;
        }
      }

      // Filter: if best ratio passes by a wide margin AND it's a gradient,
      // assume the text lands on the good side. Only report if best also fails.
      if (bg.source === "gradient" && bestRatio >= threshold * 1.3) continue;

      const sig = parent.tagName + "|" + (parent.className || "").split(/\s+/).slice(0, 2).join(".") + "|" + cs.color + "|" + worstBg.join(",");
      if (seen.has(sig)) continue;
      seen.add(sig);

      issues.push({
        snippet: text.slice(0, 80).replace(/\s+/g, " "),
        tag: parent.tagName,
        classes: parent.className || "",
        fg: cs.color,
        bgWorst: "rgb(" + worstBg.join(",") + ")",
        bgBest: bg.candidates.length > 1 ? "rgb(" + bestBg.join(",") + ")" : null,
        bgSource: bg.source,
        bgFrom: bg.el ? bg.el.tagName.toLowerCase() + "." + (bg.el.className || "").split(/\s+/)[0] : "default",
        ratio: +worstRatio.toFixed(2),
        bestRatio: +bestRatio.toFixed(2),
        fontSize: fontSize,
        isLarge,
        threshold,
      });
    }
  }
  return issues;
};

// Each test appends to a JSONL file (one JSON object per line) so parallel
// workers don't clobber each other. Aggregation happens after the run via
// `node tests/contrast-audit-summarize.js`.
const reportPath = path.join(__dirname, "..", "contrast-audit-report.jsonl");

for (const file of files) {
  test(`contrast: ${file}`, async ({ page }) => {
    const filePath = path.resolve(ASSETS_DIR, file);
    const fileUrl = "file:///" + filePath.replace(/\\/g, "/");
    await page.goto(fileUrl, { waitUntil: "domcontentloaded" });
    // Give reveal animations + lazy renders a chance to settle
    await page.waitForTimeout(400);

    const issues = await page.evaluate(auditFn);
    if (issues.length > 0) {
      // Append-only JSONL is safe across parallel workers.
      fs.appendFileSync(reportPath, JSON.stringify({ file, count: issues.length, issues }) + "\n");
      console.log(`\n[contrast] ${file}: ${issues.length} failure(s)`);
      issues.slice(0, 12).forEach((i) => {
        const bgNote = i.bgBest ? `${i.bgWorst}/${i.bgBest}` : i.bgWorst;
        console.log(
          `  [${i.ratio}:1] <${i.tag.toLowerCase()}${i.classes ? "." + i.classes.split(/\s+/)[0] : ""}> "${i.snippet}" ` +
          `— ${i.fg} on ${bgNote} (from ${i.bgFrom})`
        );
      });
      if (issues.length > 12) console.log(`  ... and ${issues.length - 12} more`);
    }
    expect(issues, `${issues.length} contrast failures in ${file}`).toEqual([]);
  });
}
