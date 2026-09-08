"""Pytest configuration and shared fixtures for AZMX brand script tests."""

import os
import sys
from pathlib import Path

import pytest

# Add scripts directory to Python path so we can import the scripts as modules
REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def repo_root():
    """Return the repository root path."""
    return REPO_ROOT


@pytest.fixture
def scripts_dir():
    """Return the scripts directory path."""
    return SCRIPTS_DIR


@pytest.fixture
def fixtures_dir():
    """Return the test fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_colors_md(fixtures_dir):
    """Return path to sample colors.md fixture."""
    return fixtures_dir / "colors.md"


@pytest.fixture
def sample_valid_html(fixtures_dir):
    """Return path to sample valid HTML fixture."""
    return fixtures_dir / "sample-valid.html"


@pytest.fixture
def sample_invalid_html(fixtures_dir):
    """Return path to sample invalid HTML fixture."""
    return fixtures_dir / "sample-invalid.html"


@pytest.fixture
def sample_css(fixtures_dir):
    """Return path to sample CSS fixture."""
    return fixtures_dir / "sample.css"


@pytest.fixture
def sample_tokens_json(fixtures_dir):
    """Return path to sample tokens JSON fixture."""
    return fixtures_dir / "sample-tokens.json"


@pytest.fixture
def sample_fields_json(fixtures_dir):
    """Return path to sample Figma fields JSON fixture."""
    return fixtures_dir / "sample-fields.json"


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test file operations."""
    return tmp_path


@pytest.fixture(autouse=True)
def preserve_cwd(request):
    """Automatically preserve and restore the current working directory for each test."""
    original_cwd = os.getcwd()
    yield
    os.chdir(original_cwd)
