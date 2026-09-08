# Presentation Transitions

How an AZMX deck built as Figma **frames** is turned into a keyboard-driven presentation: Space advances, Backspace goes back, slides cross-fade with Smart Animate. Validated on the Figma Service Partner deck, 19 slides, 2026-08-26.

This is for decks built as ordinary frames on a design page. Figma Slides has its own built-in transitions and needs none of this.

---

## The spec

| Setting | Value | Why |
|---|---|---|
| Trigger, forward | **Key/Gamepad · Space** | The key a presenter's thumb finds without looking. Also what every clicker sends. |
| Action | **Navigate to** the next frame | — |
| Animation | **Smart animate** | Elements that share a layer name across two slides tween instead of cutting. This is the whole reason to do it in Figma rather than export a PDF. |
| Easing | **Slow** | A spring preset. Reads as considered rather than snappy, which suits an editorial deck. |
| Duration | **600 ms** | Long enough to read as motion, short enough that a presenter mid-sentence is not waiting for it. Below ~400 ms it reads as a cut; above ~800 ms the room notices the deck instead of the argument. |
| Trigger, backward | **Key/Gamepad · Backspace** → **Back** | `Back` returns through actual navigation history, so it works even when the path was not linear. |
| Flow starting point | **slide 01**, named `Start` | Makes the play button open the deck at the beginning rather than at whatever frame was last selected. |
| Last slide | **Backspace only** | There is nothing to advance to. Giving it a Space action that goes nowhere is a dead key press in front of an audience. |

**Smart Animate matches layers by name.** Two slides that both contain a layer called `Headline` will tween that headline's position, size and colour between them. Two slides whose headlines are called `Headline` and `Title` will hard-cut. If a run of slides should feel continuous — an act cover flowing into its first content slide, a stat that grows — give the shared elements the **same layer name** on both frames. This costs nothing and is the difference between a deck that moves and a deck that flickers.

---

## Applying it

Run `scripts/figma-slide-transitions.js` through the Figma Console MCP (`figma_execute`) with the Desktop Bridge plugin open on the target file. Edit the two constants at the top: the page name, and the ordered list of frame IDs.

Get the frame IDs in canvas order first — do not trust layer-panel order or frame names, both of which drift:

```js
await figma.loadAllPagesAsync();
const page = figma.root.children.find(p => p.name === 'YOUR PAGE');
const slides = [];
(function scan(n){ for (const c of n.children) {
  if (c.type === 'FRAME' && Math.round(c.width) === 1920 && Math.round(c.height) === 1080) slides.push(c);
  else if ('children' in c && c.type !== 'INSTANCE') scan(c);
} })(page);
slides.sort((a,b) => Math.round(a.absoluteTransform[1][2]) - Math.round(b.absoluteTransform[1][2])
                  || Math.round(a.absoluteTransform[0][2]) - Math.round(b.absoluteTransform[0][2]));
return slides.map(s => ({ id: s.id, name: s.name }));
```

That sorts top-to-bottom then left-to-right, which matches how decks are laid out in rows. **Read the returned names back and confirm the order is the running order** before applying anything.

---

## The API shape

```js
await frame.setReactionsAsync([
  {
    trigger: { type: 'ON_KEY_DOWN', device: 'KEYBOARD', keyCodes: [32] },   // Space
    actions: [{
      type: 'NODE',
      destinationId: nextFrameId,
      navigation: 'NAVIGATE',
      transition: { type: 'SMART_ANIMATE', easing: { type: 'SLOW' }, duration: 0.6 },
      preserveScrollPosition: false
    }]
  },
  {
    trigger: { type: 'ON_KEY_DOWN', device: 'KEYBOARD', keyCodes: [8] },    // Backspace
    actions: [{ type: 'BACK' }]
  }
]);

page.flowStartingPoints = [{ nodeId: firstFrame.id, name: 'Start' }];
```

### Four things that will catch you

1. **`duration` is in seconds, not milliseconds.** 600 ms is `0.6`. Passing `600` asks for a ten-minute transition and Figma will accept it.
2. **Use `setReactionsAsync()`.** Assigning to `.reactions` is deprecated and silently does nothing in current builds.
3. **`SLOW` is a spring preset**, alongside `GENTLE`, `QUICK` and `BOUNCY`. It coexists with an explicit `duration` in the current build, but that is not guaranteed across versions — if it ever throws, fall back to `{ type: 'EASE_OUT' }`, which is the closest fixed-curve equivalent, and keep the 0.6.
4. **`setReactionsAsync` replaces every reaction on the frame.** Pass both the Space and the Backspace reaction in the same array. Calling it twice leaves only the second.

### Key codes

| Key | Code |
|---|---|
| Space | 32 |
| Backspace | 8 |
| Right arrow | 39 |
| Left arrow | 37 |

Arrows are worth adding alongside Space and Backspace when someone else may drive the deck — most presenters reach for them by instinct. Add them as extra triggers in the same array, not as a replacement.

---

## Checking it worked

```js
const f = await figma.getNodeByIdAsync('FRAME_ID');
return f.reactions.map(r => ({
  key: r.trigger.keyCodes,
  action: r.actions[0].type,
  to: r.actions[0].destinationId || null,
  transition: r.actions[0].transition || null
}));
```

Then press play. Space should advance with visible motion, not a cut. If it cuts, the two frames share no matching layer names and Smart Animate has nothing to tween — that is a naming problem, not a transition problem.

---

## RTL layout for Arabic presentations

Every AZMX deck is Arabic RTL. These rules are extracted from the production email RTL system (`email-design-system.md` §A1) and adapted for Figma slide layouts. **Violating them produces a deck that reads as unprofessional** — mirrored chevrons, left-aligned Arabic, and numerals that break bidi.

### R1. Slide canvas direction (non-negotiable)

1. **All text flows right-to-left.** Headlines, body, captions, meta — everything anchors to the slide's right edge and reads rightward.
2. **Auto-layout frames use `Right to left` spacing direction.** This is under Layout settings → Direction. Without it, elements stack LTR and the slide reads backwards.
3. **Text layers use `Right` alignment** (not `Left`, not `Center` unless it is a true centered title over a centered mark). Set this explicitly — Figma does not infer it from the frame direction.
4. **Visual hierarchy flows right → left.** The first thing an audience sees is the right edge: hero numbers, opening headlines, the slide's anchor. Secondary elements (supporting copy, sources, footnotes) sit left. This is the inverse of an English deck and must be designed intentionally, not mirrored in post.

### R2. Chevrons — the most visible RTL defect (always audit)

**Chevrons always point LEFT** (`‹` U+2039 SINGLE LEFT-POINTING ANGLE QUOTATION MARK) and **never RIGHT** (`›` U+203A). In the email system, chevrons live in `<span dir="ltr">` to prevent the Unicode bidi algorithm from auto-mirroring them. In Figma:

1. **Use the actual glyph `‹` (U+2039), not `<` (less-than).** The less-than is a code symbol and reads as broken in Arabic copy. Copy the correct glyph from this document or from `email-design-system.md`.
2. **Test every chevron in context.** Some Arabic fonts mirror U+2039 anyway (a font bug, not a Figma bug). If a glyph renders as `›` when it should be `‹`, change the font to one that respects the Unicode direction — `Azm X` and `IBM Plex Sans Arabic` both do.
3. **Common chevron use cases:**
   - **Triple-chevron eyebrows** (section intros, act breaks): `‹‹‹ القسم الأول` with 4–6px letter-spacing on the chevrons only. Put the three chevrons in their own text layer with LTR direction if the spacing glitches.
   - **Inline navigation hints** (slide footers, breadcrumbs): always `‹` preceding the action, e.g., `‹ السابق`.
   - **Bulleted lists:** use `‹` or an Arabic bullet `•` or an em-dash `—`, never `›`. Position the bullet to the **right** of the text (RTL list marker position).

### R3. Latin fragments & numerals (constant bidi traps)

**Every Latin or numeric fragment breaks RTL flow** unless explicitly marked. In the email system, these sit in `<span dir="ltr">`. In Figma:

1. **Years, dates, version numbers, English names, URLs:** wrap each in its own text layer with LTR direction, or if inline, set the entire parent text to RTL but **manually force the fragment's direction** by selecting it and setting its script to Latin. Without this:
   - `2026` in an Arabic sentence may render as `6202`
   - `Q4` becomes `4Q`
   - `v1.5` becomes `5.1v`
   - `June 13` becomes `13 June` or worse, `enuJ 31`
2. **Example safe pattern:**
   - Headline: `إطلاق المنصة في` (RTL text layer) + `2026` (LTR text layer) side by side in an RTL auto-layout.
   - OR: single text layer, entire string `إطلاق المنصة في 2026`, parent direction RTL, manually select `2026` and confirm it is LTR in the character panel.
3. **Test with a year or English word in every Arabic text block.** If it reads backwards, the direction is wrong.

### R4. Layer naming for Smart Animate RTL continuity

**Smart Animate tweens layers with matching names.** For a headline that transitions across two slides in RTL, both must:

1. **Share the exact layer name** (e.g., `Headline` on slide 1 and slide 2).
2. **Keep the same text direction** (RTL on both). If one is RTL and one is LTR, Figma treats them as different languages and may hard-cut instead of tweening, or worse, tween the geometry but re-render the glyphs mid-transition.
3. **Use consistent alignment** (both `Right`). Tweening from right-aligned to left-aligned reads as broken motion.

**RTL naming convention for shared elements:**

| Layer type | Name pattern | Notes |
|---|---|---|
| Arabic headline that tweens | `Headline` | Same name, RTL, right-aligned on all slides |
| Numeral or stat that grows | `Stat` | If the number is part of Arabic copy, keep the parent RTL; if standalone, LTR text is safe |
| Chevron trio eyebrow | `Eyebrow` or `Chevron` | If letter-spaced, keep chevrons in their own LTR layer to prevent spacing glitches |
| Footer / breadcrumb with `‹` | `Footer` | RTL parent, chevron in nested LTR layer if needed |

**What breaks:** A headline named `Headline AR` on slide 1 and `Headline` on slide 2 will hard-cut. A numeral in an LTR layer on slide 1 and inline RTL on slide 2 may tween position but flip the glyphs mid-transition (looks like a rendering bug to the audience).

### R5. Kashida & spacing (never fake it)

From the email system: **`letter-spacing` is never set on Arabic text** (kashida does the stretching). In Figma:

1. **Do not apply letter-spacing to Arabic layers.** It breaks ligatures and reads as a typographic error. If wordmark lockups (e.g., `وش صـــار؟` with kashida) are needed, **copy-paste the exact string from brand assets** — never retype it or Figma will strip the kashida.
2. **Letter-spacing is only used on:**
   - Latin all-caps (e.g., `SECTION 01` at 2–4% tracking)
   - The triple-chevron eyebrow (`‹‹‹` at 4–6px, Latin direction layer)
3. **Test:** If Arabic text looks stretched or gapped unnaturally, letter-spacing is on and must be removed.

### R6. RTL QA checklist (before final export or handoff)

Run this on every deck:

- [ ] **All text layers are right-aligned** (except true centered titles).
- [ ] **All auto-layout frames use `Right to left` direction.**
- [ ] **Every chevron is `‹` (U+2039) and points LEFT.** Audit the title slide, section breaks, footers, and any bulleted lists.
- [ ] **Every year, date, numeral, and English word renders in the correct direction** (years are not backwards, `Q4` is not `4Q`).
- [ ] **Headlines that transition across slides share the same layer name, direction, and alignment.**
- [ ] **No letter-spacing on Arabic text** (except kashida wordmarks copy-pasted from assets).
- [ ] **Play the deck in present mode** and watch the first three transitions. If any Arabic text or numerals look like they flip or re-render mid-tween, the direction or naming is inconsistent.

**The most common defects in shipped decks:** mirrored chevrons (`›` instead of `‹`), left-aligned Arabic headlines, backwards years, and headlines that hard-cut instead of tweening because one slide's layer was LTR and the other RTL. All are preventable with this checklist.

---

## What not to do

- **Do not use Dissolve.** It reads as a slideshow template. Smart Animate on a system-built deck moves the actual elements, which is the point.
- **Do not put a transition on the last slide's Space.** Nothing to navigate to.
- **Do not set transitions before the deck order is final.** Reordering slides afterwards means rewiring every frame, because `destinationId` is a hard reference.
- **Do not mix durations across a deck.** One value everywhere. A transition that changes speed mid-deck reads as a mistake.
- **Do not mirror an English deck to make it RTL.** Mirroring flips chevrons the wrong way, breaks numeral direction, and produces left-aligned Arabic. Build RTL from the ground up.
