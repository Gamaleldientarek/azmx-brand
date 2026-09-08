#!/usr/bin/env bash
#
# setup-drift-monitor.sh — AZMX Brand Drift Monitor Setup
#
# Installs and configures the brand drift monitoring system:
#   1. Creates/validates configuration file (.brand-monitor.yml)
#   2. Initializes the SQLite database (.brand-drift.db)
#   3. Installs cron job for automated monitoring
#   4. Optionally sends a test alert
#
# Usage:
#   ./scripts/setup-drift-monitor.sh [--schedule CRON_EXPR] [--dry-run] [--uninstall]
#
# Options:
#   --schedule CRON_EXPR    Custom cron schedule (default: "0 */6 * * *" = every 6 hours)
#   --dry-run               Preview changes without executing
#   --uninstall             Remove cron job
#   --help                  Show this help message
#
# Examples:
#   # Install with default schedule (every 6 hours)
#   ./scripts/setup-drift-monitor.sh
#
#   # Install with custom schedule (daily at 2 AM)
#   ./scripts/setup-drift-monitor.sh --schedule "0 2 * * *"
#
#   # Preview what would be installed
#   ./scripts/setup-drift-monitor.sh --dry-run
#
#   # Remove the cron job
#   ./scripts/setup-drift-monitor.sh --uninstall

set -euo pipefail

# Color codes for terminal output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Defaults
CRON_SCHEDULE="0 */6 * * *"  # Every 6 hours
DRY_RUN=false
UNINSTALL=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/.brand-monitor.yml"
DATABASE_FILE="$PROJECT_ROOT/.brand-drift.db"
MONITOR_SCRIPT="$SCRIPT_DIR/brand-monitor.py"
CRON_MARKER="# AZMX Brand Drift Monitor"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --schedule)
            CRON_SCHEDULE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --help|-h)
            grep '^#' "$0" | grep -v '#!/usr/bin/env' | sed 's/^# *//' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            echo "Run with --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${CYAN}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC}  $1" >&2
}

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  AZMX Brand Drift Monitor Setup${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is required but not installed"
        exit 1
    fi
    log_success "python3 found: $(python3 --version)"

    # Check required scripts exist
    local required_scripts=("brand-monitor.py" "drift-detector.py" "drift-report.py" "drift-alert.py" "extract-metrics.py" "drift-db.py")
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
            log_error "Required script not found: scripts/$script"
            exit 1
        fi
    done
    log_success "All required scripts found"

    # Check if cron is available
    if ! command -v crontab &> /dev/null; then
        log_warning "crontab not found - cron scheduling will not be available"
        log_warning "You'll need to run brand-monitor.py manually or use another scheduler"
        return 1
    fi
    log_success "crontab found"

    return 0
}

create_config() {
    log_info "Checking configuration file..."

    if [[ -f "$CONFIG_FILE" ]]; then
        log_success "Configuration file exists: .brand-monitor.yml"

        # Validate config
        if $DRY_RUN; then
            log_info "Would validate configuration file"
        else
            if python3 "$MONITOR_SCRIPT" --config "$CONFIG_FILE" --validate-config > /dev/null 2>&1; then
                log_success "Configuration file is valid"
            else
                log_error "Configuration file validation failed"
                echo ""
                echo "  Run this command to check your configuration:"
                echo "    python3 scripts/brand-monitor.py --config .brand-monitor.yml --validate-config"
                exit 1
            fi
        fi
    else
        log_warning "Configuration file not found"
        if $DRY_RUN; then
            log_info "Would create default configuration: .brand-monitor.yml"
        else
            log_info "Creating default configuration file..."
            cat > "$CONFIG_FILE" << 'EOF'
# AZMX Brand Monitor Configuration
# Configuration for brand-monitor.py watch paths and scan settings

# Directories to scan for brand deliverables
watch_paths:
  - "./prod"
  - "./examples"
  - "./docs"

# File extensions to scan (lowercase, with leading dot)
extensions:
  - ".html"
  - ".htm"
  - ".css"
  - ".md"
  - ".svg"
  - ".txt"

# Directories to skip during scanning
skip_directories:
  - ".git"
  - "node_modules"
  - "__pycache__"
  - ".venv"
  - "venv"
  - "dist"
  - "build"
  - ".next"
  - ".cache"
  - ".auto-claude"

# Path patterns to skip
skip_path_patterns:
  - "assets/images"
  - "assets/fonts"
  - ".auto-claude"

# Database settings
database:
  path: ".brand-drift.db"

# Scan settings
scan:
  timeout: 30
  skip_unchanged: true
EOF
            log_success "Created configuration file: .brand-monitor.yml"
            log_warning "Please review and customize watch_paths in .brand-monitor.yml"
        fi
    fi
}

init_database() {
    log_info "Checking database..."

    if [[ -f "$DATABASE_FILE" ]]; then
        log_success "Database exists: .brand-drift.db"

        # Check if database has proper schema
        if $DRY_RUN; then
            log_info "Would validate database schema"
        else
            local table_count
            table_count=$(python3 -c "import sqlite3; conn = sqlite3.connect('$DATABASE_FILE'); print(len(conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()))" 2>/dev/null || echo "0")
            if [[ $table_count -ge 3 ]]; then
                log_success "Database schema is valid ($table_count tables)"
            else
                log_warning "Database exists but schema appears incomplete"
                log_info "Reinitializing database..."
                python3 "$SCRIPT_DIR/drift-db.py" --init-db
                log_success "Database reinitialized"
            fi
        fi
    else
        if $DRY_RUN; then
            log_info "Would initialize database: .brand-drift.db"
        else
            log_info "Initializing database..."
            python3 "$SCRIPT_DIR/drift-db.py" --init-db
            log_success "Database initialized: .brand-drift.db"
        fi
    fi
}

install_cron() {
    if ! command -v crontab &> /dev/null; then
        log_warning "Cron not available - skipping cron installation"
        echo ""
        echo "  To run monitoring manually:"
        echo "    cd $PROJECT_ROOT"
        echo "    python3 scripts/brand-monitor.py --full-workflow"
        return
    fi

    log_info "Installing cron job..."

    # Build cron command
    local cron_command="cd $PROJECT_ROOT && python3 $MONITOR_SCRIPT --full-workflow --report-output brand-drift-report.html >> $PROJECT_ROOT/brand-monitor.log 2>&1"
    local cron_entry="$CRON_SCHEDULE $cron_command $CRON_MARKER"

    # Check if entry already exists
    if crontab -l 2>/dev/null | grep -F "$CRON_MARKER" > /dev/null; then
        log_warning "Cron job already exists - updating schedule"

        if $DRY_RUN; then
            log_info "Would update cron schedule to: $CRON_SCHEDULE"
        else
            # Remove old entry and add new one
            (crontab -l 2>/dev/null | grep -vF "$CRON_MARKER"; echo "$cron_entry") | crontab -
            log_success "Cron job updated"
        fi
    else
        if $DRY_RUN; then
            log_info "Would add cron job with schedule: $CRON_SCHEDULE"
        else
            # Add new entry
            (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
            log_success "Cron job installed"
        fi
    fi

    # Show the installed schedule
    echo ""
    log_info "Monitoring schedule: $CRON_SCHEDULE"
    echo "  $(explain_cron_schedule "$CRON_SCHEDULE")"
    echo ""
    log_info "Logs will be written to: brand-monitor.log"
}

uninstall_cron() {
    if ! command -v crontab &> /dev/null; then
        log_warning "Cron not available - nothing to uninstall"
        return
    fi

    log_info "Removing cron job..."

    if crontab -l 2>/dev/null | grep -F "$CRON_MARKER" > /dev/null; then
        if $DRY_RUN; then
            log_info "Would remove cron job"
        else
            crontab -l 2>/dev/null | grep -vF "$CRON_MARKER" | crontab -
            log_success "Cron job removed"
        fi
    else
        log_warning "No cron job found to remove"
    fi
}

explain_cron_schedule() {
    local schedule="$1"

    case "$schedule" in
        "0 */6 * * *")
            echo "Runs every 6 hours"
            ;;
        "0 */4 * * *")
            echo "Runs every 4 hours"
            ;;
        "0 */12 * * *")
            echo "Runs every 12 hours"
            ;;
        "0 2 * * *")
            echo "Runs daily at 2:00 AM"
            ;;
        "0 0 * * 0")
            echo "Runs weekly on Sunday at midnight"
            ;;
        "0 9 * * 1-5")
            echo "Runs weekdays at 9:00 AM"
            ;;
        *)
            echo "Custom schedule: $schedule"
            ;;
    esac
}

print_next_steps() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Review configuration:"
    echo "     ${CYAN}cat .brand-monitor.yml${NC}"
    echo ""
    echo "  2. Run your first scan:"
    echo "     ${CYAN}python3 scripts/brand-monitor.py --full-workflow${NC}"
    echo ""
    echo "  3. View the generated report:"
    echo "     ${CYAN}open brand-drift-report.html${NC}"
    echo ""
    echo "  4. Check cron job status:"
    echo "     ${CYAN}crontab -l | grep 'Brand Drift'${NC}"
    echo ""
    echo "For more information, see ${CYAN}references/drift-detection.md${NC}"
    echo ""
}

print_uninstall_complete() {
    echo ""
    echo -e "${GREEN}✓ Cron job removed successfully${NC}"
    echo ""
    echo "The database and configuration files were not deleted."
    echo "To completely remove the drift monitoring system:"
    echo ""
    echo "  ${CYAN}rm .brand-drift.db .brand-monitor.yml${NC}"
    echo ""
}

# Main execution
main() {
    print_header

    if $DRY_RUN; then
        log_warning "DRY RUN MODE - No changes will be made"
        echo ""
    fi

    if $UNINSTALL; then
        uninstall_cron
        print_uninstall_complete
        exit 0
    fi

    # Setup steps
    check_dependencies
    create_config
    init_database
    install_cron

    if ! $DRY_RUN; then
        print_next_steps
    else
        echo ""
        log_info "Dry run complete - run without --dry-run to apply changes"
        echo ""
    fi
}

main "$@"
