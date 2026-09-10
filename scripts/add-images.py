#!/usr/bin/env python3
"""Add new images to the AZMX brand image library.

Usage:
    python3 scripts/add-images.py [--cdn-dir PATH] <section> <file-or-folder> [more...]

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
    ap.add_argument("section", nargs="?")
    ap.add_argument("paths", nargs="*")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.section or args.section not in SECTIONS or not args.paths:
        print(__doc__)
        print("Sections:", ", ".join(SECTIONS))
        return 1

    section = args.section
    files = collect(args.paths)
    if not files:
        print("No images found.")
        return 1

    cdn_dir = os.path.abspath(os.path.expanduser(args.cdn_dir))
    if not os.path.isdir(cdn_dir):
        print(f"CDN checkout not found: {cdn_dir}\n"
              f"Clone it next to this repository (git clone https://github.com/{CDN_REPO}.git "
              f"{os.path.dirname(ROOT)}/azmx-brand-cdn) or pass --cdn-dir PATH.")
        return 1

    meta = load_meta()
    out_dir = os.path.join(cdn_dir, "images", section)
    os.makedirs(out_dir, exist_ok=True)
    n = next_index(section, meta)
    added = []
    for src in files:
        dest = os.path.join(out_dir, f"{section}-{n:03d}.jpg")
        try:
            convert_image(src, dest)
            entry = {"f": os.path.basename(dest), **analyse_image(dest)}
        except Exception as exc:  # show the real reason, then carry on with the rest
            print(f"  FAILED to convert {src}: {type(exc).__name__}: {exc}")
            if os.path.exists(dest):
                os.remove(dest)                  # never leave a half-written JPEG behind
            continue
        kb = os.path.getsize(dest) // 1024
        print(f"  added {os.path.basename(dest)}  ({kb} KB)  <- {os.path.basename(src)}")
        meta.setdefault("images", {}).setdefault(section, []).append(entry)
        added.append(dest)
        n += 1

    if not added:
        return 1

    save_meta(meta)
    print(f"\n{len(added)} image(s) added to {section}. Rebuilding index and gallery...")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "rebuild-index.py")])
    if r.returncode == 0:
        print("\nDone. Now commit and push this repository:")
        print('  git add -A && git commit -m "Add images to ' + section + '" && git push')
        print(f"then commit and push {cdn_dir} (jsDelivr picks up main within ~12 h; "
              f"purge via https://purge.jsdelivr.net/gh/{CDN_REPO}@main/images/<section>/<file>)")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
