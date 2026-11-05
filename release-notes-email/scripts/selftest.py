#!/usr/bin/env python3
"""Self-check for build_email.py (stdlib only). Run: python3 selftest.py

Builds assets/example-spec.json against placeholder PNGs, checks the .eml structure,
and checks that bad input (non-image file, bad accent, wrong spec shape) is refused.
"""
import email, json, re, struct, subprocess, sys, tempfile, zlib
from email import policy
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE.parent / "assets" / "example-spec.json"


def png(path, w=8, h=6):
    raw = b"".join(b"\x00" + b"\xcc\xcc\xcc" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def build(tmp, spec, name="t"):
    p = tmp / f"{name}.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    cmd = [sys.executable, "-I", str(HERE / "build_email.py"), str(p), "--out-dir", str(tmp / "out"), "--name", name]
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    text = EXAMPLE.read_text(encoding="utf-8")
    spec, srcs = json.loads(text), set(re.findall(r'"src": "([^"]+)"', text))
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for s in srcs:
            png(tmp / s)

        r = build(tmp, dict(spec, subject="Line one\nline two"))
        assert r.returncode == 0, r.stderr
        msg = email.message_from_bytes((tmp / "out" / "t.eml").read_bytes(), policy=policy.default)
        assert msg.get_content_type() == "multipart/related" and msg.get_param("type") == "text/html"
        assert msg["X-Unsent"] == "1" and "\n" not in msg["Subject"]
        parts = list(msg.iter_parts())
        body = parts[0].get_content()
        cids = {p["Content-ID"].strip("<>") for p in parts[1:]}
        assert set(re.findall(r'src="cid:([^"]+)"', body)) == cids and len(cids) == len(srcs), cids
        assert "{{img" not in body
        assert "data:image/png;base64," in (tmp / "out" / "t-preview.html").read_text(encoding="utf-8")

        (tmp / "images" / "secret.png").write_text("API_KEY=not-an-image")
        not_image = json.loads(text)
        not_image["sections"][0]["blocks"][2]["src"] = "images/secret.png"
        for bad, expect in [(not_image, "Not a PNG, JPEG or GIF"),
                            (dict(spec, accent="red"), "accent must be a hex color"),
                            (dict(spec, intro="Hi everyone"), "intro: expected a list of text")]:
            r = build(tmp, bad, "bad")
            assert r.returncode != 0 and expect in r.stderr, (expect, r.stderr)
        assert build(tmp, dict(spec, accent="#C33")).returncode == 0
    print("OK: build_email.py self-check passed")


if __name__ == "__main__":
    main()
