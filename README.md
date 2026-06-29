# Agent Skills

A collection of agent skills for AI coding agents. Each top-level directory is a
self-contained skill — a `SKILL.md` (with YAML front-matter `name` + `description`)
plus any supporting files. Skills span the software-engineering lifecycle along with
product, design, security, and writing workflows.

## Installation

Your agent loads skills from `~/.agents/skills` (`%USERPROFILE%\.agents\skills` on
Windows). Install by copying every skill into that directory.

### macOS / Linux

```bash
git clone https://github.com/Caliber-Completions-Services/skills.git
mkdir -p ~/.agents/skills
cp -R skills/* ~/.agents/skills/
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Caliber-Completions-Services/skills.git
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\* "$env:USERPROFILE\.agents\skills\"
```

After copying, start a new agent session so it picks up the new skills. The
`using-agent-skills` meta-skill helps the agent route to the right skill for each task.
