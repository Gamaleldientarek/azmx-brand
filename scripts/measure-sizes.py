#!/usr/bin/env python3
"""Measure the pixel size of every library JPG and record it in scripts/image-sizes.json.

Usage:
    python3 scripts/measure-sizes.py          # measure images not yet recorded
    python3 scripts/measure-sizes.py --all    # measure every image again

The gallery (scripts/rebuild-index.py) shows each image's aspect ratio and filters
by it. The JPGs live on the CDN, so this reads only the first 64 KB of each file
(an HTTP range request) and takes the size from the JPEG frame header. Run it
after adding images, then run scripts/rebuild-index.py.
"""
import concurrent.futures
import json
import os
import struct
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "scripts", "image-meta.json")
SIZES = os.path.join(ROOT, "scripts", "image-sizes.json")
SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_size(data):
    """(width, height) from the first JPEG start-of-frame marker in data, or None."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in SOF:
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    return None


def fetch_size(url):
    req = urllib.request.Request(url, headers={"Range": "bytes=0-65535", "User-Agent": "azmx-brand-gallery-build"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return jpeg_size(r.read())


def main(argv):
    meta = json.load(open(META, encoding="utf-8"))
    cdn = meta["$meta"]["cdn"].rstrip("/")
    doc = json.load(open(SIZES, encoding="utf-8")) if os.path.exists(SIZES) else {"$meta": {}, "sizes": {}}
    sizes = doc.setdefault("sizes", {})
    todo = [(s, r["f"]) for s in meta["$meta"]["sections"] for r in meta["images"].get(s, [])
            if "--all" in argv or r["f"] not in sizes]
    with concurrent.futures.ThreadPoolExecutor(16) as ex:
        for (s, f), wh in zip(todo, ex.map(lambda t: fetch_size(f"{cdn}/{t[0]}/{t[1]}"), todo)):
            if wh:
                sizes[f] = list(wh)
            else:
                print(f"  could not read the size of {s}/{f}", file=sys.stderr)
    doc["sizes"] = {k: sizes[k] for k in sorted(sizes)}
    with open(SIZES, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, indent=1) + "\n")
    print(f"Measured {len(todo)} image(s); {len(sizes)} sizes recorded in scripts/image-sizes.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
