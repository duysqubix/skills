---
name: pptx-corporate-overhaul
description: Use when an existing PowerPoint presentation has accurate content and data but poor visual design, typography, or layout. Use when slides are text-heavy, unstructured, or lack visual hierarchy. Use when you need to preserve all original data, charts, and text while applying a professional corporate visual identity.
---

# PowerPoint Corporate Overhaul

## Overview

Rebuild an existing PowerPoint from scratch using `python-pptx`, preserving every data point while applying a disciplined corporate visual system.

**Core principle:** Content is sacred; presentation is engineered.

## When to Use

- Source deck has good data but looks dated
- Slides are text walls without visual hierarchy
- Charts are unstyled
- You need dark/light variants

**Do not use when:** only minor tweaks are needed, or the deck is already well-designed.

## Workflow

1. **Extract** — Read source PPTX. Capture text, charts, images. Verify numbers.
2. **Design** — Choose Dark or Light theme from `boilerplate.py`. Define brand accent color.
3. **Structure** — Map each slide to a layout pattern.
4. **Build** — Use blank slides (`layout[6]`) and script every shape, text box, and chart.
5. **Verify** — Render to PNGs. Inspect alignment, contrast, overflow.

## Design System

**Dark:** navy bg `#0F1A2E`, card panels `#1B2A44`, brand red `#C8102E`, semantic green/amber/blue, white text, slate secondary.

**Light:** near-white bg `#F7F9FC`, white cards, dark text `#0B1326`, same semantic accents darkened.

**Rules:** `NAVY` = bg, `CARD` = panels with rounded corners (`adjustments[0] = 0.06`), `WHITE` = primary text, `SLATE` = secondary, `RED` = accent. Semantic: `GREEN` = good, `AMBER` = warning, `RED` = critical, `BLUE_SOFT` = info.

## Layout Patterns

| Pattern | Use For |
|---------|---------|
| **Cover Split** | Title slide: hero image right, panel left, oversized type, red accent bar |
| **KPI Chips** | Data slides: cards with left accent stripe, big value, label |
| **Dual Chart Cards** | Side-by-side metrics: panels with title, total, column chart |
| **Leaderboard** | Ranked lists: rows with rank, name, value, progress bar |
| **Region Cards** | Geographic breakdown: vertical cards with colored band, code, cost, share %, bar |
| **Audit Cards** | Detailed findings: cards with unit badge, severity tag, body, auditor |
| **Alert Panel** | Critical: panel with red stripe, bold headline, narrative |

## Code Patterns

See `boilerplate.py` for full implementations.

**Key helpers:** `add_rect(..., corner=True)` for rounded panels; `add_text` / `add_multi_text(runs=[...])` for text; `add_slide_chrome` for header/logo/footer/counter on content slides; `add_kpi_card` for accent-stripe chips; `style_chart` for corporate chart styling.

**Critical settings:** Set `text_frame` margins to `Emu(0)`. Always explicitly set chart series colors, data label colors, and axis colors. In light mode, darken `BORDER` and gridlines.

## Common Mistakes

- **Guessing data** — extract from source PPTX; never retype from memory
- **Default layouts** — use `layout[6]` (blank) and draw everything
- **Missing chrome** — every content slide needs header bar, logo, footer, counter
- **Chart defaults** — unstyled charts inherit ugly colors

## Supporting Files

- **`boilerplate.py`** — Both palettes, all helpers, and a minimal working 2-slide example.
