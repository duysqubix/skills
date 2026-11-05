---
name: project-roadmap
description: Build or update a high-level roadmap page for any project or plan, work or personal, drawn as a transit line with phases as stations, milestone dots, a You-are-here flag, gates and an activity log. Use for roadmaps, phase plans, launches, migrations, rollouts, events, renovations or any milestone tracker, even if "roadmap" isn't said, and to mark progress on one.
---

# Project roadmap (route map)

This skill turns any project or plan into a one-page roadmap drawn as a transit line. It fits a product launch, a system migration, a hiring push, an event, a home renovation or a study plan equally well. Each phase is a station and each step is a dot under it, with a "You are here" flag marking where the work stands. Below the map sit three cards: last done, you are here, and coming up. Under those, every phase is listed in order with its purpose, scope, exit test and steps. Beside that list are the open gates and decisions and an activity log. The page works in light and dark and on phones.

Every roadmap uses the same page, so the user can read any of them at a glance. The look is fixed on purpose: don't restyle the template, and don't swap in a document, task list or slide artifact unless the user asks for that.

## What's in this skill

`SKILL_DIR` is the base directory this skill was loaded from.

- `scripts/build_roadmap.py` checks the roadmap data and builds the page. For a live page it also writes the database seed. Run it; you don't need to read it.
- `assets/template.html` is the page itself, which the script fills in. Never hand-write the page.
- `assets/example-roadmap.json` is a complete example (a kitchen remodel) that uses every field. Read it before writing your first roadmap.

## Two modes

- **Live.** Use this whenever the Artifact tool is available and the user's capability roster includes `db`; the `artifact-capabilities` skill lists the roster. The page is published once with the `db` capability and reads everything from the artifact's database. You update it by writing rows with the `ArtifactData` tool, with no republish, and anyone with the link sees the change at once. When the You-are-here flag moves, an open page pops up a note saying what finished and where the flag is now. This is what keeps a roadmap current as work moves.
- **Static.** The data is embedded in the page. Use this when there's no Artifact tool (a plain chat or a script), when `db` isn't offered, or when the user wants a standalone HTML file. You update it by editing `roadmap.json`, rebuilding, and publishing or sending the page again.

## 1. Gather

Start from what the user gave you: their description, pasted notes and attached files. Also use anything they point to, such as a ticket or epic, a shared doc, a meeting transcript or an earlier plan. When a connected tool can read a source they mention, read it rather than asking them to paste it. You need:

- the outcome the project exists for, in one sentence
- the phases, in order, and roughly what each covers
- where things stand: what's finished and what's in progress
- who owns what: people, teams, vendors, contractors
- known dates, pending decisions and outside dependencies

**Draft what's missing.** If you only have a goal, draft the phases and steps from how that kind of project usually runs. If the user names phases but not steps, draft steps for the current and next phase and leave distant phases without steps. In both cases leave drafted steps `todo` and tell the user which parts are your draft.

**Ask little.** Ask at most one short round of questions, and only about things that change the structure. Usually that means what's already done and which dates are fixed.

**Don't invent facts.** Leave unknown dates, owners and results out rather than guessing. An empty field reads as "not known yet"; an invented one reads as fact.

**Use absolute dates.** Write "Nov 9", not "Monday", because the page is read later.

## 2. Shape it

A high-level roadmap is a handful of phases, each with a few checkable steps.

**Phases**

- Use 3 to 7. Each one ends at a point where something becomes true: a decision is made, something is built or live, people are trained, an event happens. Name it by that outcome or by the work. With more than 7 the map gets hard to scan, so group them.
- `code` sits inside the station badge, so keep it to 3 characters: P1, P2 and so on, or the project's own labels (W1, A to E).
- `short` is the station label, 16 characters or fewer. `title` is the full name.
- `purpose` is one sentence on what the phase unlocks: the reason it exists, not a task list.
- When you know them, add `scope` (2 to 5 bullets), `doneWhen` (the observable exit test), `waitsOn` (outside dependencies) and `when` (a window such as "Nov 3–14" or "Q1 2027"). When a phase finishes, you can change `when` to its real dates.
- Leave `status` off phases that have steps, and the page works it out. All steps done shows Done, any blocked shows Blocked, any started shows In progress, and otherwise it shows Planned. Set `status` only on a phase without steps, or to force `ready` (can start, nothing in the way), `blocked` or `skipped`.

**Steps**

- Use 2 to 6 per phase for a high-level roadmap.
- Each step is a milestone someone could tick off: verb first, under about 70 characters, with one owner. Write "Sign the builder's contract", not "Contract stuff".
- Go down to every task only when the user wants step-by-step tracking, such as a cutover runbook.
- A finished phase you only know the outcome of can have a single done step, or none. Don't invent its history.

**Position**

- Steps before the current point are `done` (or `skipped`), the step being worked is `active`, and the rest stay `todo`, which is the default.
- Mark only one step `active` unless work really runs in parallel.
- If nothing has started, leave everything `todo`. The flag then sits on the first open step and its card reads "Up next".

**Gates and decisions**

- A gate is anything that can hold a phase up. Code decisions D1, D2; approvals, fixes and deliveries G1, G2; and risks R1, R2. The `id` is the code in lower case (d1, g1, r1). The code is only the gate's badge: in any text, name the gate by what it decides or waits for.
- List the phase codes a gate holds up in `phases` (always a list, such as `["P3"]`). Open gates then also show on those phase rows.
- Give a gate an `owner` when you know who decides or delivers it.
- When one is settled, set `status` to `decided` or `done` and add a one-line `resolution` that says when.

**Header and footer**

- `meta.title` is the name the user uses for the project, plus "Roadmap" (for example "Kitchen Remodel Roadmap"). It becomes the artifact's name in the gallery.
- `eyebrow` is one line of context above the title, such as from → to, the team or the kind of project.
- `summary` is one or two sentences on the outcome.
- `refs` are header chips such as budget, target date or a link to the ticket.
- `footer` is an optional note. On a static page use something like "Snapshot as of Nov 2."

**Next action**

`meta.nextAction` is the single next concrete action, in one sentence. `meta.waitingOn` says whose move it is, as an owner key.

**Owners**

- Owners are short keys, each mapped to a label and a tone.
- Add the user with the `accent` tone, using their name if you know it, otherwise "You".
- Outside parties (vendors, contractors, other teams) get `amber`, and everyone else `neutral`. `ink` gives one more group a stronger chip.
- `green` and `red` also work but look like status colors, so avoid them.
- Use the same key everywhere.

**Vocabulary**

Set `phaseNoun` and `stepNoun` to the words the people involved use; the page's labels follow them. Irregular plurals go in `phaseNounPlural` and `stepNounPlural`.

| Kind of project | Nouns | Typical phases |
|---|---|---|
| Product or feature launch | phase, milestone | Discovery, Build, Beta, Launch, Grow |
| System or data migration | wave, step | Inventory, Map, Pilot, Cutover, Decommission |
| Event | stage, task | Plan, Book, Promote, Run, Wrap-up |
| Renovation or build | phase, milestone | Plan, Design and permits, Demolition, Rough-in, Finishes, Close-out |
| Hiring | stage, step | Define the role, Source, Interview, Offer, Onboard |
| Learning plan | module, lesson | Foundations, Practice, Project, Review |

**Activity**

Log only what really happened, each with a date or time. Start with the real events you know, such as an inventory finished on Oct 20, then add a final "Roadmap created." entry.

**Plain words**

People read the page cold: the user weeks from now, or someone who never saw this conversation. Every line of text has to make sense on its own.

- Name things by what they are, not by their codes. The codes (P2, D1, G1) are badges the page draws, so keep them out of the text. Write "Decide how the range hood vents", not "Decide D1", and "Permit issued", not "G1 cleared".
- Spell out abbreviations, or use the plain word: "statement of work", not "SOW"; "the first version", not "v1"; "the third layout draft", not "Layout v3". Keep an abbreviation only when it is the name people know the thing by.
- Say what happened, not where it is filed. A ticket, bead, PR or commit id, a file path, an API route or an error code is never the point of a line: write "The city's permit site was down", not "HTTP 503". When an id helps someone look the thing up, put it in parentheses after the plain words, or in a `refs` chip.
- Before you save, read each line as a stranger would. If it leans on the chat, rewrite it.

## 3. Write roadmap.json

Copy the shape of `assets/example-roadmap.json`. In outline:

```json
{
"meta": {"title": "…", "eyebrow": "…", "summary": "…", "phaseNoun": "phase", "stepNoun": "milestone",
         "timezone": "America/Chicago", "updatedAt": "2026-11-02T15:00:00Z", "nextAction": "…", "waitingOn": "builder",
         "refs": [{"label": "Target", "value": "Mar 20"}, {"label": "Ticket", "value": "OPS-42", "href": "https://…"}],
         "owners": {"me": {"label": "You", "tone": "accent"}, "builder": {"label": "Ridgeline", "tone": "amber"}},
         "footer": ""},
"phases": [
{"id": "p1", "order": 1, "code": "P1", "short": "Plan", "title": "Plan and budget", "when": "Sep 8 – Oct 3", "purpose": "…", "scope": ["…"], "doneWhen": "…", "waitsOn": "…"}
],
"steps": [
{"id": "p1-1", "phase": "p1", "order": 1, "label": "Get three bids and choose a builder", "owner": "me", "status": "done", "at": "2026-09-30", "result": "…"},
{"id": "p1-2", "phase": "p1", "order": 2, "label": "…", "owner": "builder", "status": "active", "due": "Nov 6"}
],
"gates": [
{"id": "g1", "order": 1, "code": "G1", "text": "…", "status": "open", "owner": "builder", "phases": ["P2"]}
],
"activity": [
{"at": "2026-09-30", "text": "Ridgeline chosen at $41,200.", "phase": "P1"}
]
}
```

- **Required fields:** `meta.title`; phase `id`, `order`, `code` and `title`; step `id`, `phase` (a phase id), `order` and `label`; gate `id`, `code` and `text`; activity `at` and `text`.
- **Step status** is one of todo, active, done, blocked, failed, skipped or ready. `due` is free text, `at` is when the step finished, and `result` is one line on what happened.
- **Gate status** is open, decided, done or dropped.
- **Ids** become database document ids and page anchors. Use p1 for phases, p1-1 for steps, and the lower-case code for gates, with only letters, digits, `-` and `_`.
- **Activity ids** are optional in `roadmap.json`; the build derives them from `at`.
- **Order** is a number, so 2.5 slots between 2 and 3.
- **Times** are ISO 8601 in UTC (`2026-11-02T16:05:00Z`), or a bare date (`2026-11-02`) when only the day is known.
- **`timezone`** is an IANA zone; use the user's. Without it, each viewer sees times in their own zone.

## 4. Build

Work in a folder of your own (the session's scratchpad if it has one). Run the one command that fits:

```bash
# live page, plus the database seed and the ArtifactData batch to send
python3 "$SKILL_DIR/scripts/build_roadmap.py" roadmap.json roadmap.html --live --seed-dir seed
```

```bash
# static page, for publishing with the Artifact tool
python3 "$SKILL_DIR/scripts/build_roadmap.py" roadmap.json roadmap.html
```

```bash
# standalone HTML file, for anywhere else (adds doctype, head and body)
python3 "$SKILL_DIR/scripts/build_roadmap.py" roadmap.json roadmap.html --document
```

The script checks the data first:

- It stops on errors (bad ids, non-ISO times, unknown phases, a timezone that isn't IANA). Fix them and run it again.
- Warnings point at things the page would show oddly; read them.

The page it writes for the Artifact tool is page content without a doctype or `<html>` wrapper; the tool adds its own skeleton, so don't add one. A live page shows nothing until its database is seeded. To look at the result before publishing, build a static copy under another name and screenshot it, for example with Playwright.

If Python isn't available, fill the page by hand:

1. Copy `assets/template.html`.
2. Replace both `{{TITLE}}` placeholders and `{{EYEBROW}}`.
3. For a static page, put the JSON in place of `null` in the `rm-data` script tag. Make sure no text in it contains `</`.

## 5. Publish

**Live**

1. Publish `roadmap.html` with the Artifact tool, passing:
   - `icon: "map"`
   - a one-sentence `description`
   - `capabilities: {"db": {"rules": [{"path": "", "read": "view", "write": "admin"}]}}`

   Everyone who can open the page can read it; only the owner and editors can write.
2. Seed it. Call `ArtifactData` with `action: "batch"`, the new artifact's `url`, and the `writes` list the build printed, one call per printed batch. These are all new documents, so no versions are needed.
3. Check it. Run `ArtifactData` `list` on `phases` and `steps`, and `get` on `collection: "meta"`, `doc_id: "summary"`. The counts should match `roadmap.json`. If a batch failed partway, list what landed and write only what's missing; documents that now exist need `if_version`.

From then on the database is the roadmap. Read it before every change, and never write the old `roadmap.json` back over it.

**Static**

- **With the Artifact tool:** publish `roadmap.html` with `icon: "map"` and no capabilities.
- **Without it:** deliver the `--document` file the way this environment hands files to the user. That might mean saving it to the outputs folder or attaching it in Cowork, offering it as a download in chat, or writing it to the folder the user named. Keep `roadmap.json` next to it.

Then tell the user, in a sentence or two:

- what the roadmap shows and where the flag sits
- which parts you drafted
- that it stays current if they tell you when things move

## Keeping it current

The same changes apply in both modes. Live roadmaps write them to the database; static ones write them to `roadmap.json` and rebuild.

| Change | What to write |
|---|---|
| Step finished | Step: `{"status": "done", "at": "<now>", "result": "<one line, if known>"}` |
| Step started | Step: `{"status": "active"}`, only when work really started; otherwise the flag moves to the next open step by itself |
| Step blocked | Step: `{"status": "blocked", "result": "Blocked: <why>"}`, usually with a new gate |
| Decision made, gate cleared | Gate: `{"status": "decided", "resolution": "<what was decided, and when>"}` |
| New gate, step or phase | A new record; a new step's `order` goes between its neighbours |
| Dates moved, text changed | Just the changed fields on that phase or step |
| Something removed | Delete the record |
| Every change | A new activity entry (`at`, `text`, `phase`), plus `updatedAt`, `nextAction` and `waitingOn` in meta |

Get the current time with `date -u +%Y-%m-%dT%H:%M:%SZ`. Write log entries short, factual, in the past tense and in plain words (see **Plain words** above), such as "Permit approved after 4 weeks." Once the log passes about 200 entries, remove the oldest.

**Live updates**

Use `ArtifactData`; never republish the page to change data.

1. Read what you'll change. `list` the collections involved (usually `steps`, sometimes `phases` or `gates`) and `get` `meta`/`summary`. Every document comes back with a `version`. Pass it as `if_version` when you write that document. Writes to existing documents are refused without it, and the pin stops you overwriting someone else's edit.
2. Make all the writes in one `batch`:
   - Changed fields: `update` with `collection` (`steps`, `phases`, `gates` or `meta`), `doc_id` and `data`.
   - New records: `set` (no version).
   - Removals: `delete` with `if_version`. To remove one field, write `{"<field>": {"__delete__": true}}` in an `update`.
   - Activity entries: `set` in `activity` with `doc_id` `a-YYYYMMDD-HHMMSS`, taken from the UTC time. If that id is taken (the write is refused), add `-2`.

To answer "where are we?", read `meta`/`summary` and `steps` and reply with the current step, the last one done, what's next and the open gates.

To give someone a file copy:

1. Export each collection with `ArtifactData` `list` and `out_dir: "export"`, plus `get` on `meta`/`summary` with the same `out_dir`.
2. Run `python3 "$SKILL_DIR/scripts/build_roadmap.py" --collect export > roadmap.json`.
3. Build with `--document`.

**Static updates**

1. Edit `roadmap.json`. If you don't have it, for example in a later conversation, get the page first: read the artifact by its URL, or open the file the user gives you. Then run `python3 "$SKILL_DIR/scripts/build_roadmap.py" --extract page.html > roadmap.json`.
2. Apply the changes and rebuild with the same flags as before.
3. Publish the same file path again, or the artifact's URL after reading it. Without the Artifact tool, deliver the file again.

**Other sessions and agents**

Any session with the `ArtifactData` tool can keep a live roadmap current with the recipe above. Give an agent that is doing the work itself the artifact URL and an instruction like this one:

"After each step, update the roadmap. Mark the step done with the time and a one-line result, add an activity entry, and refresh updatedAt and nextAction in meta/summary. Write every line in plain words for someone who never saw the work: no codes like D1, no ids, no shorthand. Read each document's version first and pass it as if_version."

**Roadmaps not built from this template**

These may use other collection names or fields, for example `waves` and `items`, or activity arrays inside per-phase documents. Before writing to one, read the page with the Artifact tool, find what its script subscribes to, and write in that shape.
