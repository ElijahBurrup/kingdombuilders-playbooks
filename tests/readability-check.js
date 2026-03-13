#!/usr/bin/env node
/**
 * Readability Check — Pre-deploy contrast and formatting validator for playbook HTML files.
 *
 * Usage:
 *   node tests/readability-check.js assets/The_Title.html
 *   node tests/readability-check.js          # checks ALL assets/*.html
 *
 * Checks:
 *   1. Color contrast: detects dark text on dark backgrounds and light text on light backgrounds
 *   2. Consistent margins: all visual blocks should use 40px margins
 *   3. Deep nesting: flags card-in-card-in-card patterns
 *   4. Ribbon readability: ensures ribbon backgrounds have sufficient opacity
 */

const fs = require('fs');
const path = require('path');

// ── Color utilities ──

function parseColor(str) {
  if (!str) return null;
  str = str.trim().toLowerCase();

  // Named colors
  const named = {
    white: [255, 255, 255], black: [0, 0, 0], red: [255, 0, 0],
    transparent: null
  };
  if (named[str] !== undefined) return named[str];

  // hex
  const hex = str.match(/^#([0-9a-f]{3,8})$/);
  if (hex) {
    let h = hex[1];
    if (h.length === 3) h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2];
    if (h.length === 6 || h.length === 8) {
      return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
    }
  }

  // rgb/rgba
  const rgb = str.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
  if (rgb) return [+rgb[1], +rgb[2], +rgb[3]];

  return null;
}

function relativeLuminance([r, g, b]) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function contrastRatio(c1, c2) {
  const l1 = relativeLuminance(c1);
  const l2 = relativeLuminance(c2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// ── CSS variable resolution ──

function extractCssVars(css) {
  const vars = {};
  const re = /--([\w-]+)\s*:\s*([^;]+)/g;
  let m;
  while ((m = re.exec(css)) !== null) {
    vars[m[1]] = m[2].trim();
  }
  return vars;
}

function resolveVar(value, vars, depth = 0) {
  if (!value || depth > 5) return value;
  return value.replace(/var\(--([\w-]+)\)/g, (_, name) => {
    return vars[name] ? resolveVar(vars[name], vars, depth + 1) : `var(--${name})`;
  });
}

// ── Checks ──

function checkFile(filePath) {
  const html = fs.readFileSync(filePath, 'utf8');
  const fileName = path.basename(filePath);
  const errors = [];
  const warnings = [];

  // Extract CSS variables from <style> blocks
  const styleMatch = html.match(/<style[^>]*>([\s\S]*?)<\/style>/gi);
  let allCss = '';
  if (styleMatch) {
    allCss = styleMatch.map(s => s.replace(/<\/?style[^>]*>/gi, '')).join('\n');
  }
  const cssVars = extractCssVars(allCss);

  // ── Check 1: Inline color on elements with dark/light backgrounds ──
  // Find inline styles with both color and background
  const inlineRe = /style="([^"]+)"/g;
  let im;
  let lineNum = 0;
  const lines = html.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    while ((im = inlineRe.exec(line)) !== null) {
      const style = resolveVar(im[1], cssVars);
      const colorMatch = style.match(/(?:^|;)\s*color\s*:\s*([^;]+)/);
      const bgMatch = style.match(/background(?:-color)?\s*:\s*([^;]+)/);

      if (colorMatch && bgMatch) {
        const fg = parseColor(colorMatch[1]);
        const bg = parseColor(bgMatch[1]);
        if (fg && bg) {
          const ratio = contrastRatio(fg, bg);
          if (ratio < 4.5) {
            errors.push(`Line ${i+1}: Low contrast (${ratio.toFixed(1)}:1) — color ${colorMatch[1]} on background ${bgMatch[1]}`);
          }
        }
      }
    }
  }

  // ── Check 2: CSS class rules — text color vs background combinations ──
  // Find known dark-bg classes and check their text color
  const darkBgClasses = ['memory-inner', 'memory', 'finale', 'dad-voice', 'compare-header', 'prompt-body', 'prompt-head'];
  const lightBgClasses = ['scene', 'wisdom', 'reflect', 'root-ck', 'viz-inner', 'viz-body', 'compare-cell'];

  for (const cls of darkBgClasses) {
    // Check if any element uses this class with a light-bg text color (dark text on dark bg)
    const classRuleRe = new RegExp(`\\.${cls.replace('-', '\\-')}[^{]*\\{([^}]+)\\}`, 'g');
    let cr;
    while ((cr = classRuleRe.exec(allCss)) !== null) {
      const rule = resolveVar(cr[1], cssVars);
      const colorMatch = rule.match(/(?:^|;)\s*color\s*:\s*([^;]+)/);
      if (colorMatch) {
        const fg = parseColor(colorMatch[1]);
        if (fg) {
          const lum = relativeLuminance(fg);
          if (lum < 0.15) {
            errors.push(`CSS .${cls}: Dark text (${colorMatch[1].trim()}, luminance ${lum.toFixed(2)}) on dark background class`);
          }
        }
      }
    }
  }

  for (const cls of lightBgClasses) {
    const classRuleRe = new RegExp(`\\.${cls.replace('-', '\\-')}[^{]*\\{([^}]+)\\}`, 'g');
    let cr;
    while ((cr = classRuleRe.exec(allCss)) !== null) {
      const rule = resolveVar(cr[1], cssVars);
      const colorMatch = rule.match(/(?:^|;)\s*color\s*:\s*([^;]+)/);
      if (colorMatch) {
        const fg = parseColor(colorMatch[1]);
        if (fg) {
          const lum = relativeLuminance(fg);
          if (lum > 0.85) {
            errors.push(`CSS .${cls}: Light text (${colorMatch[1].trim()}, luminance ${lum.toFixed(2)}) on light background class`);
          }
        }
      }
    }
  }

  // ── Check 3: Ribbon readability ──
  const ribbonRe = /\.ribbon\s*\{([^}]+)\}/g;
  let rr;
  while ((rr = ribbonRe.exec(allCss)) !== null) {
    const rule = rr[1];
    // Check background opacity
    const bgOpacity = rule.match(/rgba\([^)]*,\s*([\d.]+)\s*\)/g);
    if (bgOpacity) {
      for (const op of bgOpacity) {
        const alpha = parseFloat(op.match(/,\s*([\d.]+)\s*\)/)[1]);
        if (alpha < 0.07) {
          errors.push(`Ribbon background opacity too low (${alpha}). Minimum 0.08 for readability.`);
        }
      }
    }
  }
  const ribbonTextRe = /\.ribbon\s+p\s*\{([^}]+)\}/g;
  let rt;
  while ((rt = ribbonTextRe.exec(allCss)) !== null) {
    const rule = resolveVar(rt[1], cssVars);
    const colorMatch = rule.match(/color\s*:\s*([^;]+)/);
    if (colorMatch) {
      const fg = parseColor(colorMatch[1]);
      if (fg) {
        // Ribbon is on near-white background, so text needs to be dark enough
        const ratio = contrastRatio(fg, [250, 250, 248]); // approx --stone
        if (ratio < 4.5) {
          warnings.push(`Ribbon text contrast may be low (${ratio.toFixed(1)}:1 against page bg). Color: ${colorMatch[1].trim()}`);
        }
      }
    }
  }

  // ── Check 4: Margin consistency ──
  const blockClasses = ['memory', 'scene', 'viz', 'wisdom', 'reflect', 'dad-voice', 'root-ck', 'compare-table', 'prompt', 'final-test'];
  for (const cls of blockClasses) {
    const re = new RegExp(`\\.${cls.replace('-', '\\-')}\\s*\\{([^}]+)\\}`, 'g');
    let m;
    while ((m = re.exec(allCss)) !== null) {
      const marginMatch = m[1].match(/margin\s*:\s*([^;]+)/);
      if (marginMatch) {
        const val = marginMatch[1].trim();
        if (!val.includes('40px')) {
          warnings.push(`CSS .${cls}: margin is "${val}" — should be "40px 0" for consistency`);
        }
      }
    }
  }

  // ── Check 5: Deep nesting (card-in-card-in-card in HTML) ──
  const cardClasses = ['memory', 'memory-inner', 'memory-lesson', 'viz', 'viz-inner', 'scene', 'wisdom', 'reflect'];
  // Simple: check if .memory-lesson has background or border-radius (making it a visual card)
  const lessonRe = /\.memory-lesson\s*\{([^}]+)\}/g;
  let lr;
  while ((lr = lessonRe.exec(allCss)) !== null) {
    const rule = lr[1];
    if (rule.includes('background') && rule.includes('border-radius')) {
      warnings.push(`.memory-lesson styled as a full card (background + border-radius) — creates 3-level nesting. Use border-top separator instead.`);
    }
  }

  return { fileName, errors, warnings };
}

// ── Main ──

const args = process.argv.slice(2);
let files = [];

if (args.length > 0) {
  files = args.map(a => path.resolve(a));
} else {
  const assetsDir = path.join(__dirname, '..', 'assets');
  files = fs.readdirSync(assetsDir)
    .filter(f => f.endsWith('.html'))
    .map(f => path.join(assetsDir, f));
}

let totalErrors = 0;
let totalWarnings = 0;

for (const file of files) {
  if (!fs.existsSync(file)) {
    console.error(`File not found: ${file}`);
    process.exit(1);
  }
  const result = checkFile(file);

  if (result.errors.length > 0 || result.warnings.length > 0) {
    console.log(`\n=== ${result.fileName} ===`);
    for (const e of result.errors) {
      console.log(`  ERROR: ${e}`);
    }
    for (const w of result.warnings) {
      console.log(`  WARN:  ${w}`);
    }
  }

  totalErrors += result.errors.length;
  totalWarnings += result.warnings.length;
}

console.log(`\n--- Summary: ${files.length} file(s), ${totalErrors} error(s), ${totalWarnings} warning(s) ---`);

if (totalErrors > 0) {
  console.log('FAILED — fix all errors before deploying.');
  process.exit(1);
} else {
  console.log('PASSED');
  process.exit(0);
}
