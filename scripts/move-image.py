#!/usr/bin/env python3
"""Move catalogued images to another colour section.

Usage:
    python3 scripts/move-image.py [--cdn-dir PATH] <image> <section> [<image> <section> ...]

    python3 scripts/move-image.py blue-127 purple orange-048 yellow

Each image gets the next free number in its new section. The web copy is
renamed in the CDN checkout (git mv), the high-res original is moved in the
Drive folder (a move inside Drive keeps its Drive ID, so the High-res link still
works), and the catalogue entry and its concept tags follow. Then the gallery is
rebuilt. Commit and push the CDN checkout first, then this repository.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
TAGS_PATH = os.path.join(SCRIPTS, "image-tags.json")


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


add_images = _load("add_images", "add-images.py")


def rebuild_gallery():
    return add_images.rebuild_gallery()


def _rename_web_copy(cdn_dir, old, new):
    os.makedirs(os.path.dirname(new), exist_ok=True)
    r = subprocess.run(["git", "-C", cdn_dir, "mv", os.path.relpath(old, cdn_dir), os.path.relpath(new, cdn_dir)],
                       capture_output=True, text=True)
    if r.returncode != 0:                       # not a git checkout (tests): a plain rename
        os.rename(old, new)


def move(meta, tags, name, section, cdn_dir, root):
    """Move one image; return its new file name, or None (nothing changed) if it can't."""
    stem = name[:-4] if name.endswith(".jpg") else name
    old_section = stem.rsplit("-", 1)[0]
    rows = meta.get("images", {}).get(old_section, [])
    entry = next((r for r in rows if r["f"] == stem + ".jpg"), None)
    if entry is None or section not in add_images.SECTIONS:
        print(f"  {stem}: not in the catalogue, or {section!r} is not a section; skipped")
        return None
    if section == old_section:
        return entry["f"]
    old_web = os.path.join(cdn_dir, "images", old_section, entry["f"])
    if not os.path.isfile(old_web):
        print(f"  {stem}: web copy not found at {old_web}; skipped")
        return None
    n = add_images.free_index(section, meta, cdn_dir, root)
    new_f = f"{section}-{n:03d}.jpg"
    _rename_web_copy(cdn_dir, old_web, os.path.join(cdn_dir, "images", section, new_f))
    if root is not None:
        for original in sorted(Path(root, old_section).glob(stem + ".*")):
            dest = Path(root, section, new_f[:-4] + original.suffix.lower())
            dest.parent.mkdir(parents=True, exist_ok=True)
            original.rename(dest)
    rows.remove(entry)
    entry["f"] = new_f
    meta["images"].setdefault(section, []).append(entry)
    if stem + ".jpg" in tags:
        tags[new_f] = tags.pop(stem + ".jpg")
    print(f"  {stem}.jpg -> {new_f}")
    return new_f


def main(argv=None):
    ap = argparse.ArgumentParser(description="Move catalogued images to another colour section.")
    ap.add_argument("--cdn-dir", default=add_images.DEFAULT_CDN_DIR)
    ap.add_argument("pairs", nargs="+", help="<image> <section> pairs")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if len(args.pairs) % 2:
        print("Give <image> <section> pairs.")
        return 1
    cdn_dir = os.path.abspath(os.path.expanduser(args.cdn_dir))
    root = add_images.find_drive_root()
    meta = add_images.load_meta()
    with open(TAGS_PATH, encoding="utf-8") as fh:
        tags = json.load(fh)
    moved = 0
    for name, section in zip(args.pairs[::2], args.pairs[1::2]):
        if move(meta, tags, name, section, cdn_dir, root):
            moved += 1
    if not moved:
        return 1
    add_images.save_meta(meta)
    with open(TAGS_PATH, "w", encoding="utf-8") as fh:
        json.dump(tags, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return rebuild_gallery()


if __name__ == "__main__":
    sys.exit(main())
