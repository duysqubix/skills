---
name: reference-design-and-taste
description: Design & Taste family (14 skills) — image-only mockups, brand boards, decks, Google Stitch, and borrowed style worlds. impeccable owns all other frontend design. Loaded from using-agent-skills when a task needs one of those.
---

# Design & Taste — `taste-skill` (14 skills)

Image-only mockups, brand boards, decks, Google Stitch, and borrowed style worlds. **Routing:** `impeccable` is the default for all frontend design work (house rule 3 in SKILL.md) and replaces `design-taste-frontend`, `redesign-existing-projects`, and the `frontend-design` plugin as the router. Reach into this family only for what impeccable doesn't make, or for a named style world impeccable should borrow. Complementary to `frontend-ui-engineering` (production behavior / a11y / state) — taste decides *look & feel*, frontend-ui-engineering decides *how the component behaves*.

| Skill | When to invoke |
|---|---|
| `design-taste-frontend` | Fallback only when `impeccable` is unavailable. Vague brief → infer design direction, ship non-templated UI |
| `design-taste-frontend-v1` | Backward-compat only (superseded by `design-taste-frontend`) |
| `gpt-taste` | Aggressive cinematic / GSAP / Awwwards-experimental concept when `impeccable bolder` is still too safe |
| `minimalist-ui` | Clean editorial / Notion / Linear restraint |
| `industrial-brutalist-ui` | Raw Swiss / terminal / mechanical, declassified-blueprint feel |
| `high-end-visual-design` | Premium / luxury / calm agency polish |
| `redesign-existing-projects` | Fallback only; use `impeccable audit` / `polish` for an existing UI |
| `image-to-code` | Generate design images → analyze → implement to match. Only when the user wants images first; otherwise `impeccable` |
| `imagegen-frontend-web` | Website mockup **images only** (one per section) |
| `imagegen-frontend-mobile` | Mobile app screen / flow **images only** |
| `brandkit` | Logo / identity / brand-board **images only** |
| `stitch-design-taste` | Emit a `DESIGN.md` design-system for Google Stitch |
| `pptx-corporate-overhaul` | Restyle an existing PowerPoint — preserve all content/data, fix typography, layout, hierarchy |
| `full-output-enforcement` | Force complete, unabridged output; ban placeholder truncation |

