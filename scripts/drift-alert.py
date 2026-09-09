#!/usr/bin/env python3
"""
drift-alert.py — AZMX brand drift alert system.

Sends email and webhook notifications to brand managers when drift thresholds
are exceeded, sustained trends are detected, or anomalies are found.

Alert Triggers:
  - Drift threshold exceeded (configurable per metric type)
  - Sustained trend detected (3+ consecutive drift points)
  - Statistical anomaly detected (outlier in normal pattern)

Notification Channels:
  - Email (SMTP)
  - Slack webhooks
  - Microsoft Teams webhooks
  - Custom webhooks (generic JSON payload)

Email Content:
  - Executive summary of drift findings
  - Severity level (high/medium/low)
  - Trend indicators and statistics
  - Link to detailed HTML report

Usage:
    python3 scripts/drift-alert.py --check-drift
    python3 scripts/drift-alert.py --test-email --dry-run
    python3 scripts/drift-alert.py --test-webhook https://hooks.slack.com/... --webhook-type slack
    python3 scripts/drift-alert.py --test-webhook https://example.com/webhook --dry-run
    python3 scripts/drift-alert.py --send-pending-alerts
    python3 scripts/drift-alert.py --config .brand-monitor.yml
"""

from __future__ import annotations

import argparse
import html as html_mod
import importlib.util
import json
import os
import smtplib
import ssl
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional
from urllib import request
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError

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

# Default webhook configuration
DEFAULT_WEBHOOK_CONFIG = {
    "enabled": False,
    "webhooks": [],  # List of webhook URLs or configurations
    "slack": {
        "enabled": False,
        "webhook_url": None,
        "channel": None,
        "username": "AZMX Brand Drift",
        "icon_emoji": ":warning:",
    },
    "teams": {
        "enabled": False,
        "webhook_url": None,
    },
    "custom": {
        "enabled": False,
        "webhooks": [],  # List of custom webhook URLs
    },
}

# Secrets belong in the environment, not in .brand-monitor.yml (which is committed).
# Each variable, when set, overrides the corresponding config value.
ENV_SECRETS = {
    "AZMX_SMTP_PASSWORD": ("smtp", "password"),
    "AZMX_SMTP_USERNAME": ("smtp", "username"),
    "AZMX_SLACK_WEBHOOK": ("webhooks", "slack", "webhook_url"),
    "AZMX_TEAMS_WEBHOOK": ("webhooks", "teams", "webhook_url"),
}


def apply_env_secrets(smtp_config: dict[str, Any], webhook_config: dict[str, Any]) -> None:
    """Overlay AZMX_* environment variables onto the loaded config (in place)."""
    roots = {"smtp": smtp_config, "webhooks": webhook_config}
    for env_name, path in ENV_SECRETS.items():
        value = os.environ.get(env_name)
        if not value:
            continue
        node = roots[path[0]]
        for key in path[1:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = dict(DEFAULT_WEBHOOK_CONFIG.get(key, {}))
                node[key] = child
            node = child
        node[path[-1]] = value


# Color codes for terminal output
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
SEV_COLOR = {"high": "\033[31m", "medium": "\033[33m", "low": "\033[36m"}


# --------------------------------------------------------------------------
# Configuration Loading
# --------------------------------------------------------------------------

def load_config(config_path: str) -> dict[str, Any]:
    """
    Load configuration from YAML file.
    Returns combined SMTP, alert, and webhook configuration.
    """
    if not config_path or not os.path.exists(config_path):
        smtp_config = dict(DEFAULT_SMTP_CONFIG)
        webhook_config = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_WEBHOOK_CONFIG.items()}
        apply_env_secrets(smtp_config, webhook_config)
        return {
            "smtp": smtp_config,
            "alerts": dict(DEFAULT_ALERT_CONFIG),
            "webhooks": webhook_config,
        }

    try:
        import yaml
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    except ImportError:
        # Fallback to simple parser if PyYAML not installed
        config = parse_yaml_simple(config_path)

    # Extract and merge configurations
    smtp_config = {**DEFAULT_SMTP_CONFIG, **(config.get("smtp") or {})}
    alert_config = {**DEFAULT_ALERT_CONFIG, **(config.get("alerts") or {})}
    webhook_config = {**DEFAULT_WEBHOOK_CONFIG, **(config.get("webhooks") or {})}
    apply_env_secrets(smtp_config, webhook_config)

    return {
        "smtp": smtp_config,
        "alerts": alert_config,
        "webhooks": webhook_config,
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
        severity_counts[alert.get("severity") if alert.get("severity") in severity_counts else "low"] += 1

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
            if severity not in ("low", "medium", "high"):
                severity = "low"
            timestamp = html_mod.escape(str(alert.get("timestamp", "")))
            message = html_mod.escape(str(alert.get("message", "")))

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
                        html.append(f"Trend: {html_mod.escape(str(details_obj['trend']))}<br>")
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
        # Connect to SMTP server. Always verify certificates: the default
        # smtplib context does not, which would let an on-path attacker
        # harvest the SMTP password.
        tls_context = ssl.create_default_context()
        use_ssl = smtp_config.get("use_ssl", False)
        use_tls = smtp_config.get("use_tls", False) and not use_ssl
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_config["host"], smtp_config["port"], context=tls_context)
        else:
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])

        try:
            if use_tls:
                server.starttls(context=tls_context)

            # Login if credentials provided — never over a plaintext channel
            if smtp_config.get("username") and smtp_config.get("password"):
                if not (use_ssl or use_tls):
                    raise RuntimeError(
                        "SMTP credentials configured but neither use_ssl nor use_tls is set; "
                        "refusing to send the password in plaintext"
                    )
                server.login(smtp_config["username"], smtp_config["password"])

            # Send email
            server.send_message(msg)
        finally:
            try:
                server.quit()
            except Exception:
                pass

        if verbose:
            print(f"Email sent successfully to {msg['To']}")

        return True

    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        return False


# --------------------------------------------------------------------------
# Webhook Functions
# --------------------------------------------------------------------------

def format_slack_payload(
    alerts: list[dict[str, Any]],
    config: dict[str, Any]
) -> dict[str, Any]:
    """
    Format alerts as Slack message payload.

    Args:
        alerts: List of alert dictionaries
        config: Webhook configuration

    Returns:
        Slack webhook payload
    """
    slack_config = config.get("slack", {})

    # Count severity
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for alert in alerts:
        severity_counts[alert.get("severity") if alert.get("severity") in severity_counts else "low"] += 1

    # Determine overall severity and emoji
    if severity_counts["high"] > 0:
        severity_emoji = ":rotating_light:"
        severity_color = "#ff4444"
    elif severity_counts["medium"] > 0:
        severity_emoji = ":warning:"
        severity_color = "#ffaa00"
    else:
        severity_emoji = ":information_source:"
        severity_color = "#00aaff"

    # Build message blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji} AZMX Brand Drift Alert",
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Total Alerts:*\n{len(alerts)}"},
                {"type": "mrkdwn", "text": f"*High Severity:*\n{severity_counts['high']}"},
                {"type": "mrkdwn", "text": f"*Medium Severity:*\n{severity_counts['medium']}"},
                {"type": "mrkdwn", "text": f"*Low Severity:*\n{severity_counts['low']}"},
            ]
        },
        {"type": "divider"}
    ]

    # Add alert details
    for alert in alerts[:5]:  # Limit to first 5 for Slack message size
        severity = alert.get("severity", "low")
        metric_type = alert.get("metric_type", "unknown")
        message = alert.get("message", "")
        timestamp = alert.get("timestamp", "")

        severity_icon = {"high": ":red_circle:", "medium": ":large_orange_circle:", "low": ":large_blue_circle:"}.get(severity, ":white_circle:")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{severity_icon} *{metric_type.replace('_', ' ').title()}*\n{message}\n_{timestamp[:19]}_"
            }
        })

    if len(alerts) > 5:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_...and {len(alerts) - 5} more alert(s)_"
                }
            ]
        })

    payload = {
        "blocks": blocks,
        "attachments": [
            {
                "color": severity_color,
                "text": "Review the detailed drift report and apply brand corrections as needed.",
            }
        ]
    }

    # Add optional fields from config
    if slack_config.get("channel"):
        payload["channel"] = slack_config["channel"]
    if slack_config.get("username"):
        payload["username"] = slack_config["username"]
    if slack_config.get("icon_emoji"):
        payload["icon_emoji"] = slack_config["icon_emoji"]

    return payload


def format_teams_payload(
    alerts: list[dict[str, Any]],
    config: dict[str, Any]
) -> dict[str, Any]:
    """
    Format alerts as Microsoft Teams message payload.

    Args:
        alerts: List of alert dictionaries
        config: Webhook configuration

    Returns:
        Teams webhook payload (Adaptive Card)
    """
    # Count severity
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for alert in alerts:
        severity_counts[alert.get("severity") if alert.get("severity") in severity_counts else "low"] += 1

    # Determine theme color
    if severity_counts["high"] > 0:
        theme_color = "FF4444"
    elif severity_counts["medium"] > 0:
        theme_color = "FFAA00"
    else:
        theme_color = "00AAFF"

    # Build facts list
    facts = []
    for alert in alerts[:10]:  # Limit to first 10
        severity = alert.get("severity", "low")
        metric_type = alert.get("metric_type", "unknown")
        message = alert.get("message", "")

        facts.append({
            "name": f"[{severity.upper()}] {metric_type.replace('_', ' ').title()}",
            "value": message
        })

    sections = [
        {
            "activityTitle": "AZMX Brand Drift Alert",
            "activitySubtitle": f"{len(alerts)} alert(s) detected",
            "facts": [
                {"name": "Total Alerts", "value": str(len(alerts))},
                {"name": "High Severity", "value": str(severity_counts["high"])},
                {"name": "Medium Severity", "value": str(severity_counts["medium"])},
                {"name": "Low Severity", "value": str(severity_counts["low"])},
            ]
        }
    ]

    if facts:
        sections.append({
            "title": "Alert Details",
            "facts": facts
        })

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": theme_color,
        "summary": f"AZMX Brand Drift: {len(alerts)} alert(s)",
        "sections": sections
    }

    return payload


def format_custom_payload(
    alerts: list[dict[str, Any]],
    config: dict[str, Any]
) -> dict[str, Any]:
    """
    Format alerts as generic JSON payload for custom webhooks.

    Args:
        alerts: List of alert dictionaries
        config: Webhook configuration

    Returns:
        Generic JSON payload
    """
    # Count severity
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for alert in alerts:
        severity_counts[alert.get("severity") if alert.get("severity") in severity_counts else "low"] += 1

    return {
        "source": "azmx-brand-drift",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_alerts": len(alerts),
            "severity_counts": severity_counts,
        },
        "alerts": [
            {
                "id": alert.get("id"),
                "timestamp": alert.get("timestamp"),
                "metric_type": alert.get("metric_type"),
                "severity": alert.get("severity"),
                "message": alert.get("message"),
                "details": json.loads(alert.get("details", "{}")) if alert.get("details") else {},
            }
            for alert in alerts
        ]
    }



def redact_url(url: str) -> str:
    """Return scheme://host/… for logging — webhook paths are bearer-equivalent secrets."""
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}/…"
    except Exception:
        return "<url>"

def send_webhook(
    url: str,
    payload: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False
) -> bool:
    """
    Send webhook POST request.

    Args:
        url: Webhook URL
        payload: JSON payload to send
        dry_run: If True, don't actually send
        verbose: Print detailed progress

    Returns:
        True if successful, False otherwise
    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        print(f"Refusing to send webhook: URL must be https:// (got {parsed.scheme or 'no scheme'})", file=sys.stderr)
        return False

    if dry_run:
        print(f"[DRY RUN] Would send webhook to: {redact_url(url)}")
        if verbose:
            print(f"  Payload: {json.dumps(payload, indent=2)}")
        return True

    try:
        data = json.dumps(payload).encode('utf-8')
        req = request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AZMX-Brand-Drift-Alert/1.0',
            },
            method='POST'
        )

        with request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            if verbose:
                print(f"Webhook sent successfully: HTTP {status_code}")
            return status_code >= 200 and status_code < 300

    except HTTPError as e:
        print(f"HTTP Error sending webhook: {e.code} {e.reason}", file=sys.stderr)
        if verbose:
            print(f"  Response: {e.read().decode('utf-8', errors='ignore')}", file=sys.stderr)
        return False

    except URLError as e:
        print(f"URL Error sending webhook: {e.reason}", file=sys.stderr)
        return False

    except Exception as e:
        print(f"Error sending webhook: {e}", file=sys.stderr)
        return False


def send_webhooks(
    alerts: list[dict[str, Any]],
    config: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False
) -> bool:
    """
    Send alerts to all configured webhooks.

    Args:
        alerts: List of alert dictionaries
        config: Configuration dictionary
        dry_run: If True, don't actually send
        verbose: Print detailed progress

    Returns:
        True if all webhooks sent successfully, False otherwise
    """
    webhook_config = config.get("webhooks", {})

    if not webhook_config.get("enabled", False):
        if verbose:
            print("Webhooks are disabled in configuration")
        return True

    success = True

    # Send to Slack
    if webhook_config.get("slack", {}).get("enabled", False):
        slack_url = webhook_config["slack"].get("webhook_url")
        if slack_url:
            if verbose:
                print("Sending Slack webhook...")
            payload = format_slack_payload(alerts, webhook_config)
            if not send_webhook(slack_url, payload, dry_run=dry_run, verbose=verbose):
                success = False
        elif verbose:
            print("Slack enabled but webhook_url not configured")

    # Send to Teams
    if webhook_config.get("teams", {}).get("enabled", False):
        teams_url = webhook_config["teams"].get("webhook_url")
        if teams_url:
            if verbose:
                print("Sending Teams webhook...")
            payload = format_teams_payload(alerts, webhook_config)
            if not send_webhook(teams_url, payload, dry_run=dry_run, verbose=verbose):
                success = False
        elif verbose:
            print("Teams enabled but webhook_url not configured")

    # Send to custom webhooks
    if webhook_config.get("custom", {}).get("enabled", False):
        custom_webhooks = webhook_config["custom"].get("webhooks", [])
        for webhook_url in custom_webhooks:
            if verbose:
                print(f"Sending custom webhook to {redact_url(webhook_url)}...")
            payload = format_custom_payload(alerts, webhook_config)
            if not send_webhook(webhook_url, payload, dry_run=dry_run, verbose=verbose):
                success = False

    # Legacy: Send to top-level webhooks list
    for webhook_url in webhook_config.get("webhooks", []):
        if isinstance(webhook_url, str) and webhook_url:
            if verbose:
                print(f"Sending webhook to {redact_url(webhook_url)}...")
            payload = format_custom_payload(alerts, webhook_config)
            if not send_webhook(webhook_url, payload, dry_run=dry_run, verbose=verbose):
                success = False

    return success


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
            # Never hide this: a silent failure here means drift is never reported.
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
    Send email and webhooks for all pending alerts.

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
    email_success = send_email(msg, config["smtp"], dry_run=dry_run, verbose=verbose)

    # Send webhooks
    webhook_success = send_webhooks(alerts, config, dry_run=dry_run, verbose=verbose)

    success = email_success and webhook_success

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


def test_webhook(
    webhook_url: str,
    webhook_type: str = "custom",
    dry_run: bool = False,
    verbose: bool = False
) -> bool:
    """
    Send a test webhook to verify configuration.

    Args:
        webhook_url: Webhook URL to test
        webhook_type: Type of webhook (slack/teams/custom)
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

    # Format payload based on webhook type
    webhook_config = {
        "slack": DEFAULT_WEBHOOK_CONFIG["slack"],
        "teams": DEFAULT_WEBHOOK_CONFIG["teams"],
        "custom": DEFAULT_WEBHOOK_CONFIG["custom"],
    }

    if webhook_type == "slack":
        payload = format_slack_payload(test_alerts, webhook_config)
    elif webhook_type == "teams":
        payload = format_teams_payload(test_alerts, webhook_config)
    else:
        payload = format_custom_payload(test_alerts, webhook_config)

    if verbose:
        print(f"Testing {webhook_type} webhook: {webhook_url}")

    return send_webhook(webhook_url, payload, dry_run=dry_run, verbose=verbose)


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
    action_group.add_argument(
        "--test-webhook",
        metavar="URL",
        help="Send a test webhook to the specified URL"
    )

    # Options
    parser.add_argument(
        "--webhook-type",
        choices=["slack", "teams", "custom"],
        default="custom",
        help="Type of webhook for --test-webhook (default: custom)"
    )
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

    elif args.test_webhook:
        success = test_webhook(
            args.test_webhook,
            webhook_type=args.webhook_type,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        if success:
            print("Test webhook sent successfully" if not args.dry_run else "Test webhook validated")
            return 0
        else:
            print("Failed to send test webhook", file=sys.stderr)
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

        if alert_count > 0:
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
