# Brand Compliance Report Generator

Extend brand-check.py to generate comprehensive compliance reports in JSON, HTML, and markdown formats. Reports aggregate results across multiple files or an entire deliverable batch, showing: pass/fail rates by rule category, most common violations, severity distribution, per-file details, and trend data over time. Include a summary dashboard suitable for sharing with brand managers and stakeholders.

## Rationale
Currently brand-check.py provides pass/fail output per file but no aggregated view. Brand managers need visibility into brand health across all deliverables without running CLI tools. This directly extends the automated QA advantage that Frontify explicitly lacks (pain-1-1) and Bynder confines to its own platform (pain-2-5). A report generator makes brand compliance visible, measurable, and shareable — moving from developer tool to management tool.

## User Stories
- As a brand manager, I want compliance reports so that I can see brand health at a glance without running command-line tools
- As a creative director, I want trend data on brand violations so that I can identify systemic issues and provide targeted guidance to the team

## Acceptance Criteria
- [ ] brand-check.py --report flag generates a compliance report for a batch of files
- [ ] Reports are available in JSON, HTML, and markdown formats
- [ ] Reports include: total files scanned, pass/fail rate, violations by category (color, font, spacing, copy), severity distribution, and top 5 most common violations
- [ ] HTML report is self-contained (no external dependencies) and visually presentable
- [ ] Reports can be generated for visual checks, copy checks, or both combined
- [ ] Historical report data can be stored and compared to show trends over time
- [ ] Report generation completes in under 30 seconds for 100 files
