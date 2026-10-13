---
name: reference-security-ops
description: Security Operations family (12 curated + 817-skill library) — offensive and DevSecOps technique playbooks. Loaded from using-agent-skills when a task is about actively testing for a vulnerability class.
---

# Security Operations — curated cybersecurity (12 + full library)

Hands-on offensive / operational security playbooks. **Routing:** these are *technique playbooks*; `security-and-hardening` stays for *prevention while building*; the built-in `security-review` skill stays for *whole-codebase audit orchestration*; `ci-cd-and-automation` stays for *generic* CI (these add the *security gates*).

| Group | Skill | When to invoke |
|---|---|---|
| AppSec testing | `testing-for-xss-vulnerabilities` | Test for reflected, stored, and DOM-based XSS |
| AppSec testing | `exploiting-sql-injection-vulnerabilities` | Find / exploit SQLi — error, union, blind, time-based |
| AppSec testing | `testing-api-security-with-owasp-top-10` | Assess REST / GraphQL against the OWASP API Top 10 |
| AppSec testing | `testing-for-broken-access-control` | Privilege escalation, IDOR, missing function-level checks |
| DevSecOps gates | `implementing-secret-scanning-with-gitleaks` | Detect / prevent hardcoded secrets — hooks, CI, custom rules |
| DevSecOps gates | `integrating-sast-into-github-actions-pipeline` | Wire CodeQL / Semgrep into CI with blocking quality gates |
| DevSecOps gates | `performing-container-security-scanning-with-trivy` | Scan images / filesystems / K8s manifests + SBOM |
| DevSecOps gates | `securing-github-actions-workflows` | Harden workflows vs supply-chain / credential / privilege attacks |
| Supply chain | `detecting-malicious-npm-packages` | Triage npm packages for install-script malware / exfiltration |
| Supply chain | `detecting-dependency-confusion` | Detect public-over-private resolution (npm, PyPI, Maven) |
| AI / agent security | `testing-prompt-injection-in-rag-pipelines` | Probe RAG for injection via poisoned context / embeddings |
| AI / agent security | `auditing-mcp-servers-for-tool-poisoning` | Scan MCP servers for poisoning, SSRF, unauth exposure |

> **Full library (on-demand):** 817 cybersecurity skills are cloned at `~/.repos/Anthropic-Cybersecurity-Skills/skills/`. The 12 above are curated for app / dev work. For any other domain — DFIR, threat hunting, cloud IR, OT/ICS, malware RE, forensics, red-team C2, compliance — browse that directory and copy the specific `<skill>/` folder into `~/.agents/skills/` on demand. Authorized use only. For reverse engineering a shipped binary, package, or firmware sample, start with `reverse-engineer-anything` (REA) before browsing the library.

