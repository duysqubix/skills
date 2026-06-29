---
name: bd-to-jira
description: >
  Converts closed bd (beads) issues into Jira Stories: creates tickets, links to an epic,
  adds to the active sprint, transitions to Done, and logs a complexity-sized worklog.
  Labels each synced bead `jira-synced` so reruns skip it. Use when asked to "sync beads
  to jira", "bd to jira", "create jira tickets from bd", "create jira tickets from beads",
  "log completed work to jira", "retroactively log dev work to jira", "jira-synced label",
  "batch jira tickets from tracker", or "push closed beads to jira".
---

# bd-to-jira

Retroactively log closed `bd` issues as Jira Stories for accounting/sprint reporting.

## Quick start

```bash
# 1. Find beads that need syncing
bd list --all --json | python3 -c "
import json,sys
issues = json.load(sys.stdin)
for i in issues:
    if i.get('status')=='closed' and 'jira-synced' not in (i.get('labels') or []):
        print(i['id'], i['title'])
"

# 2. Reconstruct one bead -> Jira (self-sources from bd; dry-run first, then --apply).
#    Required env: EPIC, EPIC_FIELD, SPRINT_ID.  Optional: LABEL.
EPIC=CAL-153 EPIC_FIELD=customfield_10014 SPRINT_ID=134 LABEL=no-live \
  scripts/sync-bead-to-jira.sh <BEAD_ID> 2.5 "2026-06-02 14:00:00"
EPIC=CAL-153 EPIC_FIELD=customfield_10014 SPRINT_ID=134 LABEL=no-live \
  scripts/sync-bead-to-jira.sh <BEAD_ID> 2.5 "2026-06-02 14:00:00" --apply
```

The helper pulls the bead from `bd` itself — you pass only the id, worklog hours, and
start time. It auto-builds the body (Problem / What was delivered / Context) from the
bead's description + notes, and re-posts the bead's notes/comments as Jira comments.
Override the title/body with `TITLE=` / `BODY_FILE=`. Need a new epic first?
`jira epic create -n"Name" -s"Summary"`, then pass its key as EPIC.

## The 8-step pipeline (per ticket)

| Step | Tool | Expect |
|------|------|--------|
| 1. IDEMPOTENCY | `jira issue list` summary match | reuse key if exists |
| 2. CREATE | `jira issue create -tStory` | prints `<PROJ>-NNN` |
| 3. EPIC LINK | REST PUT `$EPIC_FIELD` | HTTP 204 |
| 4. SPRINT | REST POST agile sprint/issue | HTTP 204 |
| 5. DONE | `jira issue move KEY Done` | ok |
| 6. WORKLOG | `jira issue worklog add KEY DURATION` | ok |
| 7. HISTORY | `jira issue comment add` per note/comment | preserves bead history |
| 8. LABEL | `bd update <id> --add-label jira-synced` | marks synced |

**Required env (no defaults):** `EPIC`, `EPIC_FIELD`, `SPRINT_ID`.
**Optional:** `LABEL` (e.g. `no-live`, applied only if set), `TITLE`, `BODY_FILE`, `NO_COMMENTS=1`.

## Critical gotchas

- **Shell prank**: a zsh alias wraps `jira` and dumps an RPG character sheet. Always call
  `command ~/.local/bin/jira ...` and pipe through `grep -oE 'CAL-[0-9]+' | head -1` to
  extract keys. For curl, write to a file (`-o file.json`) then parse — piped streams are
  corrupted by the prank.
- **jira-cli epic/sprint flags silently no-op** — use REST for both (steps 2 and 3).
- **Worklog duration**: no decimals. Use `Xh Xm` format. `3.5` → `"3h 30m"`. See helper.
- **bd dolt bug**: `bd close` fails with `column "depends_on_id" could not be found`.
  Use `bd update <id> --status closed` instead. Label ops may print the error — filter
  with `grep -iv depends_on_id`.
- **Sprint ID**: discover at runtime via `jira sprint list --state active --plain`.
  Never hardcode.
- **Idempotency**: check for existing ticket by exact summary before creating.
- **Token in bash**: do NOT `source ~/.zshrc_local` from a bash script — it pulls in
  `~/.bun/_bun` (zsh-only syntax) and errors. Grep the token instead:
  `JIRA_API_TOKEN=$(grep -oP "(?<=JIRA_API_TOKEN=')[^']+" ~/.zshrc_local | head -1)`.

## Body & history

The script auto-builds the description (*Problem* / *What was delivered* / *Context*)
from the bead's `description` + `notes`, and re-posts `notes` and any `bd comments`
as Jira comments. See [REFERENCE.md](REFERENCE.md) for the exact template.

## Worklog sizing heuristic

Senior dev + AI assist (faster than raw human):
- Small rename/config: ~45m
- Bug fix: ~1.5h
- Medium feature: ~2.5–3.5h

Spread `--started` dates across past days in the sprint window at ~7h/day. Never future-date.

## See also

- [REFERENCE.md](REFERENCE.md) — field IDs, REST bodies, verification gate, full examples
- [scripts/sync-bead-to-jira.sh](scripts/sync-bead-to-jira.sh) — single-ticket helper
