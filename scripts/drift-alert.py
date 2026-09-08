#!/usr/bin/env python3
"""
drift-alert.py — AZMX brand drift alert system.

Sends email notifications to brand managers when drift thresholds are exceeded,
sustained trends are detected, or anomalies are found.

Alert Triggers:
  - Drift threshold exceeded (configurable per metric type)
  - Sustained trend detected (3+ consecutive drift points)
  - Statistical anomaly detected (outlier in normal pattern)

Email Content:
  - Executive summary of drift findings
  - Severity level (high/medium/low)
  - Trend indicators and statistics
  - Link to detailed HTML report

Usage:
    python3 scripts/drift-alert.py --check-drift
    python3 scripts/drift-alert.py --test-email --dry-run
    python3 scripts/drift-alert.py --send-pending-alerts
    python3 scripts/drift-alert.py --config .brand-monitor.yml
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

except Exception as e:
    print(f"Error importing drift-db.py: {e}", file=sys.stderr)
    print("Ensure drift-db.py exists in the scripts directory", file=sys.stderr)
    sys.exit(1)


# Import drift detector functions from drift-detector.py
try:
    drift_detector_path = Path(__file__).parent / "drift-detector.py"
    if not drift_detector_path.exists():
        raise ImportError(f"drift-detector.py not found at {drift_detector_path}")

    spec = importlib.util.spec_from_file_location("drift_detector", drift_detector_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {drift_detector_path}")

    drift_detector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift_detector)

except Exception as e:
    print(f"Error importing drift-detector.py: {e}", file=sys.stderr)
    print("Note: drift-detector.py is optional for basic alerts", file=sys.stderr)
    drift_detector = None


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Default SMTP configuration (can be overridden via config file)
DEFAULT_SMTP_CONFIG = {
    "host": "localhost",
    "port": 25,
    "use_tls": False,
    "use_ssl": False,
    "username": None,
    "password": None,
}

# Default alert configuration
DEFAULT_ALERT_CONFIG = {
    "from_email": "brand-drift@azmx.sa",
    "to_emails": ["brand-manager@azmx.sa"],
    "subject_prefix": "[AZMX Brand Drift]",
    "alert_thresholds": {
        "color_drift": 0.15,
        "font_drift": 0.10,
        "tone_drift": 0.10,
        "spacing_drift": 0.15,
    },
    "min_severity": "medium",  # Only send alerts for medium+ severity
}

# Color codes for terminal output
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
SEV_COLOR = {"high": "\033[31m", "medium": "\033[33m", "low": "\033[36m"}


# --------------------------------------------------------------------------
# Configuration Loading
# --------------------------------------------------------------------------

def load_config(config_path: str) -> dict[str, Any]:
    """
    Load configuration from YAML file.
    Returns combined SMTP and alert configuration.
    """
    if not os.path.exists(config_path):
        return {
            "smtp": DEFAULT_SMTP_CONFIG,
            "alerts": DEFAULT_ALERT_CONFIG,
        }

    try:
        import yaml
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    except ImportError:
        # Fallback to simple parser if PyYAML not installed
        config = parse_yaml_simple(config_path)

    # Extract and merge configurations
    smtp_config = {**DEFAULT_SMTP_CONFIG, **config.get("smtp", {})}
    alert_config = {**DEFAULT_ALERT_CONFIG, **config.get("alerts", {})}

    return {
        "smtp": smtp_config,
        "alerts": alert_config,
    }


def parse_yaml_simple(filepath: str) -> dict[str, Any]:
    """
    Simple YAML parser for basic configuration files.
    Handles simple key: value pairs and lists.
    """
    config: dict[str, Any] = {}
    current_section: Optional[str] = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.rstrip()
            if not line or line.strip().startswith("#"):
                continue

            # Section header (no indent, ends with colon)
            if line and not line[0].isspace() and line.endswith(":"):
                current_section = line[:-1].strip()
                config[current_section] = {}
                continue

            # List item
            if line.strip().startswith("- "):
                value = line.strip()[2:].strip()
                if current_section:
                    if not isinstance(config[current_section], list):
                        config[current_section] = []
                    config[current_section].append(value)
                continue

            # Key-value pair
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Try to parse value as number
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    # Keep as string
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.lower() == "null" or value == "":
                        value = None

                if current_section and isinstance(config[current_section], dict):
                    config[current_section][key] = value
                else:
                    config[key] = value

    return config


# --------------------------------------------------------------------------
# Database Alert Functions
# --------------------------------------------------------------------------

def insert_alert(
    metric_type: str,
    severity: str,
    message: str,
    details: Optional[str] = None,
    db_path: str = DB_PATH
) -> int:
    """
    Insert an alert record into the database.

    Args:
        metric_type: Type of metric that triggered the alert
        severity: Alert severity (high/medium/low)
        message: Alert message summary
        details: Optional JSON-encoded details
        db_path: Path to SQLite database file

    Returns:
        Alert ID of the inserted record
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO alerts (timestamp, metric_type, severity, message, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, metric_type, severity, message, details)
        )
        conn.commit()
        return cursor.lastrowid

    except Exception as e:
        print(f"Error inserting alert: {e}", file=sys.stderr)
        conn.rollback()
        return -1

    finally:
        conn.close()


def get_pending_alerts(
    min_severity: str = "low",
    db_path: str = DB_PATH
) -> list[dict[str, Any]]:
    """
    Get all unacknowledged alerts from the database.

    Args:
        min_severity: Minimum severity level to include
        db_path: Path to SQLite database file

    Returns:
        List of alert dictionaries
    """
    severity_order = {"high": 0, "medium": 1, "low": 2}
    min_severity_rank = severity_order.get(min_severity, 2)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, timestamp, metric_type, severity, message, details
            FROM alerts
            WHERE acknowledged = 0
            ORDER BY timestamp DESC
            """
        )
        rows = cursor.fetchall()

        # Filter by severity
        alerts = []
        for row in rows:
            alert = dict(row)
            severity_rank = severity_order.get(alert["severity"], 2)
            if severity_rank <= min_severity_rank:
                alerts.append(alert)

        return alerts

    except Exception as e:
        print(f"Error querying alerts: {e}", file=sys.stderr)
        return []

    finally:
        conn.close()


def acknowledge_alert(alert_id: int, db_path: str = DB_PATH) -> bool:
    """
    Mark an alert as acknowledged.

    Args:
        alert_id: ID of the alert to acknowledge
        db_path: Path to SQLite database file

    Returns:
        True if successful, False otherwise
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE alerts SET acknowledged = 1 WHERE id = ?",
            (alert_id,)
        )
        conn.commit()
        return True

    except Exception as e:
        print(f"Error acknowledging alert: {e}", file=sys.stderr)
        conn.rollback()
        return False

    finally:
        conn.close()


# --------------------------------------------------------------------------
# Email Functions
# --------------------------------------------------------------------------

def create_alert_email(
    alerts: list[dict[str, Any]],
    config: dict[str, Any]
) -> MIMEMultipart:
    """
    Create an email message with alert details.

    Args:
        alerts: List of alert dictionaries
        config: Alert configuration

    Returns:
        MIME multipart message
    """
    msg = MIMEMultipart("alternative")

    # Email headers
    subject_prefix = config["alerts"]["subject_prefix"]
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for alert in alerts:
        severity_counts[alert.get("severity", "low")] += 1

    if severity_counts["high"] > 0:
        subject = f"{subject_prefix} {severity_counts['high']} HIGH PRIORITY DRIFT ALERT(S)"
    elif severity_counts["medium"] > 0:
        subject = f"{subject_prefix} {severity_counts['medium']} drift alert(s) detected"
    else:
        subject = f"{subject_prefix} {len(alerts)} minor drift notification(s)"

    msg["Subject"] = subject
    msg["From"] = config["alerts"]["from_email"]
    msg["To"] = ", ".join(config["alerts"]["to_emails"])

    # Create plain text version
    text_body = create_text_email_body(alerts, severity_counts)
    msg.attach(MIMEText(text_body, "plain"))

    # Create HTML version
    html_body = create_html_email_body(alerts, severity_counts)
    msg.attach(MIMEText(html_body, "html"))

    return msg


def create_text_email_body(
    alerts: list[dict[str, Any]],
    severity_counts: dict[str, int]
) -> str:
    """
    Create plain text email body.
    """
    lines = [
        "AZMX BRAND DRIFT ALERT",
        "=" * 50,
        "",
        f"Total Alerts: {len(alerts)}",
        f"  - High Severity: {severity_counts['high']}",
        f"  - Medium Severity: {severity_counts['medium']}",
        f"  - Low Severity: {severity_counts['low']}",
        "",
        "=" * 50,
        "",
    ]

    # Group alerts by metric type
    by_type: dict[str, list[dict[str, Any]]] = {}
    for alert in alerts:
        metric_type = alert.get("metric_type", "unknown")
        if metric_type not in by_type:
            by_type[metric_type] = []
        by_type[metric_type].append(alert)

    # Add each metric type section
    for metric_type, metric_alerts in sorted(by_type.items()):
        lines.append(f"{metric_type.upper().replace('_', ' ')}")
        lines.append("-" * 50)

        for alert in metric_alerts:
            severity = alert.get("severity", "low").upper()
            timestamp = alert.get("timestamp", "")
            message = alert.get("message", "")

            lines.append(f"[{severity}] {message}")
            lines.append(f"  Time: {timestamp[:19]}")  # Strip microseconds

            # Add details if available
            details = alert.get("details")
            if details:
                try:
                    details_obj = json.loads(details)
                    if "drift_score" in details_obj:
                        lines.append(f"  Drift Score: {details_obj['drift_score']:.3f}")
                    if "trend" in details_obj:
                        lines.append(f"  Trend: {details_obj['trend']}")
                except (json.JSONDecodeError, TypeError):
                    pass

            lines.append("")

        lines.append("")

    # Footer
    lines.extend([
        "=" * 50,
        "",
        "Next Steps:",
        "1. Review the detailed drift report",
        "2. Identify files with highest drift scores",
        "3. Apply brand corrections as needed",
        "4. Monitor trend in next weekly report",
        "",
        "This is an automated alert from the AZMX Brand Drift Detection system.",
    ])

    return "\n".join(lines)


def create_html_email_body(
    alerts: list[dict[str, Any]],
    severity_counts: dict[str, int]
) -> str:
    """
    Create HTML email body.
    """
    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }",
        "h1 { color: #001AFF; border-bottom: 3px solid #001AFF; padding-bottom: 10px; }",
        "h2 { color: #666; margin-top: 30px; }",
        ".summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }",
        ".alert { border-left: 4px solid #ddd; padding: 15px; margin: 15px 0; background: #fafafa; }",
        ".alert.high { border-left-color: #ff4444; background: #fff5f5; }",
        ".alert.medium { border-left-color: #ffaa00; background: #fffaf0; }",
        ".alert.low { border-left-color: #00aaff; background: #f0f8ff; }",
        ".severity { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; text-transform: uppercase; }",
        ".severity.high { background: #ff4444; color: white; }",
        ".severity.medium { background: #ffaa00; color: white; }",
        ".severity.low { background: #00aaff; color: white; }",
        ".metric-type { font-weight: bold; color: #001AFF; }",
        ".timestamp { color: #999; font-size: 14px; }",
        ".footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>AZMX Brand Drift Alert</h1>",
        "",
        "<div class='summary'>",
        f"<strong>Total Alerts:</strong> {len(alerts)}<br>",
        f"<strong>High Severity:</strong> {severity_counts['high']} | ",
        f"<strong>Medium:</strong> {severity_counts['medium']} | ",
        f"<strong>Low:</strong> {severity_counts['low']}",
        "</div>",
    ]

    # Group alerts by metric type
    by_type: dict[str, list[dict[str, Any]]] = {}
    for alert in alerts:
        metric_type = alert.get("metric_type", "unknown")
        if metric_type not in by_type:
            by_type[metric_type] = []
        by_type[metric_type].append(alert)

    # Add each metric type section
    for metric_type, metric_alerts in sorted(by_type.items()):
        html.append(f"<h2>{metric_type.replace('_', ' ').title()}</h2>")

        for alert in metric_alerts:
            severity = alert.get("severity", "low")
            timestamp = alert.get("timestamp", "")
            message = alert.get("message", "")

            html.append(f"<div class='alert {severity}'>")
            html.append(f"<span class='severity {severity}'>{severity}</span>")
            html.append(f"<div class='metric-type'>{message}</div>")
            html.append(f"<div class='timestamp'>{timestamp[:19]}</div>")

            # Add details if available
            details = alert.get("details")
            if details:
                try:
                    details_obj = json.loads(details)
                    html.append("<div style='margin-top: 10px; font-size: 14px;'>")
                    if "drift_score" in details_obj:
                        html.append(f"Drift Score: <strong>{details_obj['drift_score']:.3f}</strong><br>")
                    if "trend" in details_obj:
                        html.append(f"Trend: {details_obj['trend']}<br>")
                    html.append("</div>")
                except (json.JSONDecodeError, TypeError):
                    pass

            html.append("</div>")

    # Footer
    html.extend([
        "<div class='footer'>",
        "<h3>Next Steps</h3>",
        "<ol>",
        "<li>Review the detailed drift report</li>",
        "<li>Identify files with highest drift scores</li>",
        "<li>Apply brand corrections as needed</li>",
        "<li>Monitor trend in next weekly report</li>",
        "</ol>",
        "<p><em>This is an automated alert from the AZMX Brand Drift Detection system.</em></p>",
        "</div>",
        "</body>",
        "</html>",
    ])

    return "\n".join(html)


def send_email(
    msg: MIMEMultipart,
    smtp_config: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False
) -> bool:
    """
    Send email via SMTP.

    Args:
        msg: MIME message to send
        smtp_config: SMTP configuration dictionary
        dry_run: If True, don't actually send (just validate)
        verbose: Print detailed progress

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would send email:")
        print(f"  From: {msg['From']}")
        print(f"  To: {msg['To']}")
        print(f"  Subject: {msg['Subject']}")
        if verbose:
            print(f"  SMTP Host: {smtp_config['host']}:{smtp_config['port']}")
            print(f"  TLS: {smtp_config.get('use_tls', False)}")
        return True

    try:
        # Connect to SMTP server
        if smtp_config.get("use_ssl", False):
            server = smtplib.SMTP_SSL(smtp_config["host"], smtp_config["port"])
        else:
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])

        if verbose:
            server.set_debuglevel(1)

        # Start TLS if required
        if smtp_config.get("use_tls", False) and not smtp_config.get("use_ssl", False):
            server.starttls()

        # Login if credentials provided
        if smtp_config.get("username") and smtp_config.get("password"):
            server.login(smtp_config["username"], smtp_config["password"])

        # Send email
        server.send_message(msg)
        server.quit()

        if verbose:
            print(f"Email sent successfully to {msg['To']}")

        return True

    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        return False


# --------------------------------------------------------------------------
# Alert Detection and Processing
# --------------------------------------------------------------------------

def check_drift_and_alert(
    config: dict[str, Any],
    db_path: str = DB_PATH,
    dry_run: bool = False,
    verbose: bool = False
) -> int:
    """
    Check for drift conditions and create alerts.

    Args:
        config: Configuration dictionary
        db_path: Path to database
        dry_run: If True, don't actually insert alerts
        verbose: Print detailed progress

    Returns:
        Number of new alerts created
    """
    if drift_detector is None:
        print("Warning: drift-detector.py not available, skipping drift analysis", file=sys.stderr)
        return 0

    alert_count = 0
    thresholds = config["alerts"]["alert_thresholds"]

    # Check each metric type
    for metric_type, threshold in thresholds.items():
        if verbose:
            print(f"Checking {metric_type} (threshold: {threshold})...")

        # Analyze drift for this metric
        try:
            # Use drift detector to analyze the metric
            result = drift_detector.analyze_drift(
                metric_type=metric_type,
                window_days=30,
                threshold=threshold,
                db_path=db_path
            )

            if result.get("drift_detected", False):
                severity = result.get("severity", "low")
                drift_score = result.get("drift_score", 0.0)
                trend = result.get("trend", "unknown")

                message = f"{metric_type.replace('_', ' ').title()} drift detected: score {drift_score:.3f}"
                details = json.dumps({
                    "drift_score": drift_score,
                    "trend": trend,
                    "threshold": threshold,
                    "analysis": result,
                })

                if dry_run:
                    print(f"[DRY RUN] Would create alert: [{severity.upper()}] {message}")
                else:
                    alert_id = insert_alert(
                        metric_type=metric_type,
                        severity=severity,
                        message=message,
                        details=details,
                        db_path=db_path
                    )
                    if alert_id > 0:
                        if verbose:
                            print(f"Created alert #{alert_id}: [{severity.upper()}] {message}")
                        alert_count += 1

        except Exception as e:
            if verbose:
                print(f"Error analyzing {metric_type}: {e}", file=sys.stderr)

    return alert_count


def send_pending_alerts(
    config: dict[str, Any],
    db_path: str = DB_PATH,
    dry_run: bool = False,
    verbose: bool = False,
    acknowledge: bool = True
) -> bool:
    """
    Send email for all pending alerts.

    Args:
        config: Configuration dictionary
        db_path: Path to database
        dry_run: If True, don't actually send
        verbose: Print detailed progress
        acknowledge: Mark alerts as acknowledged after sending

    Returns:
        True if successful, False otherwise
    """
    min_severity = config["alerts"]["min_severity"]
    alerts = get_pending_alerts(min_severity=min_severity, db_path=db_path)

    if not alerts:
        if verbose:
            print("No pending alerts to send")
        return True

    if verbose:
        print(f"Found {len(alerts)} pending alert(s)")

    # Create and send email
    msg = create_alert_email(alerts, config)
    success = send_email(msg, config["smtp"], dry_run=dry_run, verbose=verbose)

    # Acknowledge alerts if sent successfully
    if success and acknowledge and not dry_run:
        for alert in alerts:
            acknowledge_alert(alert["id"], db_path=db_path)
        if verbose:
            print(f"Acknowledged {len(alerts)} alert(s)")

    return success


def test_email(
    config: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False
) -> bool:
    """
    Send a test email to verify configuration.

    Args:
        config: Configuration dictionary
        dry_run: If True, don't actually send
        verbose: Print detailed progress

    Returns:
        True if successful, False otherwise
    """
    # Create a test alert
    test_alerts = [
        {
            "id": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metric_type": "color_drift",
            "severity": "medium",
            "message": "Test alert: Color palette drift detected",
            "details": json.dumps({
                "drift_score": 0.18,
                "trend": "increasing",
                "threshold": 0.15,
            }),
        }
    ]

    msg = create_alert_email(test_alerts, config)
    msg["Subject"] = f"{config['alerts']['subject_prefix']} TEST EMAIL"

    return send_email(msg, config["smtp"], dry_run=dry_run, verbose=verbose)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AZMX brand drift alert system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--config",
        default=".brand-monitor.yml",
        help="Path to configuration file (default: .brand-monitor.yml)"
    )
    parser.add_argument(
        "--db",
        default=DB_PATH,
        help=f"Path to database file (default: {DB_PATH})"
    )

    # Alert actions
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--check-drift",
        action="store_true",
        help="Check for drift and create alerts"
    )
    action_group.add_argument(
        "--send-pending-alerts",
        action="store_true",
        help="Send email for all pending alerts"
    )
    action_group.add_argument(
        "--test-email",
        action="store_true",
        help="Send a test email to verify configuration"
    )

    # Options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually send emails or create alerts, just show what would happen"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress information"
    )
    parser.add_argument(
        "--no-acknowledge",
        action="store_true",
        help="Don't mark alerts as acknowledged after sending"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Execute action
    if args.test_email:
        success = test_email(
            config,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        if success:
            print("Test email sent successfully" if not args.dry_run else "Test email validated")
            return 0
        else:
            print("Failed to send test email", file=sys.stderr)
            return 1

    elif args.check_drift:
        alert_count = check_drift_and_alert(
            config,
            db_path=args.db,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        if args.verbose or args.dry_run:
            print(f"Created {alert_count} new alert(s)")
        return 0

    elif args.send_pending_alerts:
        success = send_pending_alerts(
            config,
            db_path=args.db,
            dry_run=args.dry_run,
            verbose=args.verbose,
            acknowledge=not args.no_acknowledge
        )
        return 0 if success else 1

    else:
        # Default: check drift and send alerts if any
        alert_count = check_drift_and_alert(
            config,
            db_path=args.db,
            dry_run=args.dry_run,
            verbose=args.verbose
        )

        if alert_count > 0 or args.verbose:
            success = send_pending_alerts(
                config,
                db_path=args.db,
                dry_run=args.dry_run,
                verbose=args.verbose,
                acknowledge=not args.no_acknowledge
            )
            return 0 if success else 1

        return 0


if __name__ == "__main__":
    sys.exit(main())
