#!/bin/bash
# Copies the mods into a session's dev-mods folder, where the session hot-reloads them.
# Usage: scripts/dev-sync.sh <session-id> [mod…]   (all four mods when none is named)
# Runs sync-shared.sh first, so each mod carries the current shared/ files.
set -euo pipefail
cd "$(dirname "$0")/.."
session="${1:?usage: scripts/dev-sync.sh <session-id> [mod…]}"
shift
mods=("$@")
if [ ${#mods[@]} -eq 0 ]; then mods=(session-hud background-tasks conversation-cards openspec-cockpit); fi
scripts/sync-shared.sh
target="$HOME/.claude/dev-mods/$session"
mkdir -p "$target"
for mod in "${mods[@]}"; do
  [ -d "$mod" ] || { echo "skip $mod (no folder)"; continue; }
  rsync -a --delete --exclude .claude-plugin/types --exclude tsconfig.json "$mod/" "$target/$mod/"
  [ -f "$target/$mod/tsconfig.json" ] || cp "$mod/tsconfig.json" "$target/$mod/" 2>/dev/null || true
  echo "dev → $target/$mod"
done
