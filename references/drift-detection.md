# Brand Drift Detection

Proactive monitoring system that scans deliverables for brand drift patterns — not just rule violations but emerging trends that signal gradual brand erosion.

## What is Brand Drift?

Brand drift is the gradual, often invisible degradation of brand consistency over time. Unlike violations (a single deliverable breaking the rules), drift is a statistical trend: palette compliance slowly declining, non-brand fonts appearing more frequently, tone shifting away from target ranges.

Each person's prompts pull the brand in a slightly different direction. Drift detection catches these patterns early, before they become systemic.

## The System

Four components working together:

1. **brand-monitor.py** — Scans directories for deliverables, extracts brand metrics, stores results in database
2. **drift-detector.py** — Analyzes time-series metrics for trending violations using statistical algorithms
3. **drift-report.py** — Generates HTML reports with trend visualizations and executive summaries
4. **drift-alert.py** — Sends email/webhook notifications when drift exceeds configured thresholds

The full workflow runs automatically via cron, or manually on demand.

## Quick Start

### 1. Installation

Run the setup script to install and configure the system:

```bash
./scripts/setup-drift-monitor.sh
```

This will:
- Create `.brand-monitor.yml` configuration file (if missing)
- Initialize `.brand-drift.db` SQLite database
- Install cron job to run monitoring every 6 hours
- Display next steps

**Custom schedule:**

```bash
# Daily at 2 AM
./scripts/setup-drift-monitor.sh --schedule "0 2 * * *"

# Every 4 hours
./scripts/setup-drift-monitor.sh --schedule "0 */4 * * *"

# Weekdays at 9 AM
./scripts/setup-drift-monitor.sh --schedule "0 9 * * 1-5"
```

**Preview without installing:**

```bash
./scripts/setup-drift-monitor.sh --dry-run
```

### 2. Configuration

Edit `.brand-monitor.yml` to specify which directories to monitor:

```yaml
watch_paths:
  - "./prod"
  - "./examples"
  - "./docs"

extensions:
  - ".html"
  - ".htm"
  - ".css"
  - ".md"
  - ".svg"
  - ".txt"

database:
  path: ".brand-drift.db"

scan:
  timeout: 30
  skip_unchanged: true
```

**Key settings:**

- `watch_paths`: Directories to scan for deliverables (relative or absolute)
- `extensions`: File types to analyze
- `skip_unchanged`: Skip files with same hash as previous scan (performance optimization)
- `timeout`: Seconds before metrics extraction times out per file

### 3. First Run

Run the full monitoring workflow manually:

```bash
python3 scripts/brand-monitor.py --full-workflow
```

This runs all four steps:
1. Scan files and extract metrics
2. Analyze trends for drift patterns
3. Generate HTML report
4. Send alerts if thresholds exceeded

**View the report:**

```bash
open brand-drift-report.html
```

The report includes:
- Executive summary with status badges
- Trend charts for each metric type
- Weekly/monthly aggregates
- Most problematic files
- Top issues

## Usage

### Monitoring

**Scan specific directory:**

```bash
python3 scripts/brand-monitor.py --scan ./prod
```

**Scan using config file:**

```bash
python3 scripts/brand-monitor.py --config .brand-monitor.yml
```

**Preview scan without storing results:**

```bash
python3 scripts/brand-monitor.py --scan . --dry-run
```

**Validate configuration:**

```bash
python3 scripts/brand-monitor.py --config .brand-monitor.yml --validate-config
```

### Drift Detection

**Analyze specific drift type:**

```bash
python3 scripts/drift-detector.py --analyze color_drift
python3 scripts/drift-detector.py --analyze font_drift
python3 scripts/drift-detector.py --analyze tone_drift
python3 scripts/drift-detector.py --analyze spacing_drift
```

**Analyze all drift types:**

```bash
python3 scripts/drift-detector.py --detect-all
```

**Custom analysis window:**

```bash
# Last 7 days
python3 scripts/drift-detector.py --analyze color_drift --window 7

# Last 90 days
python3 scripts/drift-detector.py --analyze font_drift --window 90
```

**Override detection thresholds:**

```bash
# More sensitive (10% change triggers alert)
python3 scripts/drift-detector.py --analyze color_drift --threshold 0.10

# Less sensitive (25% change triggers alert)
python3 scripts/drift-detector.py --analyze tone_drift --threshold 0.25
```

**JSON output for automation:**

```bash
python3 scripts/drift-detector.py --detect-all --json > drift-results.json
```

### Reporting

**Generate latest report:**

```bash
python3 scripts/drift-report.py --generate
```

**Weekly summary:**

```bash
python3 scripts/drift-report.py --period weekly --output weekly-drift.html
```

**Monthly summary:**

```bash
python3 scripts/drift-report.py --period monthly --output monthly-drift.html
```

**Custom output path:**

```bash
python3 scripts/drift-report.py --generate --output reports/drift-$(date +%Y-%m-%d).html
```

### Alerting

**Test email configuration:**

```bash
python3 scripts/drift-alert.py --test-email --dry-run
```

**Check drift and send alerts:**

```bash
python3 scripts/drift-alert.py --check-drift
```

**Send pending alerts only:**

```bash
python3 scripts/drift-alert.py --send-pending-alerts
```

**Test webhook integration:**

```bash
# Slack
python3 scripts/drift-alert.py --test-webhook https://hooks.slack.com/... --webhook-type slack --dry-run

# Microsoft Teams
python3 scripts/drift-alert.py --test-webhook https://outlook.office.com/webhook/... --webhook-type teams --dry-run

# Custom JSON webhook
python3 scripts/drift-alert.py --test-webhook https://api.example.com/alerts --webhook-type custom --dry-run
```

**Preview alerts without sending:**

```bash
python3 scripts/drift-alert.py --check-drift --dry-run --verbose
```

## Configuration Reference

### Email Alerts

Add SMTP configuration to `.brand-monitor.yml`:

```yaml
smtp:
  host: "smtp.gmail.com"
  port: 587
  use_tls: true
  use_ssl: false
  # Do NOT put the username/password here — .brand-monitor.yml is committed.
  # Export them instead:  AZMX_SMTP_USERNAME  and  AZMX_SMTP_PASSWORD

alerts:
  from_email: "brand-monitor@azmx.sa"
  to_emails:
    - "brand-manager@azmx.sa"
    - "creative-director@azmx.sa"
  subject_prefix: "[AZMX Brand]"
  min_severity: "medium"
  alert_thresholds:
    color_drift: 0.15
    font_drift: 0.10
    tone_drift: 0.10
    spacing_drift: 0.15
```

**Severity levels:**
- `low`: Minor drift, under 15% change
- `medium`: Moderate drift, 15-30% change
- `high`: Significant drift, over 30% change

### Webhook Alerts

Add webhook configuration to `.brand-monitor.yml`:

```yaml
webhooks:
  enabled: true

  # Slack — the URL is a secret: export AZMX_SLACK_WEBHOOK instead of writing it here
  slack:
    enabled: true
    channel: "#brand-alerts"
    username: "Brand Monitor"
    icon_emoji: ":chart_with_downwards_trend:"

  # Microsoft Teams — export AZMX_TEAMS_WEBHOOK
  teams:
    enabled: true

  # Custom JSON webhooks (list of https:// URLs; keep secret URLs out of git)
  custom:
    enabled: false
    webhooks: []
```

Only `https://` webhook URLs are accepted. Secrets read from the environment
(`AZMX_SMTP_USERNAME`, `AZMX_SMTP_PASSWORD`, `AZMX_SLACK_WEBHOOK`,
`AZMX_TEAMS_WEBHOOK`) always override values in the YAML file.

### Watch Paths

Paths can be relative (to config file location) or absolute:

```yaml
watch_paths:
  - "./prod"                    # Relative to config file
  - "./examples"
  - "/absolute/path/to/assets"  # Absolute path
```

**Skip patterns:**

```yaml
skip_directories:
  - ".git"
  - "node_modules"
  - "__pycache__"
  - ".venv"
  - "dist"
  - "build"

skip_path_patterns:
  - "assets/images"    # Skip images directory
  - "assets/fonts"     # Skip fonts directory
  - ".auto-claude"     # Skip automation artifacts
```

## Interpreting Reports

### Status Badges

- **OK** (Green): No drift detected, brand compliance healthy
- **WATCH** (Yellow): Minor drift detected, monitor closely
- **DRIFT DETECTED** (Red): Significant drift, action required

### Drift Metrics

**Color Drift:**
- Tracks average palette distance over time
- Increasing trend = colors drifting away from brand palette
- Target: Palette compliance rate > 85%

**Font Drift:**
- Monitors brand font usage ratio
- Decreasing trend = non-brand fonts appearing more frequently
- Target: Brand font ratio > 90%

**Tone Drift:**
- Analyzes voice compliance scores (empty intensifiers, hedging, em-dashes, etc.)
- Declining scores = copy moving away from brand voice
- Target: Tone compliance score > 0.85

**Spacing Drift:**
- Detects spacing values deviating from 8px scale
- Increasing off-scale count = inconsistent spacing usage
- Target: Spacing compliance rate > 85%

### Trend Analysis

**Direction:**
- `increasing`: Metric trending upward
- `decreasing`: Metric trending downward
- `stable`: No significant trend

**Drift Score:**
- 0.0 to 1.0 scale (higher = more severe)
- < 0.15: Low severity
- 0.15-0.30: Medium severity
- > 0.30: High severity

**False Positive Filtering:**
- Single spikes are filtered out (requires sustained trend)
- Anomaly detection using Z-score and IQR methods
- High variance signals reduce drift score confidence

### Weekly/Monthly Summaries

**Period-over-period comparison:**
- Shows if drift is accelerating or improving
- Trend indicators: ↑ (worse), ↓ (better), → (stable)

**Top Issues:**
- Most frequently triggered alert types
- Focus remediation efforts here

**Most Problematic Files:**
- Files scanned most often (likely high-traffic templates)
- Good candidates for manual review

## Workflow Integration

### Cron-based Automation

The setup script installs a cron job that runs the full workflow periodically:

```bash
# View installed cron job
crontab -l | grep 'Brand Drift'

# Edit cron schedule
crontab -e

# View logs
tail -f brand-monitor.log
```

**Common schedules:**

```bash
0 */6 * * *    # Every 6 hours (default)
0 */4 * * *    # Every 4 hours
0 2 * * *      # Daily at 2:00 AM
0 0 * * 0      # Weekly on Sunday at midnight
0 9 * * 1-5    # Weekdays at 9:00 AM
```

### Manual Execution

Run individual steps as needed:

```bash
# 1. Monitor
python3 scripts/brand-monitor.py --config .brand-monitor.yml

# 2. Detect
python3 scripts/drift-detector.py --detect-all --verbose

# 3. Report
python3 scripts/drift-report.py --generate --output drift-$(date +%Y-%m-%d).html

# 4. Alert
python3 scripts/drift-alert.py --check-drift
```

Or run all steps at once:

```bash
python3 scripts/brand-monitor.py --full-workflow
```

### CI/CD Integration

Add drift detection to your CI pipeline:

```yaml
# .github/workflows/brand-check.yml
name: Brand Drift Check
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Initialize database
        run: python3 scripts/drift-db.py --init-db

      - name: Run drift detection
        run: python3 scripts/brand-monitor.py --full-workflow

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: drift-report
          path: brand-drift-report.html
```

## Troubleshooting

### Common Issues

**"No data available for analysis"**
- Database is empty or doesn't have enough data points
- Run at least 3 scans before drift detection works
- Solution: `python3 scripts/brand-monitor.py --scan ./prod` (run multiple times)

**"SMTP authentication failed"**
- Incorrect SMTP credentials
- Gmail requires app-specific password (not account password)
- Solution: Check smtp settings in `.brand-monitor.yml`

**"Configuration file validation failed"**
- YAML syntax error in `.brand-monitor.yml`
- Solution: `python3 scripts/brand-monitor.py --config .brand-monitor.yml --validate-config`

**"Metrics extraction timeout"**
- Large files taking too long to process
- Solution: Increase `scan.timeout` in config file

**Cron job not running**
- Check cron service is running: `sudo service cron status`
- Check job is installed: `crontab -l`
- Check logs for errors: `tail -f brand-monitor.log`

### Database Maintenance

**View database statistics:**

```bash
python3 scripts/drift-db.py --stats
```

**Reset database (deletes all data):**

```bash
python3 scripts/drift-db.py --reset-db
```

**Backup database:**

```bash
cp .brand-drift.db .brand-drift.db.backup-$(date +%Y%m%d)
```

**Check database integrity:**

```bash
sqlite3 .brand-drift.db "PRAGMA integrity_check;"
```

### Performance Optimization

**Skip unchanged files:**

```yaml
scan:
  skip_unchanged: true  # Only scan modified files
```

**Limit watch paths:**

```yaml
watch_paths:
  - "./prod"  # Only production files, skip examples/tests
```

**Exclude large directories:**

```yaml
skip_directories:
  - "node_modules"
  - "dist"
  - "build"
  - ".next"
```

**Reduce scan frequency:**

```bash
# Change from every 6 hours to daily
./scripts/setup-drift-monitor.sh --schedule "0 2 * * *"
```

### False Positives

If drift alerts trigger incorrectly:

1. **Increase detection threshold:**

   ```yaml
   alerts:
     alert_thresholds:
       color_drift: 0.20  # Default: 0.15
       font_drift: 0.15   # Default: 0.10
   ```

2. **Increase minimum severity:**

   ```yaml
   alerts:
     min_severity: "high"  # Only alert on severe drift
   ```

3. **Extend analysis window:**

   ```bash
   python3 scripts/drift-detector.py --analyze color_drift --window 60
   ```

4. **Review filtered anomalies:**

   ```bash
   python3 scripts/drift-detector.py --detect-all --verbose
   ```

   Look for `isolated_spikes: true` — these are filtered out automatically.

## Dependencies

Required Python packages (see `requirements.txt`):

- **Pillow** — Image processing (already used by rebuild-index.py)
- **PyYAML** — YAML configuration parsing
- **matplotlib** — Chart generation in reports

Install all dependencies:

```bash
pip3 install -r requirements.txt
```

Or install individually:

```bash
pip3 install Pillow PyYAML matplotlib
```

## Uninstalling

Remove the cron job:

```bash
./scripts/setup-drift-monitor.sh --uninstall
```

Completely remove the system:

```bash
# Remove cron job
./scripts/setup-drift-monitor.sh --uninstall

# Remove database and config
rm .brand-drift.db .brand-monitor.yml

# Remove logs
rm brand-monitor.log
```

## Advanced Usage

### Custom Metrics

The system is designed to be extended. To add custom metrics:

1. Extend `extract-metrics.py` with new metric extraction logic
2. Store metrics using namespaced types: `custom.my_metric_name`
3. Add drift analysis function to `drift-detector.py`
4. Update report template to display new metrics

### Integration with Other Tools

**Export metrics to JSON:**

```bash
python3 scripts/drift-detector.py --detect-all --json > metrics.json
```

**Query database directly:**

```bash
sqlite3 .brand-drift.db "SELECT * FROM metrics WHERE metric_type = 'color.palette_compliance_rate' ORDER BY timestamp DESC LIMIT 10;"
```

**Programmatic access:**

```python
from scripts.drift_db import get_metrics_by_type, get_trend

# Get recent color metrics
metrics = get_metrics_by_type("color.palette_compliance_rate", limit=50)

# Analyze trend
trend = get_trend("color.palette_compliance_rate", days=30)
print(f"Trend direction: {trend['direction']}")
print(f"Change: {trend['change_pct']:.1f}%")
```

## Best Practices

1. **Run initial scans for calibration**: Get at least 10 scans before relying on drift detection
2. **Review reports weekly**: Check weekly summaries to catch trends early
3. **Tune thresholds gradually**: Start conservative, tighten as you understand normal variation
4. **Document known issues**: Some legacy files may always trigger alerts — document them
5. **Combine with reactive checking**: Drift detection complements (doesn't replace) brand-check.py
6. **Monitor the monitor**: Check `brand-monitor.log` periodically for scan failures
7. **Archive reports**: Keep monthly reports for trend comparison over time
8. **Act on alerts promptly**: Drift is easier to correct early than after it spreads

## See Also

- **brand-check.py** — Reactive brand linting for individual files
- **references/colors.md** — Brand color palette definitions
- **references/voice-and-tone.md** — Brand voice guidelines
- **references/design-system.md** — Complete brand system reference

---

**Questions or issues?** Review the troubleshooting section above, or run tools with `--verbose` flag for detailed diagnostic output.
