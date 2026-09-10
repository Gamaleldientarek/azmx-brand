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
    METRIC_KEYS = drift_db.METRIC_KEYS

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

# Anomaly detection configuration
ANOMALY_Z_SCORE_THRESHOLD = 2.5  # Z-score threshold for outlier detection
ANOMALY_IQR_MULTIPLIER = 1.5     # IQR multiplier for outlier detection
MIN_SAMPLES_FOR_ANOMALY = 5      # Minimum samples needed for anomaly detection

# False positive filtering configuration
SPIKE_ISOLATION_THRESHOLD = 2    # Max consecutive anomalies to be considered isolated
MIN_SUSTAINED_POINTS = 3         # Min consecutive points for sustained trend
VARIANCE_STABILITY_THRESHOLD = 0.2  # Max coefficient of variation for stable signal


# --------------------------------------------------------------------------
# Anomaly Detection Functions
# --------------------------------------------------------------------------

def calculate_statistics(values: list[float]) -> dict[str, float]:
    """
    Calculate basic statistical measures for a dataset.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with mean, median, std_dev, variance
    """
    if not values:
        return {"mean": 0.0, "median": 0.0, "std_dev": 0.0, "variance": 0.0}

    n = len(values)
    mean = sum(values) / n

    # Calculate variance and standard deviation
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = variance ** 0.5

    # Calculate median
    sorted_vals = sorted(values)
    if n % 2 == 0:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    else:
        median = sorted_vals[n // 2]

    return {
        "mean": mean,
        "median": median,
        "std_dev": std_dev,
        "variance": variance,
    }


def detect_anomalies_zscore(values: list[float], threshold: float = ANOMALY_Z_SCORE_THRESHOLD) -> list[int]:
    """
    Detect anomalies using z-score method.

    An anomaly is a data point that is more than 'threshold' standard deviations
    away from the mean.

    Args:
        values: List of numeric values
        threshold: Z-score threshold (default: 2.5)

    Returns:
        List of indices where anomalies were detected
    """
    if len(values) < MIN_SAMPLES_FOR_ANOMALY:
        return []

    stats = calculate_statistics(values)
    mean = stats["mean"]
    std_dev = stats["std_dev"]

    if std_dev == 0:
        return []  # No variation, no anomalies

    anomalies = []
    for i, val in enumerate(values):
        z_score = abs((val - mean) / std_dev)
        if z_score > threshold:
            anomalies.append(i)

    return anomalies


def detect_anomalies_iqr(values: list[float], multiplier: float = ANOMALY_IQR_MULTIPLIER) -> list[int]:
    """
    Detect anomalies using Interquartile Range (IQR) method.

    An anomaly is a data point that falls outside the range:
    [Q1 - multiplier*IQR, Q3 + multiplier*IQR]

    Args:
        values: List of numeric values
        multiplier: IQR multiplier (default: 1.5)

    Returns:
        List of indices where anomalies were detected
    """
    if len(values) < MIN_SAMPLES_FOR_ANOMALY:
        return []

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    # Calculate Q1 and Q3
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_vals[q1_idx]
    q3 = sorted_vals[q3_idx]

    iqr = q3 - q1
    if iqr == 0:
        return []  # No variation

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    anomalies = []
    for i, val in enumerate(values):
        if val < lower_bound or val > upper_bound:
            anomalies.append(i)

    return anomalies


def is_isolated_spike(anomaly_indices: list[int], total_length: int) -> bool:
    """
    Check if anomalies are isolated spikes rather than sustained patterns.

    An isolated spike is a single anomaly or small cluster that doesn't
    represent a sustained trend.

    Args:
        anomaly_indices: Indices of detected anomalies
        total_length: Total length of the dataset

    Returns:
        True if anomalies appear to be isolated spikes
    """
    if not anomaly_indices:
        return False

    # If more than 30% of points are anomalies, it's likely a pattern shift
    if len(anomaly_indices) > total_length * 0.3:
        return False

    # Check for consecutive anomalies
    consecutive_count = 1
    max_consecutive = 1

    for i in range(1, len(anomaly_indices)):
        if anomaly_indices[i] == anomaly_indices[i - 1] + 1:
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 1

    # If there are too many consecutive anomalies, it's a sustained pattern
    if max_consecutive > SPIKE_ISOLATION_THRESHOLD:
        return False

    return True


# --------------------------------------------------------------------------
# False Positive Filtering Functions
# --------------------------------------------------------------------------

def filter_false_positives(
    values: list[float],
    drift_detected: bool,
    drift_score: float,
    trend: str
) -> tuple[bool, float, dict[str, Any]]:
    """
    Filter false positives from drift detection.

    Reduces noise by checking for:
    1. Isolated spikes (single anomalies that don't represent real drift)
    2. Insufficient sustained trend (not enough consistent points)
    3. High variance (unstable signal that may not be reliable)

    Args:
        values: List of metric values over time
        drift_detected: Initial drift detection result
        drift_score: Initial drift score
        trend: Detected trend direction

    Returns:
        Tuple of (filtered_drift_detected, adjusted_drift_score, filter_metadata)
    """
    if not drift_detected or len(values) < MIN_SAMPLES_FOR_ANOMALY:
        # Not enough data or no drift, return as-is
        return drift_detected, drift_score, {
            "filter_applied": False,
            "reason": "insufficient_data_or_no_drift"
        }

    # Step 1: Detect anomalies
    zscore_anomalies = detect_anomalies_zscore(values)
    iqr_anomalies = detect_anomalies_iqr(values)

    # Combine anomalies (union of both methods)
    all_anomalies = sorted(set(zscore_anomalies + iqr_anomalies))

    # Step 2: Check if anomalies are isolated spikes
    isolated = is_isolated_spike(all_anomalies, len(values))

    # Step 3: Calculate signal stability (coefficient of variation)
    stats = calculate_statistics(values)
    if stats["mean"] != 0:
        cv = stats["std_dev"] / abs(stats["mean"])  # Coefficient of variation
    else:
        cv = 0.0

    # Step 4: Check for sustained trend consistency
    # Count how many consecutive points support the trend
    consecutive_trend = 0
    max_consecutive = 0

    for i in range(1, len(values)):
        if trend == "decreasing" and values[i] < values[i - 1]:
            consecutive_trend += 1
            max_consecutive = max(max_consecutive, consecutive_trend)
        elif trend == "increasing" and values[i] > values[i - 1]:
            consecutive_trend += 1
            max_consecutive = max(max_consecutive, consecutive_trend)
        else:
            consecutive_trend = 0

    sustained_trend = max_consecutive >= MIN_SUSTAINED_POINTS

    # Step 5: Apply filters
    filter_metadata = {
        "filter_applied": True,
        "anomalies_detected": len(all_anomalies),
        "isolated_spikes": isolated,
        "coefficient_of_variation": cv,
        "high_variance": cv > VARIANCE_STABILITY_THRESHOLD,
        "sustained_trend": sustained_trend,
        "max_consecutive_trend": max_consecutive,
    }

    # False positive conditions:
    # 1. Isolated spikes with high variance
    # 2. No sustained trend despite initial detection
    # 3. Very high variance making signal unreliable

    false_positive = False
    adjusted_score = drift_score

    if isolated and cv > VARIANCE_STABILITY_THRESHOLD:
        false_positive = True
        filter_metadata["reason"] = "isolated_spikes_with_high_variance"
        adjusted_score *= 0.3  # Reduce confidence significantly

    elif not sustained_trend and trend != "stable":
        false_positive = True
        filter_metadata["reason"] = "insufficient_sustained_trend"
        adjusted_score *= 0.5  # Reduce confidence moderately

    elif cv > VARIANCE_STABILITY_THRESHOLD * 2:
        false_positive = True
        filter_metadata["reason"] = "extremely_high_variance"
        adjusted_score *= 0.2  # Signal too noisy to trust

    # If filtered as false positive, downgrade detection
    if false_positive:
        drift_detected = False

    return drift_detected, adjusted_score, filter_metadata


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

    # Normalize to 0-1 scale. The worst case is the value reaching 0 (for
    # higher_is_better) or 2*target (for lower_is_better); either way the
    # distance from the target saturates at |target|, so one bound serves
    # both directions. A zero target has no scale to normalise against, so
    # fall back to the raw distance instead of dividing by zero.
    max_distance = abs(target) if target else 1.0

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

# Per-type presentation spec. The stored metric each type reads is METRIC_KEYS
# (owned by drift-db.py); everything here is label/shape only. All four
# metrics are compliance rates in [0, 1] where higher is better and 1.0 is the
# target, so those defaults are shared and only listed once.
METRIC_SPECS: dict[str, dict[str, Any]] = {
    "color_drift": {
        "label": "Color",
        "no_data": "No color metrics found in the specified window",
        # Only the colour analysis ever reported a moving-average field; kept
        # per-type so the JSON shape of every consumer stays exactly the same.
        "moving_average": True,
    },
    "font_drift": {
        "label": "Font",
        "no_data": "No font metrics found in the specified window",
    },
    "tone_drift": {
        "label": "Tone",
        "no_data": "No tone metrics found in the specified window",
    },
    "spacing_drift": {
        "label": "Spacing",
        "no_data": "No spacing metrics found in the specified window",
    },
}

_SPEC_DEFAULTS: dict[str, Any] = {
    "target": 1.0,
    "higher_is_better": True,
    "moving_average": False,
    "moving_average_window": 3,
}


def _spec(drift_type: str) -> dict[str, Any]:
    if drift_type not in METRIC_SPECS or drift_type not in METRIC_KEYS:
        raise ValueError(
            f"unknown drift type {drift_type!r}; expected one of {sorted(METRIC_KEYS)}")
    return {**_SPEC_DEFAULTS, **METRIC_SPECS[drift_type]}


def fetch_metric_values(drift_type: str, db_path: str, window_days: int) -> list[float]:
    """Metric values for one drift type inside the window, oldest first."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.timestamp, m.value, m.metadata
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = ?
              AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (METRIC_KEYS[drift_type], cutoff)
        )
        return [row["value"] for row in cursor.fetchall()]
    finally:
        conn.close()


def analyze_metric(
    drift_type: str,
    db_path: str = DB_PATH,
    window_days: int = 30,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Analyze one drift type: fetch its metric series, run trend detection,
    score the drift and apply false-positive filtering.

    Args:
        drift_type: One of METRIC_KEYS (color_drift, font_drift, tone_drift, spacing_drift)
        db_path: Path to SQLite database
        window_days: Number of days to analyze (default: 30)
        verbose: Print detailed output (default: False)

    Returns:
        Dictionary with drift analysis results
    """
    spec = _spec(drift_type)
    values = fetch_metric_values(drift_type, db_path, window_days)

    if not values:
        return {
            "metric_type": drift_type,
            "status": "no_data",
            "message": spec["no_data"],
            "drift_detected": False,
        }

    avg = sum(values) / len(values)
    latest = values[-1]
    first = values[0]

    trend = detect_sustained_trend(values)
    x = list(range(len(values)))
    slope, intercept = linear_regression(x, values)

    trend_info: dict[str, Any] = {
        "direction": trend,
        "slope": slope,
        "intercept": intercept,
    }
    if spec["moving_average"]:
        ma_filtered = [v for v in moving_average(values, window=spec["moving_average_window"])
                       if v is not None]
        trend_info["moving_average_latest"] = ma_filtered[-1] if ma_filtered else None

    drift_score = calculate_trend_score(
        values, target=spec["target"], higher_is_better=spec["higher_is_better"])
    threshold = DEFAULT_THRESHOLDS[drift_type]
    drift_detected = drift_score > threshold

    filtered_drift, adjusted_score, filter_meta = filter_false_positives(
        values, drift_detected, drift_score, trend
    )

    result = {
        "metric_type": drift_type,
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
        "trend": trend_info,
        "drift_score": drift_score,
        "adjusted_drift_score": adjusted_score,
        "threshold": threshold,
        "drift_detected": filtered_drift,
        "drift_detected_raw": drift_detected,
        "severity": "high" if adjusted_score > 0.3 else "medium" if adjusted_score > 0.15 else "low",
        "false_positive_filter": filter_meta,
    }

    if verbose:
        print(f"{spec['label']} Drift Analysis (window: {window_days} days)")
        print(f"  Data points: {len(values)}")
        print(f"  Average compliance: {avg:.1%}")
        print(f"  Latest compliance: {latest:.1%}")
        print(f"  Trend: {trend} (slope: {slope:.4f})")
        print(f"  Drift score: {drift_score:.3f} -> {adjusted_score:.3f} (after filtering)")
        print(f"  Drift detected: {filtered_drift} (raw: {drift_detected})")
        if filter_meta.get("filter_applied"):
            print(f"  Filter: {filter_meta.get('reason', 'applied')}")
            print(f"    - Anomalies: {filter_meta.get('anomalies_detected', 0)}")
            print(f"    - CV: {filter_meta.get('coefficient_of_variation', 0):.3f}")

    return result


# Thin wrappers: drift-alert.py, drift-report.py and brand-monitor.py call
# these by name, so the names stay even though they share one implementation.

def analyze_color_drift(db_path: str = DB_PATH, window_days: int = 30,
                        verbose: bool = False) -> dict[str, Any]:
    """Color drift: palette compliance rate declining over time."""
    return analyze_metric("color_drift", db_path, window_days, verbose)


def analyze_font_drift(db_path: str = DB_PATH, window_days: int = 30,
                       verbose: bool = False) -> dict[str, Any]:
    """Font drift: brand font ratio declining over time."""
    return analyze_metric("font_drift", db_path, window_days, verbose)


def analyze_tone_drift(db_path: str = DB_PATH, window_days: int = 30,
                       verbose: bool = False) -> dict[str, Any]:
    """Tone drift: tone compliance scores trending away from target."""
    return analyze_metric("tone_drift", db_path, window_days, verbose)


def analyze_spacing_drift(db_path: str = DB_PATH, window_days: int = 30,
                          verbose: bool = False) -> dict[str, Any]:
    """Spacing drift: spacing compliance declining over time."""
    return analyze_metric("spacing_drift", db_path, window_days, verbose)


# --------------------------------------------------------------------------
# Main CLI
# --------------------------------------------------------------------------


ANALYZERS = {
    "color_drift": analyze_color_drift,
    "font_drift": analyze_font_drift,
    "tone_drift": analyze_tone_drift,
    "spacing_drift": analyze_spacing_drift,
}


def analyze_drift(
    metric_type: str,
    db_path: str = DB_PATH,
    window_days: int = 30,
    threshold: float | None = None,
    verbose: bool = False,
    **_ignored: Any,
) -> dict[str, Any]:
    """Run the analyzer for one drift type (used by drift-alert.py and drift-report.py).

    ``threshold`` temporarily overrides DEFAULT_THRESHOLDS[metric_type] for this call.
    """
    if metric_type not in ANALYZERS:
        raise ValueError(f"unknown drift type {metric_type!r}; expected one of {sorted(ANALYZERS)}")
    previous = DEFAULT_THRESHOLDS[metric_type]
    if threshold is not None:
        DEFAULT_THRESHOLDS[metric_type] = threshold
    try:
        return ANALYZERS[metric_type](db_path=db_path, window_days=window_days, verbose=verbose)
    finally:
        DEFAULT_THRESHOLDS[metric_type] = previous

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AZMX brand drift statistical analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--analyze",
        choices=list(METRIC_KEYS),
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
        "--quiet",
        action="store_true",
        help="Suppress the human-readable summary (exit code still reports drift)"
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

    # Override thresholds if specified. Test against None, not truthiness:
    # `--threshold 0` is a legitimate "flag any drift at all" setting.
    if args.threshold is not None:
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
        results = [analyze_metric(args.analyze, args.db, args.window, args.verbose)]

    elif args.detect_all:
        # All analyses, in the fixed METRIC_KEYS order (color, font, tone, spacing)
        results = [analyze_metric(t, args.db, args.window, args.verbose) for t in METRIC_KEYS]

    else:
        parser.print_help()
        return 0

    # Output results
    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    elif args.quiet:
        pass
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
