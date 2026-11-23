#!/usr/bin/env python3
"""Rebuild references/image-index.md and index.html from scripts/image-meta.json.

Usage:
    python3 scripts/rebuild-index.py

The JPEGs themselves live in a separate CDN repository (served through jsDelivr;
the base URL is ``$meta.cdn`` in scripts/image-meta.json), so this script does
not need any image file to run. It reads the per-image analysis (dominant colour,
nearest brand token, luminance) from scripts/image-meta.json and regenerates the
agent-readable index and the public gallery page, both linking to the CDN.

If a local ``assets/images/<section>/*.jpg`` tree is present (an offline working
copy, or a checkout from before the move), the images are re-measured with Pillow
and scripts/image-meta.json is rewritten from them.
"""
import os
import re
import sys
import json
import hashlib
import base64

try:
    from PIL import Image, ImageStat
except ImportError:  # only needed when a local assets/images tree is analysed
    Image = ImageStat = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "images")
META_PATH = os.path.join(ROOT, "scripts", "image-meta.json")
DEFAULT_CDN = "https://gamaleldientarek.github.io/azmx-brand-cdn/images"
GALLERY = "https://gamaleldientarek.github.io/azmx-brand/"

TITLES = {"gradient": "Gradients", "blue": "Abstract Blue", "orange": "Orange",
          "purple": "Purple", "green": "Green", "yellow": "Yellow",
          "red": "Red", "white": "White"}
NOTE = {
    "gradient": "Black to electric gradient fields. Event surfaces only: covers, dividers, closings.",
    "blue": "The core brand set. Default choice for any AZMX surface needing an image.",
    "white": "The only lighter set. Neutral 900 titles and Electric accents work here.",
    "orange": "Recoloured variants. Categorical or client work only, not brand colours.",
    "purple": "Measures closer to Blue 900 and Dark Navy than to purple. Safe on AZMX surfaces.",
    "red": "Recoloured variants. Semantic or client work only.",
    "green": "Recoloured variants. Semantic or client work only.",
    "yellow": "Recoloured variants. Semantic or client work only."}
ORDER = ["gradient", "blue", "white", "purple", "orange", "red", "green", "yellow"]

TOKENS = {
    "Electric #001AFF": (0x00, 0x1A, 0xFF), "Dark Navy #040038": (0x04, 0x00, 0x38),
    "Light Blue #5D8FFF": (0x5D, 0x8F, 0xFF), "White #FFFFFF": (0xFF, 0xFF, 0xFF),
    "Blue 50 #F0F5FF": (0xF0, 0xF5, 0xFF), "Blue 100 #DDE8FF": (0xDD, 0xE8, 0xFF),
    "Blue 200 #BFD5FF": (0xBF, 0xD5, 0xFF), "Blue 300 #93B6FF": (0x93, 0xB6, 0xFF),
    "Blue 500 #2661FF": (0x26, 0x61, 0xFF), "Blue 700 #0200D3": (0x02, 0x00, 0xD3),
    "Blue 900 #01006E": (0x01, 0x00, 0x6E), "Blue 950 #010040": (0x01, 0x00, 0x40),
    "Neutral 900 #111927": (0x11, 0x19, 0x27), "Neutral 200 #E5E7EB": (0xE5, 0xE7, 0xEB),
    "Red #FF2B3C": (0xFF, 0x2B, 0x3C), "Yellow #FED340": (0xFE, 0xD3, 0x40),
    "Green #22C36F": (0x22, 0xC3, 0x6F), "Orange #F47A48": (0xF4, 0x7A, 0x48),
    "Purple #C68FFF": (0xC6, 0x8F, 0xFF)}


def nearest(rgb):
    """Find the nearest brand token to the given RGB by Euclidean distance.

    Measures the distance in RGB space (sum of squared channel differences) against
    all 19 brand tokens and returns the closest match's name. Used to label each
    image's dominant colour with the brand token it resembles most.
    """
    return min(TOKENS.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(rgb, kv[1])))[0]


def luminance(rgb):
    """Calculate the sRGB relative luminance of an RGB colour.

    Applies gamma correction to each channel (linear below 0.03928, power 2.4 above),
    then combines them with the sRGB weights: 0.2126×R + 0.7152×G + 0.0722×B. Returns
    a value in [0, 1]. Used to determine whether White or Neutral 900 text will contrast
    best against each image.
    """
    def f(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def compute_csp_hash(content):
    """Compute SHA-256 hash for CSP (Content Security Policy).

    Returns the hash in the format required by CSP: sha256-<base64-hash>
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    digest = hashlib.sha256(content).digest()
    b64 = base64.b64encode(digest).decode('utf-8')
    return f"sha256-{b64}"


def load_meta():
    """Return the parsed scripts/image-meta.json, or None if it does not exist."""
    if not os.path.exists(META_PATH):
        return None
    with open(META_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def cdn_base():
    """The CDN base URL every image link points to (``$meta.cdn`` in image-meta.json)."""
    meta = load_meta()
    if meta and isinstance(meta.get("$meta"), dict) and meta["$meta"].get("cdn"):
        return meta["$meta"]["cdn"].rstrip("/")
    return DEFAULT_CDN


CDN = cdn_base()


def gallery_cdn():
    """The CDN base the public gallery (index.html) links to.

    ``$meta.gallery_cdn`` can point the gallery somewhere other than ``$meta.cdn``.
    Since 22 Nov 2026 both are GitHub Pages and the key is unset: the gallery
    used to be pinned to a jsDelivr commit, until jsDelivr started refusing the
    repository (over 50 MB). Falls back to :func:`cdn_base`.
    """
    meta = load_meta()
    if meta and isinstance(meta.get("$meta"), dict) and meta["$meta"].get("gallery_cdn"):
        return meta["$meta"]["gallery_cdn"].rstrip("/")
    return cdn_base()


GALLERY_CDN = gallery_cdn()


def hires_link(file_id):
    """Link to a high-res original in the AZM X Google Drive (the Drive viewer, with Download).

    The file is shared with azmx.sa only. The viewer, unlike a direct-download link,
    picks the signed-in AZMX account even when the browser holds several Google
    accounts (a direct link uses the first one and answers 403).
    """
    return f"https://drive.google.com/file/d/{file_id}/view"


def has_hires(entry):
    """True when an image's original is in Drive with a known file ID."""
    hi = entry.get("hi") or {}
    return bool(hi.get("id")) and not hi.get("pending")


def _mb(n):
    return f"{n / 1048576:.1f} MB"


def hires_button(entry):
    """The card's High-res link, or "" when the image has no original in Drive."""
    if not has_hires(entry):
        return ""
    hi = entry["hi"]
    title = (f"High-res original · {hi['w']} × {hi['h']} px · {_mb(hi['bytes'])} "
             f"{hi['ext'].upper()} · needs an AZMX Google sign-in")
    return (f'<a class="hi" href="{esc(hires_link(hi["id"]))}" target="_blank" rel="noopener" '
            f'title="{esc(title)}">{icon("arrows-out")}High-res</a>')


def analyse_image(path):
    """Measure one image: dominant colour, nearest brand token and luminance.

    The image is resized to 80×80, then quantized to 5 colours using MEDIANCUT
    (Pillow's median-cut algorithm, which recursively splits the colour space
    along the widest axis). The dominant colour is the most frequent RGB value in
    that 5-colour palette. Luminance is measured separately from the resized
    image's average RGB using the sRGB formula. Returns ``{dom, tok, L}`` where
    dom=dominant colour hex, tok=nearest brand token, L=sRGB luminance in [0, 1].
    """
    if Image is None:
        raise RuntimeError("Pillow is required to analyse images:  pip3 install Pillow")
    with Image.open(path) as src:
        im = src.convert("RGB").resize((80, 80))
    q = im.quantize(colors=5, method=Image.MEDIANCUT).convert("RGB")
    dom = sorted(q.getcolors(10000), reverse=True)[0][1]
    avg = tuple(int(c) for c in ImageStat.Stat(im).mean)
    return {"dom": "#%02X%02X%02X" % dom, "tok": nearest(dom), "L": round(luminance(avg), 3)}


def local_images():
    """Return {section: [filenames]} for JPEGs under assets/images, or {} if none."""
    found = {}
    for sec in ORDER:
        d = os.path.join(IMG, sec)
        if not os.path.isdir(d):
            continue
        files = sorted(fn for fn in os.listdir(d) if fn.lower().endswith(".jpg"))
        if files:
            found[sec] = files
    return found


def write_meta(secs, meta=None):
    """Write scripts/image-meta.json, keeping the existing ``$meta`` block."""
    head = (meta or {}).get("$meta") if meta else None
    if not head:
        head = {"description": "Per-image analysis used to build index.html and "
                               "references/image-index.md without the JPEG files present. "
                               "Regenerated by scripts/rebuild-index.py when assets/images exists "
                               "locally; extended by scripts/add-images.py.",
                "cdn": CDN, "sections": list(ORDER)}
    data = {"$meta": head, "images": {s: secs[s] for s in ORDER if secs.get(s)}}
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def analyse():
    """Return {section: [{f, dom, tok, L}, ...]} for every image in the library.

    If assets/images holds JPEGs they are measured with :func:`analyse_image` and
    scripts/image-meta.json is rewritten from the result (its ``$meta`` block is
    kept). Otherwise the sections are loaded from scripts/image-meta.json, which is
    the normal case now that the files live in the CDN repository.
    """
    meta = load_meta()
    found = local_images()
    if found:
        old = {}
        for sec, rows in ((meta or {}).get("images") or {}).items():
            for r in rows:
                old[(sec, r.get("f"))] = r
        secs = {}
        for sec, files in found.items():
            secs[sec] = []
            for fn in files:
                row = dict(f=fn, **analyse_image(os.path.join(IMG, sec, fn)))
                for key in ("hi", "fp"):           # not measurable from the web copy
                    if key in old.get((sec, fn), {}):
                        row[key] = old[(sec, fn)][key]
                secs[sec].append(row)
        write_meta(secs, meta)
        return secs
    if not meta:
        return {}
    images = meta.get("images", {})
    return {s: list(images[s]) for s in ORDER if images.get(s)}


def text_for(lum):
    """Return the recommended text colour scheme for a given image luminance.

    Implements AZMX text-on-image rules using two luminance thresholds: 0.18 and 0.5.
    Below 0.18 (dark images), White text with Light Blue accents provides safe contrast;
    Electric is never used here because it fails WCAG contrast on dark. Between 0.18 and
    0.5 (mid-range), White is recommended but requires manual contrast testing against
    the specific image. At 0.5 and above (light images), Neutral 900 text with Electric accents
    meets contrast requirements. These thresholds correspond to WCAG AA requirements
    (4.5:1 for normal text) while respecting the brand's Electric-never-on-dark rule.
    """
    if lum < 0.18:
        return "White + Light Blue accent"
    if lum < 0.5:
        return "White, test contrast"
    return "Neutral 900 + Electric accent"


def write_index(secs):
    """Generate the agent-readable markdown index at references/image-index.md.

    Builds a structured markdown document that catalogues every image in the library
    with its download URL, dominant colour, safe text colour, and concept tags. The
    output is designed for agent consumption: LLMs can search the file by concept tag
    (e.g., "momentum", "precision") to shortlist candidates, then choose by section
    and colour. Each section is rendered as a markdown table with columns for filename,
    tags, dominant colour hex, text-on-top recommendation, and a direct download link.
    Takes the section dictionary from analyse() and returns the total image count.
    """
    tags = load_tags()
    total = sum(len(v) for v in secs.values())
    L = ["# AZMX Image Index\n",
         f"Every image in the library ({total} total) with its direct download link, dominant colour, and the text colour that is safe on top of it.\n",
         "Download any image directly with curl, or paste the URL into a browser, Figma, Canva, or an email builder:\n",
         '```bash\ncurl -L -O "' + CDN + '/blue/blue-001.jpg"\n```\n',
         f"Browse them visually at {GALLERY}\n",
         "Each image carries three concept tags describing what it can represent in a deliverable. Search this file for a concept (for example `momentum` or `precision`) to shortlist candidates before choosing.\n",
         "`Text on top` is derived from each image's measured luminance. Dark images take White titles with Light Blue accents; Electric is never used for text on these surfaces because it fails contrast on dark.\n",
         "---\n"]
    for s in ORDER:
        rows = secs.get(s, [])
        if not rows:
            continue
        L.append(f"## {TITLES[s]} ({len(rows)})\n")
        L.append("| Image | Concept tags | Dominant | Text on top | Link |")
        L.append("|---|---|---|---|---|")
        for r in rows:
            tg = ", ".join(tags.get(r["f"], [])) or "—"
            link = f"[download]({CDN}/{s}/{r['f']})"
            if has_hires(r):
                hi = r["hi"]
                link += f" · hi-res {hi['w']}×{hi['h']} {hi['ext'].upper()} (AZMX sign-in)"
            L.append(f"| `{r['f']}` | {tg} | `{r['dom']}` | {text_for(r['L'])} | {link} |")
        L.append("")
    with open(os.path.join(ROOT, "references", "image-index.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    return total


def load_prompts():
    """Load recolour prompts from the recolor-prompts.json configuration file.

    Reads scripts/recolor-prompts.json and returns the parsed JSON data containing
    prompt definitions, model metadata, and usage notes. Returns None if the file
    does not exist. Used to populate the recolour prompt cards in the HTML gallery.
    """
    import json
    p = os.path.join(ROOT, "scripts", "recolor-prompts.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def esc(s):
    """Escape HTML entities in a string for safe HTML generation.

    Replaces the four core XML entities (&, <, >, ") with their named character
    references (&amp;, &lt;, &gt;, &quot;). Used to embed user-controlled text
    into HTML attributes and content without injection risk.
    """
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def recolour_section():
    """The recolour prompt cards, each with an always-visible copy button.

    Copy button follows the UX rules: 44px minimum target, always visible rather
    than hover-only (hover does not exist on touch), 180ms state change, and the
    result announced through a live region for screen readers.
    """
    data = load_prompts()
    if not data:
        return ""
    for p in data["prompts"]:
        if not re.fullmatch(r"[a-z0-9-]+", p["key"]):
            raise SystemExit(f"recolor-prompts.json: invalid key {p['key']!r} (use a-z, 0-9, -)")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", p["swatch"]):
            raise SystemExit(f"recolor-prompts.json: invalid swatch {p['swatch']!r} for {p['key']}")
    h = ['<section id="recolor"><h2>Recolour prompts</h2>',
         f'<p class="sub">{esc(data["note"])} Model used: <code>{esc(data["model"])}</code>.</p>',
         '<div class="pgrid">']
    for p in data["prompts"]:
        h.append(
            f'<article class="pcard">'
            f'<div class="phead">'
            f'<span class="pname"><i class="pdot" data-color="{p["swatch"]}"></i>{esc(p["label"])}</span>'
            f'<button class="copy" type="button" data-prompt="{p["key"]}" '
            f'aria-label="Copy the {esc(p["label"])} recolour prompt">'
            f'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'<rect x="5.5" y="5.5" width="8" height="8" rx="1"/>'
            f'<path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/></svg>'
            f'<span class="copy-label">Copy</span></button>'
            f'</div>'
            f'<p class="psum">{esc(p["summary"])}</p>'
            f'<p class="ptext" id="prompt-{p["key"]}">{esc(p["text"])}</p>'
            f'</article>')
    h.append('</div><p class="sr" role="status" aria-live="polite" id="copy-status"></p></section>')
    h.append("<script>\n" + COPY_SCRIPT + "\n</script>")
    return "\n".join(h)


# Aspect ratios the library uses, widest first. A measured size snaps to the nearest
# one within 6 %; the exact pixel size is still shown in the details drawer.
RATIOS = [(21, 9), (2, 1), (16, 9), (3, 2), (4, 3), (5, 4), (1, 1), (4, 5), (3, 4), (2, 3), (1, 2), (9, 16)]


def load_sizes():
    """Pixel sizes {file: (width, height)} from scripts/image-sizes.json ({} when absent).

    The JPGs live on the CDN, so their sizes are recorded once by
    scripts/measure-sizes.py rather than read here.
    """
    p = os.path.join(ROOT, "scripts", "image-sizes.json")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    return {f: (int(wh[0]), int(wh[1])) for f, wh in data.get("sizes", {}).items() if len(wh) == 2 and wh[1]}


def aspect(w, h):
    """The aspect ratio label for a pixel size, e.g. (1600, 897) -> "16:9"."""
    import math
    r = w / h
    a, b = min(RATIOS, key=lambda p: abs(p[0] / p[1] - r))
    if abs(a / b - r) / r <= 0.06:
        return f"{a}:{b}"
    g = math.gcd(w, h)
    return f"{w // g}:{h // g}"


def orientation(w, h):
    """Landscape, Portrait or Square (within 5 %)."""
    if w > h * 1.05:
        return "Landscape"
    if h > w * 1.05:
        return "Portrait"
    return "Square"


def ratio_value(label):
    a, b = label.split(":")
    return int(a) / int(b)


def ratio_filter(secs):
    """The Ratio group: one row per aspect ratio in the library, widest first, with a
    small proportional shape, the orientation and the count. One ratio at a time."""
    sizes = load_sizes()
    import collections
    counts = collections.Counter(aspect(*sizes[r["f"]]) for rows in secs.values() for r in rows if r["f"] in sizes)
    if not counts:
        return ""
    h = ['<div class="group" data-grp-wrap="ratio"><h3><button type="button" class="grp-tg" data-grp="ratio" '
         'aria-expanded="true">Aspect ratio' + icon("caret-down", "tg-ic") + '</button></h3><div class="rows" data-ratios>']
    for label in sorted(counts, key=ratio_value, reverse=True):
        a, b = label.split(":")
        kind = orientation(int(a), int(b))
        h.append(f'<button type="button" class="row" data-ratio="{label}" aria-pressed="false">'
                 f'<i class="rbox" data-ar="{a}/{b}"></i><span>{label}</span><span class="rsub">{kind}</span>'
                 f'<span class="n">{counts[label]}</span></button>')
    h.append("</div></div>")
    return "\n".join(h)


def load_tags():
    """Load image concept tags from the image-tags.json configuration file.

    Reads scripts/image-tags.json and returns a dictionary mapping image filenames
    to their concept tag arrays (e.g. {"blue-001.jpg": ["momentum", "clarity"]}).
    Returns an empty dict if the file does not exist. Used to populate the concept
    tag column in the agent-readable index and the tag filter UI in the gallery.
    """
    import json
    p = os.path.join(ROOT, "scripts", "image-tags.json")
    if not os.path.exists(p):
        return {}
    with open(p) as fh:
        return json.load(fh)


# Phosphor Regular icons (MIT), inlined so the page needs no icon request. 256 x 256 viewBox.
ICONS = json.loads(r'''{
"magnifying-glass": "<path d=\"M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z\"/>",
"download-simple": "<path d=\"M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,124.69V32a8,8,0,0,0-16,0v92.69L93.66,98.34a8,8,0,0,0-11.32,11.32Z\"/>",
"arrows-out": "<path d=\"M216,48V96a8,8,0,0,1-16,0V67.31l-42.34,42.35a8,8,0,0,1-11.32-11.32L188.69,56H160a8,8,0,0,1,0-16h48A8,8,0,0,1,216,48ZM98.34,146.34,56,188.69V160a8,8,0,0,0-16,0v48a8,8,0,0,0,8,8H96a8,8,0,0,0,0-16H67.31l42.35-42.34a8,8,0,0,0-11.32-11.32ZM208,152a8,8,0,0,0-8,8v28.69l-42.34-42.35a8,8,0,0,0-11.32,11.32L188.69,200H160a8,8,0,0,0,0,16h48a8,8,0,0,0,8-8V160A8,8,0,0,0,208,152ZM67.31,56H96a8,8,0,0,0,0-16H48a8,8,0,0,0-8,8V96a8,8,0,0,0,16,0V67.31l42.34,42.35a8,8,0,0,0,11.32-11.32Z\"/>",
"sun": "<path d=\"M120,40V16a8,8,0,0,1,16,0V40a8,8,0,0,1-16,0Zm72,88a64,64,0,1,1-64-64A64.07,64.07,0,0,1,192,128Zm-16,0a48,48,0,1,0-48,48A48.05,48.05,0,0,0,176,128ZM58.34,69.66A8,8,0,0,0,69.66,58.34l-16-16A8,8,0,0,0,42.34,53.66Zm0,116.68-16,16a8,8,0,0,0,11.32,11.32l16-16a8,8,0,0,0-11.32-11.32ZM192,72a8,8,0,0,0,5.66-2.34l16-16a8,8,0,0,0-11.32-11.32l-16,16A8,8,0,0,0,192,72Zm5.66,114.34a8,8,0,0,0-11.32,11.32l16,16a8,8,0,0,0,11.32-11.32ZM48,128a8,8,0,0,0-8-8H16a8,8,0,0,0,0,16H40A8,8,0,0,0,48,128Zm80,80a8,8,0,0,0-8,8v24a8,8,0,0,0,16,0V216A8,8,0,0,0,128,208Zm112-88H216a8,8,0,0,0,0,16h24a8,8,0,0,0,0-16Z\"/>",
"moon": "<path d=\"M233.54,142.23a8,8,0,0,0-8-2,88.08,88.08,0,0,1-109.8-109.8,8,8,0,0,0-10-10,104.84,104.84,0,0,0-52.91,37A104,104,0,0,0,136,224a103.09,103.09,0,0,0,62.52-20.88,104.84,104.84,0,0,0,37-52.91A8,8,0,0,0,233.54,142.23ZM188.9,190.34A88,88,0,0,1,65.66,67.11a89,89,0,0,1,31.4-26A106,106,0,0,0,96,56,104.11,104.11,0,0,0,200,160a106,106,0,0,0,14.92-1.06A89,89,0,0,1,188.9,190.34Z\"/>",
"x": "<path d=\"M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z\"/>",
"funnel-simple": "<path d=\"M200,136a8,8,0,0,1-8,8H64a8,8,0,0,1,0-16H192A8,8,0,0,1,200,136Zm32-56H24a8,8,0,0,0,0,16H232a8,8,0,0,0,0-16Zm-80,96H104a8,8,0,0,0,0,16h48a8,8,0,0,0,0-16Z\"/>",
"link": "<path d=\"M240,88.23a54.43,54.43,0,0,1-16,37L189.25,160a54.27,54.27,0,0,1-38.63,16h-.05A54.63,54.63,0,0,1,96,119.84a8,8,0,0,1,16,.45A38.62,38.62,0,0,0,150.58,160h0a38.39,38.39,0,0,0,27.31-11.31l34.75-34.75a38.63,38.63,0,0,0-54.63-54.63l-11,11A8,8,0,0,1,135.7,59l11-11A54.65,54.65,0,0,1,224,48,54.86,54.86,0,0,1,240,88.23ZM109,185.66l-11,11A38.41,38.41,0,0,1,70.6,208h0a38.63,38.63,0,0,1-27.29-65.94L78,107.31A38.63,38.63,0,0,1,144,135.71a8,8,0,0,0,16,.45A54.86,54.86,0,0,0,144,96a54.65,54.65,0,0,0-77.27,0L32,130.75A54.62,54.62,0,0,0,70.56,224h0a54.28,54.28,0,0,0,38.64-16l11-11A8,8,0,0,0,109,185.66Z\"/>",
"check": "<path d=\"M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z\"/>",
"arrow-square-out": "<path d=\"M224,104a8,8,0,0,1-16,0V59.32l-66.33,66.34a8,8,0,0,1-11.32-11.32L196.68,48H152a8,8,0,0,1,0-16h64a8,8,0,0,1,8,8Zm-40,24a8,8,0,0,0-8,8v72H48V80h72a8,8,0,0,0,0-16H48A16,16,0,0,0,32,80V208a16,16,0,0,0,16,16H176a16,16,0,0,0,16-16V136A8,8,0,0,0,184,128Z\"/>",
"caret-down": "<path d=\"M213.66,101.66l-80,80a8,8,0,0,1-11.32,0l-80-80A8,8,0,0,1,53.66,90.34L128,164.69l74.34-74.35a8,8,0,0,1,11.32,11.32Z\"/>",
"sidebar-simple": "<path d=\"M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM40,56H80V200H40ZM216,200H96V56H216V200Z\"/>"
}''')

# Dot colour per section: the palette's signature (gradient is drawn by CSS).
SWATCH = {"gradient": "", "blue": "#0200D3", "white": "#E5E7EB", "purple": "#C68FFF",
          "orange": "#F47A48", "red": "#FF2B3C", "green": "#22C36F", "yellow": "#FED340"}
# The picture each overview tile shows; the first image of the section when missing.
OVERVIEW_PICK = {"gradient": "gradient-003.jpg", "blue": "blue-014.jpg"}


def icon(name, cls=""):
    """One inline Phosphor icon as an SVG string (decorative: aria-hidden)."""
    cls = f"ic {cls}".strip()
    return f'<svg class="{cls}" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">{ICONS[name]}</svg>'


def dot(section):
    """The small colour dot for a section; painted from data-color by script (CSP)."""
    if section == "gradient":
        return '<i class="dot g"></i>'
    return f'<i class="dot" data-color="{SWATCH.get(section, "#E5E7EB")}"></i>'


def sidebar(secs):
    """The left panel: brand, theme and collapse buttons, search, colour sections,
    concepts, tools and the credit line.

    On desktop it is a sticky panel that collapses to a slim rail; on tablets and
    phones the same panel opens as a bottom sheet from the Filters button, so there
    is one set of controls. Colour rows are links to their section (they still work
    without script); the script turns them into filters.
    """
    total = sum(len(v) for v in secs.values())
    h = ['<aside id="panel" class="panel" aria-label="Find images">',
         '<div class="top"><a class="brand" href="#top"><img src="assets/logo/azmx-favicon.png" alt="">'
         '<span>AZMX Image Library</span></a>'
         '<button class="btn icon ghost" type="button" data-theme-toggle aria-label="Switch to dark mode">'
         + icon("moon", "i-moon") + icon("sun", "i-sun") + '</button>'
         '<button class="btn icon ghost pane-tg" type="button" data-pane aria-controls="panel" aria-expanded="true" '
         'aria-label="Collapse the panel" title="Collapse the panel ([)">' + icon("sidebar-simple") + '</button></div>',
         '<div class="rail"><button class="btn icon ghost" type="button" data-palette aria-label="Search images">'
         + icon("magnifying-glass") + '</button></div>',
         '<div class="sheet-head"><h2>Filters</h2><button class="btn icon ghost" type="button" data-sheet-close '
         'aria-label="Close filters">' + icon("x") + '</button></div>',
         '<div class="search" data-search>' + icon("magnifying-glass") +
         '<input type="search" placeholder="Search images" aria-label="Search images" readonly '
         'aria-haspopup="dialog" aria-keyshortcuts="Meta+K Control+K">'
         '<button class="clear" type="button" aria-label="Clear search">' + icon("x") + '</button>'
         '<kbd class="kbd" aria-hidden="true">⌘K</kbd></div>',
         '<div class="group" data-grp-wrap="colour"><h3><button type="button" class="grp-tg" data-grp="colour" '
         'aria-expanded="true">Colour' + icon("caret-down", "tg-ic") + '</button></h3><nav class="rows" aria-label="Colour sections">',
         f'<a class="row" href="#top" data-colour="" aria-current="true"><i class="dot all"></i>'
         f'<span>All images</span><span class="n">{total}</span></a>']
    for s in ORDER:
        if secs.get(s):
            h.append(f'<a class="row" href="#{s}" data-colour="{s}">{dot(s)}<span>{TITLES[s]}</span>'
                     f'<span class="n" data-count="{s}">{len(secs[s])}</span></a>')
    h.append('</nav></div>')
    h.append(ratio_filter(secs))
    h.append(tag_filter(secs))
    h.append('<nav class="tools" aria-label="More"><a href="#recolor"><span>Recolour prompts</span></a>'
             '<a href="https://github.com/Gamaleldientarek/azmx-brand"><span>The brand skill</span></a></nav>')
    h.append('<p class="credit">Designed with love by '
             '<a href="https://gamaleldien.com" target="_blank" rel="noopener">gamaleldien</a></p>')
    h.append("</aside>")
    return "\n".join(h)


def tag_filter(secs):
    """The Concept group: every concept tag with its count, as toggle buttons.

    Buttons carry aria-pressed so the state is exposed to assistive tech. Several
    concepts can be chosen at once (an image must carry all of them), and they
    combine with the search and the colour section.
    """
    tags = load_tags()
    if not tags:
        return ""
    import collections
    names = {r["f"] for rows in secs.values() for r in rows}
    counts = collections.Counter(t for fn, ts in tags.items() if not names or fn in names for t in ts)
    h = ['<div class="group concepts" data-grp-wrap="concept"><h3><button type="button" class="grp-tg" '
         'data-grp="concept" aria-expanded="true">Concept' + icon("caret-down", "tg-ic") + '</button></h3>',
         '<input class="tagfind" type="search" data-tagfind placeholder="Find a concept" aria-label="Find a concept">',
         '<div class="rows" data-concepts>']
    for t in sorted(counts):
        h.append(f'<button type="button" class="row" data-tag="{esc(t)}" aria-pressed="false">'
                 f'<span>{esc(t)}</span><span class="n">{counts[t]}</span>{icon("check", "ck")}</button>')
    h.append('</div></div>')
    return "\n".join(h)


def overview(secs, n_prompts=0):
    """"On this page": one tile per colour section (a sample picture, the name and
    the count) plus the recolour prompts. Tiles link to their section and the
    script turns them into colour filters. The row can be collapsed."""
    h = ['<nav class="overview" data-grp-wrap="overview" aria-label="Sections on this page">',
         '<h2 class="ov-t"><button type="button" class="grp-tg ov-tg" data-grp="overview" aria-expanded="true">'
         'On this page' + icon("caret-down", "tg-ic") + '</button></h2><div class="ov-grid">']
    for s in ORDER:
        rows = secs.get(s, [])
        if not rows:
            continue
        pick = next((r for r in rows if r["f"] == OVERVIEW_PICK.get(s)), rows[0])
        src = esc(f"{GALLERY_CDN}/{s}/{pick['f']}")
        h.append(f'<a class="ov" href="#{s}" data-colour="{s}"><img src="{src}" alt="" loading="lazy">'
                 f'<span class="ov-c"><span>{TITLES[s]}</span><span class="n">{len(rows)}</span></span></a>')
    if n_prompts:
        h.append(f'<a class="ov ov-tool" href="#recolor"><span class="ov-art">{n_prompts} prompts</span>'
                 f'<span class="ov-c"><span>Recolour prompts</span></span></a>')
    h.append("</div></nav>")
    return "\n".join(h)


GALLERY_CSS = """:root{--font-display:"thmanyah serif display",Georgia,serif;--font-body:"Azm X",-apple-system,"Segoe UI",Tahoma,sans-serif;
--surface-page:#FFFFFF;--surface-subtle:#F9FAFB;--popover:#FFFFFF;--text-primary:#111927;--text-heading:#111927;--text-secondary:#4D5761;
--text-muted:#6C737F;--text-accent:#001AFF;--border-subtle:#E5E7EB;--primary:#000000;--primary-foreground:#FFFFFF;--ring:#001AFF;
--field:#F3F4F6;--field-hover:#E5E7EB;--placeholder:#F3F4F6;--scrim:rgba(0,0,0,.6);--shadow:0 24px 64px rgba(17,25,39,.18);color-scheme:light}
.dark{--surface-page:#000000;--surface-subtle:#000000;--popover:#111927;--text-primary:#FFFFFF;--text-heading:#FFFFFF;--text-secondary:#DDE8FF;
--text-muted:#93B6FF;--text-accent:#5D8FFF;--border-subtle:rgba(255,255,255,.2);--primary:#FFFFFF;--primary-foreground:#000000;--ring:#5D8FFF;
--field:#111927;--field-hover:#1F2A37;--placeholder:#111927;--shadow:0 24px 64px rgba(0,0,0,.6);color-scheme:dark}
*{box-sizing:border-box}
html{background:var(--surface-page);color:var(--text-primary)}
body{margin:0;font-family:var(--font-body);font-size:15px;line-height:1.5;letter-spacing:0;-webkit-font-smoothing:antialiased;
display:grid;grid-template-columns:296px minmax(0,1fr);min-height:100vh;transition:grid-template-columns .2s ease}
button,input{font:inherit;color:inherit;letter-spacing:0}
a{color:inherit}
.ic{width:20px;height:20px;flex:none}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
:focus-visible{outline:2px solid var(--ring);outline-offset:2px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:40px;padding:0 14px;border-radius:8px;
border:1px solid var(--border-subtle);background:transparent;cursor:pointer;font-size:14px;text-decoration:none;white-space:nowrap;transition:background .15s,transform .1s}
.btn:hover{background:var(--field)}
.btn:active{transform:scale(.96)}
.btn.primary{background:var(--primary);color:var(--primary-foreground);border-color:var(--primary)}
.btn.primary:hover{opacity:.88}
.btn.icon{width:40px;padding:0}
.btn.ghost{border-color:transparent}
.i-sun,.dark .i-moon{display:none}.dark .i-sun{display:block}
.chip{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;border-radius:8px;border:0;background:var(--field);
font-size:13px;color:var(--text-secondary);cursor:pointer}
.chip:hover{background:var(--field-hover);color:var(--text-primary)}
.chip.x{background:var(--primary);color:var(--primary-foreground)}
.chip .ic{width:14px;height:14px}
.dot{width:12px;height:12px;border-radius:999px;flex:none;box-shadow:inset 0 0 0 1px var(--border-subtle)}
.dot.g{background:linear-gradient(145deg,#000 0%,#01006E 55%,#001AFF 100%)}
.dot.all{background:var(--field-hover)}
/* Panel */
.panel{position:sticky;top:0;height:100vh;display:flex;flex-direction:column;gap:20px;padding:20px 16px 20px 20px;
background:var(--surface-subtle);border-inline-end:1px solid var(--border-subtle);overflow-y:auto;z-index:30}
.panel>*{flex-shrink:0}
.top{display:flex;align-items:center;gap:4px}
.brand{display:flex;align-items:center;gap:8px;margin-inline-end:auto;min-width:0;white-space:nowrap;overflow:hidden;
font-size:15px;font-weight:500;text-decoration:none}
.brand img{width:24px;height:24px;border-radius:6px;flex:none}
.rail,.sheet-head{display:none}
.search{position:relative;display:flex;align-items:center}
.search>.ic{position:absolute;inset-inline-start:14px;color:var(--text-muted);pointer-events:none}
.search input{width:100%;height:44px;padding:0 64px 0 44px;border:1px solid transparent;border-radius:8px;background:var(--field);
color:var(--text-primary);cursor:pointer;outline:none}
.search input::placeholder{color:var(--text-muted)}
.search input:hover{background:var(--field-hover)}
.search input:focus-visible{border-color:var(--ring)}
.search .clear{position:absolute;inset-inline-end:4px;width:36px;height:36px;border:0;border-radius:8px;background:transparent;
display:none;align-items:center;justify-content:center;cursor:pointer;color:var(--text-secondary)}
.search .clear:hover{background:var(--field-hover)}
.search.has .clear{display:inline-flex}
.kbd{position:absolute;inset-inline-end:10px;height:24px;padding:0 8px;display:inline-flex;align-items:center;border-radius:4px;
font:500 12px/1 var(--font-body);color:var(--text-muted);background:var(--surface-page);border:1px solid var(--border-subtle);pointer-events:none}
.search.has .kbd{display:none}
.group h3{margin:0 0 4px}
.grp-tg{display:flex;align-items:center;justify-content:space-between;gap:8px;width:100%;padding:4px 12px;border:0;border-radius:8px;
background:transparent;cursor:pointer;font-size:14px;font-weight:500;color:var(--text-secondary);text-align:start}
.grp-tg:hover{background:var(--field);color:var(--text-primary)}
.tg-ic{width:16px;height:16px;color:var(--text-muted);transition:transform .15s}
.closed>h3 .tg-ic,.closed>h2 .tg-ic,.sec.closed .sec-tg .tg-ic{transform:rotate(-90deg)}
.closed>h3~*,.overview.closed .ov-grid{display:none!important}
.rows{display:flex;flex-direction:column;gap:2px}
.row{display:flex;align-items:center;gap:12px;width:100%;min-height:36px;padding:0 12px;border:0;border-radius:8px;background:transparent;
cursor:pointer;text-align:start;font-size:14px;text-decoration:none;transition:background .15s,transform .1s}
.row:hover{background:var(--field)}
.row:active{transform:scale(.98)}
.row .n,.ov-c .n{margin-inline-start:auto;font-size:12px;color:var(--text-muted);font-variant-numeric:tabular-nums}
.row[aria-current="true"],.row[aria-pressed="true"]{background:var(--primary);color:var(--primary-foreground)}
.row[aria-current="true"] .n,.row[aria-pressed="true"] .n{color:inherit;opacity:.6}
.row.off{opacity:.35;pointer-events:none}
.row .rsub{font-size:12px;color:var(--text-muted)}
.row[aria-pressed="true"] .rsub{color:inherit;opacity:.7}
.rbox{width:14px;max-height:20px;flex:none;border-radius:2px;box-shadow:inset 0 0 0 1.5px currentColor;opacity:.7}
.ratio{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:4px;background:var(--field);
font-size:12px;color:var(--text-secondary);font-variant-numeric:tabular-nums}
.row .ck{width:16px;height:16px;display:none}
.row[aria-pressed="true"] .ck{display:block}
.concepts{flex:1 0 auto;min-height:240px;display:flex;flex-direction:column}
.concepts.closed{flex:none}
.concepts .rows{flex:1 1 0;min-height:160px;overflow-y:auto;padding-inline-end:4px;margin-top:4px}
.tagfind{width:100%;height:36px;padding:0 12px;border-radius:8px;border:1px solid var(--border-subtle);background:transparent;outline:none}
.tagfind:focus{border-color:var(--ring)}
.tools{display:flex;flex-direction:column;gap:2px;padding-top:12px;border-top:1px solid var(--border-subtle)}
.tools a{display:flex;align-items:center;min-height:36px;padding:0 12px;border-radius:8px;text-decoration:none;font-size:14px;color:var(--text-secondary)}
.tools a:hover{background:var(--field);color:var(--text-primary)}
.credit{margin:-8px 0 0;padding:0 12px;font-size:13px;color:var(--text-muted)}
.credit a{color:var(--text-secondary);text-decoration:underline;text-underline-offset:.4em;text-decoration-thickness:1px}
.credit a:hover{color:var(--text-primary)}
/* Collapsed panel: a slim rail (desktop) */
@media (min-width:1024px){
  .pane-closed body{grid-template-columns:72px minmax(0,1fr)}
  .pane-closed .panel{padding:20px 12px;align-items:center}
  .pane-closed .panel>*:not(.top):not(.rail){display:none!important}
  .pane-closed .top{flex-direction:column;gap:8px}
  .pane-closed .brand{margin:0 0 8px}
  .pane-closed .brand span{display:none}
  .pane-closed .rail{display:flex;flex-direction:column;gap:8px}
  .pane-closed .pane-tg .ic{transform:scaleX(-1)}
}
/* Main */
main{min-width:0;padding:64px 48px 120px}
.mtop,.mbar{display:none}
.head{max-width:960px;margin-bottom:32px}
.eyebrow{margin:0;color:var(--text-accent);font-size:14px;font-weight:500;line-height:1.4}
h1{font-family:var(--font-display);font-weight:400;font-size:clamp(40px,5vw,64px);line-height:1.05;letter-spacing:0;margin:12px 0 16px;color:var(--text-heading)}
.lede{margin:0;max-width:62ch;color:var(--text-secondary);font-size:17px;line-height:1.6}
.lede+.lede{margin-top:12px}
.meta{margin:12px 0 0;color:var(--text-muted);font-size:14px;font-variant-numeric:tabular-nums}
.overview{margin:0 0 32px}
.ov-t{margin:0 0 8px;font:inherit}
.ov-tg{display:inline-flex;width:auto;justify-content:flex-start;padding:4px 8px;margin-inline-start:-8px}
.ov-grid{display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:12px}
.ov{display:flex;flex-direction:column;border-radius:12px;text-decoration:none;transition:transform .1s}
.ov:active{transform:scale(.97)}
.ov img,.ov-art{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:12px 12px 0 0;background:var(--placeholder)}
.ov-art{display:flex;align-items:flex-end;padding:12px;font-family:var(--font-display);font-size:18px;line-height:1.1;color:var(--text-heading)}
.ov-c{display:flex;align-items:center;gap:6px;min-height:36px;padding:8px 10px;border-radius:0 0 12px 12px;background:var(--field);font-size:13px;font-weight:500}
.ov-c>span:first-child{min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.ov:hover .ov-c{background:var(--field-hover)}
.ov[aria-current="true"] .ov-c{background:var(--primary);color:var(--primary-foreground)}
.ov[aria-current="true"] .n{color:inherit;opacity:.6}
.bar{position:sticky;top:0;z-index:10;display:flex;flex-wrap:wrap;align-items:center;gap:8px;min-height:64px;padding:12px 0;margin-bottom:8px;background:var(--surface-page)}
.bar .count{margin-inline-end:8px;font-weight:500}
.bar .end{margin-inline-start:auto;display:flex;gap:4px}
.sec{margin-top:40px}
.sec h2{margin:0 0 4px;font-family:var(--font-display);font-weight:500;font-size:32px;line-height:1.2;letter-spacing:0}
.sec-tg{display:inline-flex;align-items:center;gap:10px;padding:4px 10px 4px 4px;margin-inline-start:-4px;border:0;border-radius:8px;
background:transparent;cursor:pointer;font:inherit;color:var(--text-heading);text-align:start}
.sec-tg:hover{background:var(--field)}
.sec-tg .tg-ic{width:20px;height:20px}
.sec-tg .n{font-family:var(--font-body);font-size:14px;font-weight:400;color:var(--text-muted)}
.sec .note{margin:0 0 20px;color:var(--text-secondary);font-size:14px}
.sec.closed .sec-body,.sec[hidden],figure[hidden]{display:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:32px 24px}
figure{margin:0}
.shot{position:relative;display:block;line-height:0}
a.card{display:block;border-radius:12px}
.grid img{display:block;width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:12px;background:var(--placeholder);transition:opacity .15s}
a.card:hover img{opacity:.9}
figure[aria-current="true"] img{outline:3px solid var(--text-primary);outline-offset:3px}
figcaption{display:flex;align-items:center;gap:4px;padding-top:10px}
figcaption .name{margin-inline-end:8px;font-size:14px;font-weight:500;font-variant-numeric:tabular-nums}
figcaption .hi,figcaption .dl{margin-inline-start:auto}
figcaption .hi+.dl{margin-inline-start:0}
.hi,.dl{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 10px;border-radius:8px;font-size:13px;text-decoration:none;
color:var(--text-secondary);transition:background .15s}
.dl{width:32px;padding:0;justify-content:center}
.hi:hover,.dl:hover{background:var(--field);color:var(--text-primary)}
.hi .ic,.dl .ic{width:16px;height:16px}
.reload{position:absolute;left:12px;bottom:12px;color:#fff;font-size:13px;text-decoration:underline;text-underline-offset:.4em;line-height:1.4}
.empty{padding:48px 0;color:var(--text-secondary);max-width:46ch}
.empty strong{display:block;font-family:var(--font-display);font-weight:400;font-size:28px;color:var(--text-heading);margin-bottom:8px}
/* Recolour prompts */
#recolor{margin-top:120px;padding-top:48px;border-top:1px solid var(--border-subtle)}
#recolor h2{margin:0 0 8px;font-family:var(--font-display);font-weight:500;font-size:32px;letter-spacing:0}
.sub{margin:0 0 24px;max-width:72ch;color:var(--text-secondary);font-size:15px;line-height:1.6}
code{padding:2px 8px;border-radius:4px;background:var(--field);font-size:13px}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:24px}
.pcard{display:flex;flex-direction:column;gap:12px;padding:20px;border:1px solid var(--border-subtle);border-radius:12px}
.phead{display:flex;align-items:center;justify-content:space-between;gap:12px}
.pname{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:600}
.pdot{width:14px;height:14px;flex:none;border-radius:4px;box-shadow:inset 0 0 0 1px var(--border-subtle)}
.psum{margin:-4px 0 0;color:var(--text-secondary);font-size:13px}
.ptext{max-height:176px;overflow-y:auto;margin:0;padding:12px 8px 12px 16px;border-radius:8px;background:var(--field);white-space:pre-wrap;
color:var(--text-secondary);font-size:13.5px;line-height:1.65}
.copy{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 16px;flex:none;
border:1px solid var(--border-subtle);border-radius:8px;background:transparent;cursor:pointer;font-size:13px;transition:background .18s,color .18s}
.copy:hover{background:var(--field)}
.copy[data-copied="1"]{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}
.copy svg{width:14px;height:14px;flex:none}
footer{margin-top:80px;padding-top:32px;border-top:1px solid var(--border-subtle);color:var(--text-secondary);font-size:14px;line-height:1.8}
footer code{white-space:normal;word-break:break-all}
a.link{color:var(--text-accent)}
/* Details drawer */
.drawer{position:fixed;top:0;inset-inline-end:0;bottom:0;z-index:45;width:440px;display:none;flex-direction:column;
background:var(--surface-page);border-inline-start:1px solid var(--border-subtle);box-shadow:var(--shadow)}
.drawer.open{display:flex}
.drawer-on main{margin-inline-end:440px}
.drawer-on .ov-grid{grid-template-columns:repeat(5,minmax(0,1fr))}
.dh{display:flex;align-items:center;justify-content:space-between;padding:16px 16px 0 24px}
.dh h2{margin:0;font-family:var(--font-display);font-weight:500;font-size:24px;letter-spacing:0}
.db{display:flex;flex-direction:column;gap:20px;padding:16px 24px 32px;overflow-y:auto}
.db img{display:block;width:100%;max-height:46vh;object-fit:contain;border-radius:12px;background:var(--placeholder)}
.acts{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.acts .primary{grid-column:1/-1;width:auto;height:48px;padding:0 14px;color:var(--primary-foreground)}
.acts .primary:hover{background:var(--primary);color:var(--primary-foreground)}
.acts .hires{grid-column:1/-1}
.acts .ic{width:20px;height:20px}
.db h3{margin:0 0 8px;font-size:14px;font-weight:500;color:var(--text-secondary)}
.tagrow{display:flex;flex-wrap:wrap;gap:6px}
.facts{display:grid;grid-template-columns:128px 1fr;gap:10px 16px;margin:0;font-size:14px}
.facts dt{color:var(--text-secondary)}
.facts dd{display:flex;align-items:center;gap:8px;margin:0}
.facts .sw{width:16px;height:16px;border-radius:4px;flex:none;box-shadow:inset 0 0 0 1px var(--border-subtle)}
.quiet{margin:0;font-size:13px;color:var(--text-muted)}
/* Search palette */
.pal-wrap{position:fixed;inset:0;z-index:60;display:none;align-items:flex-start;justify-content:center;padding:14vh 16px 16px;background:var(--scrim)}
.pal-wrap.open{display:flex}
.pal{display:flex;flex-direction:column;width:min(640px,100%);max-height:72vh;overflow:hidden;border-radius:16px;background:var(--popover);box-shadow:var(--shadow)}
.dark .pal{border:1px solid var(--border-subtle)}
.pal-in{display:flex;align-items:center;gap:12px;height:64px;padding:0 16px 0 20px;border-bottom:1px solid var(--border-subtle)}
.pal-in .ic{color:var(--text-muted)}
.pal-in input{flex:1;height:100%;border:0;outline:none;background:transparent;font-size:18px}
.pal-in input::-webkit-search-cancel-button{display:none}
.pal kbd{display:inline-flex;align-items:center;justify-content:center;height:22px;min-width:22px;padding:0 6px;border-radius:4px;
border:1px solid var(--border-subtle);font:500 12px/1 var(--font-body);color:var(--text-muted)}
.pal-list{padding:8px;overflow-y:auto}
.pal-g{margin:12px 12px 4px;font-size:13px;font-weight:500;color:var(--text-muted)}
.pal-g:first-child{margin-top:4px}
.pal-row{display:flex;align-items:center;gap:12px;width:100%;min-height:44px;padding:6px 12px;border:0;border-radius:8px;background:transparent;cursor:pointer;text-align:start;font-size:15px}
.pal-row.act,.pal-row:hover{background:var(--field)}
.pal-row .ic{width:18px;height:18px;color:var(--text-muted)}
.pal-row img{width:64px;height:40px;flex:none;object-fit:cover;border-radius:6px;background:var(--placeholder)}
.pal-row b{display:block;font-weight:500}
.pal-row em{display:block;font-style:normal;font-size:13px;color:var(--text-secondary)}
.pal-n{margin-inline-start:auto;white-space:nowrap;font-size:13px;color:var(--text-muted);font-variant-numeric:tabular-nums}
.pal-hash{width:18px;text-align:center;color:var(--text-muted)}
.pal-empty{margin:0;padding:24px 12px;color:var(--text-secondary)}
.pal-foot{display:flex;gap:20px;padding:10px 20px;border-top:1px solid var(--border-subtle);font-size:13px;color:var(--text-muted)}
.pal-foot span{display:inline-flex;align-items:center;gap:6px}
.scrim{position:fixed;inset:0;z-index:40;display:none;background:var(--scrim)}
@media (max-width:1279px){.ov-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
@media (max-width:1023px){
  body,.pane-closed body{display:block}
  main{padding:0 20px 80px}
  .mtop{display:flex;align-items:center;justify-content:space-between;padding:16px 0 0}
  .mbar{position:sticky;top:0;z-index:20;display:flex;gap:8px;align-items:center;padding:12px 0;background:var(--surface-page)}
  .mbar .search{flex:1}
  .mbar .btn{height:44px}
  .head{margin:24px 0}
  .bar{position:static;min-height:0;padding:4px 0}
  .grid{grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:24px 12px}
  figcaption{flex-wrap:wrap;row-gap:4px}
  figcaption .name{font-size:13px}
  figcaption .hi{width:32px;padding:0;justify-content:center;font-size:0;gap:0}
  .panel{position:fixed;inset:auto 0 0 0;height:auto;max-height:86vh;z-index:50;padding:8px 20px 32px;align-items:stretch;
  border:0;border-radius:16px 16px 0 0;background:var(--surface-page);overflow-y:auto;transform:translateY(100%);visibility:hidden;transition:transform .2s,visibility .2s}
  .sheet-open .panel{transform:none;visibility:visible}
  .sheet-open .scrim,.drawer-on .scrim{display:block}
  .panel>.top,.panel>.rail,.panel>.search{display:none!important}
  .panel .sheet-head{display:flex;align-items:center;justify-content:space-between;position:sticky;top:-8px;padding:8px 0;background:var(--surface-page);z-index:1}
  .sheet-head h2{margin:0;font-family:var(--font-display);font-weight:500;font-size:22px}
  .panel>*{flex-shrink:0}
  .concepts{flex:none}
  .concepts .rows{overflow:visible}
  .row{min-height:48px}
  .drawer{top:auto;width:100%;max-height:92vh;border:0;border-radius:16px 16px 0 0}
  .drawer-on main{margin-inline-end:0}
}
@media (max-width:640px){
  .ov-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
  .ov-c{padding:6px 8px;font-size:12px}
  .pal-wrap{padding:0;align-items:stretch}.pal{max-height:none;border-radius:0}.pal-foot{display:none}
}
@media (hover:none),(max-width:640px){.kbd{display:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}"""


# Runs in <head> before the first paint, so a saved dark theme or collapsed panel never flashes.
THEME_SCRIPT = """(function(){var d=document.documentElement;try{
if(localStorage.getItem('azmx-library-theme')==='dark')d.classList.add('dark');
if(localStorage.getItem('azmx-library-pane')==='1')d.classList.add('pane-closed');}catch(e){}})();"""


COPY_SCRIPT = """document.querySelectorAll('.copy').forEach(function(btn){
  btn.addEventListener('click', function(){
    var key = btn.dataset.prompt;
    var text = document.getElementById('prompt-' + key).textContent;
    var label = btn.querySelector('.copy-label');
    var done = function(){
      label.textContent = 'Copied';
      btn.dataset.copied = '1';
      document.getElementById('copy-status').textContent = key + ' prompt copied to clipboard';
      setTimeout(function(){
        label.textContent = 'Copy';
        btn.removeAttribute('data-copied');
      }, 2000);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(fallback);
    } else { fallback(); }
    function fallback(){
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly','');
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); }
      catch (e) { label.textContent = 'Select manually'; }
      document.body.removeChild(ta);
    }
  });
});"""


APP_SCRIPT = """(function(){
  var ICON = __ICONS__, TITLES = __TITLES__, ORDER = __ORDER__, NOTE = __NOTE__;
  var D = document, H = D.documentElement, mac = /Mac|iPhone|iPad/.test(navigator.platform);
  function $(s, r){ return (r || D).querySelector(s); }
  function $$(s, r){ return Array.prototype.slice.call((r || D).querySelectorAll(s)); }
  function icon(n, c){ return '<svg class="ic ' + (c || '') + '" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">' + (ICON[n] || '') + '</svg>'; }
  function esc(s){ return String(s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function store(k, v){ try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} }

  // Colours are painted from data-color: a hash-based CSP blocks inline style="".
  function paint(root){ $$('[data-color]', root).forEach(function(el){
    if (/^#[0-9A-Fa-f]{6}$/.test(el.dataset.color)) el.style.background = el.dataset.color; }); }
  paint();
  $$('.rbox[data-ar]').forEach(function(b){ if (/^\\d+\\/\\d+$/.test(b.dataset.ar)) b.style.aspectRatio = b.dataset.ar; });
  if (!mac) $$('.kbd, .kbd-k').forEach(function(k){ k.textContent = 'Ctrl K'; });

  // The library, read from the cards the page already shows.
  var LIB = $$('figure[data-f]').map(function(f){
    var tags = f.dataset.tags ? f.dataset.tags.split(' ') : [], hi = $('.hi', f);
    var rt = f.dataset.ratio || '', w = +f.dataset.w || 0, hh = +f.dataset.h || 0;
    var ori = !w ? '' : (w > hh * 1.05 ? 'landscape' : (hh > w * 1.05 ? 'portrait' : 'square'));
    return { el: f, f: f.dataset.f, s: f.dataset.s, t: tags, dom: f.dataset.dom, tok: f.dataset.tok, L: +f.dataset.l,
      r: rt, w: w, hgt: hh, ori: ori,
      url: $('a.card', f).href, hi: hi ? { href: hi.href, title: hi.title } : null,
      h: (f.dataset.f.replace('.jpg', '') + ' ' + f.dataset.s + ' ' + (TITLES[f.dataset.s] || '') + ' ' + tags.join(' ') + ' ' + rt + ' ' + ori).toLowerCase() };
  });
  var S = { q: '', colour: '', ratio: '', tags: [] }, cur = null;
  function words(){ return S.q.toLowerCase().split(/\\s+/).filter(Boolean); }
  function match(i, skip){
    if (skip !== 'colour' && S.colour && i.s !== S.colour) return false;
    if (skip !== 'ratio' && S.ratio && i.r !== S.ratio) return false;
    if (skip !== 'tags') for (var k = 0; k < S.tags.length; k++) if (i.t.indexOf(S.tags[k]) < 0) return false;
    var w = words(); for (var j = 0; j < w.length; j++) if (i.h.indexOf(w[j]) < 0) return false;
    return true;
  }
  function filtered(){ return !!(S.q || S.colour || S.ratio || S.tags.length); }

  // Address bar holds the view, so a filtered view can be shared.
  (function(){ var p = new URLSearchParams(location.search);
    S.q = p.get('q') || ''; S.colour = ORDER.indexOf(p.get('colour')) > -1 ? p.get('colour') : '';
    S.ratio = LIB.some(function(i){ return i.r && i.r === p.get('ratio'); }) ? p.get('ratio') : '';
    S.tags = (p.get('tags') || '').split(',').filter(function(t){ return t && LIB.some(function(i){ return i.t.indexOf(t) > -1; }); }); })();
  function writeUrl(){ var p = new URLSearchParams(location.search); ['q', 'colour', 'ratio', 'tags', 'open'].forEach(function(k){ p.delete(k); });
    if (S.q) p.set('q', S.q); if (S.colour) p.set('colour', S.colour); if (S.ratio) p.set('ratio', S.ratio); if (S.tags.length) p.set('tags', S.tags.join(','));
    if (cur) p.set('open', cur.f); var s = p.toString();
    history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + location.hash); }

  function render(){
    var shown = 0, secs = {};
    LIB.forEach(function(i){ var m = match(i); i.el.hidden = !m; if (m) { shown++; secs[i.s] = (secs[i.s] || 0) + 1; } });
    var open = [];
    $$('section.sec').forEach(function(sec){ var n = secs[sec.id] || 0; sec.hidden = !n; $('.sec-tg .n', sec).textContent = n; if (n) open.push(sec.id); });
    var cc = {}; LIB.forEach(function(i){ if (match(i, 'colour')) cc[i.s] = (cc[i.s] || 0) + 1; });
    var all = 0; ORDER.forEach(function(k){ all += cc[k] || 0; });
    $$('[data-colour]').forEach(function(a){ var k = a.dataset.colour, on = S.colour === k;
      a.setAttribute('aria-current', on ? 'true' : 'false');
      var n = $('.n', a); if (n && a.classList.contains('row')) n.textContent = k ? (cc[k] || 0) : all;
      if (a.classList.contains('row')) a.classList.toggle('off', !!k && !cc[k] && !on); });
    var rc = {}; LIB.forEach(function(i){ if (i.r && match(i, 'ratio')) rc[i.r] = (rc[i.r] || 0) + 1; });
    $$('[data-ratios] .row').forEach(function(b){ var k = b.dataset.ratio, on = S.ratio === k;
      b.setAttribute('aria-pressed', on ? 'true' : 'false'); $('.n', b).textContent = rc[k] || 0; b.classList.toggle('off', !rc[k] && !on); });
    var tc = {}; LIB.forEach(function(i){ if (match(i, 'tags') && S.tags.every(function(t){ return i.t.indexOf(t) > -1; })) i.t.forEach(function(t){ tc[t] = (tc[t] || 0) + 1; }); });
    var tq = ($('[data-tagfind]') || {}).value || '', box = $('[data-concepts]');
    if (box) { $$('[data-concepts] .row').forEach(function(b){ var t = b.dataset.tag, on = S.tags.indexOf(t) > -1;
        b.setAttribute('aria-pressed', on ? 'true' : 'false'); $('.n', b).textContent = tc[t] || 0;
        b.hidden = !on && (!tc[t] || (tq && t.indexOf(tq.toLowerCase()) < 0)); });
      S.tags.slice().reverse().forEach(function(t){ var b = $('[data-concepts] [data-tag="' + CSS.escape(t) + '"]'); if (b) box.insertBefore(b, box.firstChild); }); }
    var b = '<span class="count">' + shown + ' of ' + LIB.length + ' images</span>';
    if (S.q) b += '<button class="chip x" type="button" data-rm="q">\\u201c' + esc(S.q) + '\\u201d' + icon('x') + '</button>';
    if (S.colour) b += '<button class="chip x" type="button" data-rm="colour">' + esc(TITLES[S.colour]) + icon('x') + '</button>';
    if (S.ratio) b += '<button class="chip x" type="button" data-rm="ratio">' + esc(S.ratio) + icon('x') + '</button>';
    S.tags.forEach(function(t){ b += '<button class="chip x" type="button" data-rm-tag="' + esc(t) + '">' + esc(t) + icon('x') + '</button>'; });
    b += '<span class="end">';
    if (filtered()) b += '<button class="btn ghost" type="button" data-clear>Clear all</button>';
    if (open.length > 1) { var allClosed = open.every(function(k){ return $('#' + k).classList.contains('closed'); });
      b += '<button class="btn ghost" type="button" data-allsec="' + open.join(',') + '" data-open="' + allClosed + '">' +
        icon('caret-down', 'tg-ic') + (allClosed ? 'Expand all' : 'Collapse all') + '</button>'; }
    $('[data-bar]').innerHTML = b + '</span>';
    $('#empty').hidden = shown > 0;
    $('#filter-status').textContent = shown + ' images shown';
    $$('[data-search]').forEach(function(s){ $('input', s).value = S.q; s.classList.toggle('has', !!S.q); });
    var nf = (S.colour ? 1 : 0) + (S.ratio ? 1 : 0) + S.tags.length, fb = $('[data-sheet-open]');
    if (fb) fb.innerHTML = icon('funnel-simple') + 'Filters' + (nf ? ' (' + nf + ')' : '');
    writeUrl();
  }

  // Theme: light by default, dark on request, remembered on this device.
  function syncTheme(){ var dk = H.classList.contains('dark');
    $$('[data-theme-toggle]').forEach(function(t){ t.setAttribute('aria-label', dk ? 'Switch to light mode' : 'Switch to dark mode');
      t.setAttribute('aria-pressed', dk ? 'true' : 'false'); }); }
  syncTheme();

  // Collapsible sections and groups, remembered on this device.
  var closed = {}; (store('azmx-library-closed') || '').split(',').forEach(function(k){
    if (/^(sec|grp):[a-z]+$/.test(k) && (k.indexOf('sec:') ? $('[data-grp-wrap="' + k.slice(4) + '"]') : D.getElementById(k.slice(4)))) closed[k] = 1; });
  function setClosed(k, c){ if (c) closed[k] = 1; else delete closed[k]; var id = k.slice(4);
    if (k.indexOf('sec:') === 0) { var s = D.getElementById(id); if (!s) return; s.classList.toggle('closed', c);
      $('.sec-tg', s).setAttribute('aria-expanded', c ? 'false' : 'true'); }
    else $$('[data-grp-wrap="' + id + '"]').forEach(function(g){ g.classList.toggle('closed', c);
      $$('[data-grp="' + id + '"]', g).forEach(function(x){ x.setAttribute('aria-expanded', c ? 'false' : 'true'); }); });
    store('azmx-library-closed', Object.keys(closed).join(',')); }
  Object.keys(closed).forEach(function(k){ setClosed(k, true); });

  // Collapsible panel (desktop) and the Filters sheet (tablet and phone).
  function setPane(c){ H.classList.toggle('pane-closed', c); var t = $('[data-pane]');
    t.setAttribute('aria-expanded', c ? 'false' : 'true'); t.setAttribute('aria-label', c ? 'Expand the panel' : 'Collapse the panel');
    t.title = (c ? 'Expand the panel' : 'Collapse the panel') + ' ([)'; store('azmx-library-pane', c ? '1' : '0'); }
  setPane(H.classList.contains('pane-closed'));
  var sheetFrom = null;
  function sheet(open){ H.classList.toggle('sheet-open', open);
    if (open) { sheetFrom = D.activeElement; setTimeout(function(){ var f = $('.panel [data-sheet-close]'); if (f) f.focus(); }, 50); }
    else if (sheetFrom) sheetFrom.focus(); }

  // Details drawer: everything about one image in one place.
  var drawer = $('#drawer'), drawerFrom = null;
  function openDrawer(i){
    if (!cur) drawerFrom = D.activeElement;
    cur = i; LIB.forEach(function(x){ x.el.setAttribute('aria-current', x === i ? 'true' : 'false'); });
    var name = i.f.replace('.jpg', ''), light = i.L >= 0.18;
    drawer.innerHTML = '<div class="dh"><h2 id="drawer-t">' + esc(name) + '</h2><button class="btn icon ghost" type="button" data-close-drawer aria-label="Close details">' + icon('x') + '</button></div>' +
      '<div class="db"><img src="' + esc(i.url) + '" alt="' + esc(i.t.join(', ') || i.f) + '">' +
      '<div class="acts"><a class="dl btn primary" href="' + esc(i.url) + '" download="' + esc(i.f) + '">' + icon('download-simple') + 'Download JPG, 1600 px</a>' +
      (i.hi ? '<a class="btn hires" href="' + esc(i.hi.href) + '" target="_blank" rel="noopener" title="' + esc(i.hi.title) + '">' + icon('arrows-out') + 'High-res original</a>' : '') +
      '<a class="btn" href="' + esc(i.url) + '" target="_blank" rel="noopener">' + icon('arrow-square-out') + 'Open full size</a>' +
      '<button class="btn" type="button" data-copy="' + esc(i.url) + '">' + icon('link') + 'Copy link</button></div>' +
      (i.hi ? '<p class="quiet">' + esc(i.hi.title.replace(/^High-res original · /, '')) + '</p>' : '<p class="quiet">No high-res original yet.</p>') +
      '<div><h3>Concepts</h3><div class="tagrow">' + i.t.map(function(t){ return '<button class="chip" type="button" data-tag="' + esc(t) + '">' + esc(t) + '</button>'; }).join('') + '</div></div>' +
      '<dl class="facts"><dt>Colour section</dt><dd>' + (i.s === 'gradient' ? '<i class="dot g"></i>' : '<i class="dot" data-color="' + esc(($('[data-colour="' + i.s + '"] .dot') || {dataset:{}}).dataset.color || '') + '"></i>') + esc(TITLES[i.s] || i.s) + '</dd>' +
      '<dt>Dominant colour</dt><dd><i class="sw" data-color="' + esc(i.dom) + '"></i>' + esc(i.dom) + '</dd>' +
      (i.w ? '<dt>Aspect ratio</dt><dd>' + esc(i.r) + ', ' + esc(i.ori) + '</dd><dt>Size</dt><dd>' + i.w + ' \u00d7 ' + i.hgt + ' px</dd>' : '') +
      '<dt>Nearest token</dt><dd>' + esc(i.tok) + '</dd>' +
      '<dt>Text on top</dt><dd>' + (light ? 'Neutral 900 text, Electric accent' : 'White title, Blue 100 body, Light Blue eyebrow') + '</dd></dl></div>';
    paint(drawer); drawer.classList.add('open'); H.classList.add('drawer-on'); writeUrl();
    $('[data-close-drawer]', drawer).focus();
  }
  function closeDrawer(){ if (!cur) return; cur.el.setAttribute('aria-current', 'false'); cur = null; drawer.classList.remove('open');
    H.classList.remove('drawer-on'); writeUrl(); if (drawerFrom && drawerFrom.focus) drawerFrom.focus(); }

  // Search palette: ⌘K / Ctrl K, "/" or a click on the search field opens it, centred.
  var pal = $('#palette'), pin = $('input', pal), plist = $('.pal-list', pal), items = [], idx = -1, palFrom = null;
  function prow(kind, val, inner){ items.push({ kind: kind, val: val });
    return '<button type="button" class="pal-row" role="option" id="pal-' + (items.length - 1) + '" data-k="' + (items.length - 1) + '">' + inner + '</button>'; }
  function group(t, rows){ return rows.length ? '<p class="pal-g">' + t + '</p>' + rows.join('') : ''; }
  function drawPal(){
    var q = pin.value.trim().toLowerCase(), w = q.split(/\\s+/).filter(Boolean), h = ''; items = [];
    var hits = LIB.filter(function(i){ return w.every(function(x){ return i.h.indexOf(x) > -1; }); });
    if (q) h += group('Search', [prow('query', pin.value.trim(), icon('magnifying-glass') + '<span>Show every image matching \\u201c' + esc(pin.value.trim()) + '\\u201d</span><span class="pal-n">' + hits.length + '</span>')]);
    var cc = {}; LIB.forEach(function(i){ cc[i.s] = (cc[i.s] || 0) + 1; });
    h += group('Colour', ORDER.filter(function(k){ return cc[k] && (!q || (k + ' ' + TITLES[k].toLowerCase()).indexOf(q) > -1); }).map(function(k){
      var d = $('[data-colour="' + k + '"] .dot'); return prow('colour', k, (d ? d.outerHTML : '') + '<span>' + esc(TITLES[k]) + '</span><span class="pal-n">' + cc[k] + '</span>'); }));
    var tc = {}; LIB.forEach(function(i){ i.t.forEach(function(t){ tc[t] = (tc[t] || 0) + 1; }); });
    var tags = Object.keys(tc).filter(function(t){ return !q || t.indexOf(q) > -1; })
      .sort(function(a, b){ return q ? (a.indexOf(q) - b.indexOf(q)) || (tc[b] - tc[a]) : tc[b] - tc[a]; }).slice(0, q ? 6 : 8);
    var rcc = {}; LIB.forEach(function(i){ if (i.r) rcc[i.r] = (rcc[i.r] || 0) + 1; });
    h += group('Aspect ratio', $$('[data-ratios] .row').map(function(b){ return b.dataset.ratio; }).filter(function(k){
      return rcc[k] && (!q || (k + ' ' + ($('.rsub', $('[data-ratio="' + k + '"]')) || {}).textContent).toLowerCase().indexOf(q) > -1); })
      .slice(0, q ? 4 : 0).map(function(k){ return prow('ratio', k, '<span class="pal-hash">\u25ad</span><span>' + esc(k) + '</span><span class="pal-n">' + rcc[k] + '</span>'); }));
    h += group('Concept', tags.map(function(t){ return prow('tag', t, '<span class="pal-hash">#</span><span>' + esc(t) + '</span><span class="pal-n">' + tc[t] + '</span>'); }));
    if (q) h += group('Images', hits.slice(0, 6).map(function(i){ return prow('image', i.f, '<img src="' + esc(i.url) + '" alt="">' +
      '<span><b>' + esc(i.f.replace('.jpg', '')) + '</b><em>' + esc(i.t.join(', ')) + '</em></span><span class="pal-n">' + esc(TITLES[i.s] || '') + '</span>'); }));
    plist.innerHTML = h || '<p class="pal-empty">Nothing matches \\u201c' + esc(pin.value) + '\\u201d. Try a concept such as growth or clarity.</p>';
    paint(plist); move(q ? 0 : -1);
  }
  function move(n){ var rows = $$('.pal-row', plist); if (!rows.length) { idx = -1; return; }
    idx = n < 0 ? -1 : (n + rows.length) % rows.length;
    rows.forEach(function(r, k){ r.classList.toggle('act', k === idx); });
    if (idx > -1) { rows[idx].scrollIntoView({ block: 'nearest' }); pin.setAttribute('aria-activedescendant', 'pal-' + idx); }
    else pin.removeAttribute('aria-activedescendant'); }
  function openPal(q){ palFrom = D.activeElement; pal.classList.add('open'); pin.value = q || ''; drawPal(); pin.focus(); }
  function closePal(){ pal.classList.remove('open'); if (palFrom && palFrom.focus) palFrom.focus(); }
  function choose(n){ var it = items[n] || (pin.value.trim() ? { kind: 'query', val: pin.value.trim() } : null); if (!it) return;
    closePal(); sheet(false);
    if (it.kind === 'query') S.q = it.val;
    else if (it.kind === 'colour') { S.colour = it.val; S.q = ''; }
    else if (it.kind === 'ratio') { S.ratio = it.val; S.q = ''; }
    else if (it.kind === 'tag') { if (S.tags.indexOf(it.val) < 0) S.tags.push(it.val); S.q = ''; }
    render();
    if (it.kind === 'image') { var im = LIB.filter(function(i){ return i.f === it.val; })[0]; if (im) { var sec = D.getElementById(im.s); if (sec.classList.contains('closed')) setClosed('sec:' + im.s, false); im.el.scrollIntoView({ block: 'center' }); openDrawer(im); } }
    else $('main').scrollIntoView(); }
  pin.addEventListener('input', drawPal);
  pin.addEventListener('keydown', function(e){
    if (e.key === 'ArrowDown') { e.preventDefault(); move(idx + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(idx - 1); }
    else if (e.key === 'Enter') { e.preventDefault(); choose(idx); } });
  plist.addEventListener('click', function(e){ var r = e.target.closest('.pal-row'); if (r) choose(+r.dataset.k); });
  pal.addEventListener('mousedown', function(e){ if (e.target === pal) closePal(); });
  $$('[data-search] input').forEach(function(i){
    i.addEventListener('click', function(){ openPal(S.q); });
    i.addEventListener('keydown', function(e){ if (e.key === 'Enter' || e.key === ' ' || (e.key.length === 1 && !e.metaKey && !e.ctrlKey)) {
      e.preventDefault(); openPal(e.key.length === 1 && e.key !== ' ' ? S.q + e.key : S.q); } }); });

  D.addEventListener('click', function(e){
    var t = e.target.closest('a,button'); if (!t) return;
    if (t.matches('[data-colour]')) { e.preventDefault(); var k = t.dataset.colour;
      S.colour = (t.classList.contains('ov') && S.colour === k) ? '' : k; render(); sheet(false); $('main').scrollIntoView(); }
    else if (t.matches('[data-ratio]')) { var rv = t.dataset.ratio; S.ratio = S.ratio === rv ? '' : rv; render(); }
    else if (t.matches('[data-tag]')) { var x = t.dataset.tag, n = S.tags.indexOf(x); if (n > -1) S.tags.splice(n, 1); else S.tags.push(x); render(); }
    else if (t.matches('[data-rm]')) { S[t.dataset.rm] = ''; render(); }
    else if (t.matches('[data-rm-tag]')) { S.tags.splice(S.tags.indexOf(t.dataset.rmTag), 1); render(); }
    else if (t.matches('[data-clear]')) { S.q = ''; S.colour = ''; S.ratio = ''; S.tags = []; render(); }
    else if (t.matches('.search .clear')) { S.q = ''; render(); }
    else if (t.matches('[data-theme-toggle]')) { var dk = !H.classList.contains('dark'); H.classList.toggle('dark', dk); store('azmx-library-theme', dk ? 'dark' : 'light'); syncTheme(); }
    else if (t.matches('[data-pane]')) setPane(!H.classList.contains('pane-closed'));
    else if (t.matches('[data-palette]')) openPal(S.q);
    else if (t.matches('[data-sheet-open]')) sheet(true);
    else if (t.matches('[data-sheet-close]')) sheet(false);
    else if (t.matches('[data-sec]')) { var s = 'sec:' + t.dataset.sec; setClosed(s, !closed[s]); render(); }
    else if (t.matches('[data-grp]')) { var g = 'grp:' + t.dataset.grp; setClosed(g, !closed[g]); }
    else if (t.matches('[data-allsec]')) { var op = t.dataset.open === 'true'; t.dataset.allsec.split(',').forEach(function(k){ setClosed('sec:' + k, !op); }); render(); }
    else if (t.matches('a.card') && !e.metaKey && !e.ctrlKey && !e.shiftKey && e.button === 0) { e.preventDefault();
      var f = t.closest('figure'); openDrawer(LIB.filter(function(i){ return i.el === f; })[0]); }
    else if (t.matches('[data-close-drawer]')) closeDrawer();
    else if (t.matches('[data-copy]')) { var u = t.dataset.copy; if (navigator.clipboard) navigator.clipboard.writeText(u);
      t.innerHTML = icon('check') + 'Copied'; $('#filter-status').textContent = 'Link copied'; }
  });
  $('.scrim').addEventListener('click', function(){ if (H.classList.contains('sheet-open')) sheet(false); else closeDrawer(); });
  var tf = $('[data-tagfind]'); if (tf) tf.addEventListener('input', render);
  D.addEventListener('keydown', function(e){
    var typing = /INPUT|TEXTAREA/.test(D.activeElement.tagName) && !D.activeElement.readOnly;
    if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); pal.classList.contains('open') ? closePal() : openPal(S.q); }
    else if (e.key === 'Escape') { if (pal.classList.contains('open')) closePal(); else if (H.classList.contains('sheet-open')) sheet(false); else closeDrawer(); }
    else if (pal.classList.contains('open') || typing) return;
    else if (e.key === '/') { e.preventDefault(); openPal(S.q); }
    else if (e.key === '[') setPane(!H.classList.contains('pane-closed'));
    else if (cur && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
      var vis = LIB.filter(function(i){ return !i.el.hidden && !D.getElementById(i.s).classList.contains('closed'); }), at = vis.indexOf(cur);
      var nx = vis[at + (e.key === 'ArrowRight' ? 1 : -1)]; if (nx) { openDrawer(nx); nx.el.scrollIntoView({ block: 'nearest' }); } }
  });
  var o = new URLSearchParams(location.search).get('open');
  render();
  if (o) { var im = LIB.filter(function(i){ return i.f === o; })[0]; if (im) openDrawer(im); }
})();"""


IMG_SCRIPT = """(function(){
  // A preview that fails to load (a CDN hiccup) retries twice, 1.5 s apart, then
  // offers a Reload link. 'error' does not bubble, so listen in the capture phase.
  var MAX = 2, WAIT = 1500;
  function base(u){ return u.split('?')[0]; }
  function retry(img){
    img.src = base(img.src) + '?r=' + img.dataset.tries;
  }
  document.addEventListener('error', function(e){
    var img = e.target;
    if (!img || img.tagName !== 'IMG' || !img.closest('.shot')) return;
    var n = +(img.dataset.tries || 0);
    if (n < MAX) {
      img.dataset.tries = n + 1;
      setTimeout(function(){ retry(img); }, WAIT);
      return;
    }
    var shot = img.closest('.shot');
    if (shot.querySelector('.reload')) return;
    var a = document.createElement('a');
    a.className = 'reload'; a.href = '#'; a.textContent = 'Reload image';
    a.addEventListener('click', function(ev){
      ev.preventDefault(); a.remove(); img.dataset.tries = 1; retry(img);
    });
    shot.appendChild(a);
  }, true);

  // Download saves the file instead of opening it: the download attribute is
  // ignored for another origin, so fetch it and save the blob. Delegated, so the
  // Download button in the details panel (built later) works the same way.
  document.addEventListener('click', function(ev){
    var link = ev.target.closest && ev.target.closest('a.dl');
    if (!link || !window.fetch || !window.URL || !URL.createObjectURL) return;
    ev.preventDefault();
    var href = link.href, name = link.getAttribute('download') || base(href).split('/').pop();
    fetch(href).then(function(r){
      if (!r.ok) throw new Error(r.status);
      return r.blob();
    }).then(function(blob){
      var url = URL.createObjectURL(blob), a = document.createElement('a');
      a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function(){ URL.revokeObjectURL(url); }, 4000);
    }).catch(function(){ window.open(href, '_blank', 'noopener'); });
  });
})();"""


def _app_script():
    """The page script with the icons, titles, order and notes it needs inlined."""
    return (APP_SCRIPT.replace("__ICONS__", json.dumps(ICONS, separators=(",", ":")))
            .replace("__TITLES__", json.dumps(TITLES, separators=(",", ":")))
            .replace("__ORDER__", json.dumps(ORDER, separators=(",", ":")))
            .replace("__NOTE__", json.dumps(NOTE, separators=(",", ":"))))


def write_gallery(secs, total):
    """Generate index.html: the public image library.

    Layout (direction C, approved by Jimmy on 23 Nov 2026): a left panel for
    finding (search, colour sections, concepts) that collapses to a slim rail, an
    "On this page" overview, collapsible colour sections of picture-and-name cards,
    and a details drawer for choosing (downloads, high-res, concepts, colour facts).
    ⌘K / Ctrl K or "/" opens a centred search palette. Light by default with a dark
    switch; theme, collapsed sections and the collapsed panel are remembered on the
    device. On tablets and phones the panel opens as a bottom sheet.

    Everything is rendered here, so the page reads and links without script; the
    script adds filtering, the palette, the drawer and the collapsing. Every
    inline <style> and <script> is hash-locked in the CSP, and the markup carries
    no style="" attribute (the CSP would block it): colours are painted from
    data-color by script.
    """
    tags = load_tags()
    sizes = load_sizes()
    app_script = _app_script()

    # CSP hashes are computed from the very strings emitted below, so editing the
    # CSS or JS can never desynchronise the policy from the page. Each hash covers
    # exactly the text between the opening and closing tag, newlines included.
    style_hash = compute_csp_hash("\n" + GALLERY_CSS + "\n")
    script_hashes = [compute_csp_hash("\n" + s + "\n") for s in (THEME_SCRIPT, COPY_SCRIPT, app_script, IMG_SCRIPT)]

    # frame-ancestors is ignored in a <meta> CSP (header-only directive), so it is
    # deliberately not listed here; GitHub Pages cannot send custom headers.
    csp_policy = (
        f"default-src 'self'; "
        f"script-src 'self' " + " ".join(f"'{h}'" for h in script_hashes) + "; "
        f"style-src 'self' '{style_hash}'; "
        f"img-src 'self' data: https:; "
        f"font-src 'self'; "
        f"connect-src 'self' https://cdn.jsdelivr.net; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )

    desc = "AZMX brand image library. Search gradients, abstract blue and recoloured brand imagery by name, concept or colour, free to download."
    h = [f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AZMX Image Library</title>
<meta name="description" content="{desc}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="assets/logo/azmx-favicon.png">
<link rel="stylesheet" href="assets/fonts.css">
<meta property="og:type" content="website">
<meta property="og:site_name" content="AZMX Brand Skill">
<meta property="og:title" content="AZMX Image Library">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://gamaleldientarek.github.io/azmx-brand/">
<meta property="og:image" content="https://gamaleldientarek.github.io/azmx-brand/assets/cover-social-1280x640.jpg">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:image:alt" content="AZMX Brand Skill">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AZMX Image Library">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://gamaleldientarek.github.io/azmx-brand/assets/cover-social-1280x640.jpg">"""]
    h.append(f'<meta http-equiv="Content-Security-Policy" content="{csp_policy}">')
    h.append('<meta http-equiv="X-Content-Type-Options" content="nosniff">')
    h.append('<meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">')
    h.append("<script>\n" + THEME_SCRIPT + "\n</script>")
    h.append("<style>\n" + GALLERY_CSS + "\n</style>")
    h.append("</head>\n<body>")
    h.append(sidebar(secs))
    h.append('<main id="top">')
    h.append('<div class="mtop"><a class="brand" href="#top"><img src="assets/logo/azmx-favicon.png" alt=""><span>AZMX Image Library</span></a>'
             '<button class="btn icon ghost" type="button" data-theme-toggle aria-label="Switch to dark mode">'
             + icon("moon", "i-moon") + icon("sun", "i-sun") + '</button></div>')
    h.append('<header class="head"><p class="eyebrow">AZMX Brand Skill</p><h1>Image Library</h1>')
    h.append(f'<p class="lede">{total} AZMX brand images in eight colour sections. Search by name, concept or colour, '
             f'open any image for its details, and download the 1600&nbsp;px JPG.</p>')
    h.append('<p class="lede">Nearly all of them are dark surfaces: set titles in White, body in Blue&nbsp;100, '
             'eyebrows in Light&nbsp;Blue, and never Electric blue as text over them.</p>')
    n_hi = sum(1 for rows in secs.values() for r in rows if has_hires(r))
    if n_hi:
        h.append(f'<p class="meta">{total} images · JPG · 1600px wide · {n_hi} with high-res</p>')
        h.append('<p class="meta">High-res downloads need an AZMX Google sign-in.</p></header>')
    else:
        h.append(f'<p class="meta">{total} images · JPG · 1600px wide</p></header>')
    recolour = recolour_section()
    h.append(overview(secs, recolour.count('class="pcard"')))
    h.append('<div class="mbar"><div class="search" data-search>' + icon("magnifying-glass") +
             '<input type="search" placeholder="Search images" aria-label="Search images" readonly aria-haspopup="dialog">'
             '<button class="clear" type="button" aria-label="Clear search">' + icon("x") + '</button></div>'
             '<button class="btn" type="button" data-sheet-open aria-haspopup="dialog" aria-controls="panel">'
             + icon("funnel-simple") + 'Filters</button></div>')
    h.append(f'<div class="bar" data-bar><span class="count">{total} of {total} images</span></div>')
    h.append('<p class="sr" role="status" aria-live="polite" id="filter-status"></p>')
    for s in ORDER:
        rows = secs.get(s, [])
        if not rows:
            continue
        h.append(f'<section id="{s}" class="sec"><h2><button type="button" class="sec-tg" data-sec="{s}" '
                 f'aria-expanded="true" aria-controls="body-{s}">{icon("caret-down", "tg-ic")}<span>{TITLES[s]}</span>'
                 f'<span class="n">{len(rows)}</span></button></h2>'
                 f'<div class="sec-body" id="body-{s}"><p class="note">{NOTE[s]}</p><div class="grid">')
        for r in rows:
            rel = esc(f"{GALLERY_CDN}/{s}/{r['f']}")
            fname = esc(r["f"])
            tg = tags.get(r["f"], [])
            tstr = esc(" ".join(tg))
            wh = sizes.get(r["f"])
            if wh:
                label = aspect(*wh)
                size_attrs = f' data-ratio="{label}" data-w="{wh[0]}" data-h="{wh[1]}"'
                ratio_tag = (f'<span class="ratio" title="{wh[0]} × {wh[1]} px, {orientation(*wh).lower()}">'
                             f'{label}</span>')
            else:
                size_attrs = ratio_tag = ""
            h.append(f'<figure data-f="{fname}" data-s="{s}" data-tags="{tstr}" data-dom="{esc(r["dom"])}" '
                     f'data-tok="{esc(r.get("tok", ""))}" data-l="{r.get("L", 0)}"{size_attrs}><span class="shot">'
                     f'<a class="card" href="{rel}" target="_blank" rel="noopener">'
                     f'<img loading="lazy" src="{rel}" alt="{esc(", ".join(tg)) or fname}"></a></span>'
                     f'<figcaption><span class="name">{esc(r["f"].rsplit(".", 1)[0])}</span>{ratio_tag}{hires_button(r)}'
                     f'<a class="dl" href="{rel}" download="{fname}" title="Download {fname}" aria-label="Download {fname}">'
                     f'{icon("download-simple")}</a></figcaption></figure>')
        h.append("</div></div></section>")
    h.append('<div class="empty" id="empty" hidden><strong>No images match</strong>'
             'Try fewer words, or remove a concept. Search covers file names, concepts and colour sections.</div>')
    h.append(recolour)
    h.append(f'<footer>Download one image:<br><code>curl -L -O "{GALLERY_CDN}/blue/blue-001.jpg"</code>'
             f'<br><br>Full brand skill and install instructions: '
             f'<a class="link" href="https://github.com/Gamaleldientarek/azmx-brand">github.com/Gamaleldientarek/azmx-brand</a>'
             f'<br><br>Designed with love by <a class="link" href="https://gamaleldien.com">gamaleldien.com</a></footer></main>')
    h.append('<aside class="drawer" id="drawer" role="dialog" aria-labelledby="drawer-t" aria-label="Image details"></aside>')
    h.append('<div class="scrim" aria-hidden="true"></div>')
    h.append('<div class="pal-wrap" id="palette"><div class="pal" role="dialog" aria-modal="true" aria-label="Search the library">'
             '<div class="pal-in">' + icon("magnifying-glass") +
             '<input type="search" placeholder="Search images, concepts or colours" role="combobox" aria-expanded="true" '
             'aria-controls="pal-list" aria-autocomplete="list" autocomplete="off" spellcheck="false"><kbd>Esc</kbd></div>'
             '<div class="pal-list" id="pal-list" role="listbox"></div>'
             '<div class="pal-foot"><span><kbd>↑</kbd><kbd>↓</kbd> to move</span><span><kbd>↵</kbd> to choose</span>'
             '<span><kbd class="kbd-k">⌘K</kbd> to open anywhere</span></div></div></div>')
    h.append("<script>\n" + app_script + "\n</script>")
    h.append("<script>\n" + IMG_SCRIPT + "\n</script>")
    h.append("</body>\n</html>")
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(h))


def write_prompts_md():
    """Regenerate references/recolor-prompts.md from scripts/recolor-prompts.json.

    Delegates to sync-references.py so there is exactly one writer of that file —
    a second, slightly different renderer here used to make `sync-references.py
    --check` fail after every gallery rebuild.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sync_references", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync-references.py"))
    sync_references = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync_references)
    sync_references.sync_recolor_prompts_to_markdown(
        os.path.join(ROOT, "scripts", "recolor-prompts.json"),
        os.path.join(ROOT, "references", "recolor-prompts.md"),
        use_color=False, quiet=True)


def main():
    """Orchestrate the complete rebuild of the image index and gallery.

    Entry point that coordinates all rebuild steps in sequence: first loads the
    per-image analysis (from scripts/image-meta.json, or by measuring a local
    assets/images tree when one is present), then generates
    the agent-readable markdown index at references/image-index.md, the public HTML
    gallery at index.html, and the recolour prompt documentation. Prints a summary
    table showing the image count per section and a final status message. Returns 0
    on success, 1 if no images are found.
    """
    secs = analyse()
    if not secs:
        print("No images found: scripts/image-meta.json is missing or empty and "
              "assets/images/ holds no JPEGs.")
        return 1
    total = write_index(secs)
    write_gallery(secs, total)
    write_prompts_md()
    for s in ORDER:
        if secs.get(s):
            print(f"  {TITLES[s]:<14} {len(secs[s]):>3}")
    src = "assets/images (image-meta.json rewritten)" if local_images() else "scripts/image-meta.json"
    print(f"\nRebuilt references/image-index.md and index.html for {total} images from {src}.")
    print(f"Image links point to {CDN}/<section>/<file>.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
