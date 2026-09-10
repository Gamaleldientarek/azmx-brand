"""Security regression tests for the generated image gallery (index.html).

Two things went wrong here before and must never come back:

* The Content-Security-Policy hashes were computed from a *copy* of the CSS/JS
  rather than the strings actually emitted, so the committed page shipped a
  style hash that did not match its own <style> block and browsers blocked the
  stylesheet.  ``test_committed_index_csp_hashes_match`` checks the committed
  page; ``test_generated_gallery_csp_hashes_match`` checks a fresh build.

* Concept tags, filenames and recolour-prompt keys were interpolated into the
  HTML unescaped (stored XSS via image-index.md / image-tags.json).
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

CSP_RE = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"')
STYLE_RE = re.compile(r"<style>(.*?)</style>", re.S)
SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.S)


def _csp_hash(text: str) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode()


def _assert_hashes_match(html: str) -> None:
    csp = CSP_RE.search(html)
    assert csp, "index.html has no Content-Security-Policy meta tag"
    policy = csp.group(1)
    styles = STYLE_RE.findall(html)
    scripts = SCRIPT_RE.findall(html)
    assert styles and scripts, "expected at least one inline <style> and <script>"
    for block in styles:
        assert _csp_hash(block) in policy, "inline <style> hash is missing from the CSP — the stylesheet would be blocked"
    for block in scripts:
        assert _csp_hash(block) in policy, "inline <script> hash is missing from the CSP — the script would be blocked"
    # Directives that browsers ignore inside a <meta> CSP must not be there (they only log errors)
    assert "frame-ancestors" not in policy
    assert "X-Frame-Options" not in html
    # A hash-based style-src blocks every inline style="" attribute (no 'unsafe-hashes'),
    # so the page must carry none — swatches are painted from data-color by script.
    markup = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    assert 'style="' not in markup, "inline style attribute found; it would be blocked by the CSP"
    assert "unsafe-inline" not in policy and "unsafe-hashes" not in policy


def _load_rebuild_index(repo_root: Path):
    pytest.importorskip("PIL")
    spec = importlib.util.spec_from_file_location("rebuild_index", repo_root / "scripts" / "rebuild-index.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def scratch_repo(tmp_path):
    """A minimal copy of the repo layout that rebuild-index.py can write into."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "references").mkdir()
    (tmp_path / "assets" / "images").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "rebuild-index.py", tmp_path / "scripts" / "rebuild-index.py")
    shutil.copy(ROOT / "scripts" / "recolor-prompts.json", tmp_path / "scripts" / "recolor-prompts.json")
    (tmp_path / "scripts" / "image-tags.json").write_text("{}", encoding="utf-8")
    return tmp_path


def test_committed_index_csp_hashes_match():
    _assert_hashes_match(INDEX.read_text(encoding="utf-8"))


def test_generated_gallery_csp_hashes_match(scratch_repo):
    module = _load_rebuild_index(scratch_repo)
    module.write_gallery({"blue": [{"f": "blue-001.jpg", "dom": "#001AFF", "tok": "x", "L": 0.1}]}, 1)
    _assert_hashes_match((scratch_repo / "index.html").read_text(encoding="utf-8"))


def test_gallery_escapes_hostile_tags_and_filenames(scratch_repo):
    payload = '<img src=x onerror=alert(1)>'
    hostile_name = 'evil" onmouseover="alert(1)".jpg'
    (scratch_repo / "scripts" / "image-tags.json").write_text(
        json.dumps({hostile_name: [payload, "a&b", "c"]}), encoding="utf-8"
    )
    module = _load_rebuild_index(scratch_repo)
    module.write_gallery({"blue": [{"f": hostile_name, "dom": "#001AFF", "tok": "x", "L": 0.1}]}, 1)
    html = (scratch_repo / "index.html").read_text(encoding="utf-8")
    assert payload not in html, "raw tag payload reached index.html"
    assert 'onmouseover="alert(1)"' not in html, "raw filename reached an attribute"
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "&amp;b" in html


def test_gallery_rejects_hostile_recolor_prompt_keys(scratch_repo):
    prompts = json.loads((ROOT / "scripts" / "recolor-prompts.json").read_text(encoding="utf-8"))
    prompts["prompts"][0]["key"] = 'x" onclick="alert(1)'
    (scratch_repo / "scripts" / "recolor-prompts.json").write_text(json.dumps(prompts), encoding="utf-8")
    module = _load_rebuild_index(scratch_repo)
    with pytest.raises(SystemExit):
        module.recolour_section()


def test_sync_references_rejects_hostile_tags(tmp_path):
    spec = importlib.util.spec_from_file_location("sync_references", ROOT / "scripts" / "sync-references.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bad = tmp_path / "image-tags.json"
    bad.write_text(json.dumps({"blue-001.jpg": ["<script>", "b", "c"]}), encoding="utf-8")
    with pytest.raises(ValueError):
        module.parse_image_tags_json(str(bad))
