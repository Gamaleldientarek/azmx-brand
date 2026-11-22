#!/usr/bin/env python3
"""Link high-res originals that reached Drive after their web copy was added.

Usage:
    python3 scripts/sync-hires.py

For every image in scripts/image-meta.json without a Drive link, look in the
"Brand Images Gallery" Drive folder for ``<section>/<same name>.<any ext>``
(``blue/blue-114.tif`` for ``blue-114.jpg``). One match: read its Drive ID and
record it as ``hi``. Two or more: say so and leave it. Then rebuild the gallery.

Use it after scripts/add-images.py ran on a machine without Drive (the image is
"high-res pending"), after Drive was paused, or to give an older image its
original: drop the file, named like the web copy, into its section folder.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(ROOT, "scripts", "image-meta.json")
ID_TIMEOUT = 30.0
ID_POLL = 1.0
ID_READER = None


def _load_hires():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hires.py")
    spec = importlib.util.spec_from_file_location("hires", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hires = _load_hires()


def find_drive_root():
    return hires.drive_root()


def rebuild_gallery():
    return subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "rebuild-index.py")]).returncode


def main(argv=None):
    root = find_drive_root()
    if root is None:
        print("No Brand Images Gallery folder found: Google Drive for Desktop must be "
              "signed in to the AZMX account (or set AZMX_HIRES_DIR).")
        return 1
    with open(META_PATH, encoding="utf-8") as fh:
        meta = json.load(fh)
    linked = pending = 0
    for section, rows in meta.get("images", {}).items():
        folder = Path(root) / section
        for row in rows:
            hi = row.get("hi") or {}
            if hi.get("id"):
                continue
            stem = os.path.splitext(row["f"])[0]
            matches = sorted(p for p in folder.glob(stem + ".*")
                             if p.suffix.lower() in hires.EXTS) if folder.is_dir() else []
            if len(matches) > 1:
                print(f"  {row['f']}: more than one original ({', '.join(p.name for p in matches)}); "
                      f"keep one and run again")
            if len(matches) != 1:
                pending += bool(hi.get("pending"))
                continue
            file_id = hires.read_drive_id(matches[0], timeout=ID_TIMEOUT, poll=ID_POLL, reader=ID_READER)
            if not file_id:
                print(f"  {matches[0].name}: no Drive ID yet (is Drive paused?)")
                pending += bool(hi.get("pending"))
                continue
            info = hires.original_info(matches[0])
            info.pop("src", None)                       # file names stay out of the public catalogue
            row["hi"] = {**info, "id": file_id}
            linked += 1
            print(f"  linked {row['f']} <- {section}/{matches[0].name}")
    print(f"{linked} linked, {pending} still pending")
    if linked:
        with open(META_PATH, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        return rebuild_gallery()
    return 0


if __name__ == "__main__":
    sys.exit(main())
