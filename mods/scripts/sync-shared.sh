#!/bin/bash
# Copies shared/*.ts into the hooks/shared/ folder of every mod that uses it.
# Edit the files in shared/, never their copies, then run this script.
set -euo pipefail
cd "$(dirname "$0")/.."
for mod in background-tasks session-hud conversation-cards openspec-cockpit; do
  [ -d "$mod" ] || continue
  mkdir -p "$mod/hooks/shared"
  for file in shared/*.ts shared/*.tsx; do
    name=$(basename "$file")
    { echo "// Copied from shared/$name by scripts/sync-shared.sh: edit the original, not this copy."; cat "$file"; } > "$mod/hooks/shared/$name"
  done
  echo "shared → $mod"
done
