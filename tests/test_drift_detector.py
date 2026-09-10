"""Tests for drift-detector.py.

The four analyze_*_drift functions collapsed into one analyze_metric(); these
tests pin the wrappers, the CLI dispatch and the JSON shape against a small
SQLite database built the way production does it: brand-monitor.py --scan
(which shells out to extract-metrics.py) on top of drift-db.py --init-db.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name.replace("-", "_")] = mod
    spec.loader.exec_module(mod)
    return mod


drift_detector = _load("drift-detector")
drift_db = _load("drift-db")

DRIFT_TYPES = ["color_drift", "font_drift", "tone_drift", "spacing_drift"]


@pytest.fixture(scope="module")
def drift_db_path(tmp_path_factory) -> Path:
    """A .brand-drift.db populated by scanning the HTML/CSS fixtures."""
    work = tmp_path_factory.mktemp("drift")
    src = work / "src"
    src.mkdir()
    for name in ("sample-valid.html", "sample-invalid.html", "sample.css",
                 "test-rtl-valid.html", "test-rtl-invalid.html"):
        shutil.copy(FIXTURES / name, src / name)

    r = subprocess.run([sys.executable, str(SCRIPTS / "drift-db.py"), "--init-db"],
                       cwd=work, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    # brand-monitor.py needs --scan DIR or --config FILE; --scan stores into ./.brand-drift.db
    r = subprocess.run([sys.executable, str(SCRIPTS / "brand-monitor.py"), "--scan", "src", "--quiet"],
                       cwd=work, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    db = work / ".brand-drift.db"
    assert db.is_file()
    return db


def _cli(db: Path, *argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / "drift-detector.py"), "--db", str(db), *argv],
                          capture_output=True, text=True, cwd=db.parent)


class TestAnalyzeMetric:
    def test_wrappers_equal_analyze_metric(self, drift_db_path):
        db = str(drift_db_path)
        for drift_type in DRIFT_TYPES:
            wrapper = drift_detector.ANALYZERS[drift_type]
            assert wrapper(db, 30, False) == drift_detector.analyze_metric(drift_type, db, 30, False)
            assert wrapper(db_path=db, window_days=30, verbose=False) == \
                drift_detector.analyze_metric(drift_type, db_path=db, window_days=30)

    def test_wrapper_names_and_dispatcher_still_exist(self):
        for drift_type in DRIFT_TYPES:
            assert callable(getattr(drift_detector, f"analyze_{drift_type}"))
            assert drift_type in drift_detector.ANALYZERS
        assert set(drift_detector.ANALYZERS) == set(drift_detector.METRIC_KEYS) == set(DRIFT_TYPES)

    def test_reads_the_metric_named_in_metric_keys(self, drift_db_path):
        """Each result is computed from METRIC_KEYS[drift_type] rows, nothing else."""
        for drift_type in DRIFT_TYPES:
            values = drift_detector.fetch_metric_values(drift_type, str(drift_db_path), 30)
            rows = drift_db.get_metrics_by_type(drift_detector.METRIC_KEYS[drift_type],
                                                db_path=str(drift_db_path))
            # drift-db returns newest first; the analyzer wants oldest first
            assert values == [r["value"] for r in sorted(rows, key=lambda r: r["timestamp"])]
            result = drift_detector.analyze_metric(drift_type, str(drift_db_path), 30)
            # 5 scanned files; the .css fixture carries no tone metric, so tone has 4
            assert result["data_points"] == len(values) >= 4
            assert result["statistics"]["latest"] == values[-1]
            assert result["statistics"]["first"] == values[0]

    def test_result_shape_is_unchanged(self, drift_db_path):
        expected_keys = {"metric_type", "status", "window_days", "data_points", "statistics",
                         "trend", "drift_score", "adjusted_drift_score", "threshold",
                         "drift_detected", "drift_detected_raw", "severity", "false_positive_filter"}
        for drift_type in DRIFT_TYPES:
            r = drift_detector.analyze_metric(drift_type, str(drift_db_path), 30)
            assert set(r) == expected_keys, drift_type
            assert r["metric_type"] == drift_type
            assert r["threshold"] == drift_detector.DEFAULT_THRESHOLDS[drift_type]
            trend_keys = {"direction", "slope", "intercept"}
            if drift_type == "color_drift":
                # only the colour analysis ever exposed the moving average
                trend_keys.add("moving_average_latest")
            assert set(r["trend"]) == trend_keys, drift_type

    def test_no_data_message_per_type(self, drift_db_path):
        r = drift_detector.analyze_metric("font_drift", str(drift_db_path), window_days=0)
        assert r == {"metric_type": "font_drift", "status": "no_data",
                     "message": "No font metrics found in the specified window",
                     "drift_detected": False}
        assert drift_detector.analyze_metric("spacing_drift", str(drift_db_path), 0)["message"] \
            == "No spacing metrics found in the specified window"

    def test_unknown_type_raises(self, drift_db_path):
        with pytest.raises(ValueError, match="unknown drift type"):
            drift_detector.analyze_metric("nope", str(drift_db_path))
        with pytest.raises(ValueError):
            drift_detector.analyze_drift("nope", str(drift_db_path))

    def test_analyze_drift_threshold_override_is_temporary(self, drift_db_path):
        before = dict(drift_detector.DEFAULT_THRESHOLDS)
        r = drift_detector.analyze_drift("color_drift", str(drift_db_path), 30, threshold=0.0)
        assert r["threshold"] == 0.0
        assert drift_detector.DEFAULT_THRESHOLDS == before

    def test_verbose_prints_type_label(self, drift_db_path, capsys):
        drift_detector.analyze_metric("tone_drift", str(drift_db_path), 30, verbose=True)
        out = capsys.readouterr().out
        assert out.startswith("Tone Drift Analysis (window: 30 days)")
        assert "Drift detected:" in out


class TestCli:
    def test_detect_all_json_matches_analyzers(self, drift_db_path):
        r = _cli(drift_db_path, "--detect-all", "--json")
        assert r.returncode in (0, 1), r.stderr
        data = json.loads(r.stdout)
        expected = [drift_detector.analyze_metric(t, str(drift_db_path), 30) for t in DRIFT_TYPES]
        assert data == expected
        assert [d["metric_type"] for d in data] == DRIFT_TYPES  # fixed order
        # and the same thing via the per-type wrappers (what drift-report.py calls)
        assert data == [drift_detector.ANALYZERS[t](str(drift_db_path), 30, False) for t in DRIFT_TYPES]

    def test_detect_all_json_is_stable_across_runs(self, drift_db_path):
        a = _cli(drift_db_path, "--detect-all", "--json").stdout
        b = _cli(drift_db_path, "--detect-all", "--json").stdout
        assert a == b

    @pytest.mark.parametrize("drift_type", DRIFT_TYPES)
    def test_analyze_single_json(self, drift_db_path, drift_type):
        r = _cli(drift_db_path, "--analyze", drift_type, "--json")
        assert r.returncode in (0, 1), r.stderr
        assert json.loads(r.stdout) == drift_detector.analyze_metric(drift_type, str(drift_db_path), 30)

    def test_threshold_zero_is_honoured(self, drift_db_path):
        """`--threshold 0` must not be dropped as falsy."""
        r = _cli(drift_db_path, "--detect-all", "--json", "--threshold", "0")
        data = json.loads(r.stdout)
        assert all(d["threshold"] == 0.0 for d in data)
        # with a zero threshold any positive drift score is raw-detected
        for d in data:
            assert d["drift_detected_raw"] == (d["drift_score"] > 0.0)
        default = json.loads(_cli(drift_db_path, "--detect-all", "--json").stdout)
        assert any(d["threshold"] != 0.0 for d in default)

    def test_exit_code_reflects_detection(self, drift_db_path):
        r = _cli(drift_db_path, "--detect-all", "--json")
        data = json.loads(r.stdout)
        assert r.returncode == (1 if any(d["drift_detected"] for d in data) else 0)

    def test_test_calibration_lists_thresholds(self, drift_db_path):
        r = _cli(drift_db_path, "--test-calibration", "--threshold", "0")
        assert r.returncode == 0
        assert "color_drift: 0.0" in r.stdout


class TestTrendScore:
    def test_higher_is_better_distance(self):
        # latest 0.75 vs target 1.0 -> 0.25, no trend on a flat series
        assert drift_detector.calculate_trend_score([0.75, 0.75, 0.75]) == pytest.approx(0.25)

    def test_lower_is_better_uses_same_bound(self):
        # 0.4 away from a target of 0.2: worst case is 2*target=0.4 away, so score 1.0 (before trend weighting)
        vals = [0.6, 0.6, 0.6]
        assert drift_detector.calculate_trend_score(vals, target=0.2, higher_is_better=False) == pytest.approx(1.0)
        # 0.1 away -> 0.5 of the 0.2 bound
        assert drift_detector.calculate_trend_score([0.3, 0.3, 0.3], target=0.2, higher_is_better=False) \
            == pytest.approx(0.5)

    def test_symmetry_between_directions(self):
        up = drift_detector.calculate_trend_score([1.3, 1.3, 1.3], target=1.0, higher_is_better=False)
        down = drift_detector.calculate_trend_score([0.7, 0.7, 0.7], target=1.0, higher_is_better=True)
        assert up == pytest.approx(down) == pytest.approx(0.3)

    def test_zero_target_does_not_divide_by_zero(self):
        assert drift_detector.calculate_trend_score([0.5, 0.5, 0.5], target=0.0, higher_is_better=False) \
            == pytest.approx(0.5)

    def test_empty(self):
        assert drift_detector.calculate_trend_score([]) == 0.0
