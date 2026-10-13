---
name: reference-ops-and-meta
description: Multi-Model Orchestration (ask) and Workflow Ops & Meta (tracker, skill-library, toolchain) families. Loaded from using-agent-skills for cross-vendor second opinions or work that operates on the tracker or the skill library itself.
---

# Multi-Model Orchestration — `oh-my-claudecode` plugin

Cross-vendor advisors. Every other skill in this library runs *inside* Claude; this family reaches **outside** it for independent perspectives, then Claude reconciles them.

| Skill | When to invoke |
|---|---|
| `/oh-my-claudecode:ask` (Codex: `$ask`) | One named external advisor per call (`omc ask codex "…"` / `omc ask gemini "…"`). Run two and synthesize for a cross-vendor check |

**Cross-vendor check with `ask`** (the retired `ccg` wrapper did this; OMC 5.x removed it): split the request into two advisor prompts — Codex takes architecture / correctness / backend / risk / test strategy, Antigravity (`agy`) or Gemini takes UX / content clarity / alternatives / docs polish — run both via `omc ask`, read the artifacts from `.omc/artifacts/ask/`, then return **one** answer with agreements, explicit conflicts, chosen direction + rationale, and an action checklist.

**Requirements & fallbacks:** needs `omc` plus at least one of `codex` / `agy` / `gemini` on PATH. Antigravity (`agy`) is the intended second lane; where it isn't installed, `gemini` takes that lane. With only one provider, continue and **state which perspective is missing**. With none, answer as Claude alone and say the external advisors were unavailable.

**Beyond `ask`:** the oh-my-claudecode plugin carries a larger workflow set not routed here — `autopilot`, `ralph`, `ralplan`, `team`, and more. Run `/oh-my-claudecode:wiki` for the full catalog.

**Routing:** reach for `ask` when the risk is *model-specific blind spots* (cross-validation, disputed architecture calls, review from genuinely independent eyes). Stay with `doubt-driven-development` when the risk is *unexamined reasoning* — that one is fresh-context self-review and needs no external CLI. Neither replaces `code-review-and-quality` as the pre-merge gate.

### Workflow Ops & Meta

Skills that operate on the tracker, the toolchain, or the skill library itself rather than on product code.

| Group | Skill | When to invoke |
|---|---|---|
| Tracker | `using-beads` | **Invoke first on every task** — `bd` reference + the bead-based SDLC. Inject into every sub-agent |
| Tracker | `to-issues` | Break an approved plan / spec / PRD into tracer-bullet vertical-slice issues |
| Tracker | `bd-to-jira` | Sync closed beads into Jira stories (epic link, sprint, Done transition, worklog); labels synced beads |
| Tracker | `bd-to-excel` | Tally the previous month's non-live hours from beads into the Non-Live Time Tracker workbook |
| Meta | `find-skills` | "Is there a skill for X?" — discover and install a skill that doesn't exist locally yet |
| Meta | `write-a-skill` | No skill exists and none is installable — author one with proper structure and progressive disclosure |
| Ops | `bw-secrets` | Create / modify / remove Bitwarden items, including shared org collections, via the `bw` CLI |
| Ops | `update-opencode` | Update Opencode and the Oh-My-OpenAgent plugin |

**Routing:** `find-skills` → `write-a-skill` is the escape hatch when the decision tree dead-ends — search before authoring. `to-issues` decomposes into the *tracker*; `planning-and-task-breakdown` decomposes into *work steps*; run planning first, then `to-issues` to file them.

