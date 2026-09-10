#!/usr/bin/env python3
"""Add new images to the AZMX brand image library.

Usage:
    python3 scripts/add-images.py <section> <file-or-folder> [more...]

    section: gradient | blue | white | orange | purple | red | green | yellow

Examples:
    python3 scripts/add-images.py blue ~/Desktop/new-render.png
    python3 scripts/add-images.py gradient ~/Desktop/exports/

What it does: resizes to 1600px wide (aspect ratio kept), compresses to JPEG
quality 70, names the file with the next free number in that section, then
rebuilds the index and the gallery so the new images appear everywhere. Commit
and push afterwards.

Conversion uses Pillow (pip install -r requirements.txt), so it runs on any OS;
it replaces the earlier macOS-only `sips` call with the same settings.
"""
import os
import subprocess
import sys

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - exercised only when Pillow is absent
    Image = ImageOps = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "images")
SECTIONS = ["gradient", "blue", "white", "orange", "purple", "red", "green", "yellow"]
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"}

# Same settings the previous `sips --resampleWidth 1600 -s format jpeg
# -s formatOptions 70` call applied.
TARGET_WIDTH = 1600
JPEG_QUALITY = 70


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


def next_index(section):
    d = os.path.join(IMG, section)
    os.makedirs(d, exist_ok=True)
    used = []
    for f in os.listdir(d):
        stem = os.path.splitext(f)[0]
        if stem.startswith(section + "-"):
            tail = stem[len(section) + 1:]
            if tail.isdigit():
                used.append(int(tail))
    return max(used) + 1 if used else 1


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in SECTIONS:
        print(__doc__)
        print("Sections:", ", ".join(SECTIONS))
        return 1

    section = sys.argv[1]
    files = collect(sys.argv[2:])
    if not files:
        print("No images found.")
        return 1

    n = next_index(section)
    added = []
    for src in files:
        dest = os.path.join(IMG, section, f"{section}-{n:03d}.jpg")
        try:
            convert_image(src, dest)
        except Exception as exc:  # show the real reason, then carry on with the rest
            print(f"  FAILED to convert {src}: {type(exc).__name__}: {exc}")
            if os.path.exists(dest):
                os.remove(dest)                  # never leave a half-written JPEG behind
            continue
        kb = os.path.getsize(dest) // 1024
        print(f"  added {os.path.basename(dest)}  ({kb} KB)  <- {os.path.basename(src)}")
        added.append(dest)
        n += 1

    if not added:
        return 1

    print(f"\n{len(added)} image(s) added to {section}. Rebuilding index and gallery...")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "rebuild-index.py")])
    if r.returncode == 0:
        print("\nDone. Now commit and push:")
        print('  git add -A && git commit -m "Add images to ' + section + '" && git push')
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
