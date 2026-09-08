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
    python3 scripts/brand-check.py [file-or-dir ...] [--quiet] [--report]

With no paths it scans the whole repo. Exits 1 if any blocker was found.
The --report flag outputs an aggregated compliance summary instead of detailed findings.
"""

from __future__ import annotations

import bisect
import json
import os
import re
import sys
from datetime import datetime

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
    """Aggregates brand-check findings across files."""

    def __init__(self, findings: list[Finding] | None = None):
        self.findings = findings or []

    def add(self, finding: Finding) -> None:
        """Add a single finding to the report."""
        self.findings.append(finding)

    def extend(self, findings: list[Finding]) -> None:
        """Add multiple findings to the report."""
        self.findings.extend(findings)

    def count_by_severity(self) -> dict[str, int]:
        """Return counts grouped by severity level."""
        counts = {"blocker": 0, "major": 0, "minor": 0}
        for f in self.findings:
            counts[f.severity] += 1
        return counts

    def count_by_code(self) -> dict[str, int]:
        """Return counts grouped by violation code."""
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.code] = counts.get(f.code, 0) + 1
        return counts

    def by_file(self) -> dict[str, list[Finding]]:
        """Group findings by file path."""
        by_file: dict[str, list[Finding]] = {}
        for f in self.findings:
            by_file.setdefault(f.path, []).append(f)
        return by_file

    def has_blockers(self) -> bool:
        """Return True if any blocker-level findings exist."""
        return any(f.severity == "blocker" for f in self.findings)

    def total(self) -> int:
        """Return total number of findings."""
        return len(self.findings)

    def to_json(self, include_trends: bool = False) -> dict:
        """Serialize the report to a JSON-compatible dictionary."""
        data = {
            "total_findings": self.total(),
            "has_blockers": self.has_blockers(),
            "summary": {
                "by_severity": self.count_by_severity(),
                "by_code": self.count_by_code(),
            },
            "files_affected": len(self.by_file()),
            "findings": [
                {
                    "path": f.path,
                    "line": f.line,
                    "severity": f.severity,
                    "code": f.code,
                    "what": f.what,
                    "fix": f.fix,
                }
                for f in self.findings
            ],
        }

        if include_trends:
            data["trend"] = self._compute_trends()

        return data

    def _compute_trends(self) -> dict:
        """Compute trend analysis by comparing with historical data."""
        history = self._load_latest_history()

        if not history:
            return {
                "status": "no_history",
                "message": "No historical data available for comparison",
                "previous_report": None,
                "changes": None,
            }

        current_sev = self.count_by_severity()
        current_code = self.count_by_code()

        prev_sev = history.get("summary", {}).get("by_severity", {})
        prev_code = history.get("summary", {}).get("by_code", {})
        prev_total = history.get("total_findings", 0)

        # Calculate changes
        total_change = self.total() - prev_total
        sev_changes = {
            sev: current_sev.get(sev, 0) - prev_sev.get(sev, 0)
            for sev in ["blocker", "major", "minor"]
        }

        # Calculate code-level changes
        all_codes = set(current_code.keys()) | set(prev_code.keys())
        code_changes = {
            code: current_code.get(code, 0) - prev_code.get(code, 0)
            for code in all_codes
        }

        # Determine overall trend status
        if total_change < 0:
            status = "improved"
        elif total_change > 0:
            status = "degraded"
        else:
            status = "stable"

        return {
            "status": status,
            "message": self._trend_message(status, total_change, sev_changes),
            "previous_report": {
                "timestamp": history.get("timestamp"),
                "total_findings": prev_total,
                "by_severity": prev_sev,
                "by_code": prev_code,
            },
            "changes": {
                "total": total_change,
                "by_severity": sev_changes,
                "by_code": code_changes,
            },
        }

    def _trend_message(self, status: str, total_change: int, sev_changes: dict) -> str:
        """Generate a human-readable trend message."""
        if status == "improved":
            return f"Compliance improved: {abs(total_change)} fewer finding(s) than previous report"
        elif status == "degraded":
            blockers_up = sev_changes.get("blocker", 0)
            if blockers_up > 0:
                return f"Compliance degraded: {total_change} more finding(s), including {blockers_up} new blocker(s)"
            return f"Compliance degraded: {total_change} more finding(s) than previous report"
        else:
            return "Compliance stable: no change from previous report"

    def _load_latest_history(self) -> dict | None:
        """Load the most recent historical report."""
        history_dir = self._get_history_dir()
        if not os.path.exists(history_dir):
            return None

        history_files = sorted(
            [f for f in os.listdir(history_dir) if f.endswith(".json")],
            reverse=True
        )

        if not history_files:
            return None

        latest_file = os.path.join(history_dir, history_files[0])
        try:
            with open(latest_file, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None

    def save_to_history(self) -> None:
        """Save the current report to historical tracking."""
        history_dir = self._get_history_dir()
        os.makedirs(history_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"report-{timestamp}.json"
        filepath = os.path.join(history_dir, filename)

        report_data = self.to_json(include_trends=False)
        report_data["timestamp"] = datetime.now().isoformat()

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(report_data, fh, indent=2)

        # Keep only the last 10 reports
        self._cleanup_old_reports(history_dir, keep=10)

    def _get_history_dir(self) -> str:
        """Get the directory path for storing historical reports."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(repo_root, ".brand-reports")

    def _cleanup_old_reports(self, history_dir: str, keep: int = 10) -> None:
        """Remove old reports, keeping only the most recent ones."""
        history_files = sorted(
            [f for f in os.listdir(history_dir) if f.endswith(".json")],
            reverse=True
        )

        for old_file in history_files[keep:]:
            try:
                os.remove(os.path.join(history_dir, old_file))
            except OSError:
                pass

    def to_html(self, scanned: int, palette_info: str) -> str:
        """Generate an HTML report following AZMX brand guidelines."""
        sev_counts = self.count_by_severity()
        code_counts = self.count_by_code()
        files_affected = self.by_file()

        status_class = "clean" if not self.has_blockers() else "has-blockers"
        status_text = "CLEAN — no brand violations found" if self.total() == 0 else \
                      f"{self.total()} finding(s) — {sev_counts['blocker']} blocker · {sev_counts['major']} major · {sev_counts['minor']} minor"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AZMX Brand Compliance Report</title>
<style>
:root{{--navy:#040038;--electric:#001AFF;--lightblue:#5D8FFF;--blue100:#DDE8FF;--blue200:#BFD5FF;--red:#FF2B3C;--orange:#F47A48;--green:#22C36F}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--navy);color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Tahoma,sans-serif;-webkit-font-smoothing:antialiased;padding:40px 24px}}
.container{{max-width:1200px;margin:0 auto}}
header{{margin-bottom:56px}}
.eyebrow{{color:var(--lightblue);text-transform:uppercase;letter-spacing:2.4px;font-size:14px;font-weight:600;margin:0 0 16px}}
h1{{font-family:Georgia,'Times New Roman',serif;font-size:clamp(32px,6vw,64px);font-weight:400;letter-spacing:-1.5px;line-height:1.1;margin:0 0 24px}}
.meta{{color:var(--blue200);opacity:.7;font-size:15px;margin:0;line-height:1.8}}
h2{{font-family:Georgia,serif;font-weight:500;font-size:clamp(24px,3vw,32px);margin:40px 0 16px;letter-spacing:-.5px;padding-top:24px;border-top:1px solid rgba(255,255,255,.14)}}
h2:first-of-type{{border-top:0;padding-top:0}}
.status{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;margin:24px 0;font-size:15px;font-weight:600;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.05)}}
.status.clean{{border-color:var(--green);background:rgba(34,195,111,.1);color:var(--green)}}
.status.has-blockers{{border-color:var(--red);background:rgba(255,43,60,.1);color:var(--red)}}
.summary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:40px}}
.summary-card{{border:1px solid rgba(255,255,255,.14);padding:16px;background:rgba(255,255,255,.02)}}
.summary-card h3{{margin:0 0 8px;font-size:13px;letter-spacing:1.2px;text-transform:uppercase;color:var(--blue200);opacity:.7;font-weight:600}}
.summary-card .value{{font-size:28px;font-weight:600;font-variant-numeric:tabular-nums}}
.severity-blocker{{color:var(--red)}}
.severity-major{{color:var(--orange)}}
.severity-minor{{color:var(--lightblue)}}
.code-list{{list-style:none;padding:0;margin:0}}
.code-list li{{padding:8px 0;border-bottom:1px solid rgba(255,255,255,.08);display:flex;justify-content:space-between;align-items:center}}
.code-list li:last-child{{border-bottom:0}}
.code-name{{color:var(--blue100);font-size:14px}}
.code-count{{color:var(--blue200);font-size:13px;opacity:.8;font-variant-numeric:tabular-nums}}
.file-list{{list-style:none;padding:0;margin:0}}
.file-item{{margin-bottom:32px;padding:16px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.02)}}
.file-path{{font-size:16px;font-weight:600;margin:0 0 16px;color:var(--lightblue);word-break:break-all}}
.finding{{margin-bottom:16px;padding:12px;border-left:3px solid;background:rgba(255,255,255,.03)}}
.finding.blocker{{border-left-color:var(--red)}}
.finding.major{{border-left-color:var(--orange)}}
.finding.minor{{border-left-color:var(--lightblue)}}
.finding-header{{display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap}}
.finding-line{{color:var(--blue200);font-size:13px;opacity:.8;font-variant-numeric:tabular-nums}}
.finding-severity{{font-size:12px;letter-spacing:.8px;text-transform:uppercase;font-weight:600}}
.finding-code{{color:var(--blue100);font-size:13px;font-weight:600}}
.finding-what{{color:var(--blue100);font-size:14px;margin-bottom:8px;line-height:1.5}}
.finding-fix{{color:var(--blue200);font-size:13px;opacity:.8;line-height:1.6;padding-left:12px;border-left:1px solid rgba(255,255,255,.14)}}
code{{background:rgba(255,255,255,.08);padding:2px 6px;font-size:12px;color:var(--blue100)}}
footer{{margin-top:64px;padding-top:32px;border-top:1px solid rgba(255,255,255,.14);color:var(--blue200);font-size:13px;opacity:.6;text-align:center}}
@media(max-width:600px){{
  .summary-grid{{grid-template-columns:1fr}}
  .finding-header{{flex-direction:column;gap:4px}}
}}
</style>
</head>
<body>
<div class="container">
<header>
<p class="eyebrow">AZMX Brand Skill</p>
<h1>Brand Compliance Report</h1>
<p class="meta">{palette_info}</p>
<p class="meta">Scanned: {scanned} file(s)</p>
<div class="status {status_class}">{status_text}</div>
</header>

<h2>Summary by Severity</h2>
<div class="summary-grid">
<div class="summary-card">
<h3>Blocker</h3>
<div class="value severity-blocker">{sev_counts['blocker']}</div>
</div>
<div class="summary-card">
<h3>Major</h3>
<div class="value severity-major">{sev_counts['major']}</div>
</div>
<div class="summary-card">
<h3>Minor</h3>
<div class="value severity-minor">{sev_counts['minor']}</div>
</div>
<div class="summary-card">
<h3>Total Findings</h3>
<div class="value">{self.total()}</div>
</div>
</div>
"""

        if code_counts:
            html += """
<h2>Summary by Violation Type</h2>
<ul class="code-list">
"""
            for code in sorted(code_counts.keys()):
                html += f'<li><span class="code-name">{code}</span><span class="code-count">{code_counts[code]}</span></li>\n'
            html += "</ul>\n"

        if files_affected:
            html += f"""
<h2>Files Affected ({len(files_affected)})</h2>
<ul class="file-list">
"""
            for path in sorted(files_affected.keys()):
                rel_path = os.path.relpath(path)
                if rel_path.startswith(".."):
                    rel_path = os.path.abspath(path)
                findings_in_file = files_affected[path]

                html += f'<li class="file-item">\n'
                html += f'<h3 class="file-path">{self._escape_html(rel_path)}</h3>\n'

                for f in findings_in_file:
                    html += f'<div class="finding {f.severity}">\n'
                    html += f'<div class="finding-header">\n'
                    html += f'<span class="finding-line">Line {f.line}</span>\n'
                    html += f'<span class="finding-severity severity-{f.severity}">{f.severity}</span>\n'
                    html += f'<span class="finding-code">{f.code}</span>\n'
                    html += f'</div>\n'
                    html += f'<div class="finding-what">{self._escape_html(f.what)}</div>\n'
                    html += f'<div class="finding-fix">Fix: {self._escape_html(f.fix)}</div>\n'
                    html += f'</div>\n'

                html += '</li>\n'
            html += "</ul>\n"

        html += """
<footer>
Generated by AZMX brand-check.py
</footer>
</div>
</body>
</html>
"""
        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def to_markdown(self, scanned: int, palette_info: str) -> str:
        """Generate a markdown report."""
        sev_counts = self.count_by_severity()
        code_counts = self.count_by_code()
        files_affected = self.by_file()

        status_emoji = "✅" if self.total() == 0 else ("❌" if self.has_blockers() else "⚠️")
        status_text = "CLEAN — no brand violations found" if self.total() == 0 else \
                      f"{self.total()} finding(s) — {sev_counts['blocker']} blocker · {sev_counts['major']} major · {sev_counts['minor']} minor"

        md = f"""# AZMX Brand Compliance Report

**Status:** {status_emoji} {status_text}

**Palette:** {palette_info}
**Scanned:** {scanned} file(s)

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| 🔴 Blocker | {sev_counts['blocker']} |
| 🟠 Major | {sev_counts['major']} |
| 🔵 Minor | {sev_counts['minor']} |
| **Total** | **{self.total()}** |

"""

        if code_counts:
            md += """## Summary by Violation Type

| Violation Code | Count |
|----------------|-------|
"""
            for code in sorted(code_counts.keys()):
                md += f"| {code} | {code_counts[code]} |\n"
            md += "\n"

        if files_affected:
            md += f"""## Files Affected ({len(files_affected)})

"""
            for path in sorted(files_affected.keys()):
                rel_path = os.path.relpath(path)
                if rel_path.startswith(".."):
                    rel_path = os.path.abspath(path)
                findings_in_file = files_affected[path]

                md += f"### {rel_path}\n\n"
                md += f"**{len(findings_in_file)} finding(s)**\n\n"

                for f in findings_in_file:
                    severity_emoji = {"blocker": "🔴", "major": "🟠", "minor": "🔵"}[f.severity]
                    md += f"#### Line {f.line} {severity_emoji} {f.severity.upper()} — {f.code}\n\n"
                    md += f"**Issue:** {f.what}\n\n"
                    md += f"**Fix:** {f.fix}\n\n"
                    md += "---\n\n"

        md += """## Report Information

Generated by AZMX brand-check.py
"""
        return md


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


def report_aggregated(report_obj: ComplianceReport, scanned: int, palette: Palette,
                      color: bool) -> int:
    """Output an aggregated compliance report with summary statistics."""
    def c(s, code):
        return f"{code}{s}{RESET}" if color else s

    print(c("AZMX Brand Compliance Report", BOLD))
    print(c(f"palette: {len(palette.legal)} legal tones from "
            f"{os.path.relpath(palette.source)}", DIM))
    print(c(f"scanned: {scanned} file(s)", DIM))
    print()

    # Summary by severity
    sev_counts = report_obj.count_by_severity()
    print(c("Summary by Severity:", BOLD))
    for sev in ["blocker", "major", "minor"]:
        count = sev_counts[sev]
        sev_label = c(sev.upper(), SEV_COLOR[sev])
        print(f"  {sev_label:>15s}: {count}")
    print()

    # Summary by violation code
    code_counts = report_obj.count_by_code()
    if code_counts:
        print(c("Summary by Violation Type:", BOLD))
        for code in sorted(code_counts.keys()):
            print(f"  {code:<10s}: {code_counts[code]}")
        print()

    # Files affected
    files_affected = report_obj.by_file()
    print(c(f"Files Affected: {len(files_affected)}", BOLD))
    for path in sorted(files_affected.keys()):
        rel = os.path.relpath(path)
        if rel.startswith(".."):
            rel = os.path.abspath(path)
        findings_count = len(files_affected[path])
        print(f"  {rel}: {findings_count} finding(s)")
    print()

    # Final status
    if report_obj.total() > 0:
        print(c(f"Total: {report_obj.total()} finding(s) — "
                f"{sev_counts['blocker']} blocker · {sev_counts['major']} major · "
                f"{sev_counts['minor']} minor", BOLD))
    else:
        print(c("Status: CLEAN — no brand violations found", BOLD))

    return 1 if report_obj.has_blockers() else 0


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print("""AZMX brand-check.py — AZMX brand linter

Usage:
    python3 scripts/brand-check.py [file-or-dir ...] [OPTIONS]

Options:
    --quiet, -q       Suppress header and summary output
    --report          Output an aggregated compliance summary instead of detailed findings
    --format FORMAT   Output format (text, json, html, or markdown, default: text)
    --output PATH     Write output to file instead of stdout
    --with-trends     Include trend analysis comparing current vs historical reports (JSON only)
    --help, -h        Show this help message

With no paths it scans the whole repo. Exits 1 if any blocker was found.
The --report flag outputs an aggregated compliance summary with statistics by severity,
violation type, and affected files.
The --format html flag generates a branded HTML report following AZMX design guidelines.
The --format markdown flag generates a markdown report.
The --with-trends flag adds historical comparison data to JSON output and saves the current
report for future trend analysis.""")
        return 0

    quiet = "--quiet" in argv or "-q" in argv
    use_report = "--report" in argv
    with_trends = "--with-trends" in argv

    # Parse --format flag
    output_format = "text"
    if "--format" in argv:
        idx = argv.index("--format")
        if idx + 1 < len(argv):
            output_format = argv[idx + 1]

    # Parse --output flag
    output_path = None
    if "--output" in argv:
        idx = argv.index("--output")
        if idx + 1 < len(argv):
            output_path = argv[idx + 1]

    # Filter out flag arguments
    paths = [a for a in argv if not a.startswith("-") and
             a not in [output_format, output_path] if output_path or output_format != "text"]
    if not paths:
        # No paths after filtering flags
        for i, a in enumerate(argv):
            if a in ["--format", "--output"]:
                # Skip flag and its value
                continue
            if i > 0 and argv[i-1] in ["--format", "--output"]:
                # This is a flag value, skip
                continue
            if not a.startswith("-"):
                paths.append(a)

    # Simplify: just collect non-flag arguments
    paths = []
    skip_next = False
    for i, a in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if a in ["--format", "--output"]:
            skip_next = True
            continue
        if not a.startswith("-"):
            paths.append(a)

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

    color = sys.stdout.isatty()

    # Handle JSON output format
    if output_format == "json":
        compliance = ComplianceReport(findings)
        json_data = compliance.to_json(include_trends=with_trends)
        json_output = json.dumps(json_data, indent=2)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(json_output)
        else:
            print(json_output)

        # Save to history if trends were requested
        if with_trends:
            compliance.save_to_history()

        return 1 if compliance.has_blockers() else 0

    # Handle HTML output format
    if output_format == "html":
        compliance = ComplianceReport(findings)
        palette_info = f"{len(palette.legal)} legal tones from {os.path.relpath(palette.source)}"
        html_output = compliance.to_html(len(files), palette_info)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(html_output)
        else:
            print(html_output)

        return 1 if compliance.has_blockers() else 0

    # Handle Markdown output format
    if output_format == "markdown":
        compliance = ComplianceReport(findings)
        palette_info = f"{len(palette.legal)} legal tones from {os.path.relpath(palette.source)}"
        markdown_output = compliance.to_markdown(len(files), palette_info)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(markdown_output)
        else:
            print(markdown_output)

        return 1 if compliance.has_blockers() else 0

    # Handle text output format
    if use_report:
        compliance = ComplianceReport(findings)
        return report_aggregated(compliance, len(files), palette, color)
    else:
        return report(findings, len(files), palette, quiet, color)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
