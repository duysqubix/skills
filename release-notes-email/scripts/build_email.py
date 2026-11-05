#!/usr/bin/env python3
"""Build an Outlook-ready release notes email from a JSON spec.

Outputs <name>.eml (opens in classic Outlook as an unsent draft with inline CID
images) and <name>-preview.html (base64 images, for browser preview / copy-paste).

Usage:
  python build_email.py spec.json --out-dir OUT [--name NAME] [--render PNG]

Spec shape (see assets/example-spec.json):
{
  "subject": str, "preheader": str, "eyebrow": str, "title": str,
  "accent": "#C8323A",
  "intro": [str, ...],
  "heads_up": {"title": str, "blocks": [Block, ...]},      # optional
  "sections": [{"title": str, "blocks": [Block, ...]}, ...],
  "closing": [str, ...], "signoff": [str, ...]
}
Block: {"type":"h3","text"} | {"type":"p","text","margin_bottom"?} | {"type":"bullets","items":[...]}
     | {"type":"img","src","alt","caption"?,"width"?}
     | {"type":"img_pair","images":[{"src","alt","caption"?}, {...}]}
Text supports **bold**. Images must be PNG, JPEG or GIF files.
"""
import argparse, base64, html, json, os, re, sys
from pathlib import Path
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.policy import SMTP

FONT = "'Segoe UI', Calibri, Arial, sans-serif"
INK, BODY, MUTED, LINE = "#1F2329", "#3A4049", "#6B727C", "#E3E5E8"


def tint(hex_color, amount=0.93):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    mix = lambda c: round(c + (255 - c) * amount)
    return "#%02X%02X%02X" % (mix(r), mix(g), mix(b))


# Sniff content, not the extension, so a spec can't embed a non-image file (.env, keys) as "image/plain".
MAGIC = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpeg", b"GIF87a": "gif", b"GIF89a": "gif"}


def image_type(path):
    with open(path, "rb") as f:
        head = f.read(8)
    return next((t for m, t in MAGIC.items() if head.startswith(m)), None)


def hex_color(c):
    if not isinstance(c, str) or not re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", c):
        sys.exit(f'accent must be a hex color like "#C8323A", got {c!r}')
    return "#" + "".join(ch * 2 for ch in c[1:]) if len(c) == 4 else c


def num(v, lo, hi, where):
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        sys.exit(f"{where} must be a whole number from {lo} to {hi}, got {v!r}")
    return v


def check(spec):
    """Exit with path-style messages for spec shapes that would render wrong (e.g. a string where a list goes)."""
    errs = []

    def need(ok, where, what):
        if not ok:
            errs.append(f"{where}: {what}")
        return ok

    def texts(v, where):
        need(isinstance(v, list) and all(isinstance(x, str) for x in v), where, "expected a list of text")

    def optional_text(d, where, keys=("alt", "caption")):
        for k in keys:
            if k in d:
                need(isinstance(d[k], str), f"{where}.{k}", "expected text")

    def blocks(bs, where):
        if not need(isinstance(bs, list), where, "expected a list of blocks"):
            return
        for i, b in enumerate(bs):
            w, kind = f"{where}[{i}]", b.get("type") if isinstance(b, dict) else None
            if kind in ("h3", "p"):
                need(isinstance(b.get("text"), str), w, 'needs "text"')
            elif kind == "bullets":
                texts(b.get("items"), w + ".items")
            elif kind == "img":
                need(isinstance(b.get("src"), str), w, 'needs "src"')
                optional_text(b, w)
            elif kind == "img_pair":
                ims = b.get("images")
                if need(isinstance(ims, list) and len(ims) == 2
                        and all(isinstance(m, dict) and isinstance(m.get("src"), str) for m in ims),
                        w + ".images", 'expected exactly 2 images, each with "src"'):
                    for j, m in enumerate(ims):
                        optional_text(m, f"{w}.images[{j}]")
            else:
                need(False, w + ".type", f"expected h3, p, bullets, img or img_pair, got {kind!r}")

    if not isinstance(spec, dict):
        sys.exit("Spec must be a JSON object")
    for k in ("subject", "preheader", "eyebrow", "title"):
        if k in spec:
            need(isinstance(spec[k], str), k, "expected text")
    for k in ("intro", "closing", "signoff"):
        if k in spec:
            texts(spec[k], k)
    if spec.get("heads_up"):
        hu = spec["heads_up"]
        if isinstance(hu, dict):
            optional_text(hu, "heads_up", ("title",))
        blocks(hu.get("blocks") if isinstance(hu, dict) else None, "heads_up.blocks")
    secs = spec.get("sections", [])
    if need(isinstance(secs, list), "sections", "expected a list"):
        for i, sec in enumerate(secs):
            need(isinstance(sec, dict) and isinstance(sec.get("title"), str), f"sections[{i}]", 'needs "title"')
            blocks(sec.get("blocks") if isinstance(sec, dict) else None, f"sections[{i}].blocks")
    if errs:
        sys.exit("Spec problems:\n  " + "\n  ".join(errs))


class Builder:
    def __init__(self, spec, base_dir):
        self.s = spec
        self.base = base_dir
        self.accent = hex_color(spec.get("accent", "#C8323A"))
        self.images = {}  # abs path -> key
        self.warnings = []

    # ---- inline helpers
    def t(self, text):
        out = html.escape(text, quote=False)
        out = re.sub(r"\*\*(.+?)\*\*", lambda m: f'<strong style="color:{INK};">{m.group(1)}</strong>', out)
        if "**" in out or "](" in out:
            self.warnings.append(f"Unconverted markup (only **bold** is supported): {text[:60]}")
        return out

    def key(self, src):
        path = src if os.path.isabs(src) else os.path.join(self.base, src)
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            sys.exit(f"Image not found: {path}")
        if not image_type(path):
            sys.exit(f"Not a PNG, JPEG or GIF image: {path}")
        if path not in self.images:
            self.images[path] = f"img{len(self.images) + 1}"
            kb = os.path.getsize(path) // 1024
            if kb > 300:
                self.warnings.append(f"{os.path.basename(path)} is {kb} KB; run prep_image.py to shrink it")
        return "{{" + self.images[path] + "}}"

    def p(self, text, mb=14):
        return (f'<p style="margin:0 0 {mb}px 0;font-family:{FONT};font-size:15px;line-height:23px;'
                f'color:{BODY};">{self.t(text)}</p>')

    def caption(self, c):
        return (f'<div style="font-family:{FONT};font-size:12px;line-height:17px;color:{MUTED};'
                f'padding-top:6px;">{self.t(c)}</div>') if c else ""

    # ---- blocks
    def block(self, b):
        kind = b.get("type")
        if kind == "h3":
            return (f'<h3 style="margin:18px 0 6px 0;font-family:{FONT};font-size:16px;line-height:22px;'
                    f'font-weight:600;color:{INK};">{self.t(b["text"])}</h3>')
        if kind == "p":
            return self.p(b["text"], num(b.get("margin_bottom", 4), 0, 60, "margin_bottom"))
        if kind == "bullets":
            lis = "".join(
                f'<li style="margin:0 0 8px 0;font-family:{FONT};font-size:15px;line-height:23px;'
                f'color:{BODY};">{self.t(i)}</li>' for i in b["items"])
            return f'<ul style="margin:6px 0 4px 0;padding:0 0 0 22px;">{lis}</ul>'
        if kind == "img":
            w = num(b.get("width", 536), 50, 536, "img width")  # 536 = content column
            if not b.get("alt"):
                self.warnings.append(f"Missing alt text for {b['src']}")
            return (f'<div style="margin:12px 0 10px 0;"><img src="{self.key(b["src"])}" width="{w}" '
                    f'alt="{html.escape(b.get("alt", ""))}" style="display:block;width:{w}px;max-width:100%;'
                    f'height:auto;border:1px solid {LINE};" />{self.caption(b.get("caption"))}</div>')
        if kind == "img_pair":
            w = num(b.get("width", 230), 50, 258, "img_pair width")  # 2 x 258 + 16px gap = 532
            cells = []
            for i, im in enumerate(b["images"][:2]):
                if not im.get("alt"):
                    self.warnings.append(f"Missing alt text for {im['src']}")
                pad = "padding-right:16px;" if i == 0 else ""
                cells.append(
                    f'<td valign="top" style="{pad}"><img src="{self.key(im["src"])}" width="{w}" '
                    f'alt="{html.escape(im.get("alt", ""))}" style="display:block;width:{w}px;height:auto;'
                    f'border:1px solid {LINE};" />{self.caption(im.get("caption"))}</td>')
            return ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                    f'style="margin:12px 0 10px 0;"><tr>{"".join(cells)}</tr></table>')
        sys.exit(f"Unknown block type: {kind}")

    def blocks(self, bs):
        return "".join(self.block(b) for b in bs)

    # ---- sections
    def h2(self, title):
        return (f'<tr><td style="padding:30px 32px 6px 32px;"><h2 style="margin:0;font-family:{FONT};'
                f'font-size:19px;line-height:26px;font-weight:600;color:{INK};border-bottom:2px solid '
                f'{self.accent};padding-bottom:6px;">{self.t(title)}</h2></td></tr>')

    def heads_up(self):
        hu = self.s.get("heads_up")
        if not hu:
            return ""
        return (f'<tr><td style="padding:22px 32px 0 32px;"><table role="presentation" width="100%" '
                f'cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="{tint(self.accent)}" style="background:{tint(self.accent)};'
                f'border-left:4px solid {self.accent};padding:16px 20px;">'
                f'<div style="font-family:{FONT};font-size:17px;line-height:24px;font-weight:600;'
                f'color:{self.accent};margin:0 0 4px 0;">{self.t(hu.get("title", "Heads up"))}</div>'
                f'{self.blocks(hu["blocks"])}</td></tr></table></td></tr>')

    def html(self):
        s = self.s
        intro = s.get("intro", [])
        intro_html = "".join(self.p(x, 0 if i == len(intro) - 1 else 14) for i, x in enumerate(intro))
        sections = "".join(
            self.h2(sec["title"]) + f'<tr><td style="padding:4px 32px 0 32px;">{self.blocks(sec["blocks"])}</td></tr>'
            for sec in s.get("sections", []))
        closing = "".join(self.p(x, 18) for x in s.get("closing", []))
        signoff = s.get("signoff", ["Thanks,", "[Your name]"])
        signoff_html = "".join(self.p(x, 2 if i < len(signoff) - 1 else 0) for i, x in enumerate(signoff))
        eyebrow = (f'<div style="font-family:{FONT};font-size:13px;font-weight:600;color:{self.accent};'
                   f'letter-spacing:0.5px;margin:0 0 6px 0;">{self.t(s["eyebrow"])}</div>') if s.get("eyebrow") else ""
        pre = (f'<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{html.escape(s["preheader"])}</div>'
               if s.get("preheader") else "")
        return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(s.get("subject", "Update"))}</title></head>
<body style="margin:0;padding:0;background:#F3F4F6;">{pre}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F3F4F6" style="background:#F3F4F6;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#FFFFFF" style="width:600px;max-width:100%;background:#FFFFFF;border:1px solid {LINE};">
<tr><td bgcolor="{self.accent}" style="background:{self.accent};height:6px;line-height:6px;font-size:0;mso-line-height-rule:exactly;">&nbsp;</td></tr>
<tr><td style="padding:28px 32px 0 32px;">{eyebrow}
<h1 style="margin:0 0 20px 0;font-family:{FONT};font-size:24px;line-height:31px;font-weight:600;color:{INK};">{self.t(s.get("title", ""))}</h1>
{intro_html}</td></tr>
{self.heads_up()}
{sections}
<tr><td style="padding:26px 32px 32px 32px;">{closing}{signoff_html}</td></tr>
</table></td></tr></table></body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", default="release-notes-email")
    ap.add_argument("--render", help="optional PNG path for a full-page screenshot (needs playwright)")
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8-sig") as f:  # -sig: tolerate a BOM from Notepad/PowerShell
        spec = json.load(f)
    check(spec)
    b = Builder(spec, os.path.dirname(os.path.abspath(a.spec)))
    body = b.html()
    os.makedirs(a.out_dir, exist_ok=True)

    preview = body
    for path, k in b.images.items():
        data = base64.b64encode(open(path, "rb").read()).decode()
        preview = preview.replace("{{" + k + "}}", f"data:image/{image_type(path)};base64,{data}")
    prev_path = os.path.join(a.out_dir, f"{a.name}-preview.html")
    open(prev_path, "w", encoding="utf-8").write(preview)

    cid_html = body
    for k in b.images.values():
        cid_html = cid_html.replace("{{" + k + "}}", f"cid:{k}@release-notes")
    msg = MIMEMultipart("related", type="text/html")
    msg["Subject"] = " ".join(spec.get("subject", "Software update").split())  # no newlines in headers
    msg["X-Unsent"] = "1"
    msg.attach(MIMEText(cid_html, "html", "utf-8"))
    for path, k in b.images.items():
        part = MIMEImage(open(path, "rb").read(), image_type(path))
        part.add_header("Content-ID", f"<{k}@release-notes>")
        part.add_header("Content-Disposition", "inline", filename=os.path.basename(path))
        msg.attach(part)
    eml_path = os.path.join(a.out_dir, f"{a.name}.eml")
    open(eml_path, "wb").write(msg.as_bytes(policy=SMTP))

    size = os.path.getsize(eml_path) // 1024
    print(f"Wrote {eml_path} ({size} KB, {len(b.images)} images)")
    print(f"Wrote {prev_path}")
    if size > 1500:
        b.warnings.append(f"Email is {size} KB; consider fewer or smaller images")
    for w in b.warnings:
        print("WARNING:", w)

    if a.render:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                br = p.chromium.launch()
                pg = br.new_page(viewport={"width": 700, "height": 900})
                pg.goto(Path(prev_path).resolve().as_uri())
                pg.screenshot(path=a.render, full_page=True)
                br.close()
            print(f"Rendered {a.render}")
        except Exception as e:
            print("Render skipped:", e)


if __name__ == "__main__":
    main()
