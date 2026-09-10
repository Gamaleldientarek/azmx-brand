# Security

## Reporting a vulnerability

This skill ships static brand assets, JSON data and local tooling; it runs no
servers. If you find a problem — a stored-XSS path in a generated page, a
script that can be made to read or write outside the repository, a leaked
credential in the history — email **ccreative@azmx.sa** with the details.
Please do not open a public issue for security reports. You will get an
acknowledgement within three working days.

## What is in scope

- The published pages: `index.html` (image gallery), `tokens.html` (token
  explorer), `api-docs/` and everything under `api/v1/`.
- The scripts in `scripts/`, in particular anything that generates HTML
  (`rebuild-index.py`, `build-token-explorer.mjs`, `generate-docs.py`,
  `drift-report.py`, `drift-alert.py`).
- The drift-monitor alert channels (`drift-alert.py`): SMTP and webhooks.

## How secrets are handled

- No credentials are committed. `.gitignore` covers `.env*`, key and
  certificate files, service-account JSON and package-manager auth files, and
  `.github/workflows/secret-scan.yml` runs gitleaks on every push.
- The drift monitor reads its SMTP password and webhook URLs from the
  environment (`AZMX_SMTP_USERNAME`, `AZMX_SMTP_PASSWORD`,
  `AZMX_SLACK_WEBHOOK`, `AZMX_TEAMS_WEBHOOK`), never from the committed
  `.brand-monitor.yml`. Webhooks must be `https://`; SMTP verifies
  certificates and refuses to log in over plaintext.
- `scripts/hooks/pre-commit` (install with `bash scripts/hooks/install.sh`)
  and `tests/test_repo_hygiene.py` reject token-shaped strings, absolute home
  paths and agent scratch files before they reach a commit.

## Generated HTML

Everything interpolated into `index.html` and `tokens.html` is escaped or
validated at the source (tag charset in `sync-references.py`, token names in
`build-token-explorer.mjs`); the gallery ships a hash-based
Content-Security-Policy computed from the exact inline CSS/JS it emits, and
`tests/test_gallery_security.py` fails if either page regresses.

## Supported versions

Only the latest release on `main` is supported. Older tags receive no fixes.
