# Bead Development Workflow (SDLC)

> The bead-based software-development lifecycle for any project that tracks work in **beads** (`bd`).
> The **core** is portable to any project. Sections marked 🟧 **Caliber overlay** are organization-specific — omit them elsewhere.
>
> `/using-beads` injects this workflow. **Read this before creating or transitioning any bead.**

---

## 0. Roles — and the one golden rule

| Role | Who | May do | May NOT do |
|---|---|---|---|
| **Main orchestrator** | the agent the user talks to / that invoked `/using-beads` | Everything: create, change status, label, comment, close, resolve, judge correctness, log hours | — |
| **Sub-agent** | any agent the orchestrator spawns | Do the work; **comment**; **raise** signal labels; add descriptive labels | **Never** change status; never judge "done"; never close |

**Golden rule (Rule 6):** the orchestrator **MUST** inject `/using-beads` into every sub-agent prompt, with the bead id and the sub-agent guardrails. Paste this block into each delegation:

```
You operate under the beads workflow — invoke /using-beads to load it.
You are a SUB-AGENT working bead <BEAD-ID>.
- Do NOT change any bead's status (no close / reopen / defer / set-state / --status / --claim).
- You MAY and SHOULD add markdown comments:  bd comment <BEAD-ID> "..."
- If you hit a blocker, need a human, need a specialist, or are ready for QA:
  RAISE the matching signal label AND leave a comment explaining why.
  The orchestrator will act on it and own the status change.
```

---

## 1. Every work item lives in an epic (Rules 1, 2, 3)

No orphan beads. Every task / bug / feature / chore is parented to an epic.

```bash
bd list --type=epic                                            # 1. ALWAYS look for a reusable epic first
bd create --type=epic --title="Billing" --description="..."    # 2. create one ONLY if nothing fits
bd create --type=feature --parent=<epic-id> --title="..." --description="..."
```

- **Reuse over proliferation (Rule 3):** prefer an existing epic. Create a new one only when nothing genuinely fits. **If you are unsure how to categorize a bead → STOP and ask the user.** (The orchestrator decides; a sub-agent surfaces the question via comment + `needs-human-input`.)
- Children **inherit the epic's labels** by default (sprint, `no-live`, …). Use `--no-inherit-labels` to opt out, or `bd label propagate <epic-id> <label>` to push a label down later.

---

## 2. Status lifecycle — ORCHESTRATOR ONLY (Rules 4, 5, 7, 13)

```
open ──claim──▶ in_progress ──────────▶ closed
                  │     ▲
       defer/block ▼     │ undefer / reopen
              deferred / blocked          ← native bd statuses
```

Only the **orchestrator** runs any of these:

```bash
bd update <id> --claim                 # open → in_progress (sets assignee + status)
bd update <id> --status in_progress
bd defer  <id> --until="2026-08-01"    # → deferred (hidden from `bd ready`)
bd update <id> --status blocked        # external blocker (mirrors the `blocked` signal label)
bd close  <id> --reason="..."          # → closed, always with a closing comment
bd reopen <id>
```

- **Rule 13:** a bead's status must always reflect reality — transition it the moment reality changes.
- **Rule 5:** the orchestrator is the *sole authority* on whether a feature was built correctly, a bug truly fixed, or an item triaged properly. A sub-agent's "done" is an input, not a decision.

---

## 3. Sub-agent ↔ orchestrator authority (Rules 7, 8, 9, 11)

- **Sub-agents NEVER touch status** — no `close` / `reopen` / `defer` / `set-state` / `--status` / `--claim`. (In a hard sandbox the orchestrator can pass `bd --readonly` for status ops, but `--readonly` blocks *all* writes incl. comments — so prefer the behavioral guardrail in §0.)
- **Sub-agents MAY and SHOULD comment** on the bead they're working (Rule 8) and **raise signal labels** (Rule 11) — always paired with a comment.
- **Both roles** treat comments as the auditable lifecycle record (Rule 9, see §6).

---

## 4. Labels (Rules 10, 11)

Apply / remove (either role, Rule 11):

```bash
bd create ... --labels S07,no-live          # at creation (comma-separated)
bd label add    <id> consult-oracle         # add
bd label remove <id> blocked                # remove
bd label list   <id>                        # inspect
```

**Always pair a *signal* label with a `bd comment` explaining why.**

### Signal labels — sub-agents RAISE, orchestrator ACTS
| Label | Meaning |
|---|---|
| `blocked` | Can't progress due to an external variable outside our control. Orchestrator mirrors it to the native `blocked` status. |
| `needs-human-input` | Ambiguous requirements, missing context, or a logical fork requiring a human decision. |
| `needs-specialist` | Wrong tools for the job; requesting a handoff to a differently-skilled agent. Pair with `bd update <id> --skills="..."`. |
| `consult-oracle` | Implementation complete; queued for a dedicated QA/testing pass before it may be closed. |

### Lifecycle labels
| Label | Meaning |
|---|---|
| `deferred` | Wanted, but not ready / not the time to act on it. Drive via `bd defer <id> --until=<date>`. |
| `S[nn]` | **Mandatory sprint** on every bead (`S01`, `S07`, `S42`, …). See §5. |

### Resolution labels — orchestrator, at / after close
| Label | Meaning |
|---|---|
| `wont-do` | Decided not to pursue, no intention to revisit. **Only on `closed` beads.** |
| `duplicate` | Redundant with an existing bead. Prefer the native `bd duplicate` (see `bd duplicate --help`). |
| `tech-debt` | Patched / bypassed to ship; flagged for a proper architectural rewrite later. |

### 🟧 Caliber overlay
| Label | Meaning |
|---|---|
| `no-live` | Work not yet deployed to the live / production environment — new features, enhancements, or backlog items that are in development, scoped, or planned but **not yet live**. A standing classification label; apply to any pre-production bead. |

---

## 5. Sprints — every bead carries `S[nn]` (Rule 10 j–l)

The **current sprint** and its **expiry date** are persisted in `bd config` (team-shared, version-controlled):

```bash
bd config set custom.sprint S07
bd config set custom.sprint.expires 2026-07-15      # ISO date (YYYY-MM-DD)
bd config get custom.sprint
```

**Before stamping any bead (and at session start) the agent MUST:**

1. Read `custom.sprint` and `custom.sprint.expires`.
2. **Either is unset** → ask the user for the current sprint label **and** its end date; store both.
3. **`today > custom.sprint.expires`** → STOP and notify the user:
   *"⚠️ Sprint `S07` expired on 2026-07-15 — what's the next sprint label and its end date?"* → update both config keys → continue.
4. **Otherwise** → stamp the current `S[nn]` on the bead (`--labels S07` on create, or `bd label add <id> S07`).

```bash
TODAY=$(date +%F); EXP=$(bd config get custom.sprint.expires)
if [ -z "$EXP" ] || [ "$TODAY" \> "$EXP" ]; then echo "SPRINT EXPIRED/UNSET — ask the user"; fi
```

**Rule 10l:** no bead may exist without an `S[nn]` label.

---

## 6. Comments = the auditable lifecycle (Rules 8, 9, 15)

```bash
bd comment <id> "Solution note: switched to a cursor pager; the offset scan was O(n^2) past 10k rows."
bd comment <id> --file notes.md           # longer markdown notes
```

- **Markdown always** (Rule 15) — in comments, descriptions (`--description`), and design notes (`--design`).
- Log **solution notes, blocker notes, decisions, and handoff context** — anything that lets the same or another agent pick the bead up cold with no prior knowledge (Rule 9).
- Both orchestrator and sub-agents are encouraged to comment liberally.

---

## 7. Dependencies (Rule 16)

```bash
bd create ... --deps 'blocks:<id>'        # declare at creation (e.g. blocks:bd-15, discovered-from:bd-20)
bd dep add <issue> <depends-on>           # <issue> depends on <depends-on>
bd blocked                                # what's currently blocked
```

Always declare dependencies when they are known.

---

## 8. Hours logging — a single, manually-summed total (Rule 17)

The **only** mechanism for logging hours is bead metadata under the `hours` key — one cumulative decimal value. **Do NOT use `--estimate`, or any other field, for hours.** Track *how much* time the ticket took, never *when* (no dates, timestamps, or per-session entries).

⚠️ **`--set-metadata` stores one value per key — it does NOT auto-sum.** `hours=` overwrites whatever was already there. To add time you MUST read the current total, do the math yourself, and write the **new total** (never the increment):

```bash
bd show   <id> --json                       # read current metadata.hours, e.g. 2.5
# 2.5 already logged + 1.5 just worked = 4.0
bd update <id> --set-metadata hours=4.0     # write the new TOTAL, not the delta
```

- The number is the best joint judgment of the human + AI. **Consult the user when unsure** before committing hours.

---

## 9. Epic closure is a human gate (Rule 14)

**Never auto-close an epic**, even when all its children are closed.

```bash
bd epic status            # completion overview across epics
bd children <epic-id>     # confirm all children are closed
# → if all children are closed, ASK THE USER before closing the epic.
```

(`bd epic close-eligible` exists but is intentionally **not** used in this workflow.)

---

## 🟧 10. Cross-environment comms (Rule 12) — OPT-IN, never auto-scaffolded

A protocol for production agents and development agents to message each other via beads. **The agent NEVER creates these epics automatically.** Offer to scaffold only on explicit user opt-in; otherwise ignore this layer entirely.

Two standing epics hold the "messages":

- **Notes from Production: For Dev**
- **Notes from Dev: For Production**

Each message is a bead whose **labels** track where it sits in the handshake (plain coexisting labels — *not* `bd set-state`, because a note and its done-marker must co-exist):

| Label | Direction | Meaning |
|---|---|---|
| `for-dev:note` | prod → dev | A note for development agents (usually written by a prod agent). |
| `for-dev:action` | prod → dev | A specific recommended action for development agents. |
| `for-dev:done` | dev → prod | **Must accompany `for-dev:note`.** Dev agents have read / addressed the note; lets prod verify. |
| `for-prod:note` | dev → prod | A note for production agents (usually written by a dev agent). |
| `for-prod:action` | dev → prod | A specific recommended action for production agents. |
| `for-prod:done` | prod → dev | **Must accompany `for-prod:note`.** Prod agents have read / addressed the note. |

Example:

```bash
# A prod agent reports a production issue for dev to triage:
bd create --type=bug --parent=<notes-from-prod-epic> \
  --title="500s on /checkout under load" --labels S07,for-dev:action,no-live \
  --description="Repro steps + stack trace (markdown)…"

# A dev agent, after addressing it, signals back:
bd label add <id> for-dev:done
bd comment   <id> "Fixed in <bead-id>; root cause was connection-pool exhaustion."
```

---

## Quick reference

```bash
bd ready                                    # claimable work (open, unblocked)
bd list --type=epic                         # find a reusable epic
bd create --type=feature --parent=<epic> --labels S07 --description="…(markdown)"
bd update <id> --claim                      # ORCHESTRATOR: → in_progress
bd comment <id> "…"                         # anyone: audit note (markdown)
bd label add/remove <id> <label>            # anyone (signal labels: + a comment)
bd dep add <issue> <depends-on>             # dependencies
bd update <id> --set-metadata hours=<total>  # running total, decimal hours
bd close <id> --reason="…"                  # ORCHESTRATOR only
bd epic status                              # before (never auto-) closing an epic
```

## Session-close checklist (with `SKILL.md`)

1. Every worked bead reflects true status; the orchestrator closes done items with `--reason` + a closing comment.
2. The `hours` running total is current (`--set-metadata hours=`, single cumulative decimal).
3. An `S[nn]` sprint label is on every touched bead, and the sprint is not expired.
4. Dependencies and signal labels are resolved or explicitly handed off.
5. Quality gates run; then follow the active commit / push profile.
