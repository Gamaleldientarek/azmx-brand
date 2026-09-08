# AZMX Content Prompts

Six tested, copy-pasteable prompt templates for producing AZMX content: one long-form article generator, one email newsletter generator, three social customisation prompts (LinkedIn, Instagram, Twitter/X), and one English-to-Arabic localisation prompt. Read this file when you are asked to write an article, create email newsletter content, adapt an article into social posts, or localise approved English copy into Arabic.

Reconstructed from the 2025 AZMX Communication Strategy deck, pages 121 to 125, with the house voice rules applied on top.

## How to use these

- **Fill every bracket before running.** A leftover `[bracket]` is a bug: the model will quietly invent the value and you will ship its guess.
- **Never leave `[Choose the brand]` or `[Enter the brand name]` unresolved.** Brand decides voice. The wrong voice is worse than no voice, and it is the one error nobody catches in review.
- **Load the matching voice file first, then paste the real thing into the TOV slot.** Naming the brand is not enough. Open the file, copy the tone rules, paste them in.
  - AZM X → `references/voice-and-tone.md`
  - Colab, Majarah, Clix, Anatomi → `references/sub-brand-voices.md`
- **Personas and audiences** live in `references/audiences-and-messaging.md`, along with the verbatim core message for each of the 8 personas. Use that wording as written; do not paraphrase a core message.
- Copy the whole fenced block, brackets included. Each prompt is self-contained; do not run one that cross-references another.

## Where house voice overrides the deck

The deck set per-platform hashtag counts and encouraged emojis on Instagram and Twitter/X. AZMX house voice wins everywhere. `references/voice-and-tone.md` mandates **3 hashtags maximum, placed at the end, and no emojis in copy, on every channel including social.** The deck's original figures are recorded below and inside each prompt so the provenance stays visible; they are superseded and must not be "corrected" back.

| Channel | Deck (2025, superseded) | House rule (in force) |
| --- | --- | --- |
| LinkedIn | 3 to 5 hashtags | 3 maximum, at the end |
| Instagram | 5 to 10 hashtags, emojis encouraged | 3 maximum, at the end, no emojis |
| Twitter/X | 2 to 4 hashtags woven into copy, emojis encouraged | 3 maximum, at the end, no emojis |
| Articles and localised copy | not specified | 3 maximum, at the end, no emojis |
| Every channel | a CTA on every post | **No mandatory CTA.** A next step only where one genuinely exists |

The emoji ban covers copy: headlines, body, captions, subject lines, social posts. The one carve-out is the email design system's section-header and digest chip glyph (C03, C04, C07, C16), which is a visual component rather than copy. No prompt below produces email components, so no prompt below may emit an emoji.

Every prompt below also requires output to pass the 6-point pre-publish checklist in `voice-and-tone.md` and to avoid the banned AI-tell vocabulary listed there.

---

## 1. The Article Generation Prompt

Long-form SEO and AEO article, 800 to 1200 words, with metadata, a hero image concept, and pre-written social snippets. Deck page 121.

```text
# YOUR REQUEST

- Topic: [Enter the core subject of the article]
- Primary Brand: [Choose the brand]
- Target Audience: [B2G / B2B / B2C / Internal — pick one]
- Persona: [Enter persona]
- Primary Keyword: [Enter the single primary keyword]
- Secondary Keywords: [List 2-4 related keywords to include]
- Internal Link Targets: [Link(s)]
- Primary CTA & Link: [Optional. Leave blank if there is no genuine next step] - [Link]
- Target Word Count: [800-1200 words]

Reference files to load before you answer:
- Brand voice: AZM X -> references/voice-and-tone.md. Colab, Majarah, Clix, Anatomi -> references/sub-brand-voices.md. Paste the actual tone rules into the Tone of Voice slot below.
- Audience and persona: references/audiences-and-messaging.md. It holds the 8 personas and their verbatim core messages. Use that wording as written.

# YOUR TASK:

## Your Role: You are an expert subject matter writer and SEO content strategist for a leading Saudi digital consultancy.

## Your Process:

- Analyze the Request: Understand the Topic, Brand, Audience, and all SEO inputs.
- AEO Research: Based on the Primary Keyword, identify 2-3 common questions from Google's "People Also Ask" section to answer within the article.
- Outline the Article: Create a logical structure using a main heading (H1), section headings (H2), and sub-headings (H3) where appropriate.
- Write the Full Article: Write a comprehensive, insightful article that is authoritative and educational, following all guidelines below.
- Create SEO Metadata & Extras: Write a compelling Meta Title and Meta Description. Suggest a concept for a featured image and provide 2-3 pre-written social media snippets to promote the article.

## Writing Guidelines:

- Tone of Voice: [Paste the specific brand's TOV]
- SEO & AEO Guidelines:
- - Keyword Integration: Naturally weave the Primary and Secondary Keywords into the headings and body text. The Primary Keyword should appear in the first paragraph.
- - AEO Tactics: Structure parts of the article to be "snippet-friendly." Use bulleted lists, numbered steps, and include a Q&A section (e.g., "Frequently Asked Questions") that directly answers the "People Also Ask" questions you identified.
- - Internal Linking: Where relevant, naturally hyperlink the specified Internal Link Targets from the request.
- - CTA Integration: If a Primary CTA was supplied, place it at the end of the article. If the slot is blank, do not invent one.

## AZMX House Rules (non-negotiable, these override anything above):

- Hashtags: 3 maximum in any social snippet, all placed at the end of the snippet. (The 2025 deck set 3-5 for LinkedIn, 5-10 for Instagram, 2-4 for Twitter/X. Superseded by references/voice-and-tone.md.)
- No emojis. Not in the article, not in the metadata, not in the social snippets.
- No mandatory CTA. Add a next step only where one genuinely exists, and never manufacture one. (The 2025 deck required a CTA on every post. Superseded by references/voice-and-tone.md.)
- Banned vocabulary, do not use: empower, unlock, elevate, seamlessly, effortlessly, robust, leverage, truly, delve. No em-dash as a default connector, use commas, periods, or a colon. No triads such as "fast, simple, and powerful": one strong claim beats three padded ones.
- The full list of AI tells is in references/voice-and-tone.md. Read it and obey it.
- Before you return anything, run the output through the 6-point pre-publish checklist in references/voice-and-tone.md: on-brand for this specific TOV, clear and concise, valuable to this audience, purposeful (one obvious takeaway; a next step only where one genuinely exists), right for the format, proofread.

## Your Final Output Format:

SEO Meta Title: [Your suggested Meta Title (under 60 characters)]
SEO Meta Description: [Your suggested Meta Description (under 160 characters)]
------------------------------------------------------------
Suggested Titles:
1. ...
2. ...
3. ...
------------------------------------------------------------
Featured Image Suggestion: [Your concept for a hero image]
------------------------------------------------------------
Social Media Snippets:
1. (LinkedIn/Twitter): [A short, engaging snippet to promote the article]
2. (LinkedIn/Twitter): [A second, different angle or quote from the article]
3. (LinkedIn/Twitter, optional): [A third angle]
------------------------------------------------------------
Full Article:
[Article Title (H1)]
[Section 1 (H2)]
[Paragraphs with internal links to [Link] where appropriate...]
[Section 2 (H2)]
[Bulleted lists, numbered steps...]
[Frequently Asked Questions (H2)]
[People Also Ask Question 1 (H3)]
[Direct answer...]
[People Also Ask Question 2 (H3)]
[Direct answer...]
------------------------------------------------------------
[Conclusion (H2)]
[Summary, and the supplied CTA if there is one...]
------------------------------------------------------------
Primary Keyword:
[Confirm the primary keyword and where it appears]
------------------------------------------------------------
Secondary Keywords:
[List the secondary keywords you used]
------------------------------------------------------------
```

Two deck slips fixed here: the Primary Keyword slot repeated the Secondary Keywords label ("List 2-4 related keywords"), and the FAQ block showed only one People Also Ask question while the process asks for 2-3.

---

## 2. The Email Newsletter Prompt

HTML email newsletter content planner for monthly newsletters, periodic reports, annual reports, and announcements following the AZMX Email Design System. Outputs copy, section structure, component selection, theme recommendation, and image concepts ready for HTML production.

```text
# YOUR REQUEST

- Email Type: [Choose one: Monthly Newsletter, Periodic Report, Annual Report, Announcement, Campaign]
- Primary Brand: [Choose the brand]
- Target Audience: [B2G / B2B / B2C / Internal — pick one]
- Persona: [Enter persona]
- Subject Line: [Enter subject line, maximum 45 characters to avoid mobile truncation]
- Preview Text: [Enter preview text, 80-100 characters shown after subject in inbox]
- Main Theme/Topic: [Enter the core theme or announcement]
- Key Sections: [List 2-5 main content sections, e.g., Hero Announcement, Feature Story, Updates Digest, Event Calendar]
- Primary CTA & Link: [Optional. Leave blank if there is no genuine next step] - [Link]
- Theme Color Preference: [Choose one: Default Blue, Custom — if custom, specify the email type's theme]

Reference files to load before you answer:
- Email design system: references/email-design-system.md. This document governs all AZMX HTML emails. Read sections A (Foundations), B (Color Tokens & Theming), and C (Components) before writing content.
- Brand voice: AZM X -> references/voice-and-tone.md. Colab, Majarah, Clix, Anatomi -> references/sub-brand-voices.md. Paste the actual tone rules into the Tone of Voice slot below.
- Audience and persona: references/audiences-and-messaging.md. It holds the 8 personas and their verbatim core messages. Use that wording as written.

# YOUR TASK:

## Your Role: You are an expert email content strategist and copywriter for a leading Saudi digital consultancy, specializing in HTML email campaigns that follow the AZMX Email Design System.

## Your Process:

- Analyze the Request: Understand the Email Type, Brand, Audience, Key Sections, and theme requirements.
- Map to Email Components: Based on the Key Sections requested and the email design system's component library (references/email-design-system.md, Section C), select the appropriate components for each section. The design system provides: Hero (C01), Section Title (C02), Section Header with emoji chip (C03), Big Card (C05), Row Cards (C08-C10), Feature Cards (C12-C15), Pull Quote (C18), Calendar/Agenda (C19-C20), and more.
- Plan the Email Structure: Create a logical flow from hero to footer, ensuring each section has a clear purpose and the right component match.
- Write Section Copy: Write compelling, on-brand copy for each section following all guidelines below. Each section should include: section title, body copy, and any metadata (dates, labels, eyebrows) the component requires.
- Define Theme & Visuals: Recommend a color theme (default blue or custom) and provide image concepts for hero, features, and cards that align with the email design system's image specifications (Section A5-A6).
- Subject Line & Preview Text Check: Verify the subject line is under 45 characters and preview text is 80-100 characters. Both must be emoji-free and pass the voice checklist.

## Email Guidelines:

- Tone of Voice: [Paste the specific brand's TOV]
- Email Design System Compliance:
- - RTL Rules: All copy must work in right-to-left Arabic layout. No emojis in copy (the only exception is the design system's section-header component emoji chip, which is visual, not copy).
- - Font Voice: Use serif voice (personality) for hero headlines, section titles, pull quotes. Use sans voice (information) for body text, pills, buttons, metadata.
- - Component Selection: Match each content section to the appropriate design system component. Reference the component library in references/email-design-system.md Section C.
- - Theme Colors: If using a custom theme, specify the theme name and ensure all color token roles remain consistent with Section B of the email design system.
- - Image Specs: All image concepts must specify: subject, composition, dimensions (2× display width), and format (progressive JPEG q70-75 for photos, full-quality PNG for designed cards/logos).
- Subject Line Rule: Maximum 45 characters to avoid truncation in mobile email clients (Gmail, Apple Mail, Outlook mobile).
- Preview Text Rule: 80-100 characters, provides context after subject line in inbox preview.
- CTA Integration: If a Primary CTA was supplied, place it in the appropriate section (typically after the hero or at the email's end). If the slot is blank, do not invent one.

## AZMX House Rules (non-negotiable, these override anything above):

- No emojis in copy. Not in subject lines, not in preview text, not in body copy, not in section titles. The one carve-out is the email design system's section-header emoji chip (Component C03), which is a visual component, not copy.
- No mandatory CTA. Add a next step only where one genuinely exists, and never manufacture one.
- Banned vocabulary, do not use: empower, unlock, elevate, seamlessly, effortlessly, robust, leverage, truly, delve. No em-dash as a default connector, use commas, periods, or a colon. No triads such as "fast, simple, and powerful": one strong claim beats three padded ones.
- The full list of AI tells is in references/voice-and-tone.md. Read it and obey it.
- Before you return anything, run the output through the 6-point pre-publish checklist in references/voice-and-tone.md: on-brand for this specific TOV, clear and concise, valuable to this audience, purposeful (one obvious takeaway; a next step only where one genuinely exists), right for the format, proofread.

## Your Final Output Format:

Subject Line: [Your final subject line (max 45 characters)]
Character Count: [Actual count]
------------------------------------------------------------
Preview Text: [Your final preview text (80-100 characters)]
Character Count: [Actual count]
------------------------------------------------------------
Theme Recommendation: [Default Blue / Custom theme name with brief rationale]
------------------------------------------------------------
Email Structure & Components:
[List each section with its matched design system component, in order from top to bottom]

Example:
1. Hero Section (Component C01) - Main announcement
2. Section Header (Component C03) - "What's New" with emoji chip
3. Feature Card (Component C14) - Product launch story
4. Row Cards (Component C08) - Three recent updates
5. Calendar Section (Component C19) - Upcoming events
6. Footer (Component C22) - Standard AZMX footer with unsubscribe
------------------------------------------------------------
Section-by-Section Copy:

[SECTION 1: Component Name (e.g., C01 Hero)]
- Headline: [Hero headline, serif voice]
- Subheadline/Body: [Supporting copy, sans voice]
- CTA: [Button text and link, if applicable]
- Image Concept: [Describe the visual - subject, composition, dimensions at 2×, format]

[SECTION 2: Component Name (e.g., C03 Section Header)]
- Emoji Chip: [Single emoji for the visual chip component]
- Section Title: [Title text, serif voice]

[SECTION 3: Component Name (e.g., C05 Big Card)]
- Eyebrow: [Optional category label, if the component supports it]
- Headline: [Card headline, serif voice]
- Body: [Body copy, sans voice]
- Metadata: [Date, author, read time, or other meta as needed]
- Image Concept: [Describe the visual]
- Link: [If applicable]

[Continue for each section...]

[FOOTER: Component C22]
- Footer Copy: [Any custom footer message, if applicable]
- Unsubscribe Link: Required, href="{{ unsubscribe }}" for Brevo
------------------------------------------------------------
Image Asset List:
[Summarize all images needed with specs]
1. Hero Image: [Description] - [Dimensions] - [Format]
2. Feature Image 1: [Description] - [Dimensions] - [Format]
3. [etc.]
------------------------------------------------------------
Production Notes:
[Any special instructions for HTML production, theme customization, or QA requirements]
------------------------------------------------------------
```

This prompt produces the content plan and copy; HTML production follows the technical specifications in `references/email-design-system.md`. Before any email send, run the QA checklist in that document, especially the iframe overflow harness at 360/375/430px, chevron direction sweep, verbatim Arabic copy check, and size < 100 KB.

---

## 3. The Content Customization Prompt: LinkedIn

Turns a published article into one LinkedIn post, roughly 150 words, with insight rationale, three CTA options, and a creative direction. Deck page 122.

```text
# YOUR REQUEST

- Source Article: [Source]
- Brand: [Enter the brand name]
- Target Audience: [B2G / B2B / B2C / Internal — pick one]
- Persona: [Enter persona]
- Visual Format: [Choose one: Single Image, Carousel (3-7 slides), Video, Text Only]
- Tone of Voice (TOV): [Paste the specific brand's TOV]
- Platform: [LinkedIn]

Reference files to load before you answer:
- Brand voice: AZM X -> references/voice-and-tone.md. Colab, Majarah, Clix, Anatomi -> references/sub-brand-voices.md. Paste the actual tone rules into the Tone of Voice slot above, do not just name the brand.
- Audience and persona: references/audiences-and-messaging.md. It holds the 8 personas and their verbatim core messages. Use that wording as written.

# YOUR TASK:

## Your Role: You are a senior content strategist and expert copywriter specializing in [B2G / B2B / B2C / Internal — same value as Target Audience above] communication for a leading Saudi digital consultancy.

## Your Process:
- Analyze the Request: Read the source article and understand the target Brand, Platform, Audience, and Visual Format.
- Extract Core Message: Identify the single most relevant takeaway from the article for this specific audience on the platform.
- Define the Strategy:
- - Suggest a Key Insight for the post and provide a brief rationale for its relevance.
- - Suggest up to 3 CTA options, or state plainly that no CTA is warranted here.
- - Suggest a Creative Direction that aligns with the chosen Visual Format and the post's core message.
- Write the Post: Craft the platform post by adapting and reframing the article's content. Do not just copy and paste. Summarize the key points, pull out a compelling quote, or focus on a single powerful data point from the article.
- Suggest Hashtags: Provide a list of 3 strategic hashtags maximum, placed at the end of the post.

## Platform Guidelines:
- Voice: Authoritative, Professional, Insightful.
- Structure: Start with a strong hook (a bold question or statement). Use 2-3 short paragraphs with ample white space for readability. The first line must earn the click on its own: it is all people see when the post is collapsed.
- Word Count: Aim for approximately 150 words.
- Hashtags: 3 maximum, all at the very end of the post. (The 2025 deck said 3-5. Superseded by references/voice-and-tone.md.)

## AZMX House Rules (non-negotiable, these override the platform guidelines above):

- Hashtags: 3 maximum, at the end. Never a hashtag wall.
- No emojis anywhere in the copy.
- No mandatory CTA. Add a next step only where one genuinely exists, and never manufacture one. (The 2025 deck required a CTA on every post. Superseded by references/voice-and-tone.md.)
- Banned vocabulary, do not use: empower, unlock, elevate, seamlessly, effortlessly, robust, leverage, truly, delve. No em-dash as a default connector, use commas, periods, or a colon. No triads such as "fast, simple, and powerful".
- The full list of AI tells is in references/voice-and-tone.md. Read it and obey it.
- Before you return anything, run the copy through the 6-point pre-publish checklist in references/voice-and-tone.md: on-brand for this specific TOV, clear and concise, valuable to this audience, purposeful (one obvious takeaway; a next step only where one genuinely exists), right for the platform, proofread.

## Your Final Output Format: You must provide your response in this exact structure:

------------------------------------------------------------
Key Insights Suggested:
* [Insight 1] (Rationale:.. Source: ...)
* [Insight 2] (Rationale:.. Source: ...)
...
------------------------------------------------------------
Call-to-Action (CTA) Options Suggested:
(Same friction ladder as the CTA progression in references/editorial-calendar.md, where it is written Download -> Engage -> Act. If no CTA is warranted, say so here instead of listing three.)
1. (Soft CTA - Learn): ...
2. (Medium CTA - Engage): ...
3. (Hard CTA - Act): ...
------------------------------------------------------------
Creative Direction Suggested:
[Your visual concept. For a carousel, describe each slide. For an image, describe the concept.]
------------------------------------------------------------
Post Copy:
[Your full, ready-to-publish post copy goes here]
------------------------------------------------------------
Hashtags Suggested:
...
------------------------------------------------------------
```

---

## 4. The Content Customization Prompt: Instagram

Same shape as LinkedIn, tuned for a visual-first caption under 125 words. Deck page 123. This is the template the deck and the house voice disagree on most: the deck encouraged emojis and 5 to 10 hashtags. Both are overridden.

```text
# YOUR REQUEST

- Source Article: [Source]
- Brand: [Enter the brand name]
- Target Audience: [B2G / B2B / B2C / Internal — pick one]
- Persona: [Enter persona]
- Visual Format: [Choose one: Single Image, Carousel (3-10 slides), Reel, Story]
- Tone of Voice (TOV): [Paste the specific brand's TOV]
- Platform: [Instagram]

Reference files to load before you answer:
- Brand voice: AZM X -> references/voice-and-tone.md. Colab, Majarah, Clix, Anatomi -> references/sub-brand-voices.md. Paste the actual tone rules into the Tone of Voice slot above, do not just name the brand.
- Audience and persona: references/audiences-and-messaging.md. It holds the 8 personas and their verbatim core messages. Use that wording as written.

# YOUR TASK:

## Your Role: You are a senior social media strategist and expert copywriter.

## Your Process:
- Analyze the Request: Read the source article and understand the target Brand, Platform, Audience, and Visual Format.
- Extract Core Message: Identify the single most relevant and visually communicable takeaway from the article for this specific audience on the platform.
- Define the Strategy:
- - Suggest a Key Insight for the post and provide its rationale.
- - Suggest up to 3 CTA options, or state plainly that no CTA is warranted here.
- - Suggest a Creative Direction that aligns with the chosen Visual Format and the post's core message.
- Write the Post: Craft the platform caption by adapting and reframing the article's content. Focus on storytelling and creating a human connection.
- Suggest Hashtags: Provide a list of 3 strategic hashtags maximum, placed at the end of the caption.

## Platform Guidelines:
- Voice: Creative, Personable, Inspiring.
- Structure: The caption must add context and personality to the visual, not just describe it. Start with a strong hook to capture attention in the first two lines. Use a more personal and approachable tone. Ask engaging questions to encourage comments. Use line breaks to make the caption scannable.
- Emojis: Do not use emojis. AZMX copy is emoji-free on every channel, Instagram included. (The 2025 deck permitted emojis here. Superseded by references/voice-and-tone.md.)
- Word Count: Aim for under 125 words.
- Hashtags: Place 3 hashtags maximum at the very end of the caption. Include a mix of broad, niche, and branded tags. (The 2025 deck said 5-10, and allowed them in the first comment. Superseded by references/voice-and-tone.md, which places them at the end of the caption.)

## AZMX House Rules (non-negotiable, these override the platform guidelines above):

- Hashtags: 3 maximum, at the end. A 10-hashtag caption is a rejected caption.
- No emojis anywhere in the copy.
- No mandatory CTA. Add a next step only where one genuinely exists, and never manufacture one. (The 2025 deck required a CTA on every post. Superseded by references/voice-and-tone.md.)
- Banned vocabulary, do not use: empower, unlock, elevate, seamlessly, effortlessly, robust, leverage, truly, delve. No em-dash as a default connector, use commas, periods, or a colon. No triads such as "fast, simple, and powerful".
- The full list of AI tells is in references/voice-and-tone.md. Read it and obey it.
- Before you return anything, run the copy through the 6-point pre-publish checklist in references/voice-and-tone.md: on-brand for this specific TOV, clear and concise, valuable to this audience, purposeful (one obvious takeaway; a next step only where one genuinely exists), right for the platform, proofread.

## Your Final Output Format: You must provide your response in this exact structure:

------------------------------------------------------------
Key Insights Suggested:
* [Insight 1] (Rationale:.. Source: ...)
* [Insight 2] (Rationale:.. Source: ...)
...
------------------------------------------------------------
Call-to-Action (CTA) Options Suggested:
(Same friction ladder as the CTA progression in references/editorial-calendar.md, where it is written Download -> Engage -> Act. If no CTA is warranted, say so here instead of listing three.)
1. (Soft CTA - Learn): ...
2. (Medium CTA - Engage): ...
3. (Hard CTA - Act): ...
------------------------------------------------------------
Creative Direction Suggested:
[Your visual concept. For a carousel, describe each slide. For a Reel, describe the visual sequence.]
------------------------------------------------------------
Post Copy:
[Your full, ready-to-publish caption goes here]
------------------------------------------------------------
Hashtags Suggested:
...
------------------------------------------------------------
```

---

## 5. The Content Customization Prompt: Twitter/X

Same shape again, constrained to the 280-character single-tweet limit or a labelled 3 to 5 tweet thread. Deck page 124.

```text
# YOUR REQUEST

- Source Article: [Source]
- Brand: [Enter the brand name]
- Target Audience: [B2G / B2B / B2C / Internal — pick one]
- Persona: [Enter persona]
- Visual Format: [Choose one: Single Image, GIF, Video, Poll, Text Only, Thread (3-5 tweets)]
- Tone of Voice (TOV): [Paste the specific brand's TOV]
- Platform: [Twitter/X]

Reference files to load before you answer:
- Brand voice: AZM X -> references/voice-and-tone.md. Colab, Majarah, Clix, Anatomi -> references/sub-brand-voices.md. Paste the actual tone rules into the Tone of Voice slot above, do not just name the brand.
- Audience and persona: references/audiences-and-messaging.md. It holds the 8 personas and their verbatim core messages. Use that wording as written.

# YOUR TASK:

## Your Role: You are a senior social media strategist and expert copywriter.

## Your Process:
- Analyze the Request: Read the source article and understand the target Brand, Platform, Audience, and Visual Format.
- Extract Core Message: Identify the single most tweetable, impactful, or controversial takeaway from the article for this specific audience on the platform.
- Define the Strategy:
- - Suggest a Key Insight for the post and provide its rationale.
- - Suggest up to 3 CTA options, or state plainly that no CTA is warranted here.
- - Suggest a Creative Direction for the chosen Visual Format.
- Write the Post: Craft the tweet(s) by adapting and reframing the article's content. Focus on creating a concise, impactful message that encourages conversation.
- Suggest Hashtags: Provide a list of 3 strategic hashtags maximum, placed at the end.

## Platform Guidelines:
- Voice: Conversational, Witty, Timely.
- Structure: Keep content short, impactful, and easy to share. A strong hook is essential. Use a direct and often informal tone. Threads can be used to tell longer stories, with each tweet being a complete thought.
- Emojis: Do not use emojis. (The 2025 deck encouraged them here for tone and readability. Superseded by references/voice-and-tone.md.)
- Character Count: Stay within the 280-character limit for a single tweet. Count the hashtags and the link inside that limit.
- Hashtags: 3 maximum, placed at the end, not woven into the sentence. (The 2025 deck said 2-4, integrated into the copy or at the end. Superseded by references/voice-and-tone.md.)

## AZMX House Rules (non-negotiable, these override the platform guidelines above):

- Hashtags: 3 maximum, at the end.
- No emojis anywhere in the copy.
- No mandatory CTA. Add a next step only where one genuinely exists, and never manufacture one. (The 2025 deck required a CTA on every post. Superseded by references/voice-and-tone.md.)
- Banned vocabulary, do not use: empower, unlock, elevate, seamlessly, effortlessly, robust, leverage, truly, delve. No em-dash as a default connector, use commas, periods, or a colon. No triads such as "fast, simple, and powerful".
- Witty is allowed. Boastful is not, and neither are exclamation marks doing the selling. The full list of AI tells is in references/voice-and-tone.md. Read it and obey it.
- Before you return anything, run the copy through the 6-point pre-publish checklist in references/voice-and-tone.md: on-brand for this specific TOV, clear and concise, valuable to this audience, purposeful (one obvious takeaway; a next step only where one genuinely exists), right for the platform, proofread.

## Your Final Output Format: You must provide your response in this exact structure:

------------------------------------------------------------
Key Insights Suggested:
* [Insight 1] (Rationale:.. Source: ...)
* [Insight 2] (Rationale:.. Source: ...)
...
------------------------------------------------------------
Call-to-Action (CTA) Options Suggested:
(Same friction ladder as the CTA progression in references/editorial-calendar.md, where it is written Download -> Engage -> Act. If no CTA is warranted, say so here instead of listing three.)
1. (Soft CTA - Learn): ...
2. (Medium CTA - Engage): ...
3. (Hard CTA - Act): ...
------------------------------------------------------------
Creative Direction Suggested:
[Your visual concept. If a Thread is chosen, suggest a visual for the first tweet and outline the structure of the thread.]
------------------------------------------------------------
Post Copy:
[Your full, ready-to-publish tweet(s) go here. For threads, please label them clearly: 1/3, 2/3, etc.]
------------------------------------------------------------
Hashtags Suggested:
...
------------------------------------------------------------
```

---

## 6. The Content Localization Prompt: English to Arabic

Localises approved English copy into modern professional Saudi Arabian Arabic, with terminology handling, cultural adaptation, and creative alternatives. Deck page 125. Use it on signed-off English only: it localises, it does not rewrite strategy.

```text
# YOUR REQUEST

- Source Text (English): [Paste English text here]
- Brand: [Enter the brand name]
- Target Audience: [B2G / B2B / B2C / Internal — pick one]
- Persona: [specific Arabic-speaking, Enter persona]
- Content Type: [Choose the context: Social Media Post, Articles, Newsletter]
- Tone of Voice (TOV): [Paste the specific brand's TOV]

Reference files to load before you answer:
- Brand voice: AZM X -> references/voice-and-tone.md. Colab, Majarah, Clix, Anatomi -> references/sub-brand-voices.md. Paste the actual tone rules into the Tone of Voice slot above, do not just name the brand.
- Audience and persona: references/audiences-and-messaging.md. It holds the 8 personas and their verbatim core messages. If the source text carries a core message, carry its meaning exactly, do not soften it in translation.

# YOUR TASK:

## Your Role: You are an expert translator and localization specialist, fluent in both English and modern, professional Saudi Arabian Arabic. You have a deep understanding of marketing, digital, technology, and business communication.

## Your Primary Goal: Your goal is to translate the source text. You must capture the original message's strategic intent, tone, and nuance, and adapt it to resonate perfectly with the target audience in Arabic, ensuring it feels natural and authentic.

## Your Process:

- Analyze the Source: Deeply understand the source text, its context (Content Type), and the target Brand and Audience.
- Match the Tone of Voice: The final Arabic text must perfectly embody the specified brand's Tone of Voice. For example, if the tone is "bold but respectful," the Arabic translation must carry that same confident yet professional attitude.
- Handle Key Terminology:
- - For common industry terms (e.g., 'UX', 'ROI', 'KPI'), use the widely accepted Arabic equivalent or the English term if it's common practice in the Arabic business community.
- - For brand-specific or highly technical terms, provide the best Arabic translation and include the English term in parentheses () for clarity on its first use.
- Adapt for Culture: If the source text uses an English idiom or cultural reference that does not translate well, do not translate it literally. Instead, find a culturally relevant Arabic equivalent that conveys the same meaning.
- Offer Creative Options: For creative or marketing-focused text (like headlines, slogans, or social media hooks), provide 2-3 alternative translations to choose the most impactful one.

## AZMX House Rules (non-negotiable):

- Hashtags: when the Content Type is a social media post, carry a maximum of 3 hashtags, placed at the end. Drop the weakest ones if the source has more. (The 2025 deck set higher per-platform counts. Superseded by references/voice-and-tone.md.)
- No emojis in the Arabic output, even if the English source contains them. Remove them rather than transliterating their meaning.
- No mandatory CTA. Add a next step only where one genuinely exists, and never manufacture one. (The 2025 deck required a CTA on every post. Superseded by references/voice-and-tone.md.)
- Do not inflate the register. Arabic marketing copy drifts into ceremonial padding under pressure: no Arabic equivalents of empower, unlock, elevate, seamlessly, effortlessly, robust, leverage, truly, delve, and no strings of three synonyms where one word carries the meaning. Restraint is the luxury in both languages.
- Keep any English terms you retain in parentheses clean of the same banned vocabulary.
- Arabic brand wordmarks are copy-pasted, never retyped. If the source text contains one, flag it in the Translator's Notes rather than typing it out.
- Before you return anything, run the Arabic through the 6-point pre-publish checklist in references/voice-and-tone.md: on-brand for this specific TOV, clear and concise, valuable to this audience, purposeful (one obvious takeaway; a next step only where one genuinely exists), right for the format, proofread.

## Your Final Output Format: You must provide your response in this exact structure:

------------------------------------------------------------
### Recommended Translation:
[Provide the main, recommended Arabic translation here]

### Alternative Options (if applicable for creative copy):
Option 1: ...
Option 2: ...

### Translator's Notes (Optional):
[Provide brief notes on any key decisions, such as why you chose a specific term or how you adapted an idiom.]
------------------------------------------------------------
```
