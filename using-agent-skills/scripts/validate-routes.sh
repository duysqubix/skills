#!/usr/bin/env bash
# Validate that this skill's routing matches reality, across SKILL.md and reference/*.md.
#
#   - every installed skill is reachable from some doc (no orphans)
#   - every skill name the docs cite actually exists (no dead routes)
#   - the "(N skills)" counts in family headings match their tables
#   - every reference/ file linked from SKILL.md exists (no broken links)
#
# Usage: ./scripts/validate-routes.sh [skills-root]
# Exit:  0 = clean, 1 = drift found.

set -uo pipefail

ROOT="${1:-$HOME/.agents/skills}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="$HERE/SKILL.md"
fail=0

[ -r "$DOC" ] || { echo "cannot read $DOC"; exit 1; }
[ -d "$ROOT" ] || { echo "cannot read skills root $ROOT"; exit 1; }

# All routing surfaces: the router plus every family reference.
mapfile -t DOCS < <(printf '%s\n' "$DOC"; find "$HERE/reference" -name '*.md' 2>/dev/null | sort)

# Names that legitimately appear without being a directory in $ROOT:
# source-repo names, documented renames, plugin skills, and CLI built-ins.
ALLOW='^(pm-skills|taste-skill|stop-slop|interview-script|summarize-interview|oh-my-claudecode|omc-reference|ai-slop-cleaner|autopilot|ultrawork|ralph|ralplan|team|ask|ccg|code-review|simplify|security-review|frontend-design|skill-name|reference|scripts|i-have-adhd|ponytail-(review|audit|debt))$'

echo "== orphans: installed but unreachable from any doc =="
while IFS= read -r s; do
  grep -qF -- "$s" "${DOCS[@]}" || { echo "  ORPHAN  $s"; fail=1; }
done < <(find "$ROOT" -mindepth 1 -maxdepth 1 -type d -not -name '.*' -printf '%f\n' | sort)

echo "== dead routes: cited by a doc but not installed =="
while IFS= read -r n; do
  [[ "$n" =~ $ALLOW ]] && continue
  [ -d "$ROOT/$n" ] && continue
  [[ "$n" != *-* ]] && continue   # skip backticked prose words
  echo "  DEAD    $n"; fail=1
done < <(grep -hoE '`[a-z][a-z0-9-]+`' "${DOCS[@]}" | tr -d '`' | sort -u)

echo "== broken links: reference/ files cited by SKILL.md =="
while IFS= read -r rel; do
  [ -r "$HERE/$rel" ] || { echo "  BROKEN  $rel"; fail=1; }
done < <(grep -oE '\(reference/[a-z-]+\.md\)' "$DOC" | tr -d '()' | sort -u)

echo "== count drift: '(N skills)' headings vs actual table rows =="
for f in "${DOCS[@]}"; do
  while IFS= read -r line; do
    hdr_ln=$(cut -d: -f1 <<<"$line")
    claimed=$(sed -E 's/.*\(([0-9]+)[^)]*skills?\).*/\1/' <<<"$line")
    actual=$(awk -v s="$hdr_ln" 'NR>s && /^\| /{c++} NR>s && /^$/ && c{print c; exit}' "$f")
    actual=$(( ${actual:-1} - 1 ))
    if [ "$claimed" != "$actual" ]; then
      echo "  DRIFT   $(basename "$f") L$hdr_ln claims $claimed, table has $actual"; fail=1
    fi
  done < <(grep -nE '^#+ .*\([0-9]+[^)]*skills?\)' "$f")
done

[ $fail -eq 0 ] && echo "OK — routes clean." || echo "drift found (see above)."
exit $fail
