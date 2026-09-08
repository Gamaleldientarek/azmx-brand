#!/usr/bin/env python3
"""
brand-check.py — AZMX brand linter.

Checks .html / .css / .md / .svg files against the AZMX brand system:

  1. Hex colours outside the legal palette (nearest legal token suggested)
  2. Non-brand font-family declarations
  3. font-style: italic / oblique  (the serif has no italic; it renders faux-slanted)
  4. padding / margin / gap px values off the 8-16-24-40-64-96-128-160 scale
  5. Electric #001AFF as text on a dark surface, or as a large fill behind text
  6. Chevron / arrow art used as background decoration or at low opacity

The legal palette is parsed from references/colors.md AT RUNTIME, so the linter
never goes stale when the brand changes.

Usage:
    python3 scripts/brand-check.py [file-or-dir ...] [options]

Options:
    -q, --quiet           Suppress progress output, show only violations
    --report              Generate compliance report (requires --format and --output)
    --format FORMAT       Report format: json, html, or markdown
    --output PATH         Output file path for the report
    --with-trends         Include trend analysis comparing against historical reports
    --save-history        Save report to reports/ directory with timestamp
    --help                Show this help message

Examples:
    # Basic brand check (terminal output)
    python3 scripts/brand-check.py index.html

    # Check entire repo quietly
    python3 scripts/brand-check.py . --quiet

    # Generate JSON compliance report
    python3 scripts/brand-check.py . --report --format json --output report.json

    # Generate HTML report with historical trends
    python3 scripts/brand-check.py . --report --format html --output report.html --with-trends

    # Generate and save markdown report to reports/ directory
    python3 scripts/brand-check.py . --report --format markdown --output reports/audit.md --save-history

With no paths it scans the whole repo. Exits 1 if any blocker was found.
"""

from __future__ import annotations

import bisect
import datetime
import glob
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

SPACING_SCALE = (8, 16, 24, 40, 64, 96, 128, 160)

BRAND_FAMILIES = {
    "thmanyah serif display",
    "azm x",
    "azm x variable",
}

# Generic / keyword families that are always acceptable as a fallback tail.
GENERIC_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy",
    "system-ui", "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded",
    "math", "emoji", "fangsong",
    "inherit", "initial", "unset", "revert", "revert-layer", "none",
}

SPACING_PROPS = re.compile(
    r"^(padding|margin)(-(top|right|bottom|left|inline|block)"
    r"(-(start|end))?)?$|^(row-|column-|grid-|grid-row-|grid-column-)?gap$"
)

CHEVRON_WORD = re.compile(r"chevron|caret|(?<![a-z])arrow", re.I)

# Elements whose inline background is *data* (a sampled image colour, a RAG
# swatch, a palette chip) rather than a brand styling decision. Without this,
# a swatch gallery reports hundreds of false "off-palette" hits.
SWATCH_CLASS = re.compile(
    r"\b(sw|swatch|swatches|chip|dot|pdot|cdot|hexdot|color-?chip|color-?dot|"
    r"colour-?chip|colour-?dot|legend-?key)\b"
)

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".cache",
}
# Binary-ish / generated asset trees that hold no hand-authored CSS.
SKIP_PATH_PARTS = {
    os.path.join("assets", "images"),
    os.path.join("assets", "fonts"),
}

EXTENSIONS = {".html", ".htm", ".css", ".md", ".svg"}

SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2}

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
SEV_COLOR = {"blocker": "\033[31m", "major": "\033[33m", "minor": "\033[36m"}


# --------------------------------------------------------------------------
# Palette, parsed from references/colors.md at runtime
# --------------------------------------------------------------------------

HEX_RE = re.compile(r"#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})\b")


def norm_hex(raw: str) -> str | None:
    """Normalise a hex token to #RRGGBB. Returns None if it carries alpha 0."""
    h = raw.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    elif len(h) in (6, 8):
        h = h[:6]
    else:
        return None
    return "#" + h.upper()


def rgb(hex6: str) -> tuple[int, int, int]:
    h = hex6.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(hex6: str) -> float:
    """Relative luminance, 0-1."""
    def lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(hex6)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


class Palette:
    def __init__(self, legal: dict[str, str], source: str):
        self.legal = legal              # #RRGGBB -> token name
        self.source = source

    def is_legal(self, hex6: str) -> bool:
        return hex6 in self.legal

    def name(self, hex6: str) -> str:
        return self.legal.get(hex6, hex6)

    def nearest(self, hex6: str) -> tuple[str, str, float]:
        r1, g1, b1 = rgb(hex6)
        best, bestd = None, 1e9
        for cand in self.legal:
            r2, g2, b2 = rgb(cand)
            d = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
            if d < bestd:
                best, bestd = cand, d
        return best, self.legal[best], bestd


def find_colors_md(start: str) -> str | None:
    """Walk up from a path looking for references/colors.md."""
    cur = os.path.abspath(start)
    if os.path.isfile(cur):
        cur = os.path.dirname(cur)
    while True:
        cand = os.path.join(cur, "references", "colors.md")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_palette(colors_md: str) -> Palette:
    """
    Parse every hex in the markdown tables. Rows carrying exactly one hex also
    donate their first cell as the token name.
    """
    legal: dict[str, str] = {}
    with open(colors_md, encoding="utf-8") as fh:
        for line in fh:
            hexes = [norm_hex(m.group(0)) for m in HEX_RE.finditer(line)]
            hexes = [h for h in hexes if h]
            if not hexes:
                continue
            token = None
            if line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells:
                    token = re.sub(r"[`*]", "", cells[0]).strip()
                    if not token or HEX_RE.search(token):
                        token = None
            for h in hexes:
                if h not in legal or (token and len(hexes) == 1):
                    legal[h] = token if (token and len(hexes) == 1) else legal.get(h, h)
    if not legal:
        raise SystemExit(f"brand-check: no hex values found in {colors_md}")
    return Palette(legal, colors_md)


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------

class Finding:
    __slots__ = ("path", "line", "severity", "code", "what", "fix")

    def __init__(self, path, line, severity, code, what, fix):
        self.path = path
        self.line = line
        self.severity = severity
        self.code = code
        self.what = what
        self.fix = fix


class ComplianceReport:
    """Aggregates brand compliance findings across multiple files."""
    __slots__ = (
        'total_files', 'pass_count', 'fail_count', 'findings_by_category',
        'severity_counts', 'top_violations', 'per_file_results', 'scan_timestamp'
    )

    def __init__(self):
        self.total_files = 0
        self.pass_count = 0  # files with no findings
        self.fail_count = 0  # files with findings
        self.findings_by_category = {}  # code -> count dict
        self.severity_counts = {"blocker": 0, "major": 0, "minor": 0}
        self.top_violations = []  # list of (code, count) tuples
        self.per_file_results = {}  # path -> list of Finding objects
        self.scan_timestamp = None

    def add_findings(self, findings: list[Finding], files_scanned: int):
        """Aggregate findings from a batch of files."""
        self.total_files = files_scanned
        self.scan_timestamp = datetime.datetime.now().isoformat()

        # Count files with/without findings
        files_with_findings = set()
        for f in findings:
            files_with_findings.add(f.path)
            self.per_file_results.setdefault(f.path, []).append(f)
            self.severity_counts[f.severity] += 1
            self.findings_by_category[f.code] = self.findings_by_category.get(f.code, 0) + 1

        self.fail_count = len(files_with_findings)
        self.pass_count = files_scanned - self.fail_count

        # Compute top violations
        violation_list = [(code, count) for code, count in self.findings_by_category.items()]
        self.top_violations = sorted(violation_list, key=lambda x: x[1], reverse=True)[:5]

    def to_json(self, include_trends=False):
        """Generate JSON report."""
        data = {
            "total_findings": sum(self.severity_counts.values()),
            "has_blockers": self.severity_counts["blocker"] > 0,
            "summary": {
                "by_severity": self.severity_counts,
                "by_code": self.findings_by_category
            },
            "files_affected": len(self.per_file_results),
            "findings": [
                {
                    "path": f.path,
                    "line": f.line,
                    "severity": f.severity,
                    "code": f.code,
                    "what": f.what,
                    "fix": f.fix
                }
                for path in sorted(self.per_file_results.keys())
                for f in self.per_file_results[path]
            ],
            "scan_timestamp": self.scan_timestamp
        }

        if include_trends:
            data["trend"] = self._compute_trends()

        return json.dumps(data, indent=2)

    def to_html(self):
        """Generate HTML report with AZMX brand styling."""
        def escape(text):
            """Escape HTML special characters."""
            return (str(text)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#x27;"))

        total_findings = sum(self.severity_counts.values())

        # Build findings HTML
        findings_html = ""
        for path in sorted(self.per_file_results.keys()):
            findings_html += f'    <div class="file-section">\n'
            findings_html += f'      <h3>{escape(path)} ({len(self.per_file_results[path])} issues)</h3>\n'
            findings_html += f'      <ul class="findings-list">\n'
            for f in self.per_file_results[path]:
                findings_html += f'        <li class="finding {escape(f.severity)}">\n'
                findings_html += f'          <span class="severity-badge">{escape(f.severity).upper()}</span>\n'
                findings_html += f'          <span class="code">[{escape(f.code)}]</span>\n'
                findings_html += f'          Line {f.line}: {escape(f.what)}<br>\n'
                findings_html += f'          <span class="fix">Fix: {escape(f.fix)}</span>\n'
                findings_html += f'        </li>\n'
            findings_html += f'      </ul>\n'
            findings_html += f'    </div>\n'

        # Build top violations HTML
        top_violations_html = ""
        for code, count in self.top_violations:
            top_violations_html += f'      <li><strong>{escape(code)}</strong>: {count} occurrences</li>\n'

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AZMX Brand Compliance Report</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: system-ui, -apple-system, sans-serif;
      line-height: 1.6;
      color: #1a1a1a;
      background: #f5f5f5;
      padding: 24px;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 40px;
    }}

    h1 {{
      color: #001AFF;
      font-size: 32px;
      margin-bottom: 8px;
    }}

    .timestamp {{
      color: #666;
      font-size: 14px;
      margin-bottom: 32px;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 40px;
    }}

    .stat-card {{
      background: #f8f9fa;
      padding: 24px;
      border-radius: 8px;
      border-left: 4px solid #001AFF;
    }}

    .stat-card h2 {{
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #666;
      margin-bottom: 8px;
    }}

    .stat-card .value {{
      font-size: 36px;
      font-weight: bold;
      color: #1a1a1a;
    }}

    .section {{
      margin-bottom: 40px;
    }}

    .section h2 {{
      font-size: 24px;
      margin-bottom: 16px;
      color: #1a1a1a;
      border-bottom: 2px solid #e0e0e0;
      padding-bottom: 8px;
    }}

    .severity-breakdown {{
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
    }}

    .severity-item {{
      flex: 1;
      min-width: 150px;
      padding: 16px;
      border-radius: 8px;
      text-align: center;
    }}

    .severity-item.blocker {{
      background: #ffe5e5;
      color: #c00;
    }}

    .severity-item.major {{
      background: #fff3cd;
      color: #856404;
    }}

    .severity-item.minor {{
      background: #e7f3ff;
      color: #004085;
    }}

    .severity-item .count {{
      font-size: 32px;
      font-weight: bold;
    }}

    .severity-item .label {{
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 4px;
    }}

    .file-section {{
      margin-bottom: 32px;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 16px;
    }}

    .file-section h3 {{
      font-size: 18px;
      margin-bottom: 12px;
      color: #001AFF;
    }}

    .findings-list {{
      list-style: none;
    }}

    .finding {{
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
      border-left: 4px solid;
    }}

    .finding.blocker {{
      background: #ffe5e5;
      border-left-color: #c00;
    }}

    .finding.major {{
      background: #fff3cd;
      border-left-color: #856404;
    }}

    .finding.minor {{
      background: #e7f3ff;
      border-left-color: #004085;
    }}

    .severity-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;
      margin-right: 8px;
    }}

    .finding.blocker .severity-badge {{
      background: #c00;
      color: white;
    }}

    .finding.major .severity-badge {{
      background: #856404;
      color: white;
    }}

    .finding.minor .severity-badge {{
      background: #004085;
      color: white;
    }}

    .code {{
      font-family: monospace;
      color: #666;
      margin-right: 8px;
    }}

    .fix {{
      display: block;
      margin-top: 4px;
      font-size: 14px;
      color: #666;
      font-style: italic;
    }}

    ul {{
      margin-left: 24px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>AZMX Brand Compliance Report</h1>
    <div class="timestamp">Generated: {escape(self.scan_timestamp)}</div>

    <div class="summary">
      <div class="stat-card">
        <h2>Total Files</h2>
        <div class="value">{self.total_files}</div>
      </div>
      <div class="stat-card">
        <h2>Files Passed</h2>
        <div class="value">{self.pass_count}</div>
      </div>
      <div class="stat-card">
        <h2>Files Failed</h2>
        <div class="value">{self.fail_count}</div>
      </div>
      <div class="stat-card">
        <h2>Total Issues</h2>
        <div class="value">{total_findings}</div>
      </div>
    </div>

    <div class="section">
      <h2>Severity Breakdown</h2>
      <div class="severity-breakdown">
        <div class="severity-item blocker">
          <div class="count">{self.severity_counts["blocker"]}</div>
          <div class="label">Blockers</div>
        </div>
        <div class="severity-item major">
          <div class="count">{self.severity_counts["major"]}</div>
          <div class="label">Major</div>
        </div>
        <div class="severity-item minor">
          <div class="count">{self.severity_counts["minor"]}</div>
          <div class="label">Minor</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>Top Violations</h2>
      <ul>
{top_violations_html}      </ul>
    </div>

    <div class="section">
      <h2>Detailed Findings</h2>
{findings_html}    </div>
  </div>
</body>
</html>'''

        return html

    def to_markdown(self):
        """Generate markdown report."""
        total_findings = sum(self.severity_counts.values())

        # Emoji indicators
        severity_emoji = {
            "blocker": "🔴",
            "major": "🟡",
            "minor": "🔵"
        }

        md = f"# AZMX Brand Compliance Report\n\n"
        md += f"**Generated:** {self.scan_timestamp}\n\n"
        md += f"---\n\n"

        # Summary stats
        md += f"## Summary\n\n"
        md += f"| Metric | Value |\n"
        md += f"|--------|-------|\n"
        md += f"| Total Files Scanned | {self.total_files} |\n"
        md += f"| Files Passed | {self.pass_count} |\n"
        md += f"| Files Failed | {self.fail_count} |\n"
        md += f"| Total Issues | {total_findings} |\n"
        md += f"\n"

        # Severity breakdown
        md += f"## Severity Breakdown\n\n"
        md += f"| Severity | Count |\n"
        md += f"|----------|-------|\n"
        md += f"| {severity_emoji['blocker']} Blockers | {self.severity_counts['blocker']} |\n"
        md += f"| {severity_emoji['major']} Major | {self.severity_counts['major']} |\n"
        md += f"| {severity_emoji['minor']} Minor | {self.severity_counts['minor']} |\n"
        md += f"\n"

        # Top violations
        md += f"## Top Violations\n\n"
        for i, (code, count) in enumerate(self.top_violations, 1):
            md += f"{i}. **{code}**: {count} occurrences\n"
        md += f"\n"

        # Detailed findings
        md += f"## Detailed Findings\n\n"
        for path in sorted(self.per_file_results.keys()):
            md += f"### {path}\n\n"
            md += f"**Issues:** {len(self.per_file_results[path])}\n\n"
            for f in self.per_file_results[path]:
                emoji = severity_emoji.get(f.severity, "")
                md += f"- {emoji} **{f.severity.upper()}** [{f.code}] Line {f.line}\n"
                md += f"  - **What:** {f.what}\n"
                md += f"  - **Fix:** {f.fix}\n"
            md += f"\n"

        return md

    def _get_history_dir(self):
        """Get directory for storing historical reports."""
        return ".brand-reports"

    def _load_latest_history(self):
        """Load most recent historical report from .brand-reports/ directory."""
        history_dir = self._get_history_dir()
        if not os.path.exists(history_dir):
            return None

        reports = glob.glob(os.path.join(history_dir, "*.json"))
        if not reports:
            return None

        # Sort by modification time, get most recent
        reports.sort(key=os.path.getmtime, reverse=True)

        try:
            with open(reports[0], 'r') as f:
                return json.load(f)
        except:
            return None

    def _compute_trends(self):
        """Compare current report with historical report."""
        prev = self._load_latest_history()

        if not prev:
            return {
                "status": "no_history",
                "message": "No historical data available for comparison",
                "previous_report": None,
                "changes": None
            }

        current_total = sum(self.severity_counts.values())
        prev_total = prev.get("total_findings", 0)
        delta = current_total - prev_total

        if delta < 0:
            status = "improved"
            message = f"Violations decreased by {abs(delta)} ({prev_total} → {current_total})"
        elif delta > 0:
            status = "degraded"
            message = f"Violations increased by {delta} ({prev_total} → {current_total})"
        else:
            status = "stable"
            message = f"No change in total violations ({current_total})"

        return {
            "status": status,
            "message": message,
            "previous_report": {
                "timestamp": prev.get("scan_timestamp"),
                "total_findings": prev_total,
                "by_severity": prev.get("summary", {}).get("by_severity", {}),
                "by_code": prev.get("summary", {}).get("by_code", {})
            },
            "changes": {
                "total": delta,
                "by_severity": {
                    sev: self.severity_counts[sev] - prev.get("summary", {}).get("by_severity", {}).get(sev, 0)
                    for sev in ("blocker", "major", "minor")
                },
                "by_code": {
                    code: self.findings_by_category.get(code, 0) - prev.get("summary", {}).get("by_code", {}).get(code, 0)
                    for code in set(list(self.findings_by_category.keys()) + list(prev.get("summary", {}).get("by_code", {}).keys()))
                }
            }
        }

    def save_to_history(self):
        """Save current report to .brand-reports/ directory for future comparisons."""
        history_dir = self._get_history_dir()
        os.makedirs(history_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = self.scan_timestamp.replace(":", "-").replace(".", "-")
        filename = os.path.join(history_dir, f"report-{timestamp}.json")

        # Save as JSON
        with open(filename, 'w') as f:
            f.write(self.to_json(include_trends=False))

        # Cleanup old reports (keep last 10)
        self._cleanup_old_reports()

    def _cleanup_old_reports(self):
        """Keep only the 10 most recent reports."""
        history_dir = self._get_history_dir()
        reports = glob.glob(os.path.join(history_dir, "*.json"))

        if len(reports) > 10:
            # Sort by modification time
            reports.sort(key=os.path.getmtime, reverse=True)
            # Remove old reports
            for old_report in reports[10:]:
                os.remove(old_report)


# --------------------------------------------------------------------------
# Source extraction: pull the CSS-bearing regions out of each file type
# --------------------------------------------------------------------------

STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
STYLE_ATTR_RE = re.compile(r"""\bstyle\s*=\s*(["'])(.*?)\1""", re.S | re.I)
PRESENT_ATTR_RE = re.compile(
    r"""\b(fill|stroke|stop-color|flood-color|lighting-color|color|font-family|font-style)"""
    r"""\s*=\s*(["'])(.*?)\2""",
    re.S | re.I,
)
FENCE_RE = re.compile(r"^([ \t]*)(```+|~~~+)", re.M)


def strip_comments(css: str) -> str:
    """Blank out /* */ comments, preserving offsets and newlines."""
    out = list(css)
    for m in re.finditer(r"/\*.*?\*/", css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def enclosing_tag(text: str, pos: int) -> str:
    """Return the opening-tag source that contains the offset `pos`."""
    start = text.rfind("<", max(0, pos - 2000), pos)
    if start == -1:
        return ""
    end = text.find(">", pos)
    return text[start: end + 1] if end != -1 else text[start: pos + 1]


def css_regions(text: str, ext: str) -> list[tuple[int, str, str, str]]:
    """
    Return [(offset, source, kind, owner_tag)] regions of CSS-ish content.
    kind: 'css' (rule blocks) | 'decls' (bare declaration list) | 'attr'
    """
    regions: list[tuple[int, str, str, str]] = []
    if ext == ".css":
        regions.append((0, text, "css", ""))
        return regions

    if ext in (".html", ".htm", ".svg"):
        for m in STYLE_BLOCK_RE.finditer(text):
            regions.append((m.start(1), m.group(1), "css", ""))
        for m in STYLE_ATTR_RE.finditer(text):
            regions.append((m.start(2), m.group(2), "decls", enclosing_tag(text, m.start())))
        for m in PRESENT_ATTR_RE.finditer(text):
            prop = m.group(1).lower()
            regions.append((m.start(3), f"{prop}:{m.group(3)}", "decls",
                            enclosing_tag(text, m.start())))
        return regions

    if ext == ".md":
        # Only fenced code blocks — prose and reference tables legitimately
        # quote hexes and font names, and flagging those is noise. Within the
        # fences, only markup languages are parsed: a ```bash or ```text block
        # can hold hexes as data (recolour maps, palette dumps) and is not a
        # styling decision.
        lines = text.splitlines(keepends=True)
        offset, inside, buf, buf_off, lang = 0, False, [], 0, ""
        for ln in lines:
            fence = re.match(r"^[ \t]*(?:```+|~~~+)[ \t]*([\w+-]*)", ln)
            if fence:
                if inside:
                    sub = _md_fence_ext(lang, "".join(buf))
                    if sub:
                        for off2, src2, kind2, own2 in css_regions("".join(buf), sub):
                            regions.append((buf_off + off2, src2, kind2, own2))
                    buf, inside, lang = [], False, ""
                else:
                    inside = True
                    lang = fence.group(1).lower()
                    buf_off = offset + len(ln)
            elif inside:
                buf.append(ln)
            offset += len(ln)
        return regions

    return regions


MARKUP_FENCE = {
    "css": ".css", "scss": ".css", "less": ".css",
    "html": ".html", "htm": ".html", "xml": ".html", "svg": ".svg",
}


def _md_fence_ext(lang: str, body: str) -> str | None:
    """Map a fence language to a parser, or None if the block is not markup."""
    if lang in MARKUP_FENCE:
        return MARKUP_FENCE[lang]
    if lang:
        return None                      # bash / text / json / py / jsx …
    # Untagged fence: accept only if it actually looks like CSS or HTML.
    if re.search(r"<[a-zA-Z][^>]*>", body):
        return ".html"
    if re.search(r"\{[^{}]*[\w-]+\s*:[^{};]+;", body, re.S):
        return ".css"
    return None


# --------------------------------------------------------------------------
# CSS block / declaration parsing
# --------------------------------------------------------------------------

class Decl:
    __slots__ = ("prop", "value", "offset")

    def __init__(self, prop, value, offset):
        self.prop = prop
        self.value = value
        self.offset = offset


class Block:
    __slots__ = ("selector", "decls", "offset", "owner_tag")

    def __init__(self, selector, decls, offset, owner_tag=""):
        self.selector = selector
        self.decls = decls
        self.offset = offset
        self.owner_tag = owner_tag


def parse_decls(body: str, base: int) -> list[Decl]:
    decls, pos = [], 0
    depth = 0
    start = 0
    # split on ';' at paren-depth 0
    for i, ch in enumerate(body):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            chunk, off = body[start:i], start
            d = _mk_decl(chunk, base + off)
            if d:
                decls.append(d)
            start = i + 1
    d = _mk_decl(body[start:], base + start)
    if d:
        decls.append(d)
    return decls


def _mk_decl(chunk: str, offset: int) -> Decl | None:
    if ":" not in chunk:
        return None
    lead = len(chunk) - len(chunk.lstrip())
    prop, _, value = chunk.partition(":")
    return Decl(prop.strip().lower(), value.strip(), offset + lead)


def parse_blocks(css: str, base: int, owner_tag: str = "") -> list[Block]:
    """Innermost brace blocks only, so @media wrappers do not swallow rules."""
    css = strip_comments(css)
    blocks: list[Block] = []
    stack: list[tuple[int, bool]] = []   # (open_pos, had_child)
    last_close = 0
    for i, ch in enumerate(css):
        if ch == "{":
            if stack:
                op, _ = stack[-1]
                stack[-1] = (op, True)
            stack.append((i, False))
        elif ch == "}":
            if not stack:
                continue
            op, had_child = stack.pop()
            if not had_child:
                sel_start = max(last_close, css.rfind("{", 0, op) + 1)
                sel_start = max(sel_start, css.rfind("}", 0, op) + 1)
                selector = " ".join(css[sel_start:op].split())
                body = css[op + 1:i]
                blocks.append(Block(selector, parse_decls(body, base + op + 1),
                                    base + sel_start, owner_tag))
            last_close = i + 1
    return blocks


# --------------------------------------------------------------------------
# Value helpers
# --------------------------------------------------------------------------

VAR_RE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,([^()]*(?:\([^()]*\)[^()]*)*))?\)")
FUNC_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)


def resolve_vars(value: str, custom: dict[str, str], depth: int = 0) -> str:
    if depth > 6 or "var(" not in value:
        return value
    def sub(m):
        name, fallback = m.group(1), (m.group(2) or "").strip()
        if name in custom:
            return custom[name]
        return fallback
    return resolve_vars(VAR_RE.sub(sub, value), custom, depth + 1)


def hexes_in(value: str) -> list[tuple[str, str]]:
    """[(normalised, raw)] for every hex literal in a value."""
    out = []
    for m in HEX_RE.finditer(value):
        n = norm_hex(m.group(0))
        if n:
            out.append((n, m.group(0)))
    return out


def first_color_hex(value: str, custom: dict[str, str]) -> str | None:
    resolved = resolve_vars(value, custom)
    hs = hexes_in(resolved)
    return hs[0][0] if hs else None


def split_families(value: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip().strip("'\"").strip() for p in parts if p.strip()]


def px_values(value: str) -> list[tuple[float, str]]:
    """Every px length in the value, including inside clamp()/min()/max()/calc()."""
    return [(abs(float(m.group(1))), m.group(0))
            for m in re.finditer(r"(-?\d*\.?\d+)px\b", value)]


def base_selector(sel: str) -> str:
    """`.copy[data-copied="1"]:hover` -> `.copy` ; `.tagbar button:hover` -> `.tagbar button`"""
    sel = sel.split(",")[0]
    sel = re.sub(r"\[[^\]]*\]", "", sel)
    sel = re.sub(r"::?[\w-]+(\([^)]*\))?", "", sel)
    return " ".join(sel.split())


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------

def is_swatch(owner_tag: str) -> bool:
    m = re.search(r"""\bclass\s*=\s*(["'])(.*?)\1""", owner_tag, re.I | re.S)
    return bool(m and SWATCH_CLASS.search(m.group(2)))


def check_file(path: str, palette: Palette) -> list[Finding]:
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [Finding(path, 0, "major", "IO", f"cannot read: {exc}", "check the path")]

    nl = [i for i, c in enumerate(text) if c == "\n"]
    def line_of(off: int) -> int:
        return bisect.bisect_right(nl, off) + 1

    regions = css_regions(text, ext)

    # Pass 1 — gather custom properties and per-selector text colours.
    all_blocks: list[Block] = []
    for off, src, kind, owner in regions:
        if kind == "css":
            all_blocks.extend(parse_blocks(src, off, owner))
        else:
            all_blocks.append(Block("", parse_decls(src, off), off, owner))

    custom: dict[str, str] = {}
    for b in all_blocks:
        for d in b.decls:
            if d.prop.startswith("--"):
                custom.setdefault(d.prop, d.value)
    for k in list(custom):
        custom[k] = resolve_vars(custom[k], custom)

    text_color_by_base: dict[str, str] = {}
    for b in all_blocks:
        if not b.selector:
            continue
        for d in b.decls:
            if d.prop == "color":
                h = first_color_hex(d.value, custom)
                if h:
                    text_color_by_base.setdefault(base_selector(b.selector), h)

    findings: list[Finding] = []
    seen: set[tuple[int, str, str]] = set()

    def add(off, severity, code, what, fix):
        ln = line_of(off)
        key = (ln, code, what)
        if key in seen:
            return
        seen.add(key)
        findings.append(Finding(path, ln, severity, code, what, fix))

    for b in all_blocks:
        swatch = is_swatch(b.owner_tag)
        bg_hex = None
        color_hex = None
        color_off = None
        bg_off = None

        for d in b.decls:
            prop, value = d.prop, d.value

            # ---- 1. palette -------------------------------------------------
            if not swatch:
                resolved_for_hex = value
                for norm, raw in hexes_in(resolved_for_hex):
                    if palette.is_legal(norm):
                        continue
                    near, near_name, dist = palette.nearest(norm)
                    sev = "minor" if dist <= 12 else "major"
                    tail = " (near-miss — snap it)" if sev == "minor" else ""
                    add(d.offset, sev, "COLOR",
                        f"{raw} in `{prop}` is not in the palette{tail}",
                        f"use {near_name} {near} (ΔRGB {dist:.0f}) "
                        f"or add the tone to references/colors.md")

            # ---- 2. fonts ---------------------------------------------------
            if prop == "font-family" or (prop.startswith("--") and "font" in prop):
                fams = split_families(resolve_vars(value, custom))
                if fams and not (len(fams) == 1 and fams[0].lower() in GENERIC_FAMILIES):
                    for idx, fam in enumerate(fams):
                        low = fam.lower()
                        if low in BRAND_FAMILIES or low in GENERIC_FAMILIES:
                            continue
                        if low.startswith("var(") or not low:
                            continue
                        primary = idx == 0
                        add(d.offset,
                            "blocker" if primary else "minor",
                            "FONT",
                            f"non-brand font family \"{fam}\" "
                            f"{'set as the primary family' if primary else 'in the fallback stack'} "
                            f"in `{prop}`",
                            "the system has two families only: "
                            "\"thmanyah serif display\" (display) and \"Azm X\" (body). "
                            + ("replace it." if primary
                               else "drop the fallback or reduce it to the generic keyword."))
            elif prop == "font" and ("\"" in value or "'" in value):
                for fam in re.findall(r"""["']([^"']+)["']""", value):
                    if fam.lower() not in BRAND_FAMILIES:
                        add(d.offset, "blocker", "FONT",
                            f"non-brand font family \"{fam}\" in the `font` shorthand",
                            "use \"thmanyah serif display\" or \"Azm X\".")

            # ---- 3. italics -------------------------------------------------
            if prop == "font-style" and re.search(r"\b(italic|oblique)\b", value, re.I):
                add(d.offset, "blocker", "ITALIC",
                    f"`font-style: {value.strip()}`",
                    "no italics anywhere — thmanyah serif display ships no italic, so "
                    "this renders a faux slant. Express emphasis with scale, weight, or colour.")

            # ---- 4. spacing scale -------------------------------------------
            if SPACING_PROPS.match(prop):
                for val, raw in px_values(resolve_vars(value, custom)):
                    if val == 0 or val in SPACING_SCALE:
                        continue
                    near = min(SPACING_SCALE, key=lambda s: abs(s - val))
                    add(d.offset, "minor", "SPACING",
                        f"`{prop}: … {raw} …` is off the spacing scale",
                        f"use {near}px. The only permitted values are "
                        f"{' · '.join(str(s) for s in SPACING_SCALE)}.")

            # ---- 5/6 collect for block-level checks -------------------------
            if prop in ("background", "background-color", "background-image"):
                h = first_color_hex(value, custom)
                if h and bg_hex is None:
                    bg_hex, bg_off = h, d.offset
            if prop == "color":
                h = first_color_hex(value, custom)
                if h and color_hex is None:
                    color_hex, color_off = h, d.offset

            # ---- 6. chevrons as decoration ----------------------------------
            if prop in ("background", "background-image", "mask", "mask-image",
                        "-webkit-mask", "-webkit-mask-image", "content", "list-style-image"):
                for m in FUNC_URL_RE.finditer(value):
                    if CHEVRON_WORD.search(m.group(2)):
                        add(d.offset, "blocker", "CHEVRON",
                            f"chevron/arrow asset used as a background in `{prop}`: {m.group(2)}",
                            "chevrons as background decoration are banned (design-system v1.1). "
                            "Backgrounds stay solid or gradient. Use the chevron functionally: "
                            "photo mask, section tick, or list bullet.")

        # low-opacity chevron field
        chevron_ctx = CHEVRON_WORD.search(b.selector or "") or \
            CHEVRON_WORD.search(b.owner_tag or "")
        if chevron_ctx:
            for d in b.decls:
                if d.prop == "opacity":
                    try:
                        o = float(d.value.strip().rstrip("%"))
                        if d.value.strip().endswith("%"):
                            o /= 100.0
                    except ValueError:
                        continue
                    if 0 < o < 0.5:
                        add(d.offset, "major", "CHEVRON",
                            f"chevron element at opacity {d.value.strip()} "
                            f"(selector `{b.selector or b.owner_tag[:40]}`)",
                            "ghost / low-opacity chevron field textures are banned. "
                            "Either make it a functional foreground chevron at full "
                            "strength, or remove it and use negative space.")

        # ---- 5. Electric on dark / Electric behind text ----------------------
        if not swatch:
            electric = "#001AFF"
            if color_hex == electric and bg_hex and luminance(bg_hex) < 0.35:
                add(color_off, "blocker", "ELECTRIC",
                    f"Electric #001AFF set as text over the dark surface {bg_hex} "
                    f"(selector `{b.selector or 'inline style'}`)",
                    "Electric fails contrast on dark. Use Light Blue #5D8FFF for the "
                    "accent on dark surfaces, White #FFFFFF for titles, "
                    "Blue 100 #DDE8FF for body.")
            if bg_hex == electric:
                inherited = text_color_by_base.get(base_selector(b.selector), None) \
                    if b.selector else None
                if color_hex or inherited:
                    add(bg_off, "major", "ELECTRIC",
                        f"Electric #001AFF used as a fill behind text "
                        f"(selector `{b.selector or 'inline style'}`)",
                        "Electric is punctuation, never a large fill behind text (it vibrates). "
                        "Fill with Dark Navy #040038 or Blue 50 #F0F5FF, and keep Electric "
                        "for the accent mark, rule, or single highlighted word.")

    findings.sort(key=lambda f: (f.line, SEVERITY_ORDER[f.severity]))
    return findings


# --------------------------------------------------------------------------
# Walking + reporting
# --------------------------------------------------------------------------

def collect(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            rel = os.path.relpath(root, p)
            if any(rel.startswith(part) for part in SKIP_PATH_PARTS):
                dirs[:] = []
                continue
            for f in sorted(files):
                if os.path.splitext(f)[1].lower() in EXTENSIONS:
                    out.append(os.path.join(root, f))
    seen, uniq = set(), []
    for p in out:
        rp = os.path.realpath(p)
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def report(findings: list[Finding], scanned: int, palette: Palette,
           quiet: bool, color: bool) -> int:
    def c(s, code):
        return f"{code}{s}{RESET}" if color else s

    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.path, []).append(f)

    counts = {"blocker": 0, "major": 0, "minor": 0}
    for f in findings:
        counts[f.severity] += 1

    if not quiet:
        print(c("AZMX brand check", BOLD))
        print(c(f"palette: {len(palette.legal)} legal tones from "
                f"{os.path.relpath(palette.source)}", DIM))
        print(c(f"scanned: {scanned} file(s)", DIM))
        print()

    for path in sorted(by_file):
        rel = os.path.relpath(path)
        if rel.startswith(".."):
            rel = os.path.abspath(path)
        print(c(rel, BOLD))
        for f in by_file[path]:
            sev = c(f"{f.severity:<7}", SEV_COLOR[f.severity])
            print(f"  {f.line:>5}  {sev} {f.code:<8} {f.what}")
            print(f"         {c('fix:', DIM)} {f.fix}")
        print()

    if not quiet:
        if findings:
            print(c(f"{counts['blocker']} blocker · {counts['major']} major · "
                    f"{counts['minor']} minor", BOLD))
        else:
            print(c("clean — no brand violations found", BOLD))

    return 1 if counts["blocker"] else 0


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0

    # Parse flags
    quiet = "--quiet" in argv or "-q" in argv
    report_mode = "--report" in argv
    with_trends = "--with-trends" in argv

    # Parse --format (default: text)
    format_type = "text"
    if "--format" in argv:
        idx = argv.index("--format")
        if idx + 1 < len(argv):
            format_type = argv[idx + 1].lower()
            if format_type not in ("text", "json", "html", "markdown"):
                print(f"brand-check: invalid format '{format_type}' (must be: text, json, html, markdown)", file=sys.stderr)
                return 2
        else:
            print("brand-check: --format requires a format argument", file=sys.stderr)
            return 2

    # Parse --output
    output_path = None
    if "--output" in argv:
        idx = argv.index("--output")
        if idx + 1 < len(argv):
            output_path = argv[idx + 1]
        else:
            print("brand-check: --output requires a path argument", file=sys.stderr)
            return 2

    # Extract file/directory paths (exclude flags and their arguments)
    paths = []
    skip_next = False
    for i, arg in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("-"):
            if arg in ("--format", "--output"):
                skip_next = True
            continue
        paths.append(arg)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not paths:
        paths = [repo_root]

    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        for p in missing:
            print(f"brand-check: no such file or directory: {p}", file=sys.stderr)
        return 2

    colors_md = find_colors_md(paths[0]) or find_colors_md(repo_root)
    if not colors_md:
        print("brand-check: could not locate references/colors.md", file=sys.stderr)
        return 2
    palette = load_palette(colors_md)

    files = collect(paths)
    findings: list[Finding] = []
    for f in files:
        findings.extend(check_file(f, palette))

    # Generate report based on mode
    if report_mode:
        report_obj = ComplianceReport()
        report_obj.add_findings(findings, len(files))

        if format_type == "json":
            output = report_obj.to_json(include_trends=with_trends)
        elif format_type == "html":
            output = report_obj.to_html()
        elif format_type == "markdown":
            output = report_obj.to_markdown()
        else:
            # text format - use existing report() function
            return report(findings, len(files), palette, quiet, sys.stdout.isatty())

        # Write output
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(output)
        else:
            print(output)

        # Save to history if trends requested
        if with_trends:
            report_obj.save_to_history()

        return 1 if report_obj.severity_counts["blocker"] > 0 else 0
    else:
        # Original terminal output mode
        color = sys.stdout.isatty()
        return report(findings, len(files), palette, quiet, color)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
