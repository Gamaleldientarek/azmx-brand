#!/bin/bash
# Unified test runner for AZMX Brand utility scripts
# Runs both Python and Node.js tests with coverage reporting

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AZMX Brand Utility Scripts Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ========================================
# Python Tests
# ========================================
echo -e "${BLUE}[1/2] Running Python Tests...${NC}"
echo ""

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo "Please create a virtual environment and install dependencies:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements-test.txt"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Run Python tests with coverage
echo "Running pytest with coverage..."
if python3 -m pytest tests/ --cov=scripts --cov-report=term-missing --cov-report=html; then
    echo -e "${GREEN}✓ Python tests passed${NC}"
    PYTHON_EXIT=0
else
    echo -e "${RED}✗ Python tests failed${NC}"
    PYTHON_EXIT=1
fi

echo ""

# Extract coverage percentage
PYTHON_COVERAGE=$(python3 -m pytest tests/ --cov=scripts --cov-report=term | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')

if [ -n "$PYTHON_COVERAGE" ]; then
    echo -e "Python Coverage: ${BLUE}${PYTHON_COVERAGE}%${NC}"

    # Check if coverage meets threshold
    if (( $(echo "$PYTHON_COVERAGE >= 80" | bc -l) )); then
        echo -e "${GREEN}✓ Coverage threshold met (>= 80%)${NC}"
    else
        echo -e "${YELLOW}⚠ Coverage below 80% threshold${NC}"
        echo -e "${YELLOW}  Current: ${PYTHON_COVERAGE}%, Target: 80%${NC}"
        echo -e "${YELLOW}  To improve coverage, add more tests for:${NC}"

        # Show which files need more coverage
        python3 -m pytest tests/ --cov=scripts --cov-report=term-missing 2>/dev/null | grep -E "scripts/.*\.py.*[0-9]+%" | while read -r line; do
            COVERAGE=$(echo "$line" | awk '{print $(NF)}' | sed 's/%//')
            if (( $(echo "$COVERAGE < 80" | bc -l) )); then
                FILE=$(echo "$line" | awk '{print $1}')
                echo -e "${YELLOW}    - $FILE ($COVERAGE%)${NC}"
            fi
        done
    fi
fi

echo ""

# ========================================
# Node.js Tests
# ========================================
echo -e "${BLUE}[2/2] Running Node.js Tests...${NC}"
echo ""

# Check if scripts directory exists
if [ ! -d "scripts" ]; then
    echo -e "${RED}ERROR: scripts directory not found${NC}"
    exit 1
fi

# Check if node_modules exists in scripts directory
if [ ! -d "scripts/node_modules" ]; then
    echo -e "${YELLOW}⚠ Node.js dependencies not installed${NC}"
    echo "Vitest is not available. To run Node.js tests:"
    echo "  cd scripts && npm install"
    echo ""
    echo "See tests/README.md for setup details."
    echo ""
    NODEJS_EXIT=2  # Exit code 2 = skipped
else
    # Check if vitest is actually installed
    cd scripts
    if ! npm list vitest > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Vitest not installed in node_modules${NC}"
        echo "To run Node.js tests:"
        echo "  cd scripts && npm install"
        echo ""
        echo "See tests/README.md for setup details."
        echo ""
        cd ..
        NODEJS_EXIT=2  # Exit code 2 = skipped
    else
        # Run Node.js tests
        echo "Running vitest with coverage..."
        if npm test -- --coverage; then
            echo -e "${GREEN}✓ Node.js tests passed${NC}"
            NODEJS_EXIT=0
        else
            echo -e "${RED}✗ Node.js tests failed${NC}"
            NODEJS_EXIT=1
        fi
        cd ..
        echo ""
    fi
fi

# ========================================
# Summary
# ========================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Python results
if [ $PYTHON_EXIT -eq 0 ]; then
    echo -e "Python Tests:   ${GREEN}PASSED${NC} (Coverage: ${PYTHON_COVERAGE}%)"
else
    echo -e "Python Tests:   ${RED}FAILED${NC}"
fi

# Node.js results
if [ $NODEJS_EXIT -eq 0 ]; then
    echo -e "Node.js Tests:  ${GREEN}PASSED${NC}"
elif [ $NODEJS_EXIT -eq 2 ]; then
    echo -e "Node.js Tests:  ${YELLOW}SKIPPED${NC} (dependencies not installed)"
else
    echo -e "Node.js Tests:  ${RED}FAILED${NC}"
fi

echo ""

# Generate HTML coverage report info
if [ -d "htmlcov" ]; then
    echo -e "${BLUE}HTML coverage report available at: htmlcov/index.html${NC}"
    echo "Open it with: open htmlcov/index.html"
    echo ""
fi

# Overall exit code
if [ $PYTHON_EXIT -ne 0 ]; then
    echo -e "${RED}Overall Status: FAILED${NC}"
    exit 1
elif [ $NODEJS_EXIT -eq 1 ]; then
    echo -e "${RED}Overall Status: FAILED${NC}"
    exit 1
elif [ $NODEJS_EXIT -eq 2 ]; then
    echo -e "${YELLOW}Overall Status: PARTIAL (Node.js tests skipped)${NC}"
    exit 0
else
    echo -e "${GREEN}Overall Status: PASSED${NC}"
    exit 0
fi
