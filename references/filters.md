# Filtering and sorting a list

How AZM X lets a reader narrow a list by one category and choose its order: a blog index, a glossary, a list of case studies, reports or jobs. The pattern runs on azmx.sa (16 November 2026). It ships as the **Filter Bar** block in design system 1.5.0 (`npx @azmxsa/cli add filter-bar`, dashboard `/docs/blocks/filter-bar`); a project on an older release builds it from `tabs`, `segmented-control` and `sheet` by these rules. Read this before designing any filter, in code, Figma or a mock-up.

## The pattern in one look

Two controls in one row, directly above the list they control:

- **Category:** one choice from a short set, with "All" first. One answer at a time.
- **Order:** one choice from two to four orders. One is the default.

| Screen | Category | Order |
|---|---|---|
| Desktop, 1024 px and up | Pills in one line | A switch: a filled pill on a grey track, with a "Sort by" label |
| Tablet and phone | A field that opens a bottom sheet | A compact field that opens a bottom sheet |

From 1440 px the pills and the switch share one row, pills at the reading start. From 1024 to 1439 px the switch sits on its own line under the pills.

## Rules

1. **Pills never wrap and never run off the page.** When they don't fit one line, use the fields. A row of pills that scrolls sideways is not a fix.
2. **Selected means filled.** The chosen pill, the chosen switch option and the chosen sheet row are filled shapes. No underline, side line or coloured rule on any state.
3. **"All" clears only the category.** It never resets the order.
4. **A category change must not wait for the network.** Load the full set with the page and show or hide items on the client. The chosen state lands in the same frame as the list, with no fade.
5. **A press is acknowledged at once.** Pills and options scale to 0.96 on press.
6. **The address holds the state** (`?category=…&sort=…`), so a filtered view can be shared. The default order and "All" leave nothing in the address, and an unknown value behaves as the default.
7. **No empty choices.** A category with no items gets no pill and no row.
8. **With a category chosen, show all its items.** Paging belongs to the unfiltered list.
9. **Pictures that are still loading show a soft grey placeholder,** never a white gap.

## The fields (tablet and phone)

One row, 8 px apart, in reading order: order first, then category.

- **Order field:** an up-down arrows icon (Phosphor `ArrowsDownUp`), then the current order. No chevron. A fixed width that fits the longest order in both languages, so the row doesn't move when the order changes.
- **Category field:** the current category, then a chevron. It fills the rest of the row on a phone. With nothing chosen it reads "All categories".
- **Both:** 48 px tall, with the design system's field fill, outline and 8 px radius. One line of text; a long value ends in an ellipsis.
- **A list with search:** put one category field under the search box, at the search box's height, radius and padding.

## The sheet

- **Header:** the title at the reading start, as a heading, and a close button at the end, at least 44 × 44.
- **Rows:** 52 px tall, the label at the start. The chosen row is filled and shows a check at the end.
- **Order:** "All" first, then the categories in the same order as the desktop pills.
- **Picking a row** applies at once, shows the check, then closes the sheet about 0.15 s later. The close button, a tap on the dimmed backdrop and Escape close it without a change.
- **Height:** the option list is capped and scrolls, so the title and the close button stay in view on a landscape phone.
- **Tablet:** 480 px wide and centred. **Phone:** full width, flush to the bottom.
- The sheet and its backdrop sit above everything, the site header included.

## Accessibility

- Fields and rows are real buttons. Enter and Space both work.
- Each field carries a hidden label that ends in a colon, so its name reads "Category: All categories". It says it opens a dialog and whether it is open.
- The sheet is a modal dialog named by its title. The page behind is inert while it is open.
- Focus moves to the chosen row on open, stays inside, and returns to the field on close. Arrow keys, Home and End move between rows.
- The chosen row says so in words, not by fill alone.
- Nothing depends on hover.

## Wording

| Use | Arabic | English |
|---|---|---|
| Order label | ترتيب حسب | Sort by |
| The editor's own order | اختيارنا | Our picks |
| Orders by date | الأحدث، الأقدم | Newest, Oldest |
| Order sheet title | ترتيب المقالات | Sort articles |
| Category label and sheet title | التصنيف | Category |
| First pill and first sheet row | الكل | All |
| Category field with nothing chosen | كل التصنيفات | All categories |
| Close button, for screen readers | إغلاق | Close |
| Empty list | لا توجد مقالات أخرى في هذا التصنيف حاليًا | No other articles in this category right now |

Change «المقالات» to the list's own noun for other lists. Arabic and English never share a sentence.

## When this pattern doesn't fit

- **More than one filter group, or filters with many values:** use one "Filters" button and a sheet that holds every group.
- **More than about seven categories, or long names:** use the category field and its sheet on every screen, desktop included.
- **A view switch that shows a different panel** (Day, Week, Month): that is Tabs or a Segmented Control on its own, not a filter.

## In decks, documents and Figma

Draw the same shapes by hand with the system's tokens: white pills with a hairline and one filled pill; a grey track with one filled option; a grey field 48 high with an 8 px radius. Show the phone version as two fields in one row, never as a wrapped or cut row of pills.
