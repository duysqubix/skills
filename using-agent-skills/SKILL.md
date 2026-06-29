---
name: using-agent-skills
description: Discovers and invokes agent skills. Use when starting a session or when you need to discover which skill applies to the current task. This is the meta-skill that governs how all other skills are discovered and invoked.
---

# Using Agent Skills

## Overview

Agent Skills is a collection of workflow skills. The **core set** covers the software-engineering lifecycle, organized by development phase. An **Extended Skill Families** set (see end of file) adds **product management, design & taste, security operations, and prose**. Each skill encodes a specific process a senior practitioner follows. This meta-skill helps you discover and apply the right skill for your current task.

## Skill Discovery

When a task arrives, the very FIRST skill you invoke is **/using-beads**, THEN identify the development phase and apply the corresponding skill:

```
Task arrives
    │
    ├── Don't know what you want yet? ──────→ interview-me
    ├── Have a rough concept, need variants? → idea-refine
    ├── New project/feature/change? ──→ spec-driven-development
    ├── Have a spec, need tasks? ──────→ planning-and-task-breakdown
    ├── Implementing code? ────────────→ incremental-implementation
    │   ├── UI work? ─────────────────→ frontend-ui-engineering
    │   ├── API work? ────────────────→ api-and-interface-design
    │   ├── Need better context? ─────→ context-engineering
    │   ├── Need doc-verified code? ───→ source-driven-development
    │   └── Stakes high / unfamiliar code? ──→ doubt-driven-development
    ├── Writing/running tests? ────────→ test-driven-development
    │   └── Browser-based? ───────────→ browser-testing-with-devtools
    ├── Something broke? ──────────────→ debugging-and-error-recovery
    ├── Reviewing code? ───────────────→ code-review-and-quality
    │   ├── Too complex? ─────────────→ code-simplification
    │   ├── Security concerns? ───────→ security-and-hardening
    │   └── Performance concerns? ────→ performance-optimization
    ├── Committing/branching? ─────────→ git-workflow-and-versioning
    ├── CI/CD pipeline work? ──────────→ ci-cd-and-automation
    ├── Deprecating/migrating? ────────→ deprecation-and-migration
    ├── Writing docs/ADRs? ───────────→ documentation-and-adrs
    ├── Adding logs/metrics/alerts? ───→ observability-and-instrumentation
    ├── Deploying/launching? ─────────→ shipping-and-launch
    │
    ├── Product / PM work (PRD, OKRs, roadmap, discovery, GTM, pricing, metrics)? → Extended: Product Management
    ├── Visual / design taste (landing, portfolio, brand, redesign look-and-feel)? → Extended: Design & Taste
    ├── Security testing / DevSecOps / supply-chain / AI-security? ──────────────→ Extended: Security Operations
    └── Polishing prose / killing AI writing tells? ────────────────────────────→ prose-anti-slop
```

## Core Operating Behaviors

These behaviors apply at all times, across all skills. They are non-negotiable.

### 1. Surface Assumptions

Before implementing anything non-trivial, explicitly state your assumptions:

```
ASSUMPTIONS I'M MAKING:
1. [assumption about requirements]
2. [assumption about architecture]
3. [assumption about scope]
→ Correct me now or I'll proceed with these.
```

Don't silently fill in ambiguous requirements. The most common failure mode is making wrong assumptions and running with them unchecked. Surface uncertainty early — it's cheaper than rework.

### 2. Manage Confusion Actively

When you encounter inconsistencies, conflicting requirements, or unclear specifications:

1. **STOP.** Do not proceed with a guess.
2. Name the specific confusion.
3. Present the tradeoff or ask the clarifying question.
4. Wait for resolution before continuing.

**Bad:** Silently picking one interpretation and hoping it's right.
**Good:** "I see X in the spec but Y in the existing code. Which takes precedence?"

### 3. Push Back When Warranted

You are not a yes-machine. When an approach has clear problems:

- Point out the issue directly
- Explain the concrete downside (quantify when possible — "this adds ~200ms latency" not "this might be slower")
- Propose an alternative
- Accept the human's decision if they override with full information

Sycophancy is a failure mode. "Of course!" followed by implementing a bad idea helps no one. Honest technical disagreement is more valuable than false agreement.

### 4. Enforce Simplicity

Your natural tendency is to overcomplicate. Actively resist it.

Before finishing any implementation, ask:
- Can this be done in fewer lines?
- Are these abstractions earning their complexity?
- Would a staff engineer look at this and say "why didn't you just..."?

If you build 1000 lines and 100 would suffice, you have failed. Prefer the boring, obvious solution. Cleverness is expensive.

### 5. Maintain Scope Discipline

Touch only what you're asked to touch.

Do NOT:
- Remove comments you don't understand
- "Clean up" code orthogonal to the task
- Refactor adjacent systems as a side effect
- Delete code that seems unused without explicit approval
- Add features not in the spec because they "seem useful"

Your job is surgical precision, not unsolicited renovation.

### 6. Verify, Don't Assume

Every skill includes a verification step. A task is not complete until verification passes. "Seems right" is never sufficient — there must be evidence (passing tests, build output, runtime data).

## Failure Modes to Avoid

These are the subtle errors that look like productivity but create problems:

1. Making wrong assumptions without checking
2. Not managing your own confusion — plowing ahead when lost
3. Not surfacing inconsistencies you notice
4. Not presenting tradeoffs on non-obvious decisions
5. Being sycophantic ("Of course!") to approaches with clear problems
6. Overcomplicating code and APIs
7. Modifying code or comments orthogonal to the task
8. Removing things you don't fully understand
9. Building without a spec because "it's obvious"
10. Skipping verification because "it looks right"

## Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.

2. **Skills are workflows, not suggestions.** Follow the steps in order. Don't skip verification steps.

3. **Multiple skills can apply.** A feature implementation might involve `idea-refine` → `spec-driven-development` → `planning-and-task-breakdown` → `incremental-implementation` → `test-driven-development` → `code-review-and-quality` → `code-simplification` → `shipping-and-launch` in sequence.

4. **When in doubt, start with a spec.** If the task is non-trivial and there's no spec, begin with `spec-driven-development`.

## Lifecycle Sequence

For a complete feature, the typical skill sequence is:

```
1.  interview-me                → Extract what the user actually wants
2.  idea-refine                 → Refine vague ideas
3.  spec-driven-development     → Define what we're building
4.  planning-and-task-breakdown → Break into verifiable chunks
5.  context-engineering         → Load the right context
6.  source-driven-development   → Verify against official docs
7.  incremental-implementation  → Build slice by slice
8.  observability-and-instrumentation → Instrument as you build (runs parallel with 7-9, not after)
9.  doubt-driven-development    → Cross-examine non-trivial decisions in-flight
10. test-driven-development     → Prove each slice works
11. code-review-and-quality     → Review before merge
12. code-simplification         → Reduce unnecessary complexity while preserving behavior
13. git-workflow-and-versioning → Clean commit history
14. documentation-and-adrs      → Document decisions
15. deprecation-and-migration   → Retire old systems and move users safely when needed
16. shipping-and-launch         → Deploy safely
```

Not every task needs every skill. A bug fix might only need: `debugging-and-error-recovery` → `test-driven-development` → `code-review-and-quality`.

## Quick Reference

| Phase | Skill | One-Line Summary |
|-------|-------|-----------------|
| Define | interview-me | Surface what the user actually wants before any plan, spec, or code exists |
| Define | idea-refine | Refine ideas through structured divergent and convergent thinking |
| Define | spec-driven-development | Requirements and acceptance criteria before code |
| Plan | planning-and-task-breakdown | Decompose into small, verifiable tasks |
| Build | incremental-implementation | Thin vertical slices, test each before expanding |
| Build | source-driven-development | Verify against official docs before implementing |
| Build | doubt-driven-development | Adversarial fresh-context review of every non-trivial decision |
| Build | context-engineering | Right context at the right time |
| Build | frontend-ui-engineering | Production-quality UI with accessibility |
| Build | api-and-interface-design | Stable interfaces with clear contracts |
| Verify | test-driven-development | Failing test first, then make it pass |
| Verify | browser-testing-with-devtools | Chrome DevTools MCP for runtime verification |
| Verify | debugging-and-error-recovery | Reproduce → localize → fix → guard |
| Review | code-review-and-quality | Five-axis review with quality gates |
| Review | code-simplification | Preserve behavior while reducing unnecessary complexity |
| Review | security-and-hardening | OWASP prevention, input validation, least privilege |
| Review | performance-optimization | Measure first, optimize only what matters |
| Ship | git-workflow-and-versioning | Atomic commits, clean history |
| Ship | ci-cd-and-automation | Automated quality gates on every change |
| Ship | deprecation-and-migration | Remove old systems and migrate users safely |
| Ship | documentation-and-adrs | Document the why, not just the what |
| Ship | observability-and-instrumentation | Structured logs, RED metrics, traces, symptom-based alerts |
| Ship | shipping-and-launch | Pre-launch checklist, monitoring, rollback plan |

---

## Extended Skill Families

The skills above cover the **software-engineering lifecycle**. The families below extend the library to **product management, design & taste, security operations, and prose**. They were imported from external skill packs and de-duplicated against the engineering set: **none duplicates an engineering skill** — each either works in a different domain or chains with one. The discovery rule is unchanged: pick the most specific applicable skill first.

**The load-bearing distinction:** product / design / security / prose skills decide and shape *what to build, how it should look, whether it holds up, and how it reads*; engineering skills decide *how it is built and verified*. They chain; they do not compete.

### Cross-family routing (when two skills look similar)

| Tempted to reach for… | …for this | Use instead / also |
|---|---|---|
| `create-prd` | engineering acceptance criteria, file plan, tests | `spec-driven-development` — the PRD frames the product, the spec drives the code (chain them) |
| `idea-refine` | product-discovery ideation with PM/Design/Eng lenses | `brainstorm-ideas-new` / `-existing` — but idea-refine still wins for sharpening one vague idea into a buildable one-pager |
| `doubt-driven-development` | pressure-testing a product strategy or PRD | `strategy-red-team` — doubt-driven stays for code/architecture decisions |
| `planning-and-task-breakdown` | ranking a product / feature backlog | `prioritize-features` / `prioritization-frameworks` — planning-and-task-breakdown stays for decomposing an approved spec |
| `test-driven-development` | designing manual / acceptance QA scenarios from stories | `test-scenarios` — TDD stays for failing-test-first code |
| `observability-and-instrumentation` | product KPIs / North Star / dashboards | `metrics-dashboard` / `north-star-metric` — observability stays for system telemetry |
| `shipping-and-launch` | documenting an AI-built app + auditing intent-vs-code | `shipping-artifacts` + `intended-vs-implemented` — shipping-and-launch stays for release / rollback |
| `documentation-and-adrs` | user-facing "what shipped" notes | `release-notes` — ADRs stay for engineering rationale / memory |
| built-in `remove-ai-slops` | removing AI tells from **prose** | `prose-anti-slop` — remove-ai-slops is **code** slop only |
| `frontend-ui-engineering` | aesthetic direction / anti-slop look & feel | the Design & Taste family — frontend-ui-engineering stays for production behavior, a11y, state |
| built-in `security-and-hardening` | actively *testing* for a specific vuln class | the Security Operations family — security-and-hardening stays for prevention while building |

### Product Management — `pm-skills` (68 skills)

Product lens: discovery, strategy, execution, research, analytics, GTM, marketing, AI-shipping. Auto-load on PM-flavored tasks (PRDs, roadmaps, OKRs, personas, pricing, launches). Typical flow: **discovery → strategy → execution → GTM → ship**.

**Discovery (13)** — `brainstorm-ideas-new` / `brainstorm-ideas-existing` (multi-lens ideation), `brainstorm-experiments-new` / `brainstorm-experiments-existing` (validation experiments / pretotypes), `identify-assumptions-new` / `identify-assumptions-existing` (risk mapping), `prioritize-assumptions`, `prioritize-features`, `analyze-feature-requests`, `opportunity-solution-tree`, `customer-interview-script` (Mom-Test guide — renamed from `interview-script`), `summarize-customer-interview` (renamed from `summarize-interview`), `metrics-dashboard`.

**Strategy (12)** — `product-strategy`, `startup-canvas` (default for a new product), `product-vision`, `value-proposition`, `lean-canvas` (fast hypothesis), `business-model` (established BMC), `monetization-strategy`, `pricing-strategy`, `swot-analysis`, `pestle-analysis`, `porters-five-forces`, `ansoff-matrix`.

**Execution (16)** — `create-prd`, `brainstorm-okrs`, `outcome-roadmap`, `sprint-plan`, `retro`, `release-notes`, `pre-mortem`, `stakeholder-map`, `summarize-meeting`, `user-stories`, `job-stories`, `wwas` (default backlog format), `test-scenarios`, `dummy-dataset`, `prioritization-frameworks`, `strategy-red-team`.

**Market research (7)** — `user-personas`, `market-segments`, `user-segmentation`, `customer-journey-map`, `market-sizing`, `competitor-analysis`, `sentiment-analysis`.

**Data analytics (3)** — `sql-queries`, `cohort-analysis`, `ab-test-analysis`.

**Go-to-market (6)** — `gtm-strategy`, `beachhead-segment`, `ideal-customer-profile`, `growth-loops`, `gtm-motions`, `competitive-battlecard`.

**Marketing & growth (5)** — `marketing-ideas`, `positioning-ideas`, `value-prop-statements`, `product-name`, `north-star-metric`.

**Toolkit (4)** — `review-resume`, `draft-nda`, `privacy-policy`, `grammar-check` (grammar / logic / flow — pair with `prose-anti-slop` for AI-tell removal).

**AI-shipping (2)** — `shipping-artifacts` (the doc set that makes a vibe-coded app reviewable), `intended-vs-implemented` (find the gap between documented intent and what the code actually does).

### Design & Taste — `taste-skill` (13 skills)

Anti-slop visual direction for landing pages, portfolios, brand, and redesigns. **Routing:** the built-in `frontend` skill is the *router* (it also brings Lighthouse / real-browser QA + brand refs); these are the deeper taste *rulebooks* it draws on. Complementary to `frontend-ui-engineering` (production behavior / a11y / state) — taste decides *look & feel*, frontend-ui-engineering decides *how the component behaves*.

| Skill | Use when |
|---|---|
| `design-taste-frontend` | **Default.** Vague brief → infer design direction, ship non-templated UI |
| `design-taste-frontend-v1` | Backward-compat only (superseded by the default above) |
| `gpt-taste` | Aggressive cinematic / GSAP / Awwwards-experimental concept when the default is too safe |
| `minimalist-ui` | Clean editorial / Notion / Linear restraint |
| `industrial-brutalist-ui` | Raw Swiss / terminal / mechanical, declassified-blueprint feel |
| `high-end-visual-design` | Premium / luxury / calm agency polish |
| `redesign-existing-projects` | Lightweight audit-and-upgrade checklist for an existing UI |
| `image-to-code` | Generate design images → analyze → implement to match |
| `imagegen-frontend-web` | Website mockup **images only** (one per section) |
| `imagegen-frontend-mobile` | Mobile app screen / flow **images only** |
| `brandkit` | Logo / identity / brand-board **images only** |
| `stitch-design-taste` | Emit a `DESIGN.md` design-system for Google Stitch |
| `full-output-enforcement` | Force complete, unabridged output; ban placeholder truncation |

### Security Operations — curated cybersecurity (12 + full library)

Hands-on offensive / operational security playbooks. **Routing:** these are *technique playbooks*; `security-and-hardening` stays for *prevention while building*; built-in `security-research` / `security-review` stay for *whole-codebase audit orchestration*; `ci-cd-and-automation` stays for *generic* CI (these add the *security gates*).

- **AppSec testing** — `testing-for-xss-vulnerabilities`, `exploiting-sql-injection-vulnerabilities`, `testing-api-security-with-owasp-top-10`, `testing-for-broken-access-control`
- **DevSecOps gates** — `implementing-secret-scanning-with-gitleaks`, `integrating-sast-into-github-actions-pipeline`, `performing-container-security-scanning-with-trivy`, `securing-github-actions-workflows`
- **Supply chain** — `detecting-malicious-npm-packages`, `detecting-dependency-confusion`
- **AI / agent security** — `testing-prompt-injection-in-rag-pipelines`, `auditing-mcp-servers-for-tool-poisoning`

> **Full library (on-demand):** 817 cybersecurity skills are cloned at `~/.repos/Anthropic-Cybersecurity-Skills/skills/`. The 12 above are curated for app / dev work. For any other domain — DFIR, threat hunting, cloud IR, OT/ICS, malware RE, forensics, red-team C2, compliance — browse that directory and copy the specific `<skill>/` folder into `~/.agents/skills/` on demand. Authorized use only.

### Prose — `prose-anti-slop` (1 skill)

Strip predictable AI writing tells from prose — filler openers, passive voice, formulaic "not X, but Y" contrasts, em-dashes, pull-quote cadence — scored on a 1–10 rubric. **Routing:** distinct from built-in `remove-ai-slops` (which cleans **code**); pairs with pm `grammar-check` (correctness / logic / flow). Use when drafting or editing any human-facing text.

---

**Provenance / updating:** these families were imported from `~/.repos/taste-skill`, `~/.repos/stop-slop`, `~/.repos/pm-skills`, and `~/.repos/Anthropic-Cybersecurity-Skills`. Re-pull a repo and re-copy a `<skill>/` folder into `~/.agents/skills/` to update it. A backup of the pre-integration version of this file is in `~/.repos/.skill-integration-backup/`.
