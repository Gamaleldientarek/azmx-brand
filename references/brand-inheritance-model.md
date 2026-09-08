# Brand Inheritance Model: AZM X and Sub-Brands

The parent-brand/sub-brand relationship formalized. What Colab, Majarah, Clix, and Anatomi inherit from AZM X, what they override, and how conflicts resolve. This document makes the multi-brand architecture extensible: a sixth brand onboards by following this model, not by inventing a new pattern.

---

## 1. The inheritance hierarchy

```
AZM X (Parent)
├── Design Tokens (Primitives → Palette → Semantic → Component)
├── Editorial Mechanics (no AI tells, max 3 hashtags, no emojis)
├── Writing Principles (lead with value, be clear, write like a human)
└── Voice Dimensions (Formality, Technicality, Attitude, Purpose)
    
Sub-Brand (Colab, Majarah, Clix, Anatomi)
├── ✓ Inherits: Token structure, editorial mechanics, writing principles
└── ✗ Overrides: Voice dimensions, palette selection (where visual system exists)
```

**The rule:** Sub-brands **inherit all mechanics** and **override the voice**. The system stays consistent; the personality shifts.

---

## 2. Token inheritance rules

Sub-brands follow AZM X's token architecture but may switch palettes or define their own visual system.

### What sub-brands inherit

| Layer | Inherits | Detail |
|---|---|---|
| **Token structure** | Yes | The five-tier system: Primitives → Palette → Semantic → Component |
| **Semantic bindings** | Yes | `surface/page`, `text/heading`, `border/subtle` and all 550+ tokens |
| **Spacing scale** | Yes | `space/none` through `space/2xl`, the exact values |
| **Type scale** | Yes | Display and Body ramps, unless the sub-brand visual system specifies otherwise |
| **Radius and border** | Yes | `radius/xs` through `radius/pill`, `border-width/hairline` etc. |
| **Icon system** | Yes | Phosphor Icons, weight Regular, unless visual system overrides |
| **Light/Dark theme switch** | Yes | The semantic layer resolves in both modes |

### What sub-brands override

| Override | How | Example |
|---|---|---|
| **Palette switch** | Set `1b. Palette` variable in Figma | Hospitals Report runs Orange; a Colab deck could run Green |
| **Visual system** | Load the sub-brand's design skill | Colab: `colab-design` (Dark green ground, Electric Green, pixel/dither motif)<br>Majarah: `majarah-design` (Deep purple ground, Electric Purple, Oswald display type) |
| **Signature color** | Via palette or sub-brand primitives | Colab and Majarah have `brand/{colab|majarah}/*` primitives; never apply these to AZM X surfaces |

### The binding rule

**Bind to Semantic. Never to Primitives.** This is the load-bearing rule that keeps sub-brands portable.

A Colab deck using AZM X tokens switches the palette to Green and binds to `surface/accent`, `text/accent`, etc. The semantic tokens resolve to Colab's green values automatically. No duplicate files, no hard-coded hex.

Colab and Majarah's **own design skills** carry their full visual systems (typography, motifs, layouts). When those skills are loaded, they supersede AZM X's visuals entirely. When not loaded, a Colab deliverable **asks which visual system applies** rather than silently dressing it in AZM X navy.

### Sub-brand palette primitives (out of bounds for AZM X)

`brand/colab/*` and `brand/majarah/*` live in Primitives so the sub-brand files can share one source. **Never apply them to an AZM X surface.** Load `colab-design` or `majarah-design` for that work.

**Accessibility note:** Colab's Electric and Jade greens are banned on light grounds (1.34:1 and 1.29:1). The semantic layer enforces this by aliasing to text-safe steps.

---

## 3. Voice dimension inheritance

Sub-brands inherit AZM X's **editorial mechanics** in full but override the **Four Dimensions** (Formality, Technicality, Attitude, Purpose).

### What sub-brands inherit: Editorial mechanics (always enforced)

These are the no-AI-tells rules. Every brand — AZM X, Colab, Majarah, Clix, Anatomi — ships copy that passes this bar.

| Mechanic | Rule | Applies to |
|---|---|---|
| **Em-dashes** | Not the default connector. Use commas, periods, or colons. | All five brands |
| **Triads** | One strong claim beats three padded ones ("fast, simple, and powerful" is a tell). | All five brands |
| **Empty intensifiers** | Ban: "truly," "seamlessly," "effortlessly," "robust," "leverage," "elevate," "unlock," "empower," "delve." | All five brands |
| **Hedging** | Commit. It does or it does not; skip "can help," "may enable." | All five brands |
| **Summaries restating headings** | If the heading said it, the body adds something new or gets cut. | All five brands |
| **Symmetrical paragraph lengths** | Vary rhythm like a human editor would. | All five brands |
| **Hashtags** | Three maximum, at the end. Every channel. | All five brands |
| **Emojis in copy** | None. Headlines, body, captions, subject lines, social posts. The one exception: email design system's section-header and digest chip glyph (C03, C04, C07, C16) — it is a visual chip, not copy. | All five brands |
| **Mandatory CTAs** | No. Where a next step exists, make it obvious. Where it does not, do not manufacture one. | All five brands |

**Source:** `voice-and-tone.md` § Writing mechanics. These rules are the shared foundation. They apply to all five without exception (narrow carve-out for email glyph noted above).

### What sub-brands inherit: Universal writing principles (always enforced)

| Principle | What it requires | Applies to |
|---|---|---|
| **Lead with value** | Answer "what's in it for me?" with a clear benefit. | All five brands |
| **Be clear and concise** | Short sentences, no jargon, the point up front. | All five brands |
| **Write like a human** | Approachable and authentic. Use contractions in English. Read it aloud; if it sounds like a robot, rewrite it. | All five brands |
| **Have a clear purpose** | Every piece carries one takeaway message and one job. | All five brands |
| **Use hashtags strategically** | Three maximum, at the end. Mix broad, niche, and branded tags. | All five brands |

**Source:** `voice-and-tone.md` § Universal writing principles.

### What sub-brands override: The Four Dimensions

Each sub-brand redefines Formality, Technicality, Attitude, and Purpose to match its archetype and audience. The parent's dimensions do not apply.

| Brand | Archetype | Formality | Technicality | Attitude | Purpose |
|---|---|---|---|---|---|
| **AZM X** | Visionary Expert & Strategic Partner | Mid-formal | Balanced | Bold but respectful | Inspirational or pragmatic |
| **Colab** | The Empathetic Analyst | Adaptable | Translates complexity | Confident in the evidence | Balances vision and action |
| **Majarah** | The Inclusive Mentor | Slightly informal | Accessible and clear | Bold and encouraging | Inspirational or pragmatic (Balanced) |
| **Clix** | The Trusted Operator | Mid-formal | Radically simple | Quietly confident | Pragmatic and scalable |
| **Anatomi** | The Analyst–Curator | Mid-formal | Balanced | Neutral and insightful | Pragmatic and aspirational |

**How to use this table:**

1. Identify the brand on the deliverable (not the team producing it).
2. Read that brand's calibration examples in `sub-brand-voices.md` before writing.
3. Check the draft against **that brand's** Four Dimensions, not AZM X's.
4. Apply AZM X's editorial mechanics regardless of which brand you are writing for.

**Example:** A Colab research report is written in Colab's voice (Formality: Adaptable, Technicality: Translates complexity) but enforces AZM X's mechanics (no emojis, max 3 hashtags, no em-dash defaults).

---

## 4. Editorial rule inheritance

Editorial rules = copywriting mechanics + format-specific guidance. Sub-brands inherit the structure and enforce their own voice within it.

### Inherited across all brands

| Rule | Detail | Source |
|---|---|---|
| **Headlines and heroes** | Serif voice (Display ramp), short, mixed-case. A single sharp idea. No period at the end. | `voice-and-tone.md` § By format |
| **Eyebrows/labels** | UPPERCASE, 1 to 3 words, functional not clever. | `voice-and-tone.md` § By format |
| **Body copy** | Sentence case, short paragraphs. Front-load the point. | `voice-and-tone.md` § By format |
| **Stats** | Let the number talk. Label in plain words underneath, no adjectives. | `voice-and-tone.md` § By format |
| **Quotes/testimonials** | Verbatim, trimmed only for length, attributed with name and title. | `voice-and-tone.md` § By format |
| **Email subject lines** | Under 45 characters. Preheader completes the subject rather than repeating it. | `voice-and-tone.md` § By format |
| **Social/LinkedIn** | First line earns the click alone (it is all people see collapsed). No hashtag walls; 3 maximum, at the end. | `voice-and-tone.md` § By format |
| **Arabic typography** | RTL layout rules from the email design system. Kashida-stretched wordmarks copy-pasted, never retyped. | `voice-and-tone.md` § Brand language |
| **Translation philosophy** | Match the brand's archetype rather than the English sentence. Colab stays precise, Majarah stays warm, Clix stays plain, Anatomi stays neutral. | `sub-brand-voices.md` § Language |

### Brand-specific tuning within inherited formats

The structure is shared; the tone adapts.

| Brand | How it tunes the inherited format |
|---|---|
| **Colab** | Headlines state a finding. Stats cite the source. Body copy separates evidence from insight (two sentences, not one). |
| **Majarah** | Headlines invite. Stats inspire. Body copy is warm but never vague (friendly is not casual). |
| **Clix** | Headlines describe the feature's ROI in plain words. Stats prove time saved. Body copy avoids enterprise jargon. |
| **Anatomi** | Headlines name the pattern or heuristic. Stats cite the comparison set. Body copy is neutral until the insight, which is bold. |

---

## 5. Conflict resolution rules

What happens when parent and sub-brand rules appear to clash.

| Conflict type | Resolution | Example |
|---|---|---|
| **Voice vs. mechanics** | **Mechanics always win.** Sub-brand voice operates within the mechanical constraints. | Majarah is warm and encouraging, but it still enforces the emoji ban and the 3-hashtag limit. |
| **Semantic token vs. sub-brand palette** | **Bind to Semantic.** The palette switch resolves automatically. | A Colab deck binds to `text/accent`. The Green palette makes that resolve to Colab's text-safe green. No conflict. |
| **Sub-brand visual system vs. AZM X tokens** | **Sub-brand visual system wins.** Load `colab-design` or `majarah-design` when working in that brand. | Majarah uses Oswald display type, not thmanyah. The Majarah skill overrides the type scale. |
| **Sub-brand voice example vs. banned word** | **Keep the example verbatim; do not reuse the word in new copy.** | Majarah's calibration sample uses "unlock," which is banned. The sample stays as-is (it is a tuning reference), but new Majarah copy does not carry "unlock." |
| **Parent Purpose mode vs. sub-brand Purpose mode** | **Use the sub-brand's Purpose definition.** Each brand defines its own modes. | Colab's Purpose is "Evidence-Driven" or "Action-Oriented," not AZM X's "Inspirational" or "Pragmatic." Use Colab's. |
| **Format rule vs. brand archetype** | **The format structure is inherited; the brand tunes the execution.** | All brands use eyebrows (UPPERCASE, 1–3 words). Colab's eyebrows name the data source ("USABILITY AUDIT"). Majarah's invite the reader ("JOIN US"). Same format, different voice. |

---

## 6. Examples for each sub-brand

Concrete inheritance in practice.

### Colab (The Empathetic Analyst)

**Inherits from AZM X:**
- Token structure: Binds to `surface/page`, `text/heading`, `text/primary`, etc.
- Editorial mechanics: No emojis, max 3 hashtags, no em-dashes as defaults, no "unlock"/"leverage"/"seamlessly"
- Format rules: Eyebrows UPPERCASE, stats let the number talk, subject lines under 45 characters
- Writing principles: Lead with value, be clear and concise, write like a human

**Overrides:**
- Voice dimensions: Formality = Adaptable (formal in reports, conversational in workshops), Technicality = Translates complexity, Attitude = Confident in the evidence, Purpose = Evidence-Driven or Action-Oriented
- Palette: Can run Green instead of Blue (or Orange, Yellow, etc.) via `1b. Palette` switch
- Visual system: When `colab-design` skill is loaded, uses Dark green ground, Electric Green accent, pixel/dither motif, and Colab's own typography

**Example in practice:**

| Surface | AZM X approach | Colab approach |
|---|---|---|
| **Deck headline** | "Designing the Future of Experience" (visionary, serif) | "Our evidence shows the checkout flow causes 40% abandonment" (precise, finding-first, serif) |
| **Stat tile** | "80%" label: "Growth in Q3" | "80%" label: "Task completion rate (n=120)" |
| **Email subject** | "New insights on digital maturity" | "Your usability audit is ready" |
| **Body copy** | "We believe a human-centric approach is the most powerful path to market leadership." | "The data shows that 85% of users who interacted with the new feature abandoned the task. Our insight is that it fails to meet their primary expectation." |

Notice: Same format structure (serif headline, stat + label, subject under 45 chars, short body sentences). Different voice (visionary vs. evidence-driven). Same mechanics (no emojis, no triads, no "unlock").

---

### Majarah (The Inclusive Mentor)

**Inherits from AZM X:**
- Token structure: Same as above
- Editorial mechanics: Same as above
- Format rules: Same as above
- Writing principles: Same as above

**Overrides:**
- Voice dimensions: Formality = Slightly informal, Technicality = Accessible and clear, Attitude = Bold and encouraging, Purpose = Inspirational or Pragmatic (Balanced)
- Palette: Can run Purple via `1b. Palette` switch
- Visual system: When `majarah-design` skill is loaded, uses Deep purple ground, Electric Purple accent, Oswald display type

**Example in practice:**

| Surface | AZM X approach | Majarah approach |
|---|---|---|
| **Deck headline** | "Designing the Future of Experience" | "Together, we're shaping the future of digital experiences in the region" |
| **Stat tile** | "200+" label: "Projects delivered" | "200+" label: "Community members" |
| **Email subject** | "Invitation to our annual summit" | "Ready to connect? Join us Friday" |
| **Body copy** | "AZMX is a leading Saudi digital consultancy." | "In this workshop, you'll learn a 5-step framework for conducting effective usability tests." |

Notice: Warmer, more inviting ("Ready to connect?") but still no emojis, still max 3 hashtags, still short sentences. The mechanics hold; the personality shifts.

---

### Clix (The Trusted Operator)

**Inherits from AZM X:**
- Token structure: Same as above
- Editorial mechanics: Same as above
- Format rules: Same as above
- Writing principles: Same as above

**Overrides:**
- Voice dimensions: Formality = Mid-formal, Technicality = Radically simple, Attitude = Quietly confident, Purpose = Pragmatic and scalable
- Palette: Can run any palette; Clix has no dedicated visual skill yet (ask which system applies)
- Visual system: None yet. Use AZM X tokens or ask.

**Example in practice:**

| Surface | AZM X approach | Clix approach |
|---|---|---|
| **Deck headline** | "Resilient, scalable systems that grow with your business" | "Create and send a compliant invoice in under 60 seconds" |
| **Stat tile** | "99.9%" label: "Uptime SLA" | "60 seconds" label: "Average invoice creation time" |
| **Email subject** | "Your Q3 performance report" | "Invoice #1234 is due next week" |
| **Body copy** | "We build resilient, scalable systems that can grow with your business." | "Clix simplifies your invoicing process, saving you time and ensuring accuracy." |

Notice: Plain business language ("Invoice #1234 is due next week"), no enterprise buzzwords, no hype ("revolutionize," "game-changing"). The mechanics and format are identical to AZM X; the vocabulary is radically simpler.

---

### Anatomi (The Analyst–Curator)

**Inherits from AZM X:**
- Token structure: Same as above
- Editorial mechanics: Same as above
- Format rules: Same as above
- Writing principles: Same as above

**Overrides:**
- Voice dimensions: Formality = Mid-formal, Technicality = Balanced, Attitude = Neutral and insightful, Purpose = Pragmatic and aspirational
- Palette: Can run any palette; Anatomi has no dedicated visual skill yet (ask which system applies)
- Visual system: None yet. Use AZM X tokens or ask.

**Example in practice:**

| Surface | AZM X approach | Anatomi approach |
|---|---|---|
| **Deck headline** | "Pioneering the future of digital experience" | "This app's onboarding is a leading example in the financial sector, scoring 9/10 on our clarity heuristic" |
| **Stat tile** | "9/10" label: "Client satisfaction" | "9/10" label: "Clarity heuristic score" |
| **Email subject** | "New insights on regional UX trends" | "Your benchmark report: Top 5 e-commerce apps" |
| **Body copy** | "We are elevating the digital maturity of the entire region." | "This app uses a prominent floating action button to keep the primary action always accessible." |

Notice: Neutral, objective, cites the method ("scoring 9/10 on our clarity heuristic"). No superlatives without evidence. The mechanics and format match AZM X; the attitude is methodical and curatorial.

---

## 7. Adding a new sub-brand

The inheritance model makes onboarding a sixth brand a configuration exercise, not a from-scratch build.

### Step 1: Define the voice dimensions

Fill in the Four Dimensions and archetype:

```
Brand: [Name]
Archetype: [One-line positioning]
Formality: [Position] — [We are] · [We are not]
Technicality: [Position] — [We are] · [We are not]
Attitude: [Position] — [We are] · [We are not]
Purpose: [Mode 1 name] or [Mode 2 name] — [Context for each]
```

Write three calibration examples per dimension (Wrong one direction / Wrong the other / Brand voice). Write Purpose mode examples.

### Step 2: Document the one trap

What is this brand's most likely failure mode, and how do you correct it?

| Brand | Most likely failure | The correction |
|---|---|---|
| [Name] | [Predictable failure] | [The fix] |

### Step 3: Configure tokens

Decide:
- Does this brand use AZM X tokens with a palette switch? If yes, which palette (Blue, Orange, Green, Yellow, Purple, Red)?
- Does this brand have its own visual system? If yes, define primitives in `brand/[name]/*` and create a `[name]-design` skill.
- Typography: Inherit AZM X's Display and Body ramps, or override?
- Icons: Phosphor Regular, or override?

### Step 4: Add the sub-brand to the reference files

1. Add a section to `sub-brand-voices.md` following the Colab/Majarah/Clix/Anatomi pattern.
2. If a visual system exists, note it in the table at the top of `sub-brand-voices.md`.
3. Add the brand to the table in § 6 of this file (Examples for each sub-brand).

### Step 5: Update the validation tooling

Add the brand to `brand-check.py` so it validates deliverables against the inherited + overridden token set.

### Step 6: Test the inheritance

Create a test deliverable (e.g., a one-slide deck) and verify:
- [ ] Token bindings resolve correctly
- [ ] Voice dimensions are distinct from AZM X and other sub-brands
- [ ] Editorial mechanics are enforced (no emojis, max 3 hashtags, no AI tells)
- [ ] Format rules are followed (eyebrows UPPERCASE, stats plain, etc.)
- [ ] Conflict resolution rules work as expected

**Expected outcome:** The new brand is production-ready without code changes. Only configuration.

---

## 8. Validation and compliance

How to verify a deliverable follows the inheritance model.

### Manual checklist

| Check | Pass/Fail | What to verify |
|---|---|---|
| **Brand identification** | | Is the brand on the deliverable correct? (Colab case study = Colab voice, not AZM X voice) |
| **Token bindings** | | Are all colors, typography, spacing bound to Semantic tokens, not Primitives or raw hex? |
| **Palette switch** | | If a sub-brand palette is used, is `1b. Palette` set correctly in Figma? |
| **Visual system** | | If a sub-brand visual system exists (`colab-design`, `majarah-design`), was it loaded? |
| **Voice dimensions** | | Does the copy match the correct brand's Four Dimensions (read the calibration examples)? |
| **Editorial mechanics** | | No emojis (except email glyph chip), max 3 hashtags, no em-dashes as defaults, no banned intensifiers? |
| **Format rules** | | Eyebrows UPPERCASE, stats plain label, subject lines under 45 chars, etc.? |
| **Conflict resolution** | | If a conflict exists, does it resolve per the table in § 5? |

### Automated validation (brand-check.py)

The validation script enforces:
- Token usage (Semantic only, no raw Primitives)
- Color accessibility (4.5:1 contrast minimum on text pairs)
- Sub-brand palette boundaries (`brand/colab/*` and `brand/majarah/*` never on AZM X surfaces)
- Spacing scale compliance (no 12px or 20px gaps)

Run `python brand-check.py [file]` before shipping.

---

## 9. Known edge cases and resolutions

| Edge case | Resolution |
|---|---|
| **AZM X copy about a sub-brand** | AZM X voice. "Colab, our UX research lab, launched a new service" is AZM X voice. |
| **Sub-brand copy about itself** | Sub-brand voice. "Our evidence shows..." in a Colab case study is Colab voice. |
| **Parent-house announcement naming several brands** | AZM X voice. "AZMX announces new offerings from Colab, Majarah, and Clix" is AZM X voice. |
| **Cross-brand collaboration deliverable** | Identify the primary brand (whose logo is largest or whose audience is targeted). Use that brand's voice. If truly equal, default to AZM X voice and state in the brief. |
| **Sub-brand with no visual system (Clix, Anatomi)** | **Ask the user which visual system to use.** Do not silently dress it in AZM X visuals. The voice is the sub-brand's; the visual system is TBD. |
| **Calibration example contains a banned word** | Keep the example verbatim (it is a tuning sample). Do not reuse that word in new copy. Example: Majarah's "unlock," Clix's "seamlessly," AZM X Inspirational's "elevating." |
| **Strategy deck guidance vs. house voice** | **House voice wins.** Max 3 hashtags (not 5–10), no emojis in copy (not "encouraged"), no mandatory CTA (not "must include"). See `voice-and-tone.md` § Where the strategy deck is superseded. |
| **Sub-brand needs a seventh palette** | Add it to `1b. Palette` primitives (e.g., Teal). Define the six role anchors (signature, ground, tint, etc.). Semantic tokens resolve automatically. No code changes. |

---

## 10. Cross-references

- `sub-brand-voices.md` — Colab, Majarah, Clix, Anatomi voice profiles with calibration examples
- `voice-and-tone.md` — AZM X voice, editorial mechanics, writing principles, format rules
- `design-tokens-usage.md` — Token structure, palette switch, binding rules, accessibility
- `audiences-and-messaging.md` — Personas and core messages per brand
- `colab-design` skill — Colab visual system (Dark green ground, Electric Green accent, pixel/dither motif)
- `majarah-design` skill — Majarah visual system (Deep purple ground, Electric Purple accent, Oswald display type)

---

## Summary: The inheritance model in one table

| Aspect | Inherited from AZM X | Overridden by sub-brand |
|---|---|---|
| **Token structure** | ✓ Five-tier system, semantic bindings, spacing/radius/border scales | Palette switch via `1b. Palette`, or full visual system via `[brand]-design` skill |
| **Editorial mechanics** | ✓ No emojis, max 3 hashtags, no AI tells, no banned intensifiers | — |
| **Writing principles** | ✓ Lead with value, be clear, write like a human, have a purpose | — |
| **Format rules** | ✓ Eyebrows UPPERCASE, stats plain, subject <45 chars, first line earns the click | Brand tunes execution (Colab cites the source, Majarah invites, Clix states ROI, Anatomi names the heuristic) |
| **Voice dimensions** | — | ✓ Formality, Technicality, Attitude, Purpose redefined per archetype |
| **Purpose modes** | — | ✓ Each brand defines its own (Colab: Evidence-Driven/Action-Oriented, Majarah: Inspirational/Pragmatic, etc.) |
| **Typography** | ✓ Display (thmanyah) and Body (Azm X Variable) ramps | Overridden if sub-brand visual system exists (e.g., Majarah uses Oswald) |
| **Conflict resolution** | ✓ Mechanics always win over voice | ✓ Sub-brand visual system wins over AZM X tokens when loaded |

**The load-bearing rule:** Bind to Semantic. Never to Primitives. This is what keeps the multi-brand architecture portable.
