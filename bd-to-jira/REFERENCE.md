# bd-to-jira Reference

Full detail for the bd → Jira sync workflow. See SKILL.md for the quick-start.

---

## Environment

**Required (no defaults — the script refuses to run without them):**

| Variable | Example | Notes |
|----------|---------|-------|
| `EPIC` | `CAL-153` | Epic key to link under. Create a new epic first if none fits. |
| `EPIC_FIELD` | `customfield_10014` | Epic-link custom field id — varies per Jira instance. |
| `SPRINT_ID` | `134` | Target sprint id. Find via `jira sprint list --state active --plain`. |

**Optional:**

| Variable | Example | Notes |
|----------|---------|-------|
| `LABEL` | `no-live` | Accounting/marker label, added on create only if set. |
| `TITLE` | | Override the bead's title. |
| `BODY_FILE` | | Use this file as the description verbatim instead of auto-building. |
| `NO_COMMENTS` | `1` | Skip re-posting notes/comments as Jira comments. |

**Overridable (have defaults):**

| Variable | Default | Notes |
|----------|---------|-------|
| `BASE` | `https://calibercompletions.atlassian.net` | Jira base URL |
| `EMAIL` | `duys@calibercompletions.com` | Auth user |
| `PROJECT` | `CAL` | Jira project key |
| `ASSIGNEE` | `Duan Uys` | Jira display name |
| `JIRA_BIN` | `~/.local/bin/jira` | jira-cli path |
| `BD_BIN` | `bd` | bd CLI path |

Load token (interactive shell): `source ~/.zshrc_local`

**In a bash script, do NOT `source ~/.zshrc_local`** — it pulls in `~/.bun/_bun`,
which uses zsh-only syntax and throws `syntax error near unexpected token '('`.
Extract the token directly instead:

```bash
JIRA_API_TOKEN=$(grep -oP "(?<=JIRA_API_TOKEN=')[^']+" ~/.zshrc_local | head -1)
export JIRA_API_TOKEN
```

jira-cli binary: `~/.local/bin/jira` v1.7.0

---

## The Shell Prank — Critical

A zsh alias wraps `jira` and prints an RPG character sheet (ASCII box + emoji inventory)
into stdout/stderr on every invocation. This corrupts any pipe that expects clean output.

**Always bypass it:**
```bash
command ~/.local/bin/jira ...
```

**Extracting a ticket key from create output:**
```bash
command ~/.local/bin/jira issue create ... | grep -oE 'CAL-[0-9]+' | head -1
```

**For curl — write to file, then parse:**
```bash
command curl -s -u "$EMAIL:$JIRA_API_TOKEN" "$BASE/rest/api/3/issue/$KEY" -o out.json
python3 -c "import json; d=json.load(open('out.json')); print(d['fields']['status']['name'])"
```
Never pipe curl output directly — the prank corrupts the stream.

---

## Field IDs

| Field | ID | Example value |
|-------|----|---------------|
| Epic link | `customfield_10014` | `"CAL-153"` |
| Sprint | `customfield_10020` | array of sprint objects; check `id` field |
| Labels | `labels` | `["no-live"]` |
| Assignee | `assignee` | `{"displayName": "Duan Uys"}` |

---

## Step 1 — CREATE

```bash
command ~/.local/bin/jira issue create \
  -tStory \
  -l no-live \
  -a "Duan Uys" \
  -s "$TITLE" \
  -b "$BODY" \
  --no-input \
| grep -oE 'CAL-[0-9]+' | head -1
```

`-l no-live` = accounting label meaning "work merged but NOT yet in production".
Used to sum worklogs for sprint accounting.

---

## Step 2 — EPIC LINK (REST)

jira-cli `--epic` flag silently no-ops. Must use REST:

```bash
curl -s -o /dev/null -w '%{http_code}' \
  -u "$EMAIL:$JIRA_API_TOKEN" \
  -H 'Content-Type: application/json' \
  -X PUT "$BASE/rest/api/3/issue/$KEY" \
  --data "{\"fields\":{\"customfield_10014\":\"$EPIC\"}}"
# expect: 204
```

---

## Step 3 — SPRINT (REST)

jira-cli `--sprint` flag silently no-ops. Must use REST:

```bash
curl -s -o /dev/null -w '%{http_code}' \
  -u "$EMAIL:$JIRA_API_TOKEN" \
  -H 'Content-Type: application/json' \
  -X POST "$BASE/rest/agile/1.0/sprint/$SPRINT_ID/issue" \
  --data "{\"issues\":[\"$KEY\"]}"
# expect: 204
```

---

## Step 4 — TRANSITION TO DONE

```bash
command ~/.local/bin/jira issue move "$KEY" "Done"
```

---

## Step 5 — WORKLOG

```bash
command ~/.local/bin/jira issue worklog add "$KEY" "$DURATION" \
  --started "$STARTED" \
  --comment "$COMMENT" \
  --no-input
```

`DURATION` format: `Xh Xm` — no decimals. Examples: `2h 30m`, `45m`, `3h`.
`STARTED` format: `YYYY-MM-DD HH:MM:SS`

### Decimal-hours to jira-cli format converter (awk)

```bash
hours_to_jira() {
  awk -v h="$1" 'BEGIN{
    th=int(h)
    m=int((h-th)*60+0.5)
    o=""
    if(th>0) o=th"h"
    if(m>0)  o=(o==""?"":o" ")m"m"
    if(o=="") o="1m"
    print o
  }'
}
# Usage: hours_to_jira 3.5  → "3h 30m"
#        hours_to_jira 0.75 → "45m"
#        hours_to_jira 2.0  → "2h"
```

---

## Sprint Discovery (runtime)

Never hardcode the sprint ID. Discover at runtime:

```bash
SPRINT_ID=$(command ~/.local/bin/jira sprint list --state active --plain \
  | grep -i active \
  | awk '{print $1}' \
  | head -1)
```

Output columns: ID NAME START END STATE. The active row's first column is the ID.

---

## Max-key / Next-key Discovery

To find the highest existing CAL ticket number:

```bash
command ~/.local/bin/jira issue list -p CAL --plain --no-headers --columns key 2>/dev/null \
  | grep -oE 'CAL-[0-9]+' \
  | sort -t- -k2 -n \
  | tail -1
```

Numeric sort (`-k2 -n`) is required — lexicographic sort breaks at CAL-100+.

---

## Idempotency Guard

Before creating, check for an existing ticket with the exact summary:

```bash
EXISTING=$(command ~/.local/bin/jira issue list -p CAL --plain --no-headers \
  --columns key,summary 2>/dev/null \
  | grep -F "	$TITLE" \
  | grep -oE 'CAL-[0-9]+' \
  | head -1)

if [[ -n "$EXISTING" ]]; then
  echo "SKIP: $TITLE already exists as $EXISTING"
  KEY="$EXISTING"
else
  # proceed with create
fi
```

Note: the separator between key and summary in `--plain` output is a tab character.

---

## Gap Detection — Which Beads Need Syncing

```bash
bd list --all --json | python3 -c "
import json, sys
issues = json.load(sys.stdin)
for i in issues:
    labels = i.get('labels') or []
    if i.get('status') == 'closed' and 'jira-synced' not in labels:
        print(i['id'], repr(i['title']))
"
```

Exclude junk beads (test/placeholder titles, user-error-no-code) — flag those to the user
rather than syncing.

---

## Labeling Synced Beads

After a successful sync:

```bash
bd update "$BEAD_ID" --add-label jira-synced 2>&1 | grep -iv depends_on_id
```

`--add-label` is the correct flag (repeatable). NOT `--label`.
The dolt bug may print `column "depends_on_id" could not be found` — filter it out.

---

## bd Dolt Bug Workarounds

| Operation | Broken command | Workaround |
|-----------|---------------|------------|
| Close issue | `bd close <id>` | `bd update <id> --status closed` |
| Add label | `bd update <id> --add-label X` | works, but filter stderr |
| Remove label | `bd update <id> --remove-label X` | works, but filter stderr |

---

## Body Template

Build from the bead's description + notes:

```
*Problem*
<what was broken/missing>

*User story*
As a <role>, I want <capability>, so that <benefit>.

*What was delivered*
- <bullet from bead NOTES "DONE..." record>
- <bullet>

*Context*
Repo: <repo/branch>
Tests: <e.g. "150 tests green">
Related beads: <IDs>
<BREAKING notes if any>
```

The helper auto-builds this from the bead's `description` (Problem) and `notes`
(What was delivered), plus a Context footer with the bead id, type, status, and
created/closed timestamps. Override with `BODY_FILE=<file>` to supply a body verbatim,
or `TITLE=<text>` to override the summary.

---

## History Reconstruction (notes + comments → Jira comments)

To preserve the bead's history, the helper re-posts as Jira comments (step 7):

1. **The `notes` blob** — the bead's free-text implementation/history record — posted
   as one comment prefixed `bd note (history):`.
2. **Each discrete `bd comment`** (from `bd comments <id> --json`) — posted in order,
   each prefixed with its original author + timestamp (`bd comment — <who> <when>:`).

Most beads in embedded-dolt mode have an empty `bd comments` stream, so the `notes`
field is usually the whole history. Set `NO_COMMENTS=1` to skip this step entirely.

```bash
# Inspect what history a bead carries before syncing:
bd show <id> --json | python3 -c 'import json,sys;d=json.load(sys.stdin)[0];print("notes:",bool(d.get("notes")))'
bd comments <id> --json   # discrete comments (often [])
```

Jira comment add: `command ~/.local/bin/jira issue comment add <KEY> "<body>" --no-input`
(also accepts the body on stdin, which the helper uses for multi-line notes).

---

## Worklog Sizing Heuristic

Estimate as a senior dev assisted by AI (faster than raw human):

| Work type | Duration |
|-----------|----------|
| Small rename / config tweak | 45m |
| Simple bug fix | 1h–1.5h |
| Medium feature / refactor | 2.5h–3.5h |
| Large feature with tests | 4h–6h |

Spread `--started` timestamps across past days within the active sprint window.
Target ~7h/day cadence. Never future-date relative to today.

Example spread for 5 tickets over 3 days:
```
Day -2: 09:00, 11:30
Day -1: 09:00, 14:00
Day  0: 10:00
```

---

## Verification Gate

After each ticket, REST GET and assert all fields landed correctly:

```bash
command curl -s \
  -u "$EMAIL:$JIRA_API_TOKEN" \
  "$BASE/rest/api/3/issue/$KEY?fields=summary,status,customfield_10014,customfield_10020,worklog,labels,assignee" \
  -o verify.json

python3 - <<EOF
import json, os
d = json.load(open('verify.json'))
f = d['fields']
epic     = os.environ.get('EPIC', 'CAL-153')
assignee = os.environ.get('ASSIGNEE', 'Duan Uys')
sprint   = int(os.environ['SPRINT_ID'])
assert f['status']['name'] == 'Done',            f"status={f['status']['name']}"
assert f['customfield_10014'] == epic,           f"epic={f['customfield_10014']}"
sprint_ids = [s['id'] for s in (f.get('customfield_10020') or [])]
assert sprint in sprint_ids,                     f"sprint not found: {sprint_ids}"
assert f['worklog']['total'] >= 1,               "no worklog"
assert 'no-live' in f['labels'],                 f"labels={f['labels']}"
assert f['assignee']['displayName'] == assignee, f"assignee={f['assignee']}"
print('OK:', d['key'])
EOF
```

`EPIC`, `ASSIGNEE`, and `SPRINT_ID` are read from the environment (same vars the
helper script uses), so the gate stays in sync with whatever you synced.

---

## Full Example — One Ticket End to End

```bash
JIRA_API_TOKEN=$(grep -oP "(?<=JIRA_API_TOKEN=')[^']+" ~/.zshrc_local | head -1); export JIRA_API_TOKEN
BASE="https://calibercompletions.atlassian.net"
EMAIL="duys@calibercompletions.com"
EPIC="CAL-153"; EPIC_FIELD="customfield_10014"   # both required
SPRINT_ID=$(command ~/.local/bin/jira sprint list --state active --plain \
  | grep -i active | awk '{print $1}' | head -1)

BEAD_ID="pulsebridge-xto"
BEAD=$(bd show "$BEAD_ID" --json)
TITLE=$(printf '%s' "$BEAD" | python3 -c 'import json,sys;d=json.load(sys.stdin)[0];print(d["title"])')
BODY=$(printf '%s' "$BEAD" | python3 -c 'import json,sys;d=json.load(sys.stdin)[0];print((d.get("description") or "")+chr(10)+chr(10)+(d.get("notes") or ""))')
NOTES=$(printf '%s' "$BEAD" | python3 -c 'import json,sys;d=json.load(sys.stdin)[0];print(d.get("notes") or "")')
DURATION="45m"
STARTED="2026-05-28 09:00:00"

# Idempotency check
KEY=$(command ~/.local/bin/jira issue list -p CAL --plain --no-headers \
  --columns key,summary 2>/dev/null \
  | grep -F "	$TITLE" | grep -oE 'CAL-[0-9]+' | head -1)

if [[ -z "$KEY" ]]; then
  KEY=$(command ~/.local/bin/jira issue create \
    -tStory -l no-live -a "Duan Uys" -s "$TITLE" -b "$BODY" --no-input \
    | grep -oE 'CAL-[0-9]+' | head -1)
  echo "Created: $KEY"
fi

# Epic
curl -s -o /dev/null -w '%{http_code}\n' \
  -u "$EMAIL:$JIRA_API_TOKEN" -H 'Content-Type: application/json' \
  -X PUT "$BASE/rest/api/3/issue/$KEY" \
  --data "{\"fields\":{\"$EPIC_FIELD\":\"$EPIC\"}}"

# Sprint
curl -s -o /dev/null -w '%{http_code}\n' \
  -u "$EMAIL:$JIRA_API_TOKEN" -H 'Content-Type: application/json' \
  -X POST "$BASE/rest/agile/1.0/sprint/$SPRINT_ID/issue" \
  --data "{\"issues\":[\"$KEY\"]}"

# Done
command ~/.local/bin/jira issue move "$KEY" "Done"

# Worklog
command ~/.local/bin/jira issue worklog add "$KEY" "$DURATION" \
  --started "$STARTED" --comment "Retroactive log" --no-input

# History: re-post the bead notes as a Jira comment
[[ -n "$NOTES" ]] && printf 'bd note (history):\n\n%s' "$NOTES" \
  | command ~/.local/bin/jira issue comment add "$KEY" --no-input

# Label bead
bd update "$BEAD_ID" --add-label jira-synced 2>&1 | grep -iv depends_on_id

echo "DONE: $BEAD_ID -> $KEY"
```
