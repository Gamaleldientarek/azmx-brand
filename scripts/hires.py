#!/usr/bin/env python3
"""High-res originals for the AZMX image library.

The 1600 px web copies live in the public CDN repository. The untouched
originals live in the company Google Drive, in the "Brand Images Gallery"
folder of the AZM X shared drive, one subfolder per section, each file named
like its web copy (``blue-114.png`` beside ``blue-114.jpg``). Only people signed
in with an AZMX Google account can open them.

This module is the shared toolkit for scripts/add-images.py,
scripts/sync-hires.py and scripts/inbox.py. It talks to Drive only through
Google Drive for Desktop: files are moved or copied into the synced folder, and
each file's Drive ID is read from the ``com.google.drivefs.item-id#S``
extended attribute that Drive for Desktop sets once the file has synced.
No Drive API, keys or sign-in step.

The Drive folder is found under ``~/Library/CloudStorage/GoogleDrive-*@azmx.sa``,
or taken from ``$AZMX_HIRES_DIR``. No account name is written in this file.
"""
import colorsys
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image

# Originals can be very large (an 8000 x 12000 TIFF is 96 MP). Pillow warns
# from 89 MP and refuses from 179 MP to guard against decompression bombs; these
# files come from AZMX's own designers, so allow up to 400 MP.
Image.MAX_IMAGE_PIXELS = 400_000_000

SECTIONS = ["gradient", "blue", "white", "orange", "purple", "red", "green", "yellow"]
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"}
GALLERY_PATH = Path("Shared drives") / "AZM X" / "Branding" / "Brand Images Gallery"
XATTR_ID = "com.google.drivefs.item-id#S"
_CATALOGUED = re.compile(r"^(" + "|".join(SECTIONS) + r")-\d{3}\.[a-z0-9]+$")


def drive_root(env=os.environ, home=None):
    """The "Brand Images Gallery" folder on this Mac, or None when it isn't there."""
    override = env.get("AZMX_HIRES_DIR")
    if override and Path(override).expanduser().is_dir():
        return Path(override).expanduser()
    home = Path.home() if home is None else Path(home)
    cloud = home / "Library" / "CloudStorage"
    if not cloud.is_dir():
        return None
    for account in sorted(cloud.glob("GoogleDrive-*@azmx.sa")):
        candidate = account / GALLERY_PATH
        if candidate.is_dir():
            return candidate
    return None


def _xattr_reader(path):
    r = subprocess.run(["xattr", "-p", XATTR_ID, str(path)], capture_output=True, text=True)
    value = r.stdout.strip()
    return value if r.returncode == 0 and value else None


def read_drive_id(path, timeout=120.0, poll=2.0, reader=None):
    """Wait until Drive for Desktop has given ``path`` a Drive ID, and return it.

    Returns None if no ID appears within ``timeout`` seconds (Drive paused or
    offline); the caller records the image as "high-res pending".
    """
    reader = reader or _xattr_reader
    deadline = time.monotonic() + timeout
    while True:
        value = reader(path)
        if value:
            return value
        if time.monotonic() >= deadline:
            return None
        time.sleep(poll)


def original_info(path):
    """Size facts recorded as ``hi`` in image-meta.json (the Drive ID is added by the caller)."""
    path = Path(path)
    with Image.open(path) as im:
        w, h = im.size
    return {"w": w, "h": h, "bytes": path.stat().st_size,
            "ext": path.suffix.lower().lstrip("."), "src": path.name}


def is_catalogued_name(name):
    """True for names this tool gives originals, such as ``blue-114.png``."""
    return bool(_CATALOGUED.match(name))


def _images_in(folder):
    return sorted(p for p in folder.iterdir()
                  if p.is_file() and not p.name.startswith(".")
                  and p.suffix.lower() in EXTS and not is_catalogued_name(p.name))


def find_new_originals(root):
    """New originals in ``root``: (path, section) pairs, section None for loose files.

    Files already named like ``blue-114.png`` were placed by this tool and are skipped.
    """
    root = Path(root)
    found = [(p, None) for p in _images_in(root)]
    for section in SECTIONS:
        folder = root / section
        if folder.is_dir():
            found += [(p, section) for p in _images_in(folder)]
    return found


def guess_section(dom_hex, lum):
    """Best-guess section for a loose original, from its dominant colour.

    ``gradient`` is never guessed: it looks like blue, so Jimmy picks it himself.
    """
    r, g, b = (int(dom_hex.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, sat, _ = colorsys.rgb_to_hsv(r, g, b)
    if sat < 0.15:
        # Near-greys: light ones are the White set; near-black ones are dark blue renders.
        return "white" if lum > 0.08 else "blue"
    # Hue ranges measured on the 240 catalogued images (22 Nov 2026): the Orange set
    # is red-orange (0-30 deg), Red is crimson (340-359), Yellow is ochre (36-40).
    deg = hue * 360
    if deg >= 330:
        return "red"
    if deg < 33:
        return "orange"
    if deg < 70:
        return "yellow"
    if deg < 170:
        return "green"
    if deg < 250:
        return "blue"
    return "purple"


def place_original(path, root, section, number):
    """Put an original in its section folder as ``<section>-NNN.<ext>``.

    Inside ``root`` the file is moved (Drive keeps its ID). From anywhere else it
    is copied and the source is left alone; the caller deletes it once it is safe.
    Never overwrites.
    """
    path, root = Path(path), Path(root)
    folder = root / section
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{section}-{number:03d}{path.suffix.lower()}"
    if dest.exists():
        raise FileExistsError(dest)
    try:
        inside = path.resolve().is_relative_to(root.resolve())
    except AttributeError:  # Python < 3.9
        inside = str(path.resolve()).startswith(str(root.resolve()) + os.sep)
    if inside:
        path.rename(dest)
    else:
        shutil.copy2(path, dest)
    return dest


COLOUR_LIMIT = 4         # mean channel difference (0-255) above which two pictures differ; a re-save moves it by 1-2


def fingerprint(path):
    """A picture's fingerprint: shape and colour, as ``<64 hex>:<96 hex>``.

    Shape is a 256-bit difference hash: the image reduced to 17 x 16 greys, each
    pixel compared with its right neighbour, so resizing and re-encoding (PNG,
    WebP, JPEG) barely change it. Colour is the average RGB of a 4 x 4 grid. Shape
    alone calls smooth gradients and recoloured versions of one picture "the
    same"; the colour grid tells them apart. Compare with :func:`fp_distance`:
    0-10 is the same picture, 11-20 is worth a look, above that they differ.
    """
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        g = rgb.convert("L").resize((17, 16), Image.LANCZOS)
        px = list(g.tobytes())
        grid = rgb.resize((4, 4), Image.BOX).tobytes()
    bits = 0
    for row in range(16):
        for col in range(16):
            bits = (bits << 1) | (px[row * 17 + col] > px[row * 17 + col + 1])
    return f"{bits:064x}:{grid.hex()}"


def fp_distance(a, b):
    """How far apart two fingerprints are: differing shape bits, or 256 when the colours differ."""
    shape_a, _, colour_a = a.partition(":")
    shape_b, _, colour_b = b.partition(":")
    if colour_a and colour_b:
        ca, cb = bytes.fromhex(colour_a), bytes.fromhex(colour_b)
        if sum(abs(x - y) for x, y in zip(ca, cb)) / len(ca) > COLOUR_LIMIT:
            return 256
    return bin(int(shape_a, 16) ^ int(shape_b, 16)).count("1")


def is_stable(path, quiet_seconds=60, now=None):
    """True once a file has not changed for ``quiet_seconds`` (it has finished copying in)."""
    now = time.time() if now is None else now
    return now - Path(path).stat().st_mtime >= quiet_seconds
