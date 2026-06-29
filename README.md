# Agent Skills

A collection of agent skills for AI coding agents. Each top-level directory is a
self-contained skill — a `SKILL.md` (with YAML front-matter `name` + `description`)
plus any supporting files. Skills span the software-engineering lifecycle along with
product, design, security, and writing workflows.

## Quick install (recommended)

Installs/updates **only this library's skills** into your agent skills directory
(`~/.agents/skills`, or `%USERPROFILE%\.agents\skills` on Windows). Any other skills you
already have are **left untouched** — nothing else is deleted or overwritten. No
`git clone` required; re-run anytime to update.

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/duysqubix/skills/main/install.sh | sh
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/duysqubix/skills/main/install.ps1 | iex
```

Override the target directory with `AGENTS_SKILLS_DIR` (macOS/Linux) or
`$env:AGENTS_SKILLS_DIR` (Windows).

> Installs from the public **`duysqubix/skills`** mirror — the
> `Caliber-Completions-Services/skills` repo is org-internal and not anonymously
> fetchable. The two remotes mirror each other.

## Manual install (git clone)

```bash
git clone https://github.com/duysqubix/skills.git
mkdir -p ~/.agents/skills
cp -R skills/* ~/.agents/skills/
```

> The manual copy is less surgical than the installer above — it copies everything
> (including this README) and overwrites same-named entries. Prefer the quick install.

## Usage

Start a new agent session after installing so it picks up the skills. The
`using-agent-skills` meta-skill routes the agent to the right skill for each task.
