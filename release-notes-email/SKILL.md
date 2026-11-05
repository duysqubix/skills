---
name: release-notes-email
description: Turn rough release notes, changelogs, ticket lists or a draft announcement into polished, end-user-friendly release notes, and build them as an Outlook-ready email with screenshots embedded inline (.eml draft plus an HTML preview). Use whenever the user wants release notes, update notes, or a "what's new" / "what's changing" announcement sent as an email, a software update email for end users, or a changelog rewritten as an email, even if they only paste a list of changes or upload screenshots and say "make this an email". For release notes that are not an email (a changelog page, in-app notes), use release-notes.
---

# Release notes email

Produce release notes that an ordinary user can skim in under a minute and act on, then package them as an email the sender can open in Outlook and send without rebuilding anything.

The two halves matter equally. Good copy that arrives as a broken paste is wasted, and a beautiful email full of developer wording is useless to the reader.

## Workflow

1. Gather inputs
2. Restructure and rewrite the content
3. Prepare screenshots
4. Write the spec and build the email
5. Check the render, then deliver

### 1. Gather inputs

Usually the user gives you some of these. Work with what you have and ask only for what is truly missing (one short question at most):

- The changes: a draft, changelog, PR or ticket list, or notes
- Product name, release date, sender name (keep `[date]` / `[Your name]` placeholders if not given)
- Screenshots (optional but strongly preferred)
- Brand accent color (default `#C8323A`, a muted red)

Default channel is an Outlook email to the product's users. If the user wants something else (Slack post, in-app panel), still apply step 2, but skip the build.

### 2. Restructure and rewrite

Order by **impact on the reader's day**, never by how engineering organized the work.

```
Eyebrow (product + "update") and a short headline naming the 2–3 biggest changes
Intro: when it goes live + what they need to do (often "nothing, just refresh")
Heads up box: behavior changes, action needed, anything that could block work
What's new: new features, each = benefit first, then how to use it, then screenshot
Improvements: bulleted, each starting with a bold 2–4 word label
Fixes: bulleted, described by the symptom the user saw
Closing: how to get help (usually "reply to this email")
Sign-off
```

What belongs in **Heads up**: anything that changes an existing routine or could stop someone (a ticket that's no longer auto-created, a new rule that blocks closing, invoices grouped differently, a moved button, a forced re-login). If people miss these they file support requests, so they go first, in a tinted box. If there are none, omit the box entirely.

Writing rules:

- Use the names readers see on screen (button labels, page names), bolded. Not module, table or API names.
- Describe fixes by symptom ("Some items were showing a $0.00 total"), never cause ("null check in tax calc").
- Write to "you". Short sentences. Sentence case headings.
- Go easy on emojis — default to none in the email.
- Cut anything users can't see (refactors, dependency bumps) unless it changes speed or reliability, then describe the effect ("loads a little faster").
- Keep the user's own wording where it's already plain; polish rather than rewrite for the sake of it.

Quick translation examples:

| Technical | User-facing |
|---|---|
| Refactored ticket service to async | Saving a ticket is now nearly instant |
| Persist filter state in URL params | Your search and filters stay put when you come back |
| Moved reminder cron to 08:00 local | Reminders now arrive the morning a task is due |
| Fixed negative tax on OOS SKUs | Some out-of-stock items showed a negative tax. They now show their cost with no tax |

**Verify against the screenshots.** If the draft says a button is "next to Export to PDF" but the screenshot shows it inside a three-dot menu, the screenshot wins — fix the copy and mention it to the user. Readers follow the instructions literally.

### 3. Prepare screenshots

Map each screenshot to the change it illustrates. Use one where it shows the change; skip ones that don't visibly show anything new (e.g. a list page illustrating "filters persist") and tell the user why. 5–7 images is a good ceiling.

Crop to what matters: cut app sidebars and empty space, keep the area around the feature. Use `scripts/prep_image.py` (`<skill-dir>` is this skill's folder):

```bash
# Desktop shot: crop (fractions of width/height, or pixels) and resize to 1120px (shown at 536px, sharp on hi-DPI)
python3 <skill-dir>/scripts/prep_image.py in.png images/grid-desktop.png --crop 0.178,0,1,0.5 --width 1120
# Phone shot: resize to 440px (shown at 230px, paired side by side)
python3 <skill-dir>/scripts/prep_image.py phone.png images/grid-phone.png --crop 0,0,1,0.63 --width 440
# Contact sheet to eyeball all crops at once
python3 <skill-dir>/scripts/prep_image.py --sheet sheet.png images/*.png
```

`prep_image.py` needs Pillow 9.1+. If `import PIL` fails, run it as `uv run --no-project --with pillow python3 <skill-dir>/scripts/prep_image.py …`, or install Pillow. On WSL, convert Windows screenshot paths first: `wslpath -u 'C:\Users\…\shot.png'`.

Prefer fractional crops. Images shown in your context are often scaled down from their real size, so pixel coordinates you read off the preview will be wrong unless you rescale (real width ÷ displayed width). Fractions avoid that. Always check the contact sheet before building.

Pair phone screenshots side by side (`img_pair`). Give every image alt text and a short caption when two similar images could be confused ("On a task" / "On the project page").

While looking at screenshots, watch for:
- Developer wording visible in the UI (e.g. "null", raw IDs, enum names like `STATUS_PENDING`). Point it out so the user can fix the UI or crop it.
- The biggest change having no screenshot. Say which shot would help most.
- Real customer or personal data the user may not want broadcast.

### 4. Write the spec and build

Write a JSON spec (see `assets/example-spec.json` for a complete worked example) and run:

```bash
python3 <skill-dir>/scripts/build_email.py spec.json --out-dir out --name Product-update-email --render out/render.png
```

Put `--out-dir` where the user can double-click the result. On WSL, use a Windows folder such as `/mnt/c/Users/<you>/Downloads`, so Windows hands the `.eml` to Outlook. You can open it for the user with `explorer.exe "$(wslpath -w <out-dir>/<name>.eml)"`; it exits 1 even when it works, so don't retry (that opens a second draft).

This produces:
- `<name>.eml` — opens in classic Outlook as a new unsent message (via `X-Unsent: 1`) with subject, formatting and images embedded inline (CID). The user adds recipients and sends.
- `<name>-preview.html` — same email with base64 images, for a browser check or copy-paste fallback.
- the optional `--render` PNG, a full-page screenshot for your own review. It needs the `playwright` Python package and Chromium. Without them the build still succeeds and prints "Render skipped"; open the preview HTML in a browser instead.

Spec text supports `**bold**` only (no links or other markdown; the build warns on a leftover `**` or `](`). Block types: `h3`, `p`, `bullets`, `img`, `img_pair` (exactly 2 images). Optional keys: `width` on `img` / `img_pair`, `margin_bottom` on `p`, `heads_up.title`. Image paths are relative to the spec file and must be PNG, JPEG or GIF. A malformed spec stops the build with a message naming the bad key. The layout is table-based with inline styles because Outlook desktop renders with Word's engine (no flexbox, unreliable border-radius), so don't hand-edit in modern CSS.

### 5. Check and deliver

View the render. Look for cut-off images, huge gaps, wrong order, unreadable screenshots. Fix and rebuild if needed.

Give the user the `.eml` path first, then the preview. Keep the reply short and structured:

- **How to use it**: double-click the .eml → classic Outlook opens a draft. If it opens read-only (new Outlook), open the preview HTML in Edge/Chrome, Ctrl+A, Ctrl+C, paste into a new message.
- **Before you send**: the placeholders to replace, and send a test to yourself + check on a phone.
- **What changed from your draft**: only the meaningful changes (reordering, corrected UI locations, cut items).
- **Things to look at**: dev wording in screenshots, missing screenshots, anything uncertain.
