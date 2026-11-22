#!/usr/bin/env python3
"""Add new images from a drop folder that keeps filling while you work.

Usage:
    python3 scripts/inbox.py review --inbox FOLDER
    python3 scripts/inbox.py apply  --inbox FOLDER [--cdn-dir PATH] [--no-commit]
    python3 scripts/inbox.py backfill-fp [--cdn-dir PATH]

review
    Looks at every image in FOLDER that has not changed for a minute (so a file
    still copying in waits for the next round). Files in FOLDER/<section>/ keep
    that section; loose files get a section guessed from their colour. Each
    file is flagged when it repeats an image already in the library or earlier
    in this batch (``duplicate``, or ``possible-duplicate`` when close), or is
    narrower than 1600 px (``small``). Writes FOLDER/_review/inbox-plan.json and
    FOLDER/_review/review.html, a contact sheet to check before anything moves.

apply
    Adds only the files in the plan that are unchanged since the review, one at
    a time: the 1600 px web copy goes to the CDN checkout (never upscaled), the
    untouched original is copied into the Drive folder under its new number and,
    once the copy is checked, removed from FOLDER. Duplicates are skipped; small
    and possible-duplicate files only go in when their plan entry says
    ``"ok": true``. Files added after the review stay for the next round. If
    anything fails, that file stays in FOLDER with nothing left behind.

backfill-fp
    Gives every library image a fingerprint (``fp``) from its web copy in the
    CDN checkout, so new images can be checked against the whole library.
"""
import argparse
import html
import importlib.util
import json
import os
import sys
from pathlib import Path

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
REVIEW_DIR = "_review"
DUPLICATE, POSSIBLE = 10, 20          # fingerprint distances, see hires.fingerprint
QUIET_SECONDS = 60


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


add_images = _load("add_images", "add-images.py")
hires = add_images.hires


def _inbox_files(box):
    """(relative name, path, section or None) for every image in the drop folder."""
    out = []
    for p in sorted(box.iterdir()):
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in hires.EXTS:
            out.append((p.name, p, None))
    for section in hires.SECTIONS:
        folder = box / section
        if folder.is_dir():
            for p in sorted(folder.iterdir()):
                if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in hires.EXTS:
                    out.append((f"{section}/{p.name}", p, section))
    return out


def _catalogue_fps(meta):
    return [(f"{sec}/{r['f']}", r["fp"]) for sec, rows in meta.get("images", {}).items()
            for r in rows if r.get("fp")]


def review(box, now=None):
    meta = add_images.load_meta()
    known = _catalogue_fps(meta)
    rows, waiting = [], []
    for rel, path, section in _inbox_files(box):
        if not hires.is_stable(path, QUIET_SECONDS, now):
            waiting.append(rel)
            continue
        st = path.stat()
        row = {"file": rel, "size": st.st_size, "mtime": st.st_mtime, "w": 0, "h": 0,
               "fp": None, "flags": [], "dup_of": None, "guessed": section is None}
        try:
            with hires.Image.open(path) as im:
                row["w"], row["h"] = hires.ImageOps.exif_transpose(im).size
            row["fp"] = hires.fingerprint(path)
            if section is None:
                a = add_images.analyse_image(str(path))
                section = hires.guess_section(a["dom"], a["L"])
        except Exception as exc:                       # empty, broken, HEIC without a plugin, too big
            row.update(flags=["unreadable"], error=f"{type(exc).__name__}: {exc}")
            row["section"] = section or "?"
            rows.append(row)
            continue
        row["section"] = section
        if row["w"] < add_images.TARGET_WIDTH:
            row["flags"].append("small")
        rows.append(row)

    # Best version first (most pixels, then most bytes), so a smaller re-save is the
    # one flagged as the duplicate, never the original.
    rows.sort(key=lambda r: (-r["w"] * r["h"], -r["size"], r["file"]))
    seen = list(known)
    for row in rows:
        if not row["fp"]:
            continue
        best = min(((hires.fp_distance(row["fp"], fp), name) for name, fp in seen), default=None)
        if best and best[0] <= POSSIBLE:
            row["flags"].insert(0, "duplicate" if best[0] <= DUPLICATE else "possible-duplicate")
            row["dup_of"] = best[1]
        seen.append((row["file"], row["fp"]))
    rows.sort(key=lambda r: r["file"])

    out = box / REVIEW_DIR
    out.mkdir(exist_ok=True)
    (out / "inbox-plan.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    (out / "review.html").write_text(_sheet(rows, meta), encoding="utf-8")
    counts = {}
    for r in rows:
        counts[r["section"]] = counts.get(r["section"], 0) + 1
    print(f"{len(rows)} image(s) reviewed: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    for flag in ("unreadable", "duplicate", "possible-duplicate", "small"):
        n = sum(flag in r["flags"] for r in rows)
        if n:
            print(f"  {n} {flag}")
    if waiting:
        print(f"  {len(waiting)} still copying in, left for the next round: {', '.join(waiting)}")
    print(f"Check {out / 'review.html'}")
    return 0


def _sheet(rows, meta):
    cdn = (meta.get("$meta", {}).get("gallery_cdn") or meta.get("$meta", {}).get("cdn") or "").rstrip("/")
    cards = []
    for r in rows:
        dup = ""
        if r["dup_of"]:
            src = (f"{cdn}/{r['dup_of']}" if "/" in r["dup_of"] and r["dup_of"].split("/")[0] in hires.SECTIONS
                   and r["dup_of"].endswith(".jpg") else f"../{r['dup_of']}")
            dup = (f'<div class="dup"><img src="{html.escape(src)}" alt=""><span>same as '
                   f'{html.escape(r["dup_of"])}</span></div>')
        flags = "".join(f'<b class="{f}">{f}</b>' for f in r["flags"])
        guess = " (guess)" if r["guessed"] else ""
        cards.append(
            f'<figure><img src="../{html.escape(r["file"])}" alt="">{dup}'
            f'<figcaption><strong>{html.escape(r["section"])}{guess}</strong> {flags}<br>'
            f'{html.escape(r["file"])}<br>{r["w"]} × {r["h"]} px · {r["size"] // 1024} KB</figcaption></figure>')
    return ("<!doctype html><meta charset=utf-8><title>Inbox review</title><style>"
            "body{background:#000;color:#DDE8FF;font:14px/1.5 system-ui;margin:32px}"
            "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}"
            "figure{margin:0}img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}"
            ".dup{display:flex;gap:8px;align-items:center;margin-top:6px}.dup img{width:40%}"
            "b{font-weight:500;padding:1px 6px;border-radius:6px;background:#2661FF;color:#fff;margin-left:4px}"
            "b.duplicate{background:#FF2B3C}b.small{background:#F47A48}"
            "</style><h1>Inbox review</h1><p>" + str(len(rows)) + " images. Nothing has moved yet.</p>"
            "<main>" + "".join(cards) + "</main>")


def apply(box, cdn_dir, no_commit):
    plan_path = box / REVIEW_DIR / "inbox-plan.json"
    if not plan_path.is_file():
        print("No review yet: run  inbox.py review --inbox FOLDER  first.")
        return 1
    root = add_images.find_drive_root()
    if root is not None and (box.resolve() == Path(root).resolve()
                             or Path(root).resolve() in box.resolve().parents):
        print("The drop folder is inside the Drive folder; use a folder outside it "
              "(or drop straight into Drive and run add-images.py --from-drive).")
        return 1
    if root is None:
        print("No Brand Images Gallery folder found: originals are only removed from the inbox "
              "once they are safe in Drive, so apply needs Google Drive for Desktop (or AZMX_HIRES_DIR).")
        return 1
    if not os.path.isdir(cdn_dir):
        print(f"CDN checkout not found: {cdn_dir}")
        return 1
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    meta = add_images.load_meta()
    planned = {r["file"] for r in plan}
    numbers, added, skipped = {}, [], []
    for row in plan:
        path = box / row["file"]
        if not path.exists():
            continue                                    # done in an earlier run
        st = path.stat()
        if st.st_size != row["size"] or st.st_mtime != row["mtime"]:
            skipped.append(f"{row['file']} (changed since the review)")
            continue
        if "unreadable" in row["flags"]:
            skipped.append(f"{row['file']} (unreadable: {row.get('error', '')})")
            continue
        if "duplicate" in row["flags"]:
            skipped.append(f"{row['file']} (duplicate of {row['dup_of']})")
            continue
        if ({"small", "possible-duplicate"} & set(row["flags"])) and not row.get("ok"):
            skipped.append(f"{row['file']} ({', '.join(row['flags'])}: waiting for an OK)")
            continue
        section = row["section"]
        n = numbers.get(section) or add_images.free_index(section, meta, cdn_dir, root)
        entry = add_images.add_one(path, section, n, cdn_dir, meta, root)
        if not entry:
            skipped.append(f"{row['file']} (failed, see above)")
            continue
        add_images.save_meta(meta)                      # after every image: a crash loses nothing
        placed = Path(root) / section / f"{section}-{n:03d}{path.suffix.lower()}"
        if not entry["hi"].get("id"):
            print(f"  kept {row['file']} in the inbox: Drive has not confirmed {placed.name} yet")
        elif placed.is_file() and placed.stat().st_size == st.st_size:
            path.unlink()                               # the original is safe in Drive
        else:
            print(f"  kept {row['file']} in the inbox: the Drive copy could not be checked")
        added.append(section)
        numbers[section] = n + 1

    late = [rel for rel, _, _ in _inbox_files(box) if rel not in planned]
    if skipped:
        print("Left in the inbox:")
        for s in skipped:
            print(f"  {s}")
    if late:
        print(f"New since the review (next round): {', '.join(late)}")
    if not added:
        print("Nothing added.")
        return 0
    label = ", ".join(sorted(set(added)))
    if not no_commit:
        sha = add_images.commit_and_pin(cdn_dir, meta, set(added))
        print(f"Committed the JPEGs ({sha[:7]}); push it before this repository.")
    print(f"{len(added)} image(s) added to {label}. Rebuilding index and gallery...")
    code = add_images.rebuild_gallery()
    if code != 0:
        return code
    if not no_commit:
        add_images._commit_brand(label)
        print("Committed in both repositories. Nothing is pushed.")
    return 0


def backfill_fp(cdn_dir):
    meta = add_images.load_meta()
    done = missing = 0
    for section, rows in meta.get("images", {}).items():
        for r in rows:
            if r.get("fp"):
                continue
            p = Path(cdn_dir) / "images" / section / r["f"]
            if p.is_file():
                r["fp"] = hires.fingerprint(p)
                done += 1
            else:
                missing += 1
    add_images.save_meta(meta)
    print(f"{done} fingerprint(s) added" + (f", {missing} web copies not found" if missing else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Review and add images from a drop folder.")
    ap.add_argument("command", choices=["review", "apply", "backfill-fp"])
    ap.add_argument("--inbox")
    ap.add_argument("--cdn-dir", default=add_images.DEFAULT_CDN_DIR)
    ap.add_argument("--no-commit", action="store_true")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    cdn_dir = os.path.abspath(os.path.expanduser(args.cdn_dir))
    if args.command == "backfill-fp":
        return backfill_fp(cdn_dir)
    if not args.inbox or not Path(args.inbox).expanduser().is_dir():
        print("Pass the drop folder: --inbox FOLDER")
        return 1
    box = Path(args.inbox).expanduser()
    if args.command == "review":
        return review(box)
    return apply(box, cdn_dir, args.no_commit)


if __name__ == "__main__":
    sys.exit(main())
