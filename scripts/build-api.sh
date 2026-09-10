#!/usr/bin/env bash
#
# AZMX Brand API Build Script
#
# Orchestrates the complete API build pipeline:
# 1. Extract API data from markdown reference files (api/v1/*.json + index.json)
# 2. Generate and validate the OpenAPI 3.0 specification (JSON + YAML)
# 3. Generate the API documentation site (api-docs/index.html)
# 4. Validate all generated JSON endpoints
#
# Intermediate parser output goes to data/ (gitignored). Requires PyYAML and
# openapi-spec-validator: pip install -r requirements.txt -r requirements-test.txt
#
# Usage:
#   bash scripts/build-api.sh              # Full build
#   bash scripts/build-api.sh --dry-run    # Show steps without executing
#   bash scripts/build-api.sh --help       # Show this help
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
DRY_RUN=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            grep '^#' "$0" | cut -c 3-
            exit 0
            ;;
        *)
            echo -e "${RED}✗ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

log_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Execute command (respects --dry-run)
execute() {
    local cmd="$1"
    local description="$2"

    if [ "$VERBOSE" = true ]; then
        log_info "Command: $cmd"
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN]${NC} $description"
        echo -e "${YELLOW}         ${NC} Would execute: $cmd"
        return 0
    fi

    log_info "$description"
    if eval "$cmd"; then
        log_success "Completed: $description"
        return 0
    else
        log_error "Failed: $description"
        return 1
    fi
}

# Check Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        return 1
    fi

    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_info "Using Python $python_version"

    if ! python3 -c "import yaml, openapi_spec_validator" 2>/dev/null; then
        log_error "Missing Python packages. Run: pip install -r requirements.txt -r requirements-test.txt"
        return 1
    fi
    return 0
}

# Main build pipeline
main() {
    cd "$ROOT_DIR"

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   AZMX Brand API Build Pipeline               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY RUN mode - no changes will be made${NC}"
        echo ""
    fi

    log_info "Root directory: $ROOT_DIR"

    # Pre-flight checks
    log_step "Step 0: Pre-flight Checks"
    check_python || exit 1

    # Required directories
    if [ ! -d "references" ]; then
        log_error "Missing references/ directory"
        exit 1
    fi
    log_success "All required directories present"

    # Step 1: Extract API data
    log_step "Step 1: Extract API Data from References"
    execute \
        "python3 scripts/extract-api-data.py" \
        "Running data extraction parsers (colors, voice, audiences, prompts, typography, images, tokens)"

    # Step 2: Generate OpenAPI specification
    log_step "Step 2: Generate OpenAPI Specification"
    execute \
        "python3 scripts/generate-openapi.py --validate" \
        "Generating and validating OpenAPI 3.0 spec (JSON + YAML)"

    # Step 3: Generate documentation site
    log_step "Step 3: Generate API Documentation Site"
    execute \
        "python3 scripts/generate-docs.py --output api-docs/" \
        "Generating documentation site with Redoc"

    # Step 4: Validate all JSON endpoints
    log_step "Step 4: Validate API Endpoints"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would validate all JSON files in api/v1/"
    else
        local json_count=0
        local failed_count=0

        if [ -d "api/v1" ]; then
            for json_file in api/v1/*.json; do
                if [ -f "$json_file" ]; then
                    json_count=$((json_count + 1))
                    if python3 -m json.tool "$json_file" > /dev/null 2>&1; then
                        if [ "$VERBOSE" = true ]; then
                            log_success "Valid: $(basename "$json_file")"
                        fi
                    else
                        log_error "Invalid JSON: $(basename "$json_file")"
                        failed_count=$((failed_count + 1))
                    fi
                fi
            done

            if [ $failed_count -eq 0 ]; then
                log_success "All $json_count JSON endpoints validated successfully"
            else
                log_error "$failed_count of $json_count endpoints failed validation"
                exit 1
            fi
        else
            log_error "api/v1/ directory not found"
            exit 1
        fi
    fi

    # Summary
    echo ""
    log_step "Build Summary"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Dry run completed - no files were modified${NC}"
    else
        log_success "API data extracted from markdown references"
        log_success "OpenAPI 3.0 specification generated"
        log_success "API documentation site generated"
        log_success "All JSON endpoints validated"

        echo ""
        log_info "Generated files:"
        log_info "  • api/v1/*.json (API endpoints, index.json computed from the data)"
        log_info "  • api/v1/openapi.json + openapi.yaml (OpenAPI 3.0 spec)"
        log_info "  • api-docs/index.html (Documentation site, loads ../api/v1/openapi.json)"
    fi

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✓ Build Pipeline Completed Successfully     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$DRY_RUN" = false ]; then
        log_info "Next steps:"
        log_info "  • Review generated files in api/v1/ and api-docs/"
        log_info "  • Run the tests: python -m pytest tests/test_brand_api.py -q"
        log_info "  • View docs: open api-docs/index.html"
    fi

    return 0
}

# Run main function
main "$@"
