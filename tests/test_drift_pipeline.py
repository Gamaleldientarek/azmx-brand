"""End-to-end test of the brand drift pipeline.

    brand-monitor.py --scan  ->  drift-detector.py  ->  drift-report.py  ->  drift-alert.py

Everything runs as a subprocess against a throw-away SQLite database in
tmp_path, exactly the way scripts/setup-drift-monitor.sh wires it up. Two small
HTML files are scanned: one on-brand, one off-brand (non-brand font and colour,
banned buzzwords) whose *filename* carries an HTML injection so the report's
escaping is exercised too.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

HOSTILE_NAME = "offbrand<img src=x onerror=alert(1)>.html"

ON_BRAND_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>AZM X</title>
<style>
  body { font-family: "Azm X Variable", sans-serif; color: #111927; background: #FFFFFF; padding: 16px; margin: 24px; }
  h1 { font-family: "thmanyah serif display", serif; color: #001AFF; margin: 24px 0 16px; }
</style></head>
<body><h1>Welcome to AZM X</h1><p>We build what matters. Let's begin.</p></body></html>
"""

OFF_BRAND_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Synergy</title>
<style>
  body { font-family: "Comic Sans MS", cursive; color: #FF00FF; background: #00FF00; padding: 13px; margin: 7px; }
  h1 { font-family: "Papyrus", fantasy; color: #ABCDEF; }
</style></head>
<body><h1>Synergy leverage paradigm</h1>
<p>Our world-class best-in-class cutting-edge solution disrupts everything!!! Unlock synergies now!!!</p>
</body></html>
"""


def _load_metric_keys() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("drift_db", SCRIPTS / "drift-db.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.METRIC_KEYS)


METRIC_KEYS = _load_metric_keys()


def run(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"},
    )


@pytest.fixture(scope="module")
def workspace(tmp_path_factory) -> dict[str, Path]:
    root = tmp_path_factory.mktemp("drift")
    site = root / "site"
    site.mkdir()
    (site / "onbrand.html").write_text(ON_BRAND_HTML, encoding="utf-8")
    (site / HOSTILE_NAME).write_text(OFF_BRAND_HTML, encoding="utf-8")

    db = root / "drift.db"
    config = root / ".brand-monitor.yml"
    config.write_text(
        "\n".join(
            [
                "watch_paths:",
                '  - "./site"',
                "extensions:",
                '  - ".html"',
                "database:",
                f'  path: "{db.as_posix()}"',
                "scan:",
                "  timeout: 30",
                "  skip_unchanged: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"root": root, "site": site, "db": db, "config": config}


def _counts(db: Path) -> tuple[int, int]:
    with sqlite3.connect(db) as conn:
        scans = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
        metrics = conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
    return scans, metrics


@pytest.mark.integration
def test_monitor_scan_populates_db(workspace):
    root, db, config = workspace["root"], workspace["db"], workspace["config"]
    result = run("brand-monitor.py", "--scan", "site", "--config", str(config), "--quiet", cwd=root)
    assert result.returncode == 0, result.stderr
    assert db.exists(), "database.path from .brand-monitor.yml was not used"

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        scans = conn.execute("SELECT file_path FROM scans ORDER BY file_path").fetchall()
        assert len(scans) == 2, [dict(r) for r in scans]
        paths = {Path(r["file_path"]).name for r in scans}
        assert paths == {"onbrand.html", HOSTILE_NAME}

        metric_types = {r[0] for r in conn.execute("SELECT DISTINCT metric_type FROM metrics")}
        for drift_type, key in METRIC_KEYS.items():
            assert key in metric_types, f"{drift_type} expects metric {key!r}; stored: {sorted(metric_types)}"

        # every scan has every drift metric, and values are 0..1 rates
        for scan in scans:
            scan_id = conn.execute("SELECT id FROM scans WHERE file_path = ?", (scan["file_path"],)).fetchone()[0]
            for key in METRIC_KEYS.values():
                row = conn.execute(
                    "SELECT value FROM metrics WHERE scan_id = ? AND metric_type = ?", (scan_id, key)
                ).fetchone()
                assert row is not None, f"{scan['file_path']} has no {key}"
                assert 0.0 <= row[0] <= 1.0

        # the off-brand file must actually score worse than the on-brand one
        def rate(name_fragment: str, key: str) -> float:
            return conn.execute(
                "SELECT m.value FROM metrics m JOIN scans s ON s.id = m.scan_id "
                "WHERE s.file_path LIKE ? AND m.metric_type = ?",
                (f"%{name_fragment}", key),
            ).fetchone()[0]

        assert rate("onbrand.html", METRIC_KEYS["font_drift"]) > rate(HOSTILE_NAME, METRIC_KEYS["font_drift"])
        assert rate("onbrand.html", METRIC_KEYS["color_drift"]) > rate(HOSTILE_NAME, METRIC_KEYS["color_drift"])
        assert rate("onbrand.html", METRIC_KEYS["tone_drift"]) >= rate(HOSTILE_NAME, METRIC_KEYS["tone_drift"])


@pytest.mark.integration
def test_rescan_of_unchanged_files_adds_no_rows(workspace):
    root, db, config = workspace["root"], workspace["db"], workspace["config"]
    before = _counts(db)
    result = run("brand-monitor.py", "--scan", "site", "--config", str(config), "--quiet", cwd=root)
    assert result.returncode == 0, result.stderr
    assert _counts(db) == before, "re-scanning unchanged files must not add scans/metrics rows"


@pytest.mark.integration
def test_detector_analyses_every_drift_type(workspace):
    root, db = workspace["root"], workspace["db"]
    result = run("drift-detector.py", "--detect-all", "--db", str(db), "--json", cwd=root)
    # exit code 1 means "drift detected", which the off-brand file may well trigger;
    # anything else is a crash.
    assert result.returncode in (0, 1), result.stderr
    assert "Traceback" not in result.stderr
    results = json.loads(result.stdout)
    assert isinstance(results, list) and results

    by_type = {r["metric_type"]: r for r in results}
    assert set(by_type) == set(METRIC_KEYS), f"detector covered {sorted(by_type)}, expected {sorted(METRIC_KEYS)}"
    for drift_type, r in by_type.items():
        assert r["status"] != "error", f"{drift_type}: {r}"
        assert r["status"] == "ok", f"{drift_type} should have data from the scan: {r}"
        assert r["data_points"] == 2
        assert "drift_detected" in r and "severity" in r


@pytest.mark.integration
def test_report_renders_and_escapes_hostile_filename(workspace):
    root, db = workspace["root"], workspace["db"]
    out = root / "r.html"
    # --period makes the report include the "files with most issues" list, which
    # is where a file name reaches the HTML.
    result = run("drift-report.py", "--db", str(db), "--output", str(out), "--period", "weekly", cwd=root)
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    assert out.exists() and out.stat().st_size > 0

    html = out.read_text(encoding="utf-8")
    assert "<img src=x" not in html, "raw hostile filename reached the report"
    assert "onerror=alert(1)>" not in html
    assert "offbrand&lt;img src=x onerror=alert(1)&gt;.html" in html, "file list should show the escaped name"
    assert "<html" in html.lower() and "</html>" in html.lower()


@pytest.mark.integration
def test_alert_check_drift_dry_run(workspace):
    root, db, config = workspace["root"], workspace["db"], workspace["config"]
    result = run(
        "drift-alert.py", "--check-drift", "--db", str(db), "--config", str(config), "--dry-run", cwd=root
    )
    assert result.returncode == 0, result.stderr
    assert "Error analyzing" not in result.stderr
    assert "Traceback" not in result.stderr
    assert "DRY RUN" in result.stdout or "Created 0 new alert(s)" in result.stdout

    # dry run must not have written alerts
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == 0
