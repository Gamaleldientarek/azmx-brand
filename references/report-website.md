# AZM X reports on the web

How an AZM X report looks as a web page. A report has two pages: a **download page** (the PDF behind a short form, with a "Read online" text link) and a **reading page** that carries most of the report in HTML, in Arabic and English. This file holds the brand-level pattern. The site's own build method, ids and the owner's decision log live in the website's repository (its `azmx-report` skill and the `azmx-site` plugin's `azmx-report-website` skill).

## Page structure

1. **Hero:** breadcrumb, a short subject line in the accent colour (label-lg), the report's own title as the only H1 (thmanyah), a one-paragraph lead (Azm X), the cover picture beside it. A facts row under a hairline: three facts (period or year, chapters, reading time) with values in **regular weight**. Two buttons: primary «ابدأ القراءة» / "Start reading", secondary «تنزيل التقرير الكامل» / "Download the full report". No tags or pills in the hero, no icons on the buttons.
2. **Chapter index** beside the text on desktop (hidden on tablet and phone), with the download button and file type and size under it. The reading-progress bar at the top marks progress; no "current chapter" overlay in the index.
3. **Chapters:** one H2 each, the chapter's main finding, its text, and the figures that carry it. Each chart sits under one sentence that states its finding. Method and sample stay on the page, short, near the findings. The PDF keeps criterion-level detail, appendices and references.
4. **End of the page, two separate sections:** a grey band «تابع من هنا» with three white cards (a service, a case study, an article, each with its picture), then a black band with one serif line about the report's subject and the homepage's button pair (primary «تحدث مع فريقنا», secondary «جميع الخدمات»).

## Colour and type

- Each report runs **one palette** (the page's accent, tint and deep follow it); black stays the dark ground. Never two palettes on one surface.
- Titles that must follow the reading direction are set directly (thmanyah for chapter and card headings, Azm X 600 for card titles), aligned to start.
- Small labels and eyebrows are paragraphs, not headings.

## Sections that suit report data

| Data | Section |
|---|---|
| Three to five headline figures | Number tiles, each with a small dot or bar chart |
| One worked example | One huge number with a dot field |
| Before and after | Two facing panels |
| A case study | Its numbers first, then challenges and results as two lists |
| A roadmap or process | Numbered rows, each with a picture |
| What something is made of | A list of parts beside a sticky picture |
| Many series or groups | A native tab component, one variant per tab |
| Scores by group | A score table with values in cells |

Pictures come from the report itself, recoloured to its palette, never stretched. Charts animate once on entry and sit still under reduced motion. Cards grow 2 % on hover and don't lift.

## Arabic

- Every text with no Arabic letter (numbers, ranges, «2026», stars, Latin names, table cells) starts with a right-to-left mark (U+200F) so it sits on the right; its English value is the plain text.
- Marks in circles (✓ / ✕) are icons, centred, never text glyphs.
- The rest of `rtl-layout-guide.md` applies.

## Search

- The reading page's title leads with the topic's search phrase; the description (≤ 160 characters) and the first paragraph carry it; the H1 stays the report's own title.
- The download page's title ends «| تنزيل التقرير بصيغة PDF | عزم إكس» / "| Download the PDF report | AZM X", so the two pages don't compete.
- About six links inside the text to the services, articles and case studies the sentence is about.
