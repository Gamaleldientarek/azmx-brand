#!/usr/bin/env python3
"""
drift-db.py — AZMX brand drift database management.

Provides SQLite database schema and connection management for storing
time-series brand metrics and drift detection results.

Schema:
  - scans: Individual file scan records with timestamps
  - metrics: Quantitative measurements from each scan
  - alerts: Generated alerts when drift thresholds are exceeded

Usage:
    python3 scripts/drift-db.py --init-db       Initialize database schema
    python3 scripts/drift-db.py --reset-db      Drop all tables and reinitialize
    python3 scripts/drift-db.py --stats         Show database statistics
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Optional


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DB_PATH = ".brand-drift.db"

SCHEMA_VERSION = 1

# --------------------------------------------------------------------------
# Database Schema
# --------------------------------------------------------------------------

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_info (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- File scans: records of individual file analysis
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    scan_duration_ms INTEGER,
    UNIQUE(file_path, file_hash)
);

-- Metrics: quantitative brand measurements from scans
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    metric_type TEXT NOT NULL,
    value REAL NOT NULL,
    metadata TEXT,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

-- Alerts: drift detection alerts when thresholds exceeded
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    acknowledged INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp);
CREATE INDEX IF NOT EXISTS idx_scans_file_path ON scans(file_path);
CREATE INDEX IF NOT EXISTS idx_metrics_scan_id ON metrics(scan_id);
CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
"""


# --------------------------------------------------------------------------
# Database Connection
# --------------------------------------------------------------------------

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Get a connection to the drift database.
    Enables foreign key constraints and row factory for dict-like access.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: str = DB_PATH, force: bool = False) -> bool:
    """
    Initialize the database schema.

    Args:
        db_path: Path to SQLite database file
        force: If True, drop existing tables first

    Returns:
        True if initialization succeeded
    """
    if force and os.path.exists(db_path):
        print(f"Dropping existing database: {db_path}")
        os.remove(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Execute schema
        cursor.executescript(SCHEMA_SQL)

        # Record schema version
        cursor.execute(
            "INSERT OR REPLACE INTO schema_info (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat())
        )

        conn.commit()
        print(f"Database initialized: {db_path}")
        print(f"Schema version: {SCHEMA_VERSION}")
        return True

    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        return False

    finally:
        conn.close()


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file's contents."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (IOError, OSError) as e:
        print(f"Warning: Cannot hash {file_path}: {e}", file=sys.stderr)
        return ""


# --------------------------------------------------------------------------
# Query Functions
# --------------------------------------------------------------------------

def get_metrics_by_type(
    metric_type: str,
    db_path: str = DB_PATH,
    limit: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    Retrieve metrics of a specific type with optional filtering.

    Args:
        metric_type: Type of metric to retrieve (e.g., 'color_violations')
        db_path: Path to SQLite database file
        limit: Maximum number of records to return
        start_date: ISO format timestamp to filter from (inclusive)
        end_date: ISO format timestamp to filter to (inclusive)

    Returns:
        List of metric records with scan metadata, ordered by timestamp descending
    """
    if not os.path.exists(db_path):
        return []

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Build query with optional filters
        query = """
            SELECT
                m.id,
                m.metric_type,
                m.value,
                m.metadata,
                s.timestamp,
                s.file_path,
                s.file_hash
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = ?
        """
        params: list[Any] = [metric_type]

        if start_date:
            query += " AND s.timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND s.timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY s.timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as e:
        print(f"Error querying metrics: {e}", file=sys.stderr)
        return []

    finally:
        conn.close()


def get_trend(
    metric_type: str,
    db_path: str = DB_PATH,
    days: int = 30
) -> dict[str, Any]:
    """
    Analyze trend over time for a specific metric type.

    Args:
        metric_type: Type of metric to analyze
        db_path: Path to SQLite database file
        days: Number of days to analyze (from most recent)

    Returns:
        Dictionary with trend analysis:
        - data_points: List of (timestamp, value) tuples
        - avg: Average value over the period
        - min: Minimum value
        - max: Maximum value
        - latest: Most recent value
        - trend: 'increasing', 'decreasing', or 'stable'
        - change_pct: Percentage change from first to latest
    """
    if not os.path.exists(db_path):
        return {
            "data_points": [],
            "avg": 0,
            "min": 0,
            "max": 0,
            "latest": 0,
            "trend": "stable",
            "change_pct": 0
        }

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Calculate the cutoff timestamp (days ago from now)
        cutoff = datetime.now(timezone.utc)
        from datetime import timedelta
        cutoff = (cutoff - timedelta(days=days)).isoformat()

        # Get time-series data
        cursor.execute(
            """
            SELECT s.timestamp, m.value
            FROM metrics m
            JOIN scans s ON m.scan_id = s.id
            WHERE m.metric_type = ? AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
            """,
            (metric_type, cutoff)
        )
        rows = cursor.fetchall()

        if not rows:
            return {
                "data_points": [],
                "avg": 0,
                "min": 0,
                "max": 0,
                "latest": 0,
                "trend": "stable",
                "change_pct": 0
            }

        # Extract data points
        data_points = [(row["timestamp"], row["value"]) for row in rows]
        values = [v for _, v in data_points]

        # Calculate statistics
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        latest = values[-1]
        first = values[0]

        # Determine trend
        if len(values) < 2:
            trend = "stable"
            change_pct = 0.0
        else:
            change = latest - first
            change_pct = (change / first * 100) if first != 0 else 0.0

            # Consider < 5% change as stable
            if abs(change_pct) < 5:
                trend = "stable"
            elif change > 0:
                trend = "increasing"
            else:
                trend = "decreasing"

        return {
            "data_points": data_points,
            "avg": avg,
            "min": min_val,
            "max": max_val,
            "latest": latest,
            "trend": trend,
            "change_pct": change_pct
        }

    except sqlite3.Error as e:
        print(f"Error analyzing trend: {e}", file=sys.stderr)
        return {
            "data_points": [],
            "avg": 0,
            "min": 0,
            "max": 0,
            "latest": 0,
            "trend": "stable",
            "change_pct": 0
        }

    finally:
        conn.close()


def show_stats(db_path: str = DB_PATH) -> None:
    """Display database statistics."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Schema version
        cursor.execute("SELECT version, applied_at FROM schema_info ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"Schema version: {row['version']}")
            print(f"Applied at: {row['applied_at']}")

        # Table counts
        cursor.execute("SELECT COUNT(*) as count FROM scans")
        scans_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM metrics")
        metrics_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM alerts")
        alerts_count = cursor.fetchone()['count']

        print(f"\nTable counts:")
        print(f"  Scans: {scans_count}")
        print(f"  Metrics: {metrics_count}")
        print(f"  Alerts: {alerts_count}")

        # Recent activity
        cursor.execute(
            "SELECT timestamp, file_path FROM scans ORDER BY timestamp DESC LIMIT 1"
        )
        latest_scan = cursor.fetchone()
        if latest_scan:
            print(f"\nLatest scan:")
            print(f"  Time: {latest_scan['timestamp']}")
            print(f"  File: {latest_scan['file_path']}")

        # Alert summary
        cursor.execute(
            "SELECT severity, COUNT(*) as count FROM alerts GROUP BY severity"
        )
        alert_summary = cursor.fetchall()
        if alert_summary:
            print(f"\nAlerts by severity:")
            for row in alert_summary:
                print(f"  {row['severity']}: {row['count']}")

    finally:
        conn.close()


# --------------------------------------------------------------------------
# Main CLI
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AZMX brand drift database management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database schema"
    )

    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Drop all tables and reinitialize (DESTRUCTIVE)"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics"
    )

    parser.add_argument(
        "--db",
        default=DB_PATH,
        help=f"Database path (default: {DB_PATH})"
    )

    args = parser.parse_args()

    # Require at least one action
    if not any([args.init_db, args.reset_db, args.stats]):
        parser.print_help()
        return 0

    # Execute actions
    if args.reset_db:
        if not init_database(args.db, force=True):
            return 1
    elif args.init_db:
        if not init_database(args.db, force=False):
            return 1

    if args.stats:
        show_stats(args.db)

    return 0


if __name__ == "__main__":
    sys.exit(main())
