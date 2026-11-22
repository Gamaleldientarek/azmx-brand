# Image library: reliable previews and high-res downloads for AZMX staff

Date: 22 Nov 2026 · Status: draft for Jimmy's approval · Gallery: https://gamaleldientarek.github.io/azmx-brand/

## Why

The image library is the AZMX team's source for brand imagery. Two problems:

1. Some cards sometimes show no preview. Jimmy saw one near gradient-019.
2. The library only holds web copies: `scripts/add-images.py` resizes every image to 1600 px, saves it as JPEG quality 70, and keeps nothing larger. Designers who need print-quality or large-screen images have nowhere to get them.

Success: every card always shows its preview, and anyone at AZMX can get the full-resolution file from the same card in one click, or find it by browsing a folder in the company drive.

## What we found (22 Nov)

- All 240 images on the page answer 200 from jsDelivr and decode cleanly (1600 px wide, RGB). A full scroll in the built-in browser and in Jimmy's Dia loaded all 240 with no errors.
- The only 404s, `blue-101` and `red-007`, are not on the page (numbering gaps).
- On the first pass from the shell, 5 files (blue-036, orange-016, gradient-018, blue-094, blue-102) came back empty, then loaded fine on retry.
- The page links jsDelivr's **branch** URL (`azmx-brand-cdn@main`). jsDelivr caches a branch URL for only 12 hours at its edge (`s-maxage=43200`) and then fetches it again from GitHub. When that fetch is slow or fails, the browser shows an empty card until the next reload. That fits "one or two images, sometimes".
- Side finding: the card's Download button can't force a download, because browsers ignore the `download` attribute for files on another domain (jsDelivr). It opens the image in the same tab instead.

## Goals

- Previews load reliably, with no visible empty card.
- Every image can have a high-res original, downloadable by AZMX staff only (signed in with an @azmx.sa account).
- The high-res files are also browsable in the company drive, in the same sections as the site.
- Adding new images stays one command, and that command handles both sizes.

## Non-goals

- No change to the 1600 px web copies or the page design beyond one extra button per card.
- No public high-res hosting.
- No new paid service.

## Anti-goals (a failure even if it "works")

- High-res files reachable by anyone outside AZMX.
- Original files renamed or recompressed, so a designer can't trust they have the master.
- A second, hand-maintained list of links that drifts from the gallery.

## Approaches considered

| | How | Trade-off |
|---|---|---|
| **A. Google Drive shared drive (chosen)** | Originals in `Shared drives/AZM X/Branding/Brand Images Gallery/<section>/`. Each card links to its Drive file. | Free. Access limited to azmx.sa. Staff can browse the folder too. Each file needs its Drive ID, which Drive for Desktop already exposes on this Mac. |
| B. Cloudflare R2 | Public bucket, 10 GB free, direct links | Anyone with the link can download. Rejected: Jimmy wants staff only. |
| C. GitHub, in the CDN repository | `images-full/` next to `images/` | jsDelivr won't serve files over 20 MB, and the repository would grow fast. Public. Rejected. |

Jimmy picked staff-only on 22 Nov, which settles A.

## Design

### Part 1: previews (no Drive work needed)

1. **Pin the CDN version.** The gallery links images at a fixed commit of `azmx-brand-cdn` (`@<commit hash>`) instead of `@main`. jsDelivr caches a fixed version permanently, so the 12-hour refetch from GitHub stops. `add-images.py` records the new commit after each CDN commit. See "Settled after the builder check" for what the pin covers.
2. **Retry on error.** A short inline script retries a failed image up to twice, with a cache-busting query string, before it gives up and shows a plain "Reload image" link on the card. That covers any CDN hiccup that's left.
3. **Real download.** A small script fetches the image and saves it under its file name when Download is clicked. jsDelivr allows this (`access-control-allow-origin: *`), but the page's security policy currently blocks it (`connect-src 'self'`), so `https://cdn.jsdelivr.net` is added to `connect-src`. If the fetch fails, the link falls back to opening the image in a new tab.

The page's inline scripts are locked by hash in its security policy. `rebuild-index.py` already computes those hashes, so the new scripts go through it, never into `index.html` by hand.

### Part 2: high-res storage

- **Folder:** `Shared drives/AZM X/Branding/Brand Images Gallery/`, with one subfolder per section (`gradient`, `blue`, `white`, `purple`, `orange`, `red`, `green`, `yellow`). Jimmy created the folder himself on 22 Nov (Drive ID `12Md4XcYshvxJ5ZnanEjEaj3tnc0aDwCM`), and it is empty.
- **Files:** each original keeps its format (PNG, TIFF, JPEG…) and full size, renamed to match its web copy: `blue-114.png` pairs with `blue-114.jpg`.
- **Access:** members of the AZM X shared drive can already open it. Jimmy sets the folder's general access to "AZM X (azmx.sa): anyone in this group with the link can view", so staff who aren't drive members can open card links too. Jimmy changes that setting in Drive himself.
- **Upload path:** Jimmy uploads the new originals into the folder himself (22 Nov). The script works on them through Drive for Desktop, under the `GoogleDrive-*@azmx.sa` folder in `~/Library/CloudStorage`. Once Drive has synced a file, the script reads its Drive ID from the `com.google.drivefs.item-id#S` extended attribute. No Drive API keys, no sign-in step.

### Part 3: the gallery and the catalogue

- `scripts/image-meta.json` gains an optional `hi` object per image: `{"id": "<drive id>", "w": 6000, "h": 3364, "bytes": 41234567, "ext": "png"}`, or `{"pending": true}`. The original file name is not stored (final review, 22 Nov): Midjourney names carry the account and prompt, and the file is public.
- `rebuild-index.py` adds a second button to cards that have `hi`: **"High-res"** (with the pixel size and file size in its tooltip), linking to `https://drive.google.com/uc?export=download&id=<id>`. Cards without `hi` keep the current single button.
- The header line changes from "240 images · JPG · 1600px wide" to also count how many have high-res and add "High-res downloads need an AZMX Google sign-in."
- `references/image-index.md` lists the high-res size per image, so agents using the brand skill know it exists.

### Part 4: one command for new images

`add-images.py` changes from "resize, keep the small copy" to:

1. Find new originals in `Brand Images Gallery`: any image file not yet named `<section>-NNN.<ext>`. A file dropped into a section subfolder belongs to that section. A file dropped in the folder's root is sorted by its dominant colour, and the script lists its guesses and waits for Jimmy's OK before moving anything.
2. Write the 1600 px web JPEG into the CDN checkout (unchanged behaviour).
3. Move the untouched original into its section subfolder and rename it to the same number as its web copy (`blue-114.png`). A move inside Drive keeps the file's ID. It also accepts a local folder, as today: those originals are copied into Drive.
4. Read the Drive ID once Drive has synced the file (with a timeout and a clear message if Drive is paused).
5. Record `hi` in `image-meta.json` and rebuild the gallery.
6. Commit both repositories and point the gallery at the new CDN commit. Pushing still waits for Jimmy's yes, CDN repository first.

### Part 5: high-res for the existing 240 (later, not in this build)

Jimmy doesn't have the originals of the existing 240 for now (22 Nov) and will look for them. Until then those cards keep their single Download button and show no High-res button.

This build covers the new folder Jimmy is providing: every image in it goes through Part 4 and gets both sizes from the start.

When originals of old images turn up, a later `scripts/match-hires.py` pairs each original with its web copy by comparing small thumbnails. The comparison must include colour, because the orange, purple, red, green and yellow images are recolours of blue ones and would otherwise match their blue source. If the originals come from the Figma file instead of loose files, the pairing can use the Figma export order. That's decided when the files exist.

## Testing

- Extend `tests/test_add_images.py`, `test_rebuild_index.py` and `test_image_gallery.py`: a card with `hi` renders the second button, a card without `hi` doesn't, and the pinned CDN URL is used everywhere.
- A check script that loads every image URL in the built `index.html` and every Drive link's HEAD while signed in, and reports any failure.
- A manual check in Dia: scroll the whole page, open three high-res links signed in as azmx.sa, and one in a private window to confirm it asks for sign-in.

## Left to the builder

- The exact retry delays, and the button's icon and wording, all within the design system's rules (secondary action as a text link if that reads better beside Download).
- The perceptual-hash threshold, tuned on the first real folder.

## Settled after the builder check

- **Public repositories.** `azmx-brand` and `azmx-brand-cdn` are public. Drive file IDs go into the public gallery and catalogue: the card links need them, and a file shared only with azmx.sa can't be opened without an AZMX sign-in, so the ID alone gives nothing away. The Drive account name never goes into a script. The script finds the AZMX Drive folder by looking for a `GoogleDrive-*@azmx.sa` folder under `~/Library/CloudStorage`, or reads `AZMX_HIRES_DIR` if that's set.
- **Who runs it.** Only on Jimmy's Mac (or a Claude session there), because it needs Drive for Desktop. Anywhere else (a teammate, a cloud session), `add-images.py` still adds the web copy and records the image as "high-res pending". A new `scripts/sync-hires.py`, run later on the Mac, links originals that were placed in Drive under the image's name and fills in `hi`.
- **What the pin covers.** Only the gallery (`index.html`) uses the pinned CDN version. `SKILL.md`, the README, `references/`, `api/v1/*.json` and `openapi.json` keep `@main`, so outside users and agents see no change. The pin is a commit hash of `azmx-brand-cdn`, so no tag is needed. Order of release: push the CDN repository first, then the brand repository whose gallery points at that commit. Both pushes wait for Jimmy's yes, as now.
- **Keeping `hi` safe.** `rebuild-index.py`'s local re-measure path rewrites `image-meta.json`; it must carry `hi` and any pending flag over. `tests/test_gallery_security.py` changes to allow `https://cdn.jsdelivr.net` in `connect-src` (Part 1.3).

## Calls I made (Jimmy to check)

- Files in the gallery folder are renamed to match their web copy (`blue-114.png`). The original name is not kept (it can carry the Midjourney account and prompt).
- Files dropped in the folder root are sorted by colour, with Jimmy's OK before anything moves.
- Originals keep their own format and are never recompressed.
- The gallery is pinned to a CDN commit; everything else keeps `@main`.
- Drive IDs are public in the gallery; the Drive account name is not.
