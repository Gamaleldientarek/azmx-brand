# Image Library High-Res Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gallery previews load reliably, and new images get a staff-only high-res download from Google Drive, added with one command.

**Architecture:** The gallery page alone is pinned to a fixed `azmx-brand-cdn` commit, and gains a retry-and-download script. A new importable module `scripts/hires.py` finds originals in the "Brand Images Gallery" Drive folder through Drive for Desktop, reads their Drive IDs from extended attributes, and records them as `hi` on each image in `scripts/image-meta.json`. `rebuild-index.py` renders a High-res button for every image that has `hi`.

**Tech Stack:** Python 3 with Pillow 12.3.0, pytest 8, plain HTML/JS emitted by `rebuild-index.py`, macOS `xattr`, Google Drive for Desktop.

**Spec:** `docs/superpowers/specs/2026-11-22-image-library-hires-design.md`

## Global Constraints

- Web copies stay as they are: 1600 px wide, JPEG quality 70 (`TARGET_WIDTH`, `JPEG_QUALITY` in `add-images.py`).
- Originals are never recompressed or re-encoded. They are only moved and renamed to `<section>-NNN.<original ext, lower case>`.
- Drive folder: `Shared drives/AZM X/Branding/Brand Images Gallery/` with subfolders `gradient blue white purple orange red green yellow`. Found under `~/Library/CloudStorage/GoogleDrive-*@azmx.sa/`, or at `$AZMX_HIRES_DIR` when that's set. Never write an account email into code, tests or docs.
- Drive ID source: the `com.google.drivefs.item-id#S` extended attribute.
- High-res link format: `https://drive.google.com/uc?export=download&id=<id>`.
- Only `index.html` uses the pinned CDN commit (`$meta.gallery_cdn`). `$meta.cdn` stays `…/azmx-brand-cdn@main/images`, so the API, `SKILL.md`, `README.md`, `references/` and `openapi.json` don't change.
- CSP: `connect-src 'self' https://cdn.jsdelivr.net`. Every inline script is hashed through `compute_csp_hash`, never hand-written into `index.html`.
- No pushes. Both repositories get local commits only; pushing (CDN repository first) waits for Jimmy's explicit yes.
- No sharing-setting changes in Drive. Jimmy sets the folder's general access himself.

## Review Focus

1. **Drive paused or file not yet synced:** no ID within the timeout → the image is still added at web size and recorded `"hi": {"pending": true}`, with a printed line saying which file. Nothing crashes. Test in Task 5.
2. **Running the command twice:** an original already named `<section>-NNN.ext` that matches a catalogue entry is never processed again, so there are no duplicate numbers. Test in Task 5.
3. **Original names with spaces, Arabic or upper-case extensions** (`صورة 1.PNG`): handled, and the original name is kept in `hi.src`. Test in Task 4.
4. **Very large originals** (over Pillow's default 89 MP decompression-bomb warning, e.g. an 8000×12000 TIFF): convert without error. `hires.py` sets `Image.MAX_IMAGE_PIXELS = 400_000_000` for this tool only. Test in Task 4.
5. **Local re-measure path:** when `assets/images/` exists, `rebuild-index.py` rewrites `image-meta.json` and must keep each entry's `hi`. Test in Task 3.

---

### Task 0: Set up

**Files:** none changed.

- [ ] **Step 1:** `cd ~/Code/azmx-brand && git switch image-library-hires`
- [ ] **Step 2:** `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-test.txt` (`.venv` is already ignored by `norecursedirs`; check that `.gitignore` covers it, and add `.venv/` if not).
- [ ] **Step 3:** `python3 -m pytest tests/test_add_images.py tests/test_rebuild_index.py tests/test_image_gallery.py tests/test_gallery_security.py -q`. Expected: all pass. Write down the count as the baseline.
- [ ] **Step 4:** Clone the CDN repository next to this one: `git clone https://github.com/Gamaleldientarek/azmx-brand-cdn.git ../azmx-brand-cdn`. Record `git -C ../azmx-brand-cdn rev-parse HEAD` as `PIN0`.

### Task 1: Pin the gallery to a CDN commit

**Files:**
- Modify: `scripts/rebuild-index.py` (beside `cdn_base()`, around line 107; `write_gallery`, lines 536–640)
- Modify: `scripts/image-meta.json` (`$meta`)
- Test: `tests/test_rebuild_index.py`

**Interfaces:**
- Produces: `gallery_cdn() -> str` in `rebuild-index.py`: `$meta.gallery_cdn` stripped of a trailing `/`, or `cdn_base()` when absent. Module constant `GALLERY_CDN = gallery_cdn()`.
- Produces: `$meta.gallery_cdn` = `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@<sha>/images`.

- [ ] **Step 1: Write the failing tests** in `tests/test_rebuild_index.py`, following that file's existing temp-meta fixtures:
  - `test_gallery_cdn_uses_pinned_value`: with `$meta.gallery_cdn = ".../azmx-brand-cdn@abc123/images/"`, `gallery_cdn()` returns it without the trailing slash.
  - `test_gallery_cdn_falls_back_to_cdn`: without the key, it equals `cdn_base()`.
  - `test_gallery_links_pinned_index_md_not`: after a rebuild, every `src=` and `href=` image URL in `index.html` contains `@abc123/`, and `references/image-index.md` still contains `@main/`.
- [ ] **Step 2:** Run them. Expected: FAIL (`gallery_cdn` not defined).
- [ ] **Step 3:** Implement `gallery_cdn()`. Use `GALLERY_CDN` everywhere `write_gallery` builds an image URL, including the footer `curl` example. `write_index` and `cdn_base` stay unchanged.
- [ ] **Step 4:** Run the tests. Expected: PASS, and the baseline count still passes.
- [ ] **Step 5:** Set `$meta.gallery_cdn` to the `PIN0` URL in `scripts/image-meta.json`, run `python3 scripts/rebuild-index.py`, and check that `grep -c "@main/" index.html` prints `0`.
- [ ] **Step 6: Commit** `scripts/rebuild-index.py scripts/image-meta.json tests/test_rebuild_index.py index.html references/image-index.md`, with the message "Gallery: pin images to a fixed CDN commit".

### Task 2: Retry failed previews, real downloads

**Files:**
- Modify: `scripts/rebuild-index.py` (new constant `IMG_SCRIPT` next to `TAG_SCRIPT`; CSP in `write_gallery`)
- Modify: `tests/test_gallery_security.py`, `tests/test_image_gallery.py`

**Interfaces:**
- Produces: `IMG_SCRIPT: str`, emitted as a third `<script>` and hashed as `script_hash_3`.

Behaviour of `IMG_SCRIPT`:
- On an `<img>` `error` inside `.shot`, retry up to 2 times, 1.5 s apart, by setting `src` to the original URL plus `?r=<n>`.
- After the last failure, add `<a class="reload" href="#">Reload image</a>` to the card. Clicking it resets the counter and retries.
- Because `error` doesn't bubble, the script attaches its listener with `document.addEventListener('error', fn, true)`.
- On a `.dl` click: `preventDefault`, `fetch(href)`, then save the blob through an object URL with `a.download = <file name>`. On any fetch failure, `window.open(href, '_blank', 'noopener')`.

- [ ] **Step 1: Write the failing tests:**
  - `test_gallery_security.py::test_connect_src_allows_jsdelivr`: the CSP's `connect-src` is exactly `'self' https://cdn.jsdelivr.net`. Replace the old assertion that it's `'self'` only.
  - `test_gallery_security.py::test_every_inline_script_hashed`: there are 3 inline scripts, and each one's hash appears in `script-src`.
  - `test_image_gallery.py::test_img_script_present`: `index.html` contains `addEventListener('error'` and `'Reload image'`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Add `IMG_SCRIPT`, append it after `TAG_SCRIPT` in `write_gallery`, add `script_hash_3` to `script-src`, and change `connect-src`. Add `.reload` styling to `GALLERY_CSS` in the existing link style (`a.link`).
- [ ] **Step 4:** Run the four gallery and index test files. Expected: PASS.
- [ ] **Step 5: Manual check:** `python3 -m http.server 8765`, open `http://localhost:8765/` in the built-in browser, and in the console run `document.querySelector('.shot img').src='https://cdn.jsdelivr.net/gh/x/y@main/nope.jpg'`. After about 3 s, "Reload image" shows on that card. Clicking Download on another card saves `<file>.jpg` and no new tab opens.
- [ ] **Step 6: Commit** with the message "Gallery: retry failed previews and download images directly".

### Task 3: High-res button and catalogue field

**Files:**
- Modify: `scripts/rebuild-index.py` (`write_gallery` card loop, header lines; `write_index`; `analyse`)
- Test: `tests/test_image_gallery.py`, `tests/test_rebuild_index.py`

**Interfaces:**
- Consumes: catalogue entries of the form `{"f", "dom", "tok", "L", "hi"?}` where `hi` is either `{"id": str, "w": int, "h": int, "bytes": int, "ext": str, "src": str}` or `{"pending": true, "src": str}`.
- Produces: `hires_link(file_id: str) -> str` in `rebuild-index.py`, returning `https://drive.google.com/uc?export=download&id=<file_id>`.

- [ ] **Step 1: Write the failing tests:**
  - `test_card_with_hi_has_hires_button`: an entry with `hi.id="ID1", w=6000, h=3364, bytes=41234567` renders `<a class="hi" href="https://drive.google.com/uc?export=download&amp;id=ID1"`, with the text `High-res`, a `title` containing `6000 × 3364` and `39.3 MB`, and `target="_blank" rel="noopener"`.
  - `test_card_without_hi_or_pending_has_no_hires_button`: no `class="hi"` for entries without `hi` or with `hi.pending`.
  - `test_header_counts_hires`: with 2 of 3 images carrying `hi.id`, the header reads `3 images · JPG · 1600px wide · 2 with high-res` and contains `High-res downloads need an AZMX Google sign-in.`
  - `test_index_md_lists_hires_size`: `references/image-index.md` shows `hi-res 6000×3364 PNG` on that image's line.
  - `test_remeasure_keeps_hi` (Review Focus 5): a local `assets/images/blue/blue-001.jpg` plus a meta entry with `hi` → after `analyse()`, the rewritten `image-meta.json` entry still has the same `hi`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. The `.hi` link sits inside `.shot` next to `.dl` and uses the same pill style with a different icon, which `GALLERY_CSS` defines. MB means bytes / 1,048,576, rounded to 1 decimal. In `analyse()`, merge `hi` from the old entry when re-measuring.
- [ ] **Step 4:** Run all four test files. Expected: PASS.
- [ ] **Step 5: Commit** with the message "Gallery: high-res button and catalogue field".

### Task 4: `scripts/hires.py`: find, convert and identify originals in Drive

**Files:**
- Create: `scripts/hires.py`
- Test: `tests/test_hires.py`

**Interfaces (produces):**
- `SECTIONS: list[str]`, the same 8 in the same order as `add-images.py`.
- `drive_root(env: dict = os.environ, home: Path = Path.home()) -> Path | None`: `$AZMX_HIRES_DIR` if set and it exists; otherwise the first `home/"Library/CloudStorage"/"GoogleDrive-*@azmx.sa"/"Shared drives/AZM X/Branding/Brand Images Gallery"` that exists; otherwise `None`.
- `read_drive_id(path: Path, timeout: float = 120.0, poll: float = 2.0, reader=None) -> str | None`: polls `xattr -p com.google.drivefs.item-id#S <path>` through `subprocess.run` until it gets a non-empty value or the timeout passes. `reader(path) -> str | None` is injectable for tests.
- `original_info(path: Path) -> dict`: returns `{"w", "h", "bytes", "ext", "src"}`, where `ext` is the lower-case extension without the dot and `src` is `path.name`. It opens the file with Pillow only to read its size.
- `is_catalogued_name(name: str) -> bool`: true for `^(gradient|blue|white|purple|orange|red|green|yellow)-\d{3}\.[a-z0-9]+$`.
- `find_new_originals(root: Path) -> list[tuple[Path, str | None]]`: lists image files (`EXTS` from `add-images.py`) directly in `root` (section `None`) and in each section subfolder (that section), skipping names where `is_catalogued_name` is true and hidden files.
- `guess_section(dom_hex: str, lum: float) -> str`: for root-dropped files. If saturation < 0.15 and lum > 0.25 → `white`. Otherwise by hue in degrees: [345,15) `red`, [15,40) `orange`, [40,70) `yellow`, [70,170) `green`, [170,255) `blue`, [255,345) `purple`. `gradient` is never guessed; Jimmy corrects it.
- `place_original(path: Path, root: Path, section: str, number: int) -> Path`: makes `root/section` if needed and moves `path` to `root/section/f"{section}-{number:03d}.{ext}"`. If `path` is outside `root`, it copies with `shutil.copy2` instead and leaves the source alone. Returns the new path, and raises `FileExistsError` instead of overwriting.
- Sets `Image.MAX_IMAGE_PIXELS = 400_000_000` at import.

- [ ] **Step 1: Write the failing tests** in `tests/test_hires.py`, all with `tmp_path` and no real Drive:
  - `test_drive_root_env_wins`, `test_drive_root_globs_azmx_account` (a fake `home` with `Library/CloudStorage/GoogleDrive-x@azmx.sa/Shared drives/AZM X/Branding/Brand Images Gallery`), and `test_drive_root_none_when_missing`.
  - `test_read_drive_id_polls_until_value` (the reader returns `None`, `None`, then `"ID9"` → `"ID9"`), and `test_read_drive_id_times_out` (`timeout=0.05, poll=0.01` → `None`).
  - `test_find_new_originals_sections_and_root`: `root/a.png`, `root/blue/صورة 1.PNG`, `root/blue/blue-001.png` and `root/.DS_Store` → `[(root/"a.png", None), (root/"blue"/"صورة 1.PNG", "blue")]`, in that order.
  - `test_place_original_moves_and_lowercases_ext`: `صورة 1.PNG` → `blue/blue-114.png`, and the source no longer exists.
  - `test_place_original_copies_from_outside_root`: the source still exists afterwards.
  - `test_place_original_refuses_overwrite`.
  - `test_guess_section`: `("#0406DC", 0.07)` → `blue`, `("#F26D18", 0.09)` → `orange`, `("#EAEAED", 0.45)` → `white`, `("#3F007F", 0.03)` → `purple`, `("#049445", 0.15)` → `green`, `("#8F6106", 0.15)` → `yellow`, `("#AF021C", 0.07)` → `red`.
  - `test_original_info_large_image` (Review Focus 4): with `MAX_IMAGE_PIXELS` temporarily lowered to 100, `original_info` on a 20×20 PNG returns `w=20, h=20` with no `DecompressionBombError`. This proves the module raises the limit itself, so the test sets its low value before reimporting the module.
- [ ] **Step 2:** `python3 -m pytest tests/test_hires.py -q`. Expected: FAIL (module missing).
- [ ] **Step 3:** Implement `scripts/hires.py` to these signatures. Use `colorsys.rgb_to_hsv` in `guess_section`.
- [ ] **Step 4:** Run it. Expected: PASS.
- [ ] **Step 5: Commit** with the message "hires.py: find, place and identify high-res originals in Drive".

### Task 5: `add-images.py --from-drive` and `scripts/sync-hires.py`

**Files:**
- Modify: `scripts/add-images.py` (`parse_args`, `main`, new `add_one`)
- Create: `scripts/sync-hires.py`
- Test: `tests/test_add_images.py`, new `tests/test_sync_hires.py`

**Interfaces:**
- Consumes: everything Task 4 produces.
- Produces in `add-images.py`:
  - `add_one(src: Path, section: str, number: int, cdn_dir: str, meta: dict, root: Path | None, id_reader=None) -> dict | None`. It converts `src` to `<cdn>/images/<section>/<section>-NNN.jpg`. If `root` is set, it calls `place_original` and then `read_drive_id`, setting `hi` to `original_info(...) | {"id": ...}`, or to `{"pending": True, "src": src.name}` when the ID times out. If `root` is `None`, `hi` is `{"pending": True, "src": src.name}`. It appends the entry to `meta` and returns it, or returns `None` when conversion fails (the current error handling stays). The web JPEG is always made from `src` before the move.
  - New CLI flags: `--from-drive` (no section or paths needed; uses `find_new_originals(drive_root())`), `--yes` (accept colour guesses for root-dropped files without asking), and `--no-commit`.
  - After adding images, unless `--no-commit`: `git -C <cdn_dir> add images && git -C <cdn_dir> commit -m "Add images: <sections>"`. It then sets `meta["$meta"]["gallery_cdn"]` to `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@<new HEAD>/images`, saves, rebuilds, and commits this repository. The closing message prints the two push commands in order, CDN first, and does not run them.
- Produces `sync-hires.py`, with `main(argv=None) -> int`: for each catalogue entry without `hi.id`, it looks for `root/<section>/<stem>.*` (one match; two or more → print and skip). If it finds one, it reads the ID and records `hi`. It prints `N linked, M still pending` and rebuilds when N > 0. This is also how old images get high-res later, if Jimmy drops a correctly named original.

- [ ] **Step 1: Write the failing tests** (use `tmp_path` for the CDN checkout and Drive root, a fake `id_reader`, and `--no-commit` everywhere except one git test with a `git init` temp repo):
  - `test_from_drive_section_folder`: `root/blue/new.png` with next number 114 gives `cdn/images/blue/blue-114.jpg` 1600 wide, `root/blue/blue-114.png`, and meta `hi == {"id":"ID1","w":…,"h":…,"bytes":…,"ext":"png","src":"new.png"}`.
  - `test_from_drive_root_file_needs_confirmation`: a root-dropped file without `--yes` and with input `"n"` (patch `builtins.input`) → nothing moved, exit code 1. With `--yes`, it goes to the guessed section.
  - `test_drive_paused_records_pending` (Review Focus 1): the reader always returns `None` and the timeout is patched to 0.01 → the web JPEG exists, `hi == {"pending": True, "src": "new.png"}`, and the exit code is 0.
  - `test_rerun_is_idempotent` (Review Focus 2): running `--from-drive` twice leaves one catalogue entry and one JPEG.
  - `test_local_mode_without_drive_marks_pending`: `drive_root()` returns `None` → the existing CLI `add-images.py blue <dir>` works as before, plus `hi.pending`.
  - `test_commit_sets_gallery_cdn`: a temp git CDN repo → after the run, `$meta.gallery_cdn` ends with `@<HEAD sha>/images`.
  - `test_sync_links_named_original`: an entry `blue-114.jpg` without `hi`, plus `root/blue/blue-114.tif` → gets `hi.id`.
  - `test_sync_skips_ambiguous`: both `blue-114.tif` and `blue-114.png` → still pending, and the output mentions both names.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. Keep the existing positional CLI working, and keep every existing test in `test_add_images.py` passing.
- [ ] **Step 4:** Run the full image test set (the 4 files + `test_hires.py` + `test_sync_hires.py`). Expected: PASS.
- [ ] **Step 5: Commit** with the message "add-images: originals from Drive, high-res links, pinned gallery; sync-hires.py".

### Task 5a: Inbox with review, so Jimmy can keep adding images

Added 22 Nov after Jimmy chose a local drop folder in his Downloads (path given in chat; pass it as `--inbox`, never hard-code it). He keeps adding files while batches run.

**Files:**
- Modify: `scripts/hires.py` (fingerprints, stability)
- Create: `scripts/inbox.py` (review and apply)
- Test: `tests/test_inbox.py`

**Interfaces (produces):**
- `hires.fingerprint(path: Path) -> str`: a 256-bit difference hash (greyscale 17×16, each pixel against its right neighbour) as 64 hex characters. `hires.fp_distance(a: str, b: str) -> int` returns the Hamming distance.
- `hires.is_stable(path: Path, quiet_seconds: float = 60, now=None) -> bool`: true when the file's mtime is older than `quiet_seconds`.
- Every catalogue entry gains `fp` (taken from its web JPEG). `scripts/inbox.py --backfill-fp --cdn-dir ../azmx-brand-cdn` fills `fp` for the existing 240 from the CDN checkout.
- `inbox.py review --inbox PATH`:
  - Takes every stable image file in the inbox. Files directly in it get a guessed section (`guess_section`); files in `PATH/<section>/` keep that section.
  - Flags each file: `duplicate` (distance ≤ 10 to a catalogue entry or to an earlier file in this review), `possible-duplicate` (11–20), or `small` (width < 1600).
  - Writes `PATH/_review/inbox-plan.json`, a list of `{"file", "size", "mtime", "section", "fp", "flags", "dup_of"}`, and `PATH/_review/review.html`, a contact sheet: thumbnail, file name, pixel size, guessed section, flags, and the image it duplicates shown beside it.
- `inbox.py apply --inbox PATH [--cdn-dir] [--no-commit]`:
  - Processes only the files in `inbox-plan.json` whose size and mtime still match, one at a time, in plan order.
  - Skips `duplicate` files, and `small` and `possible-duplicate` files unless the plan entry has `"ok": true` (Jimmy's call, set through review).
  - For each file: make the web JPEG at `min(1600, width)`, never upscaling; record the entry with `fp`; copy the original to the Drive section folder through `place_original`; check the copy's size matches; delete it from the inbox; read the Drive ID (pending on timeout).
  - Files that appeared after the review are untouched and listed as "new since review".
  - Ends with the same commit and pin step as Task 5.
- The `_review` folder is ignored by `review`.

- [ ] **Step 1: Write the failing tests** (`tmp_path` inbox, fake Drive root, fake ID reader, `--no-commit`):
  - `test_review_skips_unstable_files`: a file with mtime = now is absent from the plan.
  - `test_review_flags_duplicate_against_catalogue_and_batch`: an image already catalogued (same pixels) gets `duplicate`, and a re-saved copy of an earlier inbox file gets `duplicate` with `dup_of` set.
  - `test_review_flags_small`: 1456×816 → `small`.
  - `test_review_section_from_subfolder`: `PATH/red/x.png` → `section == "red"` with no guess.
  - `test_apply_only_planned_and_unchanged`: a file added after the review stays in the inbox, and so does a planned file whose mtime changed; both are listed in the output.
  - `test_apply_moves_original_and_never_upscales`: a 1456 px original gives a 1456 px web JPEG (with `"ok": true`), a 2944 px one gives 1600 px; both originals are now in Drive under the new numbers and gone from the inbox.
  - `test_apply_interrupted_leaves_file_in_inbox`: patch `place_original` to raise on the 2nd file → the 1st file is fully done, the 2nd is still in the inbox, its JPEG is removed, and the catalogue has only the 1st.
  - `test_rerun_apply_is_noop`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. Reuse `add_one` from Task 5; give it a `max_width` that defaults to `TARGET_WIDTH` and a `fp` field.
- [ ] **Step 4:** Run all image tests. Expected: PASS.
- [ ] **Step 5: Commit** with the message "inbox.py: review sheet, duplicate checks, safe apply".

### Task 6: Docs, live run and verification

**Files:**
- Modify: `references/image-pipeline.md` (Add step, new "High-res originals" section), `CONTRIBUTING.md` (the image section), `CHANGELOG.md` (new entry, following the existing version pattern)

- [ ] **Step 1:** Document the flow in `image-pipeline.md` and `CONTRIBUTING.md`:
  - Jimmy drops originals into a section folder, or into the root of "Brand Images Gallery".
  - Run `python3 scripts/add-images.py --from-drive`.
  - Anywhere without Drive, images stay "high-res pending"; run `sync-hires.py` later on the Mac.
  - Pushing order: CDN repository first.
  - High-res needs an AZMX sign-in.

  Name the folder as `AZM X › Branding › Brand Images Gallery`, without any account email.
- [ ] **Step 2:** Run the whole suite, `./run-tests.sh`. Expected: everything passes; compare with the Task 0 baseline plus the new tests.
- [ ] **Step 3: Live run on Jimmy's drop folder.** Run `python3 scripts/inbox.py --backfill-fp`, then `inbox.py review`. Open `review.html` for Jimmy and wait for his corrections (sections, which `small` and `possible-duplicate` images to keep). Write them into the plan, then run `inbox.py apply`. Check the result: every new card in a local `http.server` preview has a High-res button; three Drive links open in Dia signed in as azmx.sa; one opens a sign-in page in a private window.
- [ ] **Step 4:** Scroll the whole local gallery in the built-in browser and run the same check as on 22 Nov: every `img` is `complete` with `naturalWidth > 0`, and there are no `error` events.
- [ ] **Step 5:** Commit the docs. Then **stop and ask Jimmy** before pushing, listing the two push commands in order:
  1. `git -C ../azmx-brand-cdn push`
  2. `git push -u origin image-library-hires`, then a PR to `main`

  Before pushing, check the staged diff for any account email or token.
- [ ] **Step 6:** After Jimmy pushes and GitHub Pages rebuilds, repeat Step 4 on `https://gamaleldientarek.github.io/azmx-brand/`.
- [ ] **Step 7:** Tell Jimmy the one setting only he can change: in Drive, give "Brand Images Gallery" the general access "AZM X (azmx.sa): anyone in this group with the link can view", so staff outside the shared drive can open the links.
