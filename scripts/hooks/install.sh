#!/usr/bin/env bash
# Install the repo-hygiene pre-commit hook into .git/hooks/pre-commit.
#
#     bash scripts/hooks/install.sh
#
# Copies scripts/hooks/pre-commit into the local .git/hooks directory. It only
# ever touches `pre-commit`; any other hook already present (Auto-Claude installs
# a post-commit hook, for instance) is left exactly as it is. core.hooksPath is
# deliberately NOT set, so other tools' hooks keep working.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/pre-commit"

if ! GIT_DIR="$(git -C "$HERE" rev-parse --git-dir 2>/dev/null)"; then
  echo "install.sh: not inside a git checkout; nothing to install" >&2
  exit 1
fi
# rev-parse may return a relative path (".git"); make it absolute.
case "$GIT_DIR" in
  /*) ;;
  *) GIT_DIR="$(cd "$HERE" && cd "$GIT_DIR" && pwd)" ;;
esac

HOOKS_DIR="$GIT_DIR/hooks"
DEST="$HOOKS_DIR/pre-commit"
mkdir -p "$HOOKS_DIR"

if [ -e "$DEST" ] && ! grep -q 'AZMX brand skill — pre-commit repo-hygiene guard' "$DEST"; then
  BACKUP="$DEST.backup.$(date +%Y%m%d%H%M%S)"
  cp "$DEST" "$BACKUP"
  echo "install.sh: existing pre-commit hook was not ours; backed it up to $BACKUP" >&2
fi

cp "$SRC" "$DEST"
chmod +x "$DEST"

if [ -e "$HOOKS_DIR/post-commit" ]; then
  echo "install.sh: left existing post-commit hook untouched"
fi
echo "install.sh: installed $DEST"
