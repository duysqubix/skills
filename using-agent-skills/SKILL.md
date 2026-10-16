---
name: using-agent-skills
description: Routes a task to the right agent skill and enforces three house rules — i-have-adhd shapes all output, ponytail is the only simplicity lane while coding, impeccable owns frontend design. Covers the software-engineering lifecycle (spec, planning, implementation, testing, debugging, review, shipping), reverse engineering of shipped artifacts (REA), and five extended families — product management (PRD, OKRs, roadmap, personas, pricing, GTM), design & taste, security testing, prose, and multi-model orchestration. Use when starting a session, when a task arrives and no skill is obviously in play, when two skills look like they overlap, when work needs tracking in beads/bd, or when the user asks what skill applies or wants a second opinion from Codex or Gemini. With the argument `update` (or when asked to update or upgrade the skill library), reinstalls the whole library from duysqubix/skills.
---

# Using Agent Skills

Each skill encodes a process a senior practitioner follows. This meta-skill picks the right one.

Skills live in `~/.agents/skills/` (invoked `/<name>` in Claude, `$<name>` in Codex) and in plugins (invoked `/<plugin>:<name>` or `$<plugin>:<name>`): oh-my-claudecode, ponytail, i-have-adhd. All are in scope.

## Argument: `update`

Invoked as `/using-agent-skills update` (Claude) or `$using-agent-skills update` (Codex), or when the user asks to update / upgrade the skill library: skip routing, update the whole library, then stop.

1. Run the installer from [duysqubix/skills](https://github.com/duysqubix/skills). macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/duysqubix/skills/main/install.sh | sh`. Windows: `irm https://raw.githubusercontent.com/duysqubix/skills/main/install.ps1 | iex`. It clean-replaces every skill the repo ships in `~/.agents/skills` (this one included), leaves other skills alone, and links new skills into `~/.claude/skills` for Claude. Codex reads `~/.agents/skills` directly.
2. If `~/.repos/skills` is a git clone (the editing copy), run `git -C ~/.repos/skills pull --ff-only`. If it is dirty or diverged, report that and leave it alone.
3. Report the installer's `Installed/updated N skill(s)` line and the pull result, then tell the user to start a new session to load the new versions.

The installer overwrites local edits to shipped skills. If the user has changed one in `~/.agents/skills` without pushing it, confirm before running.

## House rules (always on)

These sit above the routing tree. They hold for every task, in Claude and Codex alike, until the user turns one off.

### 1. Output → `i-have-adhd`

Every user-facing response follows `i-have-adhd`. It is user-invoked only (`disable-model-invocation: true`), so apply its rules even when nobody switched it on:

1. First line is the next action: a command, a path, or the answer. No preamble.
2. Multi-step work is a numbered list. One bounded action per step, fewest steps that work.
3. Restate state every turn ("Step 3 of 5 done: schema updated"). Show what now works, concretely.
4. Lists cap at 5; split into now/later. A tangent becomes one separate question at the end.
5. Concrete time estimates. Errors stated flat: cause, then fix. End on one next action, with no recap and no closer.

Break the shape only when the user asks you to explain or walk through something (run long, add headers), before a destructive action (confirm first), after three failed fixes (name the suspect assumption, ask one question), or when the task or harness requires it.

Terse-voice skills (caveman and friends) may compress the wording; they never override this shape. Off only when the user says "stop adhd mode" or "normal mode".

### 2. Coding → `ponytail`, and only `ponytail`, for simplicity

Ponytail is on for every coding task: writing, fixing, refactoring, reviewing, choosing dependencies. A session hook starts it in Claude and Codex; if it is not active, invoke `ponytail:ponytail`. It is the **sole** simplicity lane:

| Need | Use |
|---|---|
| Write / fix / refactor code | `ponytail` (level `full`) |
| Review a diff for over-engineering | `ponytail-review` |
| Audit a whole repo for over-engineering | `ponytail-audit` |
| List deliberate shortcuts (`ponytail:` comments) | `ponytail-debt` |

Do **not** use the overlapping skills ponytail replaces: `code-simplification`, `karpathy-guidelines`, `oh-my-claudecode:minimal-code-discipline`, `oh-my-claudecode:ai-slop-cleaner`, `caveman:lean-build`, built-in `simplify`. Ponytail decides *how little* to build; correctness skills still run beside it: `using-beads`, `test-driven-development`, `debugging-and-error-recovery`, `code-review-and-quality`, `security-and-hardening`.

### 3. Frontend design → `impeccable`

All frontend design work starts with `impeccable`: new UI, redesigns, critique, audit, polish, typography, color, layout, motion, UX copy, design systems. It runs its own context setup and sub-commands (`shape`, `critique`, `audit`, `polish`, `bolder`, `quieter`, …).

- It replaces `design-taste-frontend`, `redesign-existing-projects`, and the `frontend-design` plugin as the default. Don't run them alongside it.
- `frontend-ui-engineering` still owns component behavior, state, and a11y wiring. Chain it after.
- The Design & Taste family stays for what impeccable doesn't make: image-only mockups, brand boards, PowerPoint, Google Stitch, or a named style world to borrow.

## Quick start

A bug report arrives: *"we keep getting duplicate webhook deliveries in prod."*

```
1. using-beads                   → file/claim the bug        (runs on EVERY task, first)
2. debugging-and-error-recovery  → reproduce → localize → fix → guard
3. test-driven-development       → failing test pinning the dedup invariant
4. code-review-and-quality       → pre-merge gate
5. git-workflow-and-versioning   → atomic commit
```

Note what is *absent*: no `spec-driven-development`, no PM family. **Not every task needs every skill** — walk the tree, take the matches, skip the rest. House rules ride along unlisted: `ponytail` keeps the fix to the smallest root-cause change, and `i-have-adhd` shapes the report.

## Skill Discovery

Invoke **`using-beads`** first on every task — beads is the primary project-management tracker. Then identify the phase:

```
Task arrives
    │
    ├── Don't know what you want yet? ──────→ interview-me
    ├── Have a plan, want it stress-tested? → grill-me
    ├── Have a rough concept, need variants? → idea-refine
    ├── New project/feature/change? ──→ spec-driven-development
    ├── Have a spec, need tasks? ──────→ planning-and-task-breakdown
    │   └── Tasks → tracker issues? ──→ to-issues
    ├── Frontend design / UX (build, redesign, critique, polish)? → impeccable
    ├── Implementing code? ────────────→ incremental-implementation  (+ ponytail, always)
    │   ├── UI work? ─────────────────→ frontend-ui-engineering
    │   ├── API work? ────────────────→ api-and-interface-design
    │   ├── Need better context? ─────→ context-engineering
    │   ├── Need doc-verified code? ───→ source-driven-development
    │   └── Stakes high / unfamiliar code? ──→ doubt-driven-development
    ├── Writing/running tests? ────────→ test-driven-development
    │   └── Browser-based? ───────────→ browser-testing-with-devtools
    ├── Something broke? ──────────────→ debugging-and-error-recovery
    ├── Reviewing code? ───────────────→ code-review-and-quality
    │   ├── Over-engineered? ─────────→ ponytail-review  (whole repo: ponytail-audit)
    │   ├── Security concerns? ───────→ security-and-hardening
    │   └── Performance concerns? ────→ performance-optimization
    ├── Committing/branching? ─────────→ git-workflow-and-versioning
    ├── CI/CD pipeline work? ──────────→ ci-cd-and-automation
    ├── Deprecating/migrating? ────────→ deprecation-and-migration
    ├── Writing docs/ADRs? ───────────→ documentation-and-adrs
    ├── Adding logs/metrics/alerts? ───→ observability-and-instrumentation
    ├── Deploying/launching? ─────────→ shipping-and-launch
    ├── Reverse engineering a shipped binary, app, package, firmware, or web bundle?
    │                                  → reverse-engineer-anything  (REA: rea MCP + CLI; not for source repos)
    │
    ├── Want a non-Claude second opinion? ─→ /oh-my-claudecode:ask  (one advisor per call; run Codex + Gemini, synthesize)
    ├── No skill seems to fit? ────────────→ find-skills (find/install) → write-a-skill (author one)
    │
    └── Anything below? ──────────────────→ load the family reference, then route inside it
```

## Extended families

The lifecycle above is the **core set**. These families cover other domains — load a reference only when its trigger fires. They chain with engineering skills; they do not compete with them. The load-bearing distinction: these decide *what to build, how it should look, whether it holds up, and how it reads*; engineering skills decide *how it is built and verified*.

| Family | Load when the task is about… | Reference |
|---|---|---|
| Product Management (68) | PRDs, OKRs, roadmaps, discovery, personas, pricing, metrics, GTM, launches | [reference/product-management.md](reference/product-management.md) |
| Design & Taste (14) | What `impeccable` doesn't make: image-only mockups, brand boards, decks, Stitch, borrowed style worlds | [reference/design-and-taste.md](reference/design-and-taste.md) |
| Security Operations (12) | Actively *testing* a vuln class, DevSecOps gates, supply chain, AI/agent security | [reference/security-ops.md](reference/security-ops.md) |
| Multi-Model + Ops & Meta | Cross-vendor second opinions (`ask`); tracker, toolchain, and skill-library work | [reference/ops-and-meta.md](reference/ops-and-meta.md) |
| Prose (2) | Human-facing text — strip AI writing tells, scored 1–10; or edit a draft while keeping the writer's voice | `prose-anti-slop`; `no-ai-slop` for voice-preserving edits or detect-only (no reference needed) |
| Music | Driving a live Ableton Live session (MIDI clips, devices, tempo, arrangement) | `ableton-mcp` (no reference needed) |

### Cross-family routing (when two skills look similar)

| Tempted to reach for… | …for this | Use instead / also |
|---|---|---|
| `create-prd` | engineering acceptance criteria, file plan, tests | `spec-driven-development` — the PRD frames the product, the spec drives the code (chain them) |
| `idea-refine` | product-discovery ideation with PM/Design/Eng lenses | `brainstorm-ideas-new` / `-existing` — idea-refine still wins for sharpening one vague idea |
| `doubt-driven-development` | pressure-testing a product strategy or PRD | `strategy-red-team` — doubt-driven stays for code/architecture decisions |
| `doubt-driven-development` | a second opinion from a **different model** | `/oh-my-claudecode:ask` — doubt-driven is fresh-context self-review; ask is cross-vendor |
| `planning-and-task-breakdown` | ranking a product / feature backlog | `prioritize-features` / `prioritization-frameworks` — planning stays for decomposing an approved spec |
| `planning-and-task-breakdown` | filing the decomposed work into the tracker | `to-issues` — plan into steps first, then file them |
| `test-driven-development` | designing manual / acceptance QA scenarios from stories | `test-scenarios` — TDD stays for failing-test-first code |
| `observability-and-instrumentation` | product KPIs / North Star / dashboards | `metrics-dashboard` / `north-star-metric` — observability stays for system telemetry |
| `shipping-and-launch` | documenting an AI-built app + auditing intent-vs-code | `shipping-artifacts` + `intended-vs-implemented` — shipping-and-launch stays for release / rollback |
| `documentation-and-adrs` | user-facing "what shipped" notes | `release-notes` — ADRs stay for engineering rationale / memory |
| `oh-my-claudecode:ai-slop-cleaner` | removing AI tells from prose, or code slop | `prose-anti-slop` for prose; `ponytail-review` for code (house rule 2) |
| `frontend-ui-engineering` | aesthetic direction / anti-slop look & feel | `impeccable` (house rule 3) — frontend-ui-engineering stays for production behavior, a11y, state |
| `design-taste-frontend` / `frontend-design` plugin | frontend design direction | `impeccable` (house rule 3) — the taste family stays for image-only, brand, deck, Stitch work |
| `debugging-and-error-recovery` | explaining a shipped binary, app, or package you have no source for | `reverse-engineer-anything` — debugging stays for code you own |
| `security-and-hardening` | actively *testing* for a specific vuln class | the Security Operations family — security-and-hardening stays for prevention while building |
| built-in `code-review` | the full five-axis review workflow + quality gates | `code-review-and-quality` — built-in `code-review` is the fast diff/PR pass; chain, don't substitute |
| built-in `simplify` / `code-simplification` | complexity reduction | `ponytail-review` (diff) or `ponytail-audit` (repo) — house rule 2 |

## Core Operating Behaviors

Non-negotiable, across all skills.

1. **Surface assumptions.** Before anything non-trivial, state them and invite correction — the most common failure mode is a wrong assumption run unchecked. Cheaper than rework:
   ```
   ASSUMPTIONS I'M MAKING:
   1. [requirements]  2. [architecture]  3. [scope]
   → Correct me now or I'll proceed with these.
   ```
2. **Manage confusion actively.** On an inconsistency or conflicting requirement: **stop**, name the specific confusion, present the tradeoff, wait. Bad: silently picking an interpretation. Good: *"I see X in the spec but Y in the code. Which takes precedence?"*
3. **Push back when warranted.** Name the concrete downside, quantified where possible ("adds ~200ms latency", not "might be slower"), propose an alternative, then accept an informed override. Sycophancy is a failure mode.
4. **Enforce simplicity.** Fewer lines? Are these abstractions earning their complexity? Would a staff engineer say *"why didn't you just…"*? 1000 lines where 100 suffice is a failure. Cleverness is expensive. The mechanism is `ponytail` (house rule 2).
5. **Maintain scope discipline.** Touch only what you were asked to touch. Do not remove comments you don't understand, "clean up" orthogonal code, refactor adjacent systems, delete seemingly-unused code, or add unrequested features. Surgical precision, not unsolicited renovation.
6. **Verify, don't assume.** Every skill ends in verification. "Seems right" is never sufficient — produce evidence: passing tests, build output, runtime data.

## Failure Modes to Avoid

Subtle errors that look like productivity: wrong assumptions left unchecked · plowing ahead while lost · not surfacing noticed inconsistencies · not presenting tradeoffs on non-obvious decisions · sycophancy toward flawed approaches · overcomplicating code and APIs · touching code orthogonal to the task · removing things you don't understand · building without a spec because "it's obvious" · skipping verification because "it looks right".

## Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.
2. **Skills are workflows, not suggestions.** Follow the steps in order; don't skip verification.
3. **Multiple skills can apply**, and usually do — chain them.
4. **When in doubt, start with a spec.** Non-trivial task with no spec → `spec-driven-development`.
5. **Pick the most specific applicable skill first**, in the core set and in every family.

## Lifecycle Sequence

Full feature, in order — `interview-me` → `idea-refine` → `spec-driven-development` → `planning-and-task-breakdown` → `context-engineering` → `source-driven-development` → `incremental-implementation` → `test-driven-development` → `code-review-and-quality` → `ponytail-review` → `git-workflow-and-versioning` → `documentation-and-adrs` → `shipping-and-launch`.

Running alongside rather than after: `ponytail` (every coding step), `impeccable` (any UI step), `observability-and-instrumentation` (instrument as you build), and `doubt-driven-development` (cross-examine decisions in flight). `deprecation-and-migration` enters only when retiring an old system.

## Quick Reference

| Phase | Skill | One-Line Summary |
|-------|-------|-----------------|
| Define | interview-me | Surface what the user actually wants before any plan, spec, or code exists |
| Define | grill-me | Relentlessly interrogate an existing plan/design until every branch is resolved |
| Define | idea-refine | Refine ideas through structured divergent and convergent thinking |
| Define | spec-driven-development | Requirements and acceptance criteria before code |
| Plan | planning-and-task-breakdown | Decompose into small, verifiable tasks |
| Build | incremental-implementation | Thin vertical slices, test each before expanding |
| Build | source-driven-development | Verify against official docs before implementing |
| Build | doubt-driven-development | Adversarial fresh-context review of every non-trivial decision |
| Build | ponytail | **Always on while coding.** Laziest solution that works; the only simplicity lane |
| Build | context-engineering | Right context at the right time |
| Build | impeccable | **All frontend design.** Shape, critique, audit, polish, redesign |
| Build | frontend-ui-engineering | Production-quality UI with accessibility |
| Build | api-and-interface-design | Stable interfaces with clear contracts |
| Verify | test-driven-development | Failing test first, then make it pass |
| Verify | browser-testing-with-devtools | Chrome DevTools MCP for runtime verification |
| Verify | debugging-and-error-recovery | Reproduce → localize → fix → guard |
| Verify | reverse-engineer-anything | Evidence-backed RE of shipped binaries, apps, packages, firmware, web bundles (REA) |
| Review | code-review-and-quality | Five-axis review with quality gates |
| Review | ponytail-review | Over-engineering review: what to delete (whole repo: ponytail-audit) |
| Review | security-and-hardening | OWASP prevention, input validation, least privilege |
| Review | performance-optimization | Measure first, optimize only what matters |
| Ship | git-workflow-and-versioning | Atomic commits, clean history |
| Ship | ci-cd-and-automation | Automated quality gates on every change |
| Ship | deprecation-and-migration | Remove old systems and migrate users safely |
| Ship | documentation-and-adrs | Document the why, not just the what |
| Ship | observability-and-instrumentation | Structured logs, RED metrics, traces, symptom-based alerts |
| Ship | shipping-and-launch | Pre-launch checklist, monitoring, rollback plan |
| Output | i-have-adhd | **Shapes every response.** Next action first, numbered steps, lists ≤5 |
| Track | using-beads | **Runs on every task.** `bd` tracker + the bead-based SDLC |
| Track | to-issues | Split an approved plan/spec/PRD into independently-grabbable tracker issues |
| Advise | /oh-my-claudecode:ask | Route a question to Codex, Gemini, or another CLI advisor; run two and synthesize to cross-check |

## Maintenance

**Distribution:** this library ships from [duysqubix/skills](https://github.com/duysqubix/skills). Edit in `~/.repos/skills`, push to `main`, then run `using-agent-skills update` on each machine.

**Provenance:** the extended families were imported from `~/.repos/taste-skill`, `~/.repos/stop-slop`, `~/.repos/pm-skills`, and `~/.repos/Anthropic-Cybersecurity-Skills`. Re-pull a repo and re-copy a `<skill>/` folder into `~/.agents/skills/` to update it. Multi-model orchestration is **not** in that root — `ask` ships with the oh-my-claudecode plugin and updates with it; run `/oh-my-claudecode:wiki` for its full catalog.

**House-rule and REA sources:**

- `impeccable` is vendored here in its Codex flavor (`$impeccable`, `.agents/` paths) from [pbakaus/impeccable](https://github.com/pbakaus/impeccable), Apache-2.0. Claude gets its own flavor (plus impeccable's hook manifests) from `npx impeccable install --providers=claude,codex`. `npx impeccable update` rewrites `~/.agents/skills/impeccable/` in place; commit the diff.
- `reverse-engineer-anything` is vendored from REA ([morluto/rea](https://github.com/morluto/rea), MIT). It needs the `rea` MCP server: `npm install --global rea-agents`, then `rea setup` (registers the MCP for Claude Code and Codex and installs the skill). REA ships no agent hooks. `rea update` refreshes it in place; commit the diff.
- `ponytail` ([DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)) and `i-have-adhd` ([ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd)) are Claude/Codex plugins, not in this root. Ponytail's session hook turns it on at startup in both harnesses.

**Keeping this file honest:** run [`scripts/validate-routes.sh`](scripts/validate-routes.sh) after adding, renaming, or removing any skill. It flags installed-but-unreachable skills, cited-but-nonexistent skills, and `(N skills)` counts that no longer match their tables. A name here that no longer resolves is a *dead route* — worse than an omission, because it sends the agent somewhere that isn't there.
