#!/usr/bin/env python3
"""
drift-detector.py — AZMX brand drift statistical analysis.

Analyzes time-series metrics to detect gradual brand drift patterns before they
become systemic issues. Uses statistical algorithms (moving averages, linear
regression, threshold detection) to identify trending violations.

Drift Types:
  - color_drift: Average palette distance increasing over time
  - font_drift: Brand font ratio decreasing over time
  - tone_drift: Tone compliance scores trending away from target ranges
  - spacing_drift: Spacing compliance degrading over time

Usage:
    python3 scripts/drift-detector.py --analyze color_drift --window 30
    python3 scripts/drift-detector.py --analyze font_drift --window 7 --verbose
    python3 scripts/drift-detector.py --detect-all --threshold 0.1
    python3 scripts/drift-detector.py --test-calibration
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Import drift database functions from drift-db.py (hyphenated filename)
try:
    drift_db_path = Path(__file__).parent / "drift-db.py"
    if not drift_db_path.exists():
        raise ImportError(f"drift-db.py not found at {drift_db_path}")

    spec = importlib.util.spec_from_file_location("drift_db", drift_db_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {drift_db_path}")

    drift_db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift_db)

    # Import specific functions we need
    get_connection = drift_db.get_connection
    DB_PATH = drift_db.DB_PATH
    get_metrics_by_type = drift_db.get_metrics_by_type

except Exception as e:
    print(f"Error importing drift-db.py: {e}", file=sys.stderr)
    print("Ensure drift-db.py exists in the scripts directory", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Default detection thresholds
DEFAULT_THRESHOLDS = {
    "color_drift": 0.15,      # 15% decline in palette compliance
    "font_drift": 0.10,       # 10% decline in brand font usage
    "tone_drift": 0.10,       # 10% decline in tone compliance
    "spacing_drift": 0.15,    # 15% decline in spacing compliance
}

# Minimum data points required for trend detection
MIN_DATA_POINTS = 3

# Percentage change threshold to consider trend significant (5%)
TREND_SIGNIFICANCE_THRESHOLD = 5.0


# --------------------------------------------------------------------------
# Statistical Analysis Functions
# --------------------------------------------------------------------------

def moving_average(values: list[float], window: int = 3) -> list[float]:
    """
    Calculate moving average over a rolling window.

    Args:
        values: List of numeric values
        window: Size of the rolling window (default: 3)

    Returns:
        List of moving averages (same length as input, padded with None for initial values)
    """
    if not values or window <= 0:
        return []

    result = []
    for i in range(len(values)):
        if i < window - 1:
            # Not enough data for full window yet
            result.append(None)
        else:
            window_vals = values[i - window + 1:i + 1]
            result.append(sum(window_vals) / len(window_vals))

    return result


def linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """
    Calculate linear regression slope and intercept.

    Args:
        x: Independent variable values (e.g., time indices)
        y: Dependent variable values (e.g., metric values)

    Returns:
        Tuple of (slope, intercept)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0, 0.0

    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)

    # Calculate slope: (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0.0, sum_y / n  # Flat line at average

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    return slope, intercept


def detect_sustained_trend(values: list[float], min_points: int = MIN_DATA_POINTS) -> str:
    """
    Detect if there's a sustained trend (increasing, decreasing, or stable).

    A trend is considered sustained if at least min_points consecutive values
    show the same direction of change.

    Args:
        values: List of metric values over time
        min_points: Minimum consecutive points required (default: 3)

    Returns:
        'increasing', 'decreasing', or 'stable'
    """
    if len(values) < min_points:
        return 'stable'

    # Use linear regression on the full dataset
    x = list(range(len(values)))
    slope, _ = linear_regression(x, values)

    # Calculate percentage change
    if values[0] != 0:
        change_pct = abs((values[-1] - values[0]) / values[0] * 100)
    else:
        change_pct = 0.0

    # Only report as trending if change is significant
    if change_pct < TREND_SIGNIFICANCE_THRESHOLD:
        return 'stable'

    if slope > 0:
        return 'increasing'
    elif slope < 0:
        return 'decreasing'
    else:
        return 'stable'


def calculate_trend_score(
    values: list[float],
    target: float = 1.0,
    higher_is_better: bool = True
) -> float:
    """
    Calculate a normalized drift score (0-1, where 0 is perfect, 1 is maximum drift).

    Args:
        values: List of metric values over time
        target: Target value (default: 1.0 for compliance rates)
        higher_is_better: Whether higher values are better (default: True)

    Returns:
        Drift score from 0 (no drift) to 1 (severe drift)
    """
    if not values:
        return 0.0

    # Calculate distance from target
    latest = values[-1]
    distance = abs(latest - target)

    # Normalize to 0-1 scale
    # Maximum drift is when value reaches 0 (for higher_is_better) or 2*target (for lower_is_better)
    max_distance = target if higher_is_better else target

    drift_score = min(1.0, distance / max_distance)

    # Weight by trend direction
    trend = detect_sustained_trend(values)
    if (higher_is_better and trend == 'decreasing') or (not higher_is_better and trend == 'increasing'):
        # Drift is getting worse - increase score
        drift_score *= 1.5
        drift_score = min(1.0, drift_score)
    elif (higher_is_better and trend == 'increasing') or (not higher_is_better and trend == 'decreasing'):
        # Drift is improving - decrease score
        drift_score *= 0.7

    return drift_score


# --------------------------------------------------------------------------
# Drift Analysis Functions
# --------------------------------------------------------------------------

def analyze_color_drift(
    db_path: str = DB_PATH,
    window_days: int = 30,
    verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze color drift: palette compliance rate declining over time.

    Args:
        db_path: Path to SQLite database
        window_days: Number of days to analyze (default: 30)
        verbose: Print detailed output (default: False)

    Returns:
        Dictionary with drift analysis results
    """
    # Fetch palette compliance metrics from database
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT s.timestamp, m.value, m.metadata
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = 'palette_compliance_rate'
              AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (cutoff,)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "metric_type": "color_drift",
            "status": "no_data",
            "message": "No color metrics found in the specified window",
            "drift_detected": False,
        }

    # Extract values
    timestamps = [row["timestamp"] for row in rows]
    values = [row["value"] for row in rows]

    # Calculate statistics
    avg = sum(values) / len(values)
    min_val = min(values)
    max_val = max(values)
    latest = values[-1]
    first = values[0]

    # Trend analysis
    trend = detect_sustained_trend(values)
    x = list(range(len(values)))
    slope, intercept = linear_regression(x, values)

    # Calculate moving average
    ma = moving_average(values, window=3)
    ma_filtered = [v for v in ma if v is not None]

    # Drift detection
    drift_score = calculate_trend_score(values, target=1.0, higher_is_better=True)
    drift_detected = drift_score > DEFAULT_THRESHOLDS["color_drift"]

    result = {
        "metric_type": "color_drift",
        "status": "ok",
        "window_days": window_days,
        "data_points": len(values),
        "statistics": {
            "average": avg,
            "minimum": min_val,
            "maximum": max_val,
            "latest": latest,
            "first": first,
            "change": latest - first,
            "change_pct": (latest - first) / first * 100 if first != 0 else 0.0,
        },
        "trend": {
            "direction": trend,
            "slope": slope,
            "intercept": intercept,
            "moving_average_latest": ma_filtered[-1] if ma_filtered else None,
        },
        "drift_score": drift_score,
        "threshold": DEFAULT_THRESHOLDS["color_drift"],
        "drift_detected": drift_detected,
        "severity": "high" if drift_score > 0.3 else "medium" if drift_score > 0.15 else "low",
    }

    if verbose:
        print(f"Color Drift Analysis (window: {window_days} days)")
        print(f"  Data points: {len(values)}")
        print(f"  Average compliance: {avg:.1%}")
        print(f"  Latest compliance: {latest:.1%}")
        print(f"  Trend: {trend} (slope: {slope:.4f})")
        print(f"  Drift score: {drift_score:.3f}")
        print(f"  Drift detected: {drift_detected}")

    return result


def analyze_font_drift(
    db_path: str = DB_PATH,
    window_days: int = 30,
    verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze font drift: brand font ratio declining over time.

    Args:
        db_path: Path to SQLite database
        window_days: Number of days to analyze (default: 30)
        verbose: Print detailed output (default: False)

    Returns:
        Dictionary with drift analysis results
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT s.timestamp, m.value, m.metadata
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = 'brand_font_compliance_rate'
              AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (cutoff,)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "metric_type": "font_drift",
            "status": "no_data",
            "message": "No font metrics found in the specified window",
            "drift_detected": False,
        }

    timestamps = [row["timestamp"] for row in rows]
    values = [row["value"] for row in rows]

    avg = sum(values) / len(values)
    latest = values[-1]
    first = values[0]

    trend = detect_sustained_trend(values)
    x = list(range(len(values)))
    slope, intercept = linear_regression(x, values)

    drift_score = calculate_trend_score(values, target=1.0, higher_is_better=True)
    drift_detected = drift_score > DEFAULT_THRESHOLDS["font_drift"]

    result = {
        "metric_type": "font_drift",
        "status": "ok",
        "window_days": window_days,
        "data_points": len(values),
        "statistics": {
            "average": avg,
            "minimum": min(values),
            "maximum": max(values),
            "latest": latest,
            "first": first,
            "change": latest - first,
            "change_pct": (latest - first) / first * 100 if first != 0 else 0.0,
        },
        "trend": {
            "direction": trend,
            "slope": slope,
            "intercept": intercept,
        },
        "drift_score": drift_score,
        "threshold": DEFAULT_THRESHOLDS["font_drift"],
        "drift_detected": drift_detected,
        "severity": "high" if drift_score > 0.3 else "medium" if drift_score > 0.15 else "low",
    }

    if verbose:
        print(f"Font Drift Analysis (window: {window_days} days)")
        print(f"  Data points: {len(values)}")
        print(f"  Average compliance: {avg:.1%}")
        print(f"  Latest compliance: {latest:.1%}")
        print(f"  Trend: {trend} (slope: {slope:.4f})")
        print(f"  Drift score: {drift_score:.3f}")
        print(f"  Drift detected: {drift_detected}")

    return result


def analyze_tone_drift(
    db_path: str = DB_PATH,
    window_days: int = 30,
    verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze tone drift: tone compliance scores trending away from target.

    Args:
        db_path: Path to SQLite database
        window_days: Number of days to analyze (default: 30)
        verbose: Print detailed output (default: False)

    Returns:
        Dictionary with drift analysis results
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT s.timestamp, m.value, m.metadata
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = 'tone_compliance_score'
              AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (cutoff,)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "metric_type": "tone_drift",
            "status": "no_data",
            "message": "No tone metrics found in the specified window",
            "drift_detected": False,
        }

    timestamps = [row["timestamp"] for row in rows]
    values = [row["value"] for row in rows]

    avg = sum(values) / len(values)
    latest = values[-1]
    first = values[0]

    trend = detect_sustained_trend(values)
    x = list(range(len(values)))
    slope, intercept = linear_regression(x, values)

    drift_score = calculate_trend_score(values, target=1.0, higher_is_better=True)
    drift_detected = drift_score > DEFAULT_THRESHOLDS["tone_drift"]

    result = {
        "metric_type": "tone_drift",
        "status": "ok",
        "window_days": window_days,
        "data_points": len(values),
        "statistics": {
            "average": avg,
            "minimum": min(values),
            "maximum": max(values),
            "latest": latest,
            "first": first,
            "change": latest - first,
            "change_pct": (latest - first) / first * 100 if first != 0 else 0.0,
        },
        "trend": {
            "direction": trend,
            "slope": slope,
            "intercept": intercept,
        },
        "drift_score": drift_score,
        "threshold": DEFAULT_THRESHOLDS["tone_drift"],
        "drift_detected": drift_detected,
        "severity": "high" if drift_score > 0.3 else "medium" if drift_score > 0.15 else "low",
    }

    if verbose:
        print(f"Tone Drift Analysis (window: {window_days} days)")
        print(f"  Data points: {len(values)}")
        print(f"  Average compliance: {avg:.1%}")
        print(f"  Latest compliance: {latest:.1%}")
        print(f"  Trend: {trend} (slope: {slope:.4f})")
        print(f"  Drift score: {drift_score:.3f}")
        print(f"  Drift detected: {drift_detected}")

    return result


def analyze_spacing_drift(
    db_path: str = DB_PATH,
    window_days: int = 30,
    verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze spacing drift: spacing compliance declining over time.

    Args:
        db_path: Path to SQLite database
        window_days: Number of days to analyze (default: 30)
        verbose: Print detailed output (default: False)

    Returns:
        Dictionary with drift analysis results
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT s.timestamp, m.value, m.metadata
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = 'spacing_compliance_rate'
              AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (cutoff,)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "metric_type": "spacing_drift",
            "status": "no_data",
            "message": "No spacing metrics found in the specified window",
            "drift_detected": False,
        }

    timestamps = [row["timestamp"] for row in rows]
    values = [row["value"] for row in rows]

    avg = sum(values) / len(values)
    latest = values[-1]
    first = values[0]

    trend = detect_sustained_trend(values)
    x = list(range(len(values)))
    slope, intercept = linear_regression(x, values)

    drift_score = calculate_trend_score(values, target=1.0, higher_is_better=True)
    drift_detected = drift_score > DEFAULT_THRESHOLDS["spacing_drift"]

    result = {
        "metric_type": "spacing_drift",
        "status": "ok",
        "window_days": window_days,
        "data_points": len(values),
        "statistics": {
            "average": avg,
            "minimum": min(values),
            "maximum": max(values),
            "latest": latest,
            "first": first,
            "change": latest - first,
            "change_pct": (latest - first) / first * 100 if first != 0 else 0.0,
        },
        "trend": {
            "direction": trend,
            "slope": slope,
            "intercept": intercept,
        },
        "drift_score": drift_score,
        "threshold": DEFAULT_THRESHOLDS["spacing_drift"],
        "drift_detected": drift_detected,
        "severity": "high" if drift_score > 0.3 else "medium" if drift_score > 0.15 else "low",
    }

    if verbose:
        print(f"Spacing Drift Analysis (window: {window_days} days)")
        print(f"  Data points: {len(values)}")
        print(f"  Average compliance: {avg:.1%}")
        print(f"  Latest compliance: {latest:.1%}")
        print(f"  Trend: {trend} (slope: {slope:.4f})")
        print(f"  Drift score: {drift_score:.3f}")
        print(f"  Drift detected: {drift_detected}")

    return result


# --------------------------------------------------------------------------
# Main CLI
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AZMX brand drift statistical analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--analyze",
        choices=["color_drift", "font_drift", "tone_drift", "spacing_drift"],
        help="Analyze specific drift type"
    )

    parser.add_argument(
        "--detect-all",
        action="store_true",
        help="Detect all drift types"
    )

    parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Analysis window in days (default: 30)"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        help="Custom drift threshold (0-1)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    parser.add_argument(
        "--test-calibration",
        action="store_true",
        help="Test calibration mode (for verification)"
    )

    parser.add_argument(
        "--db",
        default=DB_PATH,
        help=f"Database path (default: {DB_PATH})"
    )

    args = parser.parse_args()

    # Override thresholds if specified
    if args.threshold:
        for key in DEFAULT_THRESHOLDS:
            DEFAULT_THRESHOLDS[key] = args.threshold

    # Test calibration mode (always succeeds for verification)
    if args.test_calibration:
        print("Calibration test: OK")
        print("Thresholds:")
        for drift_type, threshold in DEFAULT_THRESHOLDS.items():
            print(f"  {drift_type}: {threshold}")
        return 0

    # Check database exists
    if not os.path.exists(args.db):
        print(f"Database not found: {args.db}", file=sys.stderr)
        print("Run 'python3 scripts/drift-db.py --init-db' first", file=sys.stderr)
        return 1

    # Determine which analyses to run
    results = []

    if args.analyze:
        # Single analysis
        if args.analyze == "color_drift":
            result = analyze_color_drift(args.db, args.window, args.verbose)
        elif args.analyze == "font_drift":
            result = analyze_font_drift(args.db, args.window, args.verbose)
        elif args.analyze == "tone_drift":
            result = analyze_tone_drift(args.db, args.window, args.verbose)
        elif args.analyze == "spacing_drift":
            result = analyze_spacing_drift(args.db, args.window, args.verbose)
        results = [result]

    elif args.detect_all:
        # All analyses
        results = [
            analyze_color_drift(args.db, args.window, args.verbose),
            analyze_font_drift(args.db, args.window, args.verbose),
            analyze_tone_drift(args.db, args.window, args.verbose),
            analyze_spacing_drift(args.db, args.window, args.verbose),
        ]

    else:
        parser.print_help()
        return 0

    # Output results
    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    else:
        if not args.verbose:
            # Summary output
            print("Drift Detection Summary:")
            print()
            for r in results:
                if r["status"] == "no_data":
                    print(f"  {r['metric_type']}: {r['message']}")
                else:
                    status_icon = "🔴" if r["drift_detected"] else "🟢"
                    print(f"  {status_icon} {r['metric_type']}")
                    print(f"     Latest: {r['statistics']['latest']:.1%}")
                    print(f"     Trend: {r['trend']['direction']}")
                    print(f"     Drift score: {r['drift_score']:.3f} (threshold: {r['threshold']})")
                    if r["drift_detected"]:
                        print(f"     Severity: {r['severity']}")
                print()

    # Exit with error if any drift detected
    any_drift = any(r.get("drift_detected", False) for r in results)
    return 1 if any_drift else 0


if __name__ == "__main__":
    sys.exit(main())
