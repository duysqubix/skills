#!/usr/bin/env bash
# sync-bead-to-jira.sh — reconstruct ONE bd issue as a Jira ticket (history-preserving).
#
# Pulls the bead straight from `bd`, rebuilds title + a structured body, links it to an
# epic, adds it to a sprint, transitions it to Done, logs a worklog, and re-posts the
# bead's notes (and any bd comments) as Jira comments so the history is preserved.
#
# Usage:
#   sync-bead-to-jira.sh <BEAD_ID> <DURATION> <STARTED> [--apply]
#
# DURATION : decimal hours (e.g. 2.5) OR an already-formatted jira string ("2h 30m")
# STARTED  : "YYYY-MM-DD HH:MM:SS"  (worklog start; use a past date in the sprint window)
# --apply  : actually mutate Jira + bd. Without it, dry-run only (prints the plan).
#
# Required env (NO defaults — refuses to run without them):
#   EPIC        Epic ticket key to link under (e.g. CAL-153). Create a new epic first
#               if none fits, then pass its key here.
#   EPIC_FIELD  Jira epic-link custom field id (per-instance, e.g. customfield_10014)
#   SPRINT_ID   Target sprint id (find via: jira sprint list --state active --plain)
#
# Optional env:
#   LABEL       Accounting/marker label added on create (e.g. no-live). Omitted if unset.
#   TITLE       Override the bead title (default: bead's own title).
#   BODY_FILE   Use this file as the description verbatim (default: auto-built from bead).
#   NO_COMMENTS=1  Skip re-posting notes/comments as Jira comments.
#
# Env overrides (have defaults):
#   BASE        Jira base URL         (default: https://calibercompletions.atlassian.net)
#   EMAIL       Jira auth user        (default: duys@calibercompletions.com)
#   PROJECT     Jira project key      (default: CAL)
#   ASSIGNEE    Jira display name     (default: Duan Uys)
#   JIRA_BIN    Path to jira binary   (default: ~/.local/bin/jira)
#   BD_BIN      Path to bd binary     (default: bd on PATH)

set -euo pipefail

# ── defaults (overridable) ────────────────────────────────────────────────────
BASE="${BASE:-https://calibercompletions.atlassian.net}"
EMAIL="${EMAIL:-duys@calibercompletions.com}"
PROJECT="${PROJECT:-CAL}"
ASSIGNEE="${ASSIGNEE:-Duan Uys}"
JIRA_BIN="${JIRA_BIN:-$HOME/.local/bin/jira}"
BD_BIN="${BD_BIN:-bd}"

# ── required (no defaults) ─────────────────────────────────────────────────────
EPIC="${EPIC:-}"
EPIC_FIELD="${EPIC_FIELD:-}"
SPRINT_ID="${SPRINT_ID:-}"
# ── optional ───────────────────────────────────────────────────────────────────
LABEL="${LABEL:-}"

usage() { sed -n '2,34p' "$0" | sed 's/^# \?//'; exit "${1:-0}"; }

J() { command "$JIRA_BIN" "$@"; }   # bypass the zsh `jira` prank wrapper

[[ "${1:-}" =~ ^(-h|--help)$ ]] && usage 0
[[ $# -lt 3 ]] && { echo "ERROR: need <BEAD_ID> <DURATION> <STARTED>" >&2; usage 1; }

BEAD_ID="$1"
DURATION_RAW="$2"
STARTED="$3"
APPLY=false
[[ "${4:-}" == "--apply" ]] && APPLY=true

# ── validate required env ──────────────────────────────────────────────────────
missing=()
[[ -z "$EPIC" ]]       && missing+=("EPIC")
[[ -z "$EPIC_FIELD" ]] && missing+=("EPIC_FIELD")
[[ -z "$SPRINT_ID" ]]  && missing+=("SPRINT_ID")
if (( ${#missing[@]} )); then
  echo "ERROR: required env not set: ${missing[*]}" >&2
  echo "  EPIC=<epic-key> EPIC_FIELD=<customfield_id> SPRINT_ID=<id> $0 ..." >&2
  exit 1
fi

# ── load token (do NOT source ~/.zshrc_local — its ~/.bun/_bun breaks bash) ─────
if [[ -z "${JIRA_API_TOKEN:-}" ]] && [[ -f "$HOME/.zshrc_local" ]]; then
  JIRA_API_TOKEN=$(grep -oP "(?<=JIRA_API_TOKEN=')[^']+" "$HOME/.zshrc_local" | head -1)
  export JIRA_API_TOKEN
fi
[[ -z "${JIRA_API_TOKEN:-}" ]] && { echo "ERROR: JIRA_API_TOKEN not set." >&2; exit 1; }

# ── pull the bead from bd (single source of truth) ─────────────────────────────
BEAD_JSON="$("$BD_BIN" show "$BEAD_ID" --json 2>/dev/null || true)"
[[ -z "$BEAD_JSON" ]] && { echo "ERROR: bead not found: $BEAD_ID" >&2; exit 1; }

# Capture any env TITLE override BEFORE we read the bead's own title.
TITLE_OVERRIDE="${TITLE:-}"

# bd show returns a 1-element array; pull the title (tab-delimited, newline-safe).
BEAD_TITLE="$(printf '%s' "$BEAD_JSON" | python3 -c '
import json,sys
d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d
print((d.get("title") or "").replace("\t"," ").replace("\n"," ").strip())
')"
BD_TYPE="$(printf '%s' "$BEAD_JSON" | python3 -c 'import json,sys;d=json.load(sys.stdin);d=d[0] if isinstance(d,list) else d;print(d.get("issue_type") or "?")')"
BD_STATUS="$(printf '%s' "$BEAD_JSON" | python3 -c 'import json,sys;d=json.load(sys.stdin);d=d[0] if isinstance(d,list) else d;print(d.get("status") or "?")')"

# env TITLE wins; else the bead's own title; else the bead id as last resort.
TITLE="${TITLE_OVERRIDE:-$BEAD_TITLE}"
[[ -n "$TITLE" ]] || TITLE="$BEAD_ID"

# Build the description body. If BODY_FILE given, use it verbatim; else auto-build.
if [[ -n "${BODY_FILE:-}" ]]; then
  [[ -f "$BODY_FILE" ]] || { echo "ERROR: BODY_FILE not found: $BODY_FILE" >&2; exit 1; }
  BODY="$(cat "$BODY_FILE")"
else
  BODY="$(printf '%s' "$BEAD_JSON" | python3 -c '
import json,sys
d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d
desc=(d.get("description") or "").strip()
notes=(d.get("notes") or "").strip()
out=[]
out.append("*Problem / Original ask*")
out.append(desc or "(no description on the bead)")
out.append("")
if notes:
    out.append("*What was delivered*")
    out.append(notes)
    out.append("")
out.append("*Context*")
bid=d.get("id",""); btype=d.get("issue_type","?"); bstat=d.get("status","?")
out.append("Reconstructed from bd issue %s (type=%s, status=%s)." % (bid, btype, bstat))
ca,cl=d.get("created_at"),d.get("closed_at")
if ca: out.append(f"Created: {ca}")
if cl: out.append(f"Closed: {cl}")
print("\n".join(out))
')"
fi

# ── decimal hours → jira duration ──────────────────────────────────────────────
hours_to_jira() {
  awk -v h="$1" 'BEGIN{
    th=int(h); m=int((h-th)*60+0.5); o=""
    if(th>0) o=th"h"
    if(m>0)  o=(o==""?"":o" ")m"m"
    if(o=="") o="1m"
    print o
  }'
}
if [[ "$DURATION_RAW" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  DURATION="$(hours_to_jira "$DURATION_RAW")"
else
  DURATION="$DURATION_RAW"
fi

# ── build the list of history comments to re-post (notes + bd comments) ─────────
COMMENTS_FILE="$(mktemp)"; trap 'rm -f "$COMMENTS_FILE"' EXIT
if [[ "${NO_COMMENTS:-0}" != "1" ]]; then
  # 1) the bead's notes blob
  printf '%s' "$BEAD_JSON" | python3 -c '
import json,sys
d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d
n=(d.get("notes") or "").strip()
if n: print("\x1e"+f"bd note (history):\n\n{n}")
' >> "$COMMENTS_FILE"
  # 2) any discrete bd comments, in order, author+time prefixed
  "$BD_BIN" comments "$BEAD_ID" --json 2>/dev/null | python3 -c '
import json,sys
try: cs=json.load(sys.stdin)
except: cs=[]
for c in (cs or []):
    who=c.get("author") or c.get("created_by") or "?"
    when=(c.get("created_at") or "")[:19]
    body=(c.get("text") or c.get("body") or "").strip()
    if body: print("\x1e"+f"bd comment — {who} {when}:\n\n{body}")
' >> "$COMMENTS_FILE" || true
fi
N_COMMENTS=$({ grep -c $'\x1e' "$COMMENTS_FILE" 2>/dev/null || true; } | head -1)
N_COMMENTS=${N_COMMENTS//[^0-9]/}; N_COMMENTS=${N_COMMENTS:-0}

# ── print plan ─────────────────────────────────────────────────────────────────
line() { printf '%s\n' "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }
line; echo "  bd-to-jira reconstruct"; line
echo "  BEAD      : $BEAD_ID  (type=$BD_TYPE status=$BD_STATUS)"
echo "  TITLE     : $TITLE"
echo "  BODY      : $(printf '%s' "$BODY" | wc -l) lines $( [[ -n "${BODY_FILE:-}" ]] && echo '(from BODY_FILE)' || echo '(auto-built)')"
echo "  DURATION  : $DURATION_RAW → $DURATION   @ $STARTED"
echo "  EPIC      : $EPIC   (field $EPIC_FIELD)"
echo "  SPRINT    : $SPRINT_ID"
echo "  PROJECT   : $PROJECT     ASSIGNEE: $ASSIGNEE"
echo "  LABEL     : ${LABEL:-<none>}"
echo "  COMMENTS  : $N_COMMENTS history comment(s) to re-post"
echo "  APPLY     : $APPLY"
line
echo "  1. idempotency check (existing ticket w/ same summary)"
echo "  2. create Story$( [[ -n "$LABEL" ]] && echo " -l $LABEL") -a '$ASSIGNEE'"
echo "  3. epic link  PUT  $EPIC_FIELD=$EPIC"
echo "  4. sprint     POST sprint/$SPRINT_ID/issue"
echo "  5. move Done"
echo "  6. worklog    $DURATION @ $STARTED"
echo "  7. re-post $N_COMMENTS history comment(s)"
echo "  8. label bead jira-synced"
line

if [[ "$APPLY" == false ]]; then
  echo; echo "  DRY-RUN — pass --apply to execute."; exit 0
fi

# ── step 1: idempotency ────────────────────────────────────────────────────────
# Durable key = a `bd-<id>` label stamped on every ticket we create. We search for
# THAT (JQL), not the summary text — summaries get reworded, the bead-id label does not.
echo; echo "[1/8] checking for existing ticket (label bd-$BEAD_ID)..."
BEAD_LABEL="bd-$BEAD_ID"
JQL="project=$PROJECT AND labels=$BEAD_LABEL"
command curl -s -G -u "$EMAIL:$JIRA_API_TOKEN" -H 'Content-Type: application/json' \
  --data-urlencode "jql=$JQL" --data-urlencode 'fields=key' \
  "$BASE/rest/api/3/search/jql" -o "$COMMENTS_FILE.idem" 2>/dev/null || true
KEY=$(python3 -c '
import json,sys
try: d=json.load(open(sys.argv[1]))
except Exception: d={}
iss=d.get("issues") or []
print(iss[0]["key"] if iss else "")
' "$COMMENTS_FILE.idem" 2>/dev/null || true)
rm -f "$COMMENTS_FILE.idem"

CREATED=false
if [[ -n "$KEY" ]]; then
  echo "  SKIP create — already synced as: $KEY (label $BEAD_LABEL)"
  echo "  (existing ticket: epic/sprint/Done re-asserted; worklog + comments NOT re-applied)"
else
  echo "[2/8] creating Story..."
  # Always stamp the bead-id label (+ optional accounting LABEL) so reruns are idempotent.
  CREATE_ARGS=(-tStory -a "$ASSIGNEE" -s "$TITLE" -b "$BODY" -l "$BEAD_LABEL" --no-input)
  [[ -n "$LABEL" ]] && CREATE_ARGS=(-l "$LABEL" "${CREATE_ARGS[@]}")
  KEY=$(J issue create "${CREATE_ARGS[@]}" | grep -oE "${PROJECT}-[0-9]+" | head -1)
  [[ -z "$KEY" ]] && { echo "ERROR: failed to capture ticket key." >&2; exit 1; }
  echo "  created: $KEY (labeled $BEAD_LABEL)"
  CREATED=true
fi

# ── step 3: epic link ──────────────────────────────────────────────────────────
echo "[3/8] linking epic ($EPIC via $EPIC_FIELD)..."
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -u "$EMAIL:$JIRA_API_TOKEN" \
  -H 'Content-Type: application/json' -X PUT "$BASE/rest/api/3/issue/$KEY" \
  --data "{\"fields\":{\"$EPIC_FIELD\":\"$EPIC\"}}")
echo "  HTTP $HTTP (expect 204)"
[[ "$HTTP" != "204" ]] && echo "  WARNING: unexpected HTTP for epic link" >&2

# ── step 4: sprint ─────────────────────────────────────────────────────────────
echo "[4/8] adding to sprint $SPRINT_ID..."
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -u "$EMAIL:$JIRA_API_TOKEN" \
  -H 'Content-Type: application/json' -X POST "$BASE/rest/agile/1.0/sprint/$SPRINT_ID/issue" \
  --data "{\"issues\":[\"$KEY\"]}")
echo "  HTTP $HTTP (expect 204)"
[[ "$HTTP" != "204" ]] && echo "  WARNING: unexpected HTTP for sprint add" >&2

# ── step 5: done ───────────────────────────────────────────────────────────────
echo "[5/8] transitioning to Done..."
J issue move "$KEY" "Done"

# ── step 6: worklog (fresh-create only — worklogs are NOT idempotent) ───────────
if [[ "$CREATED" == true ]]; then
  echo "[6/8] worklog $DURATION @ $STARTED..."
  J issue worklog add "$KEY" "$DURATION" --started "$STARTED" \
    --comment "Retroactive log: $BEAD_ID" --no-input
else
  echo "[6/8] worklog SKIPPED (existing ticket — would duplicate hours)"
fi

# ── step 7: re-post history comments (fresh-create only — comments are NOT idempotent) ──
if [[ "$CREATED" == true && "${N_COMMENTS:-0}" =~ ^[0-9]+$ && "${N_COMMENTS:-0}" -gt 0 ]]; then
  echo "[7/8] posting $N_COMMENTS history comment(s)..."
  # records are separated by the RS char (\x1e)
  while IFS= read -r -d $'\x1e' rec; do
    [[ -z "${rec//[$'\n\t ']/}" ]] && continue
    printf '%s' "$rec" | J issue comment add "$KEY" --no-input >/dev/null
    echo "  + comment posted"
  done < <(cat "$COMMENTS_FILE"; printf '\x1e')
elif [[ "$CREATED" != true ]]; then
  echo "[7/8] comments SKIPPED (existing ticket — would duplicate)"
fi

# ── step 8: label bead ─────────────────────────────────────────────────────────
echo "[8/8] labeling bead jira-synced..."
"$BD_BIN" update "$BEAD_ID" --add-label jira-synced 2>&1 | grep -iv depends_on_id || true

echo; echo "  $BEAD_ID -> $KEY  (+$N_COMMENTS comments)"; echo "  DONE"
