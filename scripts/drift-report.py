#!/usr/bin/env python3
"""
drift-report.py — AZMX brand drift report generation.

Generates HTML reports with trend visualizations and drift analysis summaries.
Reports include time-series charts for color, font, tone, and spacing drift,
along with current status indicators and actionable recommendations.

Usage:
    python3 scripts/drift-report.py --generate --output report.html
    python3 scripts/drift-report.py --period weekly --output weekly.html
    python3 scripts/drift-report.py --window 30 --verbose
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import io
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Import drift database and detector functions
try:
    drift_db_path = Path(__file__).parent / "drift-db.py"
    if not drift_db_path.exists():
        raise ImportError(f"drift-db.py not found at {drift_db_path}")

    spec = importlib.util.spec_from_file_location("drift_db", drift_db_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {drift_db_path}")

    drift_db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift_db)

    get_connection = drift_db.get_connection
    DB_PATH = drift_db.DB_PATH

except Exception as e:
    print(f"Error importing drift-db.py: {e}", file=sys.stderr)
    sys.exit(1)

try:
    drift_detector_path = Path(__file__).parent / "drift-detector.py"
    if not drift_detector_path.exists():
        raise ImportError(f"drift-detector.py not found at {drift_detector_path}")

    spec = importlib.util.spec_from_file_location("drift_detector", drift_detector_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {drift_detector_path}")

    drift_detector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift_detector)

    analyze_color_drift = drift_detector.analyze_color_drift
    analyze_font_drift = drift_detector.analyze_font_drift
    analyze_tone_drift = drift_detector.analyze_tone_drift
    analyze_spacing_drift = drift_detector.analyze_spacing_drift

except Exception as e:
    print(f"Error importing drift-detector.py: {e}", file=sys.stderr)
    sys.exit(1)

# Try to import matplotlib for chart generation
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_WINDOW_DAYS = 30
PERIOD_WINDOWS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}


# --------------------------------------------------------------------------
# Chart Generation
# --------------------------------------------------------------------------

def create_trend_chart(
    timestamps: list[str],
    values: list[float],
    title: str,
    ylabel: str,
    threshold: Optional[float] = None,
    higher_is_better: bool = True
) -> str:
    """
    Create a time-series trend chart and return it as a base64-encoded PNG.

    Args:
        timestamps: List of ISO timestamp strings
        values: List of metric values
        ylabel: Y-axis label
        title: Chart title
        threshold: Optional threshold line to display
        higher_is_better: Whether higher values are better (for color coding)

    Returns:
        Base64-encoded PNG image data URL
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""

    if not timestamps or not values:
        return ""

    # Parse timestamps
    dates = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]

    # Create figure with AZMX brand colors
    fig = Figure(figsize=(10, 4), facecolor='#040038')
    ax = fig.add_subplot(111, facecolor='#040038')

    # Plot the data
    line_color = '#001AFF' if higher_is_better else '#5D8FFF'
    ax.plot(dates, values, marker='o', linewidth=2, markersize=4,
            color=line_color, label='Actual')

    # Add threshold line if provided
    if threshold is not None:
        ax.axhline(y=threshold, color='#FF2B3C', linestyle='--',
                   linewidth=1.5, alpha=0.7, label='Threshold')

    # Style the chart
    ax.set_title(title, color='#FFFFFF', fontsize=14, pad=15, fontweight='600')
    ax.set_ylabel(ylabel, color='#DDE8FF', fontsize=11)
    ax.tick_params(colors='#DDE8FF', labelsize=9)

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate()

    # Grid
    ax.grid(True, alpha=0.15, color='#FFFFFF', linestyle='-', linewidth=0.5)

    # Legend
    if threshold is not None:
        ax.legend(loc='upper right', framealpha=0.9, fontsize=9,
                  facecolor='#01006E', edgecolor='#5D8FFF')

    # Spine colors
    for spine in ax.spines.values():
        spine.set_edgecolor('#5D8FFF')
        spine.set_alpha(0.3)

    fig.tight_layout()

    # Convert to base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor='#040038')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"


def create_status_badge(drift_detected: bool, score: float) -> str:
    """
    Create an HTML status badge based on drift detection.

    Args:
        drift_detected: Whether drift was detected
        score: Drift score

    Returns:
        HTML string for status badge
    """
    if drift_detected:
        color = '#FF2B3C'
        status = 'DRIFT DETECTED'
        icon = '⚠'
    elif score > 0.05:
        color = '#FED340'
        status = 'WATCH'
        icon = '⚡'
    else:
        color = '#22C36F'
        status = 'OK'
        icon = '✓'

    return f"""<div class="status-badge" style="background: {color}20; border: 2px solid {color}; color: {color};">
        <span class="status-icon">{icon}</span>
        <span class="status-text">{status}</span>
        <span class="status-score">{score:.3f}</span>
    </div>"""


# --------------------------------------------------------------------------
# Aggregation Functions
# --------------------------------------------------------------------------

def calculate_period_aggregates(
    db_path: str,
    window_days: int,
    period_name: Optional[str] = None,
    verbose: bool = False
) -> dict[str, Any]:
    """
    Calculate aggregated statistics for a reporting period.

    Args:
        db_path: Path to SQLite database
        window_days: Number of days in the period
        period_name: Name of the period (daily/weekly/monthly)
        verbose: Print detailed output

    Returns:
        Dictionary with aggregated statistics
    """
    if verbose:
        print(f"Calculating {period_name or 'period'} aggregates...")

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

    try:
        # Total scans in period
        cursor.execute(
            "SELECT COUNT(*) FROM scans WHERE timestamp >= ?",
            (cutoff,)
        )
        total_scans = cursor.fetchone()[0]

        # Alerts by type (using severity as type)
        cursor.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM alerts
            WHERE timestamp >= ?
            GROUP BY severity
            ORDER BY count DESC
            """,
            (cutoff,)
        )
        violations_by_type = {row['severity']: row['count'] for row in cursor.fetchall()}

        # Total alerts
        total_violations = sum(violations_by_type.values())

        # Average drift scores by metric type
        metric_averages = {}
        for metric_type in ['avg_palette_distance', 'brand_font_compliance_rate',
                           'tone_compliance_score', 'spacing_compliance_rate']:
            cursor.execute(
                """
                SELECT AVG(m.value) as avg_value
                FROM metrics m
                JOIN scans s ON m.scan_id = s.id
                WHERE m.metric_type = ? AND s.timestamp >= ?
                """,
                (metric_type, cutoff)
            )
            result = cursor.fetchone()
            metric_averages[metric_type] = result['avg_value'] if result['avg_value'] is not None else 0.0

        # Top alerts (most frequent messages)
        cursor.execute(
            """
            SELECT message, COUNT(*) as count
            FROM alerts
            WHERE timestamp >= ?
            GROUP BY message
            ORDER BY count DESC
            LIMIT 5
            """,
            (cutoff,)
        )
        top_violations = [
            {'description': row['message'], 'count': row['count']}
            for row in cursor.fetchall()
        ]

        # Files with most issues (based on scans)
        cursor.execute(
            """
            SELECT file_path, COUNT(*) as count
            FROM scans
            WHERE timestamp >= ?
            GROUP BY file_path
            ORDER BY count DESC
            LIMIT 5
            """,
            (cutoff,)
        )
        problematic_files = [
            {'file': row['file_path'], 'count': row['count']}
            for row in cursor.fetchall()
        ]

        # Trend comparison (current period vs previous period)
        previous_cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days * 2)).isoformat()
        cursor.execute(
            """
            SELECT COUNT(*) FROM alerts
            WHERE timestamp >= ? AND timestamp < ?
            """,
            (previous_cutoff, cutoff)
        )
        previous_violations = cursor.fetchone()[0]

        # Calculate trend
        if previous_violations > 0:
            trend_pct = ((total_violations - previous_violations) / previous_violations) * 100
        else:
            trend_pct = 0 if total_violations == 0 else 100

    finally:
        conn.close()

    aggregates = {
        'period_name': period_name,
        'window_days': window_days,
        'total_scans': total_scans,
        'total_violations': total_violations,
        'violations_by_type': violations_by_type,
        'metric_averages': metric_averages,
        'top_violations': top_violations,
        'problematic_files': problematic_files,
        'previous_violations': previous_violations,
        'trend_pct': trend_pct,
    }

    if verbose:
        print(f"  Total scans: {total_scans}")
        print(f"  Total violations: {total_violations}")
        print(f"  Trend: {trend_pct:+.1f}% vs previous period")

    return aggregates


# --------------------------------------------------------------------------
# Data Collection
# --------------------------------------------------------------------------

def collect_drift_data(db_path: str, window_days: int, verbose: bool = False) -> dict[str, Any]:
    """
    Collect all drift analysis data for the report.

    Args:
        db_path: Path to SQLite database
        window_days: Number of days to analyze
        verbose: Print detailed output

    Returns:
        Dictionary with all drift analysis results
    """
    if verbose:
        print(f"Collecting drift data for {window_days}-day window...")

    results = {}

    # Analyze each drift type
    results['color'] = analyze_color_drift(db_path, window_days, verbose)
    results['font'] = analyze_font_drift(db_path, window_days, verbose)
    results['tone'] = analyze_tone_drift(db_path, window_days, verbose)
    results['spacing'] = analyze_spacing_drift(db_path, window_days, verbose)

    # Collect overall statistics
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Count total scans
        cursor.execute("SELECT COUNT(*) FROM scans")
        total_scans = cursor.fetchone()[0]

        # Count scans in window
        cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM scans WHERE timestamp >= ?", (cutoff,))
        window_scans = cursor.fetchone()[0]

        # Get latest scan time
        cursor.execute("SELECT MAX(timestamp) FROM scans")
        latest_scan = cursor.fetchone()[0]

    finally:
        conn.close()

    results['summary'] = {
        'total_scans': total_scans,
        'window_scans': window_scans,
        'window_days': window_days,
        'latest_scan': latest_scan,
        'report_generated': datetime.now(timezone.utc).isoformat(),
    }

    if verbose:
        print(f"  Total scans: {total_scans}")
        print(f"  Scans in window: {window_scans}")
        print(f"  Latest scan: {latest_scan or 'never'}")

    return results


def get_metric_timeseries(
    db_path: str,
    metric_type: str,
    window_days: int
) -> tuple[list[str], list[float]]:
    """
    Get time-series data for a specific metric type.

    Args:
        db_path: Path to SQLite database
        metric_type: Type of metric to query
        window_days: Number of days to query

    Returns:
        Tuple of (timestamps, values)
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT s.timestamp, m.value
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = ?
              AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (metric_type, cutoff)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return [], []

    timestamps = [row['timestamp'] for row in rows]
    values = [row['value'] for row in rows]

    return timestamps, values


# --------------------------------------------------------------------------
# Report Generation
# --------------------------------------------------------------------------

def generate_report_html(data: dict[str, Any], window_days: int, aggregates: Optional[dict[str, Any]] = None) -> str:
    """
    Generate HTML report from drift analysis data.

    Args:
        data: Drift analysis results
        window_days: Analysis window in days
        aggregates: Optional period aggregation statistics

    Returns:
        HTML string
    """
    summary = data['summary']
    color = data['color']
    font = data['font']
    tone = data['tone']
    spacing = data['spacing']

    # Generate charts if matplotlib is available
    charts = {}
    if MATPLOTLIB_AVAILABLE:
        # Color drift chart
        ts, vals = get_metric_timeseries(DB_PATH, 'avg_palette_distance', window_days)
        if ts and vals:
            charts['color'] = create_trend_chart(
                ts, vals, 'Color Palette Distance Over Time',
                'Average Distance', higher_is_better=False
            )

        # Font drift chart
        ts, vals = get_metric_timeseries(DB_PATH, 'brand_font_compliance_rate', window_days)
        if ts and vals:
            charts['font'] = create_trend_chart(
                ts, vals, 'Brand Font Usage Over Time',
                'Compliance Rate', higher_is_better=True
            )

        # Tone drift chart
        ts, vals = get_metric_timeseries(DB_PATH, 'tone_compliance_score', window_days)
        if ts and vals:
            charts['tone'] = create_trend_chart(
                ts, vals, 'Tone Compliance Over Time',
                'Compliance Score', higher_is_better=True
            )

        # Spacing drift chart
        ts, vals = get_metric_timeseries(DB_PATH, 'spacing_compliance_rate', window_days)
        if ts and vals:
            charts['spacing'] = create_trend_chart(
                ts, vals, 'Spacing Compliance Over Time',
                'Compliance Rate', higher_is_better=True
            )

    # Read HTML template
    template_path = Path(__file__).parent / 'templates' / 'drift-report.html'
    if template_path.exists():
        with open(template_path, 'r') as f:
            template = f.read()
    else:
        # Inline template if file doesn't exist
        template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>AZMX Brand Drift Report</title>
    {styles}
</head>
<body>
    <header>
        <div class="eyebrow">Brand Intelligence Report</div>
        <h1>Drift Detection Analysis</h1>
        <p class="lede">Proactive monitoring of brand consistency trends across deliverables.</p>
        <div class="meta">
            Report generated: {report_time}<br>
            Analysis window: {window_days} days ({window_scans} scans)<br>
            Latest scan: {latest_scan}
        </div>
    </header>
    <main>
        {content}
    </main>
</body>
</html>"""

    # Format report time
    report_time = datetime.fromisoformat(summary['report_generated'].replace('Z', '+00:00'))
    report_time_str = report_time.strftime('%B %d, %Y at %H:%M UTC')

    latest_scan = summary['latest_scan']
    if latest_scan:
        latest_scan_dt = datetime.fromisoformat(latest_scan.replace('Z', '+00:00'))
        latest_scan_str = latest_scan_dt.strftime('%B %d, %Y at %H:%M UTC')
    else:
        latest_scan_str = 'Never'

    # Build content sections
    content_sections = []

    # Period aggregates section (if available)
    if aggregates:
        period_title = f"{aggregates['period_name'].title()} Summary" if aggregates.get('period_name') else "Period Summary"
        trend_color = '#FF2B3C' if aggregates['trend_pct'] > 0 else '#22C36F'
        trend_icon = '↑' if aggregates['trend_pct'] > 0 else '↓'

        # Build violations by type list
        violations_list = ''
        for vtype, count in aggregates['violations_by_type'].items():
            violations_list += f'<li><strong>{vtype}:</strong> {count} violations</li>'

        # Build top violations list
        top_violations_list = ''
        for item in aggregates['top_violations']:
            top_violations_list += f'<li>{item["description"]} <span class="count">({item["count"]}×)</span></li>'

        # Build problematic files list
        problematic_files_list = ''
        for item in aggregates['problematic_files']:
            file_display = item['file'].split('/')[-1] if '/' in item['file'] else item['file']
            problematic_files_list += f'<li><code>{file_display}</code> <span class="count">({item["count"]}×)</span></li>'

        aggregates_section = f"""
    <section class="period-summary">
        <h2>{period_title}</h2>
        <div class="summary-stats">
            <div class="stat-row">
                <div class="stat-item">
                    <div class="stat-value">{aggregates['total_scans']}</div>
                    <div class="stat-label">Total Scans</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{aggregates['total_violations']}</div>
                    <div class="stat-label">Total Violations</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {trend_color};">
                        {trend_icon} {abs(aggregates['trend_pct']):.1f}%
                    </div>
                    <div class="stat-label">vs Previous Period</div>
                </div>
            </div>
        </div>

        <div class="aggregates-grid">
            <div class="aggregate-card">
                <h3>Violations by Type</h3>
                <ul class="violation-list">
                    {violations_list if violations_list else '<li>No violations detected</li>'}
                </ul>
            </div>

            <div class="aggregate-card">
                <h3>Top Issues</h3>
                <ul class="violation-list">
                    {top_violations_list if top_violations_list else '<li>No issues detected</li>'}
                </ul>
            </div>
        </div>

        {f'''<div class="aggregate-card full-width">
            <h3>Most Problematic Files</h3>
            <ul class="file-list">
                {problematic_files_list}
            </ul>
        </div>''' if problematic_files_list else ''}

        <div class="metrics-summary">
            <h3>Average Metrics</h3>
            <div class="metrics-row">
                <div class="metric-item">
                    <div class="metric-name">Color Distance</div>
                    <div class="metric-value">{aggregates['metric_averages'].get('avg_palette_distance', 0):.3f}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-name">Font Compliance</div>
                    <div class="metric-value">{aggregates['metric_averages'].get('brand_font_compliance_rate', 0):.1%}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-name">Tone Compliance</div>
                    <div class="metric-value">{aggregates['metric_averages'].get('tone_compliance_score', 0):.1%}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-name">Spacing Compliance</div>
                    <div class="metric-value">{aggregates['metric_averages'].get('spacing_compliance_rate', 0):.1%}</div>
                </div>
            </div>
        </div>
    </section>
        """
        content_sections.append(aggregates_section)

    # Overview section
    overview = f"""
    <section class="overview">
        <h2>Executive Summary</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Color Drift</div>
                {create_status_badge(color.get('drift_detected', False), color.get('drift_score', 0))}
                <div class="metric-detail">{color.get('data_points', 0)} data points</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Font Drift</div>
                {create_status_badge(font.get('drift_detected', False), font.get('drift_score', 0))}
                <div class="metric-detail">{font.get('data_points', 0)} data points</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Tone Drift</div>
                {create_status_badge(tone.get('drift_detected', False), tone.get('drift_score', 0))}
                <div class="metric-detail">{tone.get('data_points', 0)} data points</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Spacing Drift</div>
                {create_status_badge(spacing.get('drift_detected', False), spacing.get('drift_score', 0))}
                <div class="metric-detail">{spacing.get('data_points', 0)} data points</div>
            </div>
        </div>
    </section>
    """
    content_sections.append(overview)

    # Detailed sections for each metric
    if charts.get('color'):
        color_section = f"""
    <section class="drift-detail">
        <h2>Color Drift Analysis</h2>
        <div class="chart-container">
            <img src="{charts['color']}" alt="Color drift trend chart" class="trend-chart">
        </div>
        <div class="stats">
            <p><strong>Trend:</strong> {color.get('trend', {}).get('direction', 'unknown').title()}</p>
            <p><strong>Data points:</strong> {color.get('data_points', 0)}</p>
            <p><strong>Status:</strong> {color.get('status', 'unknown')}</p>
        </div>
    </section>
        """
        content_sections.append(color_section)

    if charts.get('font'):
        font_section = f"""
    <section class="drift-detail">
        <h2>Font Drift Analysis</h2>
        <div class="chart-container">
            <img src="{charts['font']}" alt="Font drift trend chart" class="trend-chart">
        </div>
        <div class="stats">
            <p><strong>Trend:</strong> {font.get('trend', {}).get('direction', 'unknown').title()}</p>
            <p><strong>Data points:</strong> {font.get('data_points', 0)}</p>
            <p><strong>Status:</strong> {font.get('status', 'unknown')}</p>
        </div>
    </section>
        """
        content_sections.append(font_section)

    if charts.get('tone'):
        tone_section = f"""
    <section class="drift-detail">
        <h2>Tone Drift Analysis</h2>
        <div class="chart-container">
            <img src="{charts['tone']}" alt="Tone drift trend chart" class="trend-chart">
        </div>
        <div class="stats">
            <p><strong>Trend:</strong> {tone.get('trend', {}).get('direction', 'unknown').title()}</p>
            <p><strong>Data points:</strong> {tone.get('data_points', 0)}</p>
            <p><strong>Status:</strong> {tone.get('status', 'unknown')}</p>
        </div>
    </section>
        """
        content_sections.append(tone_section)

    if charts.get('spacing'):
        spacing_section = f"""
    <section class="drift-detail">
        <h2>Spacing Drift Analysis</h2>
        <div class="chart-container">
            <img src="{charts['spacing']}" alt="Spacing drift trend chart" class="trend-chart">
        </div>
        <div class="stats">
            <p><strong>Trend:</strong> {spacing.get('trend', {}).get('direction', 'unknown').title()}</p>
            <p><strong>Data points:</strong> {spacing.get('data_points', 0)}</p>
            <p><strong>Status:</strong> {spacing.get('status', 'unknown')}</p>
        </div>
    </section>
        """
        content_sections.append(spacing_section)

    # No data message if no charts
    if not charts:
        content_sections.append("""
    <section class="no-data">
        <p>No visualization data available. Install matplotlib to see trend charts:</p>
        <pre>pip3 install matplotlib</pre>
    </section>
        """)

    content = '\n'.join(content_sections)

    # CSS styles
    styles = """<style>
:root {
    --navy: #040038;
    --electric: #001AFF;
    --lightblue: #5D8FFF;
    --blue100: #DDE8FF;
    --blue200: #BFD5FF;
    --green: #22C36F;
    --yellow: #FED340;
    --red: #FF2B3C;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: var(--navy);
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, sans-serif;
    -webkit-font-smoothing: antialiased;
}

header {
    padding: 48px 32px;
    max-width: 1200px;
    margin: 0 auto;
}

.eyebrow {
    color: var(--lightblue);
    text-transform: uppercase;
    letter-spacing: 2.4px;
    font-size: 14px;
    font-weight: 600;
    margin: 0 0 16px;
}

h1 {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 48px;
    font-weight: 400;
    letter-spacing: -1px;
    line-height: 1.1;
    margin: 0 0 16px;
}

h2 {
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.5px;
    margin: 0 0 20px;
    color: var(--blue100);
}

.lede {
    color: var(--blue100);
    font-size: 18px;
    line-height: 1.6;
    max-width: 60ch;
    margin: 0 0 12px;
    opacity: 0.88;
}

.meta {
    color: var(--blue200);
    opacity: 0.7;
    font-size: 14px;
    margin: 20px 0 0;
    line-height: 1.6;
}

main {
    padding: 0 32px 48px;
    max-width: 1200px;
    margin: 0 auto;
}

section {
    margin: 32px 0;
    padding: 24px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    margin-top: 24px;
}

.metric-card {
    padding: 20px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
}

.metric-label {
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--blue200);
    margin-bottom: 12px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin: 8px 0;
}

.status-icon {
    font-size: 16px;
}

.status-score {
    margin-left: auto;
    font-variant-numeric: tabular-nums;
}

.metric-detail {
    font-size: 12px;
    color: var(--blue200);
    opacity: 0.7;
    margin-top: 8px;
}

.chart-container {
    margin: 20px 0;
}

.trend-chart {
    width: 100%;
    height: auto;
    border-radius: 4px;
}

.stats {
    margin-top: 16px;
    color: var(--blue100);
    font-size: 14px;
    line-height: 1.8;
}

.stats strong {
    color: var(--lightblue);
}

.no-data {
    text-align: center;
    padding: 48px 24px;
    color: var(--blue200);
}

.no-data pre {
    display: inline-block;
    background: rgba(0, 26, 255, 0.1);
    border: 1px solid var(--electric);
    padding: 12px 20px;
    border-radius: 4px;
    color: var(--lightblue);
    margin-top: 16px;
}

.period-summary {
    background: linear-gradient(135deg, rgba(0, 26, 255, 0.08) 0%, rgba(0, 26, 255, 0.02) 100%);
    border-color: rgba(0, 26, 255, 0.3);
}

.summary-stats {
    margin: 24px 0;
}

.stat-row {
    display: flex;
    gap: 32px;
    justify-content: center;
    flex-wrap: wrap;
}

.stat-item {
    text-align: center;
    min-width: 140px;
}

.stat-value {
    font-size: 36px;
    font-weight: 700;
    color: var(--electric);
    margin-bottom: 8px;
    font-variant-numeric: tabular-nums;
}

.stat-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--blue200);
    opacity: 0.8;
}

.aggregates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 24px 0;
}

.aggregate-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 20px;
}

.aggregate-card.full-width {
    grid-column: 1 / -1;
}

.aggregate-card h3 {
    font-size: 16px;
    font-weight: 600;
    color: var(--lightblue);
    margin: 0 0 16px;
    letter-spacing: 0.5px;
}

.violation-list, .file-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.violation-list li, .file-list li {
    padding: 10px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--blue100);
    font-size: 14px;
    line-height: 1.6;
}

.violation-list li:last-child, .file-list li:last-child {
    border-bottom: none;
}

.violation-list .count, .file-list .count {
    color: var(--blue200);
    opacity: 0.7;
    font-size: 13px;
    margin-left: 8px;
}

.file-list code {
    background: rgba(0, 26, 255, 0.1);
    padding: 2px 8px;
    border-radius: 3px;
    font-family: 'SF Mono', Monaco, 'Courier New', monospace;
    font-size: 13px;
    color: var(--lightblue);
}

.metrics-summary {
    margin-top: 24px;
}

.metrics-summary h3 {
    font-size: 16px;
    font-weight: 600;
    color: var(--lightblue);
    margin: 0 0 16px;
    letter-spacing: 0.5px;
}

.metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
}

.metric-item {
    padding: 12px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
    text-align: center;
}

.metric-name {
    font-size: 12px;
    color: var(--blue200);
    opacity: 0.8;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 20px;
    font-weight: 600;
    color: var(--electric);
    font-variant-numeric: tabular-nums;
}
</style>"""

    # Fill in template
    html = template.format(
        styles=styles,
        report_time=report_time_str,
        window_days=window_days,
        window_scans=summary['window_scans'],
        latest_scan=latest_scan_str,
        content=content
    )

    return html


def save_report(html: str, output_path: str) -> None:
    """
    Save HTML report to file.

    Args:
        html: HTML content
        output_path: Output file path
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report saved to: {output_path}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate AZMX brand drift reports with trend visualizations'
    )
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate a drift report'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='drift-report.html',
        help='Output file path (default: drift-report.html)'
    )
    parser.add_argument(
        '--period',
        type=str,
        choices=['daily', 'weekly', 'monthly'],
        help='Report period (daily/weekly/monthly)'
    )
    parser.add_argument(
        '--window',
        type=int,
        help='Custom analysis window in days (overrides --period)'
    )
    parser.add_argument(
        '--db',
        type=str,
        default=DB_PATH,
        help=f'Path to drift database (default: {DB_PATH})'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed output'
    )

    args = parser.parse_args()

    # Auto-enable generate if period or output is specified
    if args.period or args.output != 'drift-report.html':
        args.generate = True

    if not args.generate:
        parser.print_help()
        return 0

    # Determine window size
    if args.window:
        window_days = args.window
    elif args.period:
        window_days = PERIOD_WINDOWS[args.period]
    else:
        window_days = DEFAULT_WINDOW_DAYS

    if args.verbose:
        print(f"Generating drift report...")
        print(f"  Database: {args.db}")
        print(f"  Window: {window_days} days")
        print(f"  Output: {args.output}")

    # Check if database exists
    if not Path(args.db).exists():
        print(f"Error: Database not found at {args.db}", file=sys.stderr)
        print("Run brand-monitor.py to create and populate the database", file=sys.stderr)
        return 1

    # Collect drift data
    try:
        data = collect_drift_data(args.db, window_days, args.verbose)
    except Exception as e:
        print(f"Error collecting drift data: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Calculate period aggregates if period is specified
    aggregates = None
    if args.period:
        try:
            aggregates = calculate_period_aggregates(
                args.db, window_days, args.period, args.verbose
            )
        except Exception as e:
            print(f"Error calculating period aggregates: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    # Generate report HTML
    try:
        html = generate_report_html(data, window_days, aggregates)
    except Exception as e:
        print(f"Error generating report HTML: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Save report
    try:
        save_report(html, args.output)
    except Exception as e:
        print(f"Error saving report: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    if args.verbose:
        print("Report generation complete")

    return 0


if __name__ == '__main__':
    sys.exit(main())
