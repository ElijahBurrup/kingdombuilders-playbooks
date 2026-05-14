#!/usr/bin/env node
/**
 * Summarize the JSONL report produced by tests/contrast-audit.spec.js.
 *
 * Run:
 *   node tests/contrast-audit-summarize.js
 *
 * Output: an aggregated JSON file + a human-readable report to stdout.
 */

const fs = require("fs");
const path = require("path");

const REPORT_PATH = path.join(__dirname, "..", "contrast-audit-report.jsonl");
const SUMMARY_PATH = path.join(__dirname, "..", "contrast-audit-summary.json");

if (!fs.existsSync(REPORT_PATH)) {
  console.log("No contrast issues found. Clean run.");
  process.exit(0);
}

const lines = fs.readFileSync(REPORT_PATH, "utf8").trim().split("\n").filter(Boolean);
const entries = lines.map((l) => JSON.parse(l));

const byFile = new Map();
for (const e of entries) {
  // Multiple workers might write the same file's results (retries, etc.).
  // Keep the latest.
  byFile.set(e.file, e);
}
const aggregated = Array.from(byFile.values()).sort((a, b) => b.count - a.count);

const totalIssues = aggregated.reduce((s, x) => s + x.count, 0);

// Pattern aggregation: group by (tag.class, fg, bgWorst) signature
const patternMap = new Map();
for (const file of aggregated) {
  for (const i of file.issues) {
    const sig = `${i.tag.toLowerCase()}.${(i.classes || "").split(/\s+/)[0]}|${i.fg}|${i.bgWorst}`;
    if (!patternMap.has(sig)) patternMap.set(sig, { sig, count: 0, files: new Set(), example: i });
    const p = patternMap.get(sig);
    p.count++;
    p.files.add(file.file);
  }
}
const patterns = Array.from(patternMap.values())
  .map((p) => ({ ...p, files: Array.from(p.files) }))
  .sort((a, b) => b.count - a.count);

fs.writeFileSync(
  SUMMARY_PATH,
  JSON.stringify({ totalFiles: aggregated.length, totalIssues, files: aggregated, patterns }, null, 2)
);

console.log(`Contrast audit summary`);
console.log(`======================`);
console.log(`Files with issues:  ${aggregated.length}`);
console.log(`Total issues:       ${totalIssues}`);
console.log(`Distinct patterns:  ${patterns.length}`);
console.log(``);
console.log(`Top 15 offenders by file:`);
for (const f of aggregated.slice(0, 15)) {
  console.log(`  ${String(f.count).padStart(3)}  ${f.file}`);
}
console.log(``);
console.log(`Top 15 patterns (signature → file count):`);
for (const p of patterns.slice(0, 15)) {
  const example = p.example;
  console.log(`  ${String(p.count).padStart(3)}  [${example.ratio}:1] <${example.tag.toLowerCase()}.${(example.classes || "").split(/\s+/)[0]}> on ${example.bgWorst}`);
  console.log(`       across ${p.files.length} file(s): ${p.files.slice(0, 3).join(", ")}${p.files.length > 3 ? "..." : ""}`);
}
console.log(``);
console.log(`Full summary: ${SUMMARY_PATH}`);
