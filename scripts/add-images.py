#!/usr/bin/env python3
"""Add new images to the AZMX brand image library.

Usage:
    python3 scripts/add-images.py [--cdn-dir PATH] [--no-commit] <section> <file-or-folder> [more...]
    python3 scripts/add-images.py [--cdn-dir PATH] [--no-commit] [--yes] --from-drive

    section: gradient | blue | white | orange | purple | red | green | yellow

Examples:
    python3 scripts/add-images.py blue ~/Desktop/new-render.png
    python3 scripts/add-images.py gradient ~/Desktop/exports/
    python3 scripts/add-images.py --cdn-dir ~/src/azmx-brand-cdn red ~/Desktop/red/

What it does: resizes to 1600px wide (aspect ratio kept), compresses to JPEG
quality 70, names the file with the next free number in that section (taken
from scripts/image-meta.json, the catalogue of what is already on the CDN),
writes the JPEG into the CDN repository checkout (`<cdn-dir>/images/<section>/`,
default `../azmx-brand-cdn` next to this repo), measures the image and appends
its entry to scripts/image-meta.json, then rebuilds the index and the gallery so
the new images appear everywhere. Commit and push both repositories afterwards.

The JPEGs are not stored in this repository: they are served from jsDelivr
(`$meta.cdn` in scripts/image-meta.json), which mirrors the CDN repository's
main branch.

Conversion uses Pillow (pip install -r requirements.txt), so it runs on any OS;
it replaces the earlier macOS-only `sips` call with the same settings.
"""
import argparse
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - exercised only when Pillow is absent
    Image = ImageOps = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(ROOT, "scripts", "image-meta.json")
DEFAULT_CDN_DIR = os.path.join(os.path.dirname(ROOT), "azmx-brand-cdn")
CDN_REPO = "Gamaleldientarek/azmx-brand-cdn"
SECTIONS = ["gradient", "blue", "white", "orange", "purple", "red", "green", "yellow"]
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"}

# Same settings the previous `sips --resampleWidth 1600 -s format jpeg
# -s formatOptions 70` call applied.
TARGET_WIDTH = 1600
JPEG_QUALITY = 70

# High-res originals in the company Drive (see scripts/hires.py). The Drive ID
# of a placed original is read once Drive for Desktop has synced it.
ID_TIMEOUT = 120.0
ID_POLL = 2.0
ID_READER = None          # None = read the real extended attribute
CDN_URL = "https://cdn.jsdelivr.net/gh/" + CDN_REPO + "@{sha}/images"


def _load_hires():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hires.py")
    spec = importlib.util.spec_from_file_location("hires", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hires = _load_hires()


def find_drive_root():
    """The "Brand Images Gallery" Drive folder on this Mac, or None (no Drive here)."""
    return hires.drive_root()


_REBUILD_INDEX = None


def _rebuild_index_module():
    """Import scripts/rebuild-index.py once (hyphenated name, so via importlib)."""
    global _REBUILD_INDEX
    if _REBUILD_INDEX is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild-index.py")
        spec = importlib.util.spec_from_file_location("rebuild_index", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _REBUILD_INDEX = module
    return _REBUILD_INDEX


def analyse_image(path):
    """Per-image analysis ({dom, tok, L}); the single implementation lives in rebuild-index.py."""
    return _rebuild_index_module().analyse_image(path)


def convert_image(src, dest, width=TARGET_WIDTH, quality=JPEG_QUALITY):
    """
    Resize `src` to `width` px wide (height follows the aspect ratio, as sips
    --resampleWidth does), flatten to RGB and save as a JPEG at `quality`.

    Raises on any failure (unreadable file, unsupported format, write error) so
    the caller can show the real reason instead of a bare "FAILED".
    """
    if Image is None:
        raise RuntimeError("Pillow is not installed: pip install -r requirements.txt")
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)        # honour camera orientation
        w, h = im.size
        if w != width:
            im = im.resize((width, max(1, round(h * width / w))), Image.LANCZOS)
        if im.mode != "RGB":
            im = im.convert("RGB")               # drop alpha / palette for JPEG
        im.save(dest, "JPEG", quality=quality, optimize=True)


def collect(paths):
    out = []
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if os.path.splitext(f)[1].lower() in EXTS:
                    out.append(os.path.join(p, f))
        elif os.path.splitext(p)[1].lower() in EXTS:
            out.append(p)
        else:
            print(f"  skipped (not an image): {p}")
    return out


def load_meta():
    """Read scripts/image-meta.json, or return an empty catalogue if it is missing."""
    if not os.path.exists(META_PATH):
        return {"$meta": {"cdn": "", "sections": list(SECTIONS)}, "images": {}}
    with open(META_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_meta(meta):
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def next_index(section, meta=None):
    """Next free number for `section`, from the highest index recorded in image-meta.json.

    The catalogue, not a local folder, is the source of truth: the JPEGs live in
    the CDN repository and a working copy may be partial or absent.
    """
    meta = load_meta() if meta is None else meta
    used = []
    for entry in meta.get("images", {}).get(section, []):
        stem = os.path.splitext(entry.get("f", ""))[0]
        if stem.startswith(section + "-"):
            tail = stem[len(section) + 1:]
            if tail.isdigit():
                used.append(int(tail))
    return max(used) + 1 if used else 1


def parse_args(argv):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--cdn-dir", default=DEFAULT_CDN_DIR)
    ap.add_argument("--from-drive", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("section", nargs="?")
    ap.add_argument("paths", nargs="*")
    return ap.parse_args(argv)


def add_one(src, section, number, cdn_dir, meta, root, id_reader=None, max_width=TARGET_WIDTH):
    """Add one image: web JPEG in the CDN checkout, original in Drive, entry in ``meta``.

    The web copy is made from ``src`` first (never wider than ``max_width`` and
    never upscaled). With a Drive ``root`` the original is placed there as
    ``<section>-NNN.<ext>`` and its Drive ID recorded as ``hi``; if Drive gives no
    ID in time, or there is no Drive on this machine, ``hi`` is
    ``{"pending": True, "src": <original name>}`` and scripts/sync-hires.py links it
    later. Returns the new entry, or None (with nothing left behind) on failure.
    """
    src = Path(src)
    dest = os.path.join(cdn_dir, "images", section, f"{section}-{number:03d}.jpg")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        with Image.open(src) as im:
            width = min(max_width, im.size[0])
        convert_image(str(src), dest, width=width)
        entry = {"f": os.path.basename(dest), **analyse_image(dest)}
        if root is not None:
            placed = hires.place_original(src, root, section, number)
            file_id = hires.read_drive_id(placed, timeout=ID_TIMEOUT, poll=ID_POLL,
                                          reader=id_reader or ID_READER)
            if file_id:
                entry["hi"] = {**hires.original_info(placed), "src": src.name, "id": file_id}
            else:
                print(f"  Drive gave no ID for {placed.name} yet (paused?); "
                      f"recorded as pending, run scripts/sync-hires.py later")
                entry["hi"] = {"pending": True, "src": src.name}
        else:
            entry["hi"] = {"pending": True, "src": src.name}
    except Exception as exc:  # show the real reason, then carry on with the rest
        print(f"  FAILED to convert {src}: {type(exc).__name__}: {exc}")
        if os.path.exists(dest):
            os.remove(dest)                      # never leave a half-written JPEG behind
        return None
    kb = os.path.getsize(dest) // 1024
    print(f"  added {os.path.basename(dest)}  ({kb} KB)  <- {src.name}")
    meta.setdefault("images", {}).setdefault(section, []).append(entry)
    return entry


def rebuild_gallery():
    """Regenerate index.html and references/image-index.md; returns the exit code."""
    return subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "rebuild-index.py")]).returncode


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout.strip()


def commit_and_pin(cdn_dir, meta, sections):
    """Commit the new JPEGs, pin the gallery to that CDN commit, commit this repository.

    Nothing is pushed: pushing (CDN repository first) waits for the owner's yes.
    """
    label = ", ".join(sorted(sections))
    _git(cdn_dir, "add", "images")
    _git(cdn_dir, "commit", "-q", "-m", f"Add images: {label}")
    sha = _git(cdn_dir, "rev-parse", "HEAD")
    meta.setdefault("$meta", {})["gallery_cdn"] = CDN_URL.format(sha=sha)
    save_meta(meta)
    return sha


def _commit_brand(label):
    files = [f for f in ("scripts/image-meta.json", "index.html", "references/image-index.md")
             if os.path.exists(os.path.join(ROOT, f))]
    _git(ROOT, "add", *files)
    _git(ROOT, "commit", "-q", "-m", f"Add images: {label}")


def drive_jobs(root, meta, assume_yes):
    """New originals in the Drive folder as (path, section) pairs, after confirming guesses."""
    found = hires.find_new_originals(root)
    loose = [p for p, sec in found if sec is None]
    guesses = {}
    for p in loose:
        a = analyse_image(str(p))
        guesses[p] = hires.guess_section(a["dom"], a["L"])
    if loose:
        print("Loose files in the Drive folder, sorted by colour:")
        for p in loose:
            print(f"  {guesses[p]:<9} <- {p.name}")
        if not assume_yes:
            answer = input("Move them into these sections? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Nothing moved. Drop them into a section folder, or re-run with --yes.")
                return None
    return [(p, sec or guesses[p]) for p, sec in found]


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.from_drive:
        if args.section:
            args.paths = [args.section] + args.paths
            args.section = None
    elif not args.section or args.section not in SECTIONS or not args.paths:
        print(__doc__)
        print("Sections:", ", ".join(SECTIONS))
        return 1

    cdn_dir = os.path.abspath(os.path.expanduser(args.cdn_dir))
    root = find_drive_root()
    meta = load_meta()

    if args.from_drive:
        if root is None:
            print("No Brand Images Gallery folder found: Google Drive for Desktop must be "
                  "signed in to the AZMX account (or set AZMX_HIRES_DIR).")
            return 1
        jobs = drive_jobs(root, meta, args.yes)
        if jobs is None:
            return 1
        if not jobs:
            print("No new originals in the Drive folder.")
            return 0
    else:
        files = collect(args.paths)
        if not files:
            print("No images found.")
            return 1
        jobs = [(Path(f), args.section) for f in files]

    if not os.path.isdir(cdn_dir):
        print(f"CDN checkout not found: {cdn_dir}\n"
              f"Clone it next to this repository (git clone https://github.com/{CDN_REPO}.git "
              f"{os.path.dirname(ROOT)}/azmx-brand-cdn) or pass --cdn-dir PATH.")
        return 1

    numbers = {}
    added = []
    for src, section in jobs:
        n = numbers.get(section) or next_index(section, meta)
        if add_one(src, section, n, cdn_dir, meta, root):
            added.append(section)
            numbers[section] = n + 1

    if not added:
        return 1

    save_meta(meta)
    label = ", ".join(sorted(set(added)))
    if not args.no_commit:
        sha = commit_and_pin(cdn_dir, meta, set(added))
        print(f"\nCommitted the JPEGs in {cdn_dir} ({sha[:7]}); the gallery now points at that commit.")
    print(f"\n{len(added)} image(s) added to {label}. Rebuilding index and gallery...")
    code = rebuild_gallery()
    if code != 0:
        return code
    pending = sum(1 for rows in meta.get("images", {}).values() for r in rows
                  if (r.get("hi") or {}).get("pending"))
    if pending:
        print(f"{pending} image(s) still wait for their high-res original (scripts/sync-hires.py).")
    if args.no_commit:
        print(f"\nDone. Nothing committed (--no-commit): commit and push {cdn_dir} first, "
              f"then this repository.")
    else:
        _commit_brand(label)
        print("\nDone and committed in both repositories. Nothing is pushed. When approved, push in this order:")
        print(f"  git -C {cdn_dir} push")
        print("  git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
