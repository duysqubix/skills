#!/usr/bin/env python3
"""Build a route-map roadmap page from roadmap.json, using ../assets/template.html.

Build (checks the data first; stops on errors, prints warnings):
  python3 build_roadmap.py roadmap.json roadmap.html                    static page for the Artifact tool
  python3 build_roadmap.py roadmap.json roadmap.html --document         static standalone HTML file
  python3 build_roadmap.py roadmap.json roadmap.html --live --seed-dir seed
                                                                         live page + one JSON file per database
                                                                         document, and the ArtifactData batch to send
Get roadmap.json back:
  python3 build_roadmap.py --extract page.html > roadmap.json           from a static page
  python3 build_roadmap.py --collect export_dir > roadmap.json          from an ArtifactData export (out_dir)
"""
import argparse, html, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "template.html"
COLLECTIONS = ("phases", "steps", "gates", "activity")
DOC_ID = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
STEP_STATUS = {"todo", "active", "done", "blocked", "failed", "skipped", "ready"}
PHASE_STATUS = {"planned", "ready", "active", "blocked", "done", "skipped"}
GATE_STATUS = {"open", "decided", "done", "dropped"}
TONES = {"accent", "amber", "ink", "neutral", "green", "red"}
RESERVED = {"settings", "sidebar", "customize", "upgrade", "downloads"}
DATA_OPEN = '<script type="application/json" id="rm-data">'


def plural(n, word):
    if n == 1:
        return "%d %s" % (n, word)
    if re.search(r"[^aeiou]y$", word):
        return "%d %sies" % (n, word[:-1])
    return "%d %s%s" % (n, word, "es" if word.endswith("s") else "s")


def check(data):
    """Validate roadmap data in place (fills derived activity ids). Returns (errors, warnings)."""
    errors, warnings = [], []
    m = data.get("meta")
    if not isinstance(m, dict) or not m.get("title"):
        errors.append("meta.title is required")
        m = m if isinstance(m, dict) else {}
        data["meta"] = m
    owners = m.get("owners") or {}
    if not isinstance(owners, dict):
        errors.append("meta.owners must be an object of key: {label, tone}")
        owners = {}
    for k, o in owners.items():
        if not isinstance(o, dict) or not o.get("label"):
            errors.append("meta.owners.%s needs a label" % k)
        elif o.get("tone", "neutral") not in TONES:
            warnings.append("meta.owners.%s tone %r is not one of %s" % (k, o.get("tone"), ", ".join(sorted(TONES))))
    if m.get("waitingOn") and m["waitingOn"] not in owners:
        warnings.append("meta.waitingOn %r is not an owner key, so it shows as written" % m["waitingOn"])
    if m.get("timezone"):
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(m["timezone"])
        except Exception:
            errors.append("meta.timezone %r is not an IANA zone such as America/Chicago" % m["timezone"])
    if "refs" in m and not (isinstance(m["refs"], list) and all(isinstance(r, dict) and "label" in r for r in m["refs"])):
        errors.append("meta.refs must be a list of {label, value, href}")

    def when(where, v):
        if v in (None, ""):
            return
        if not isinstance(v, str) or not ISO.match(v):
            errors.append("%s %r is not an ISO date or time (2026-11-02 or 2026-11-02T16:05:00Z)" % (where, v))
        elif "T" in v and not re.search(r"(Z|[+-]\d{2}:?\d{2})$", v):
            warnings.append("%s %r has no zone, so each viewer reads it in their own; add Z for UTC" % (where, v))

    when("meta.updatedAt", m.get("updatedAt"))
    for coll in COLLECTIONS:
        if not isinstance(data.setdefault(coll, []), list):
            errors.append("%s must be a list" % coll)
            data[coll] = []
        bad = [x for x in data[coll] if not isinstance(x, dict)]
        if bad:
            errors.append("every entry in %s must be an object" % coll)
            data[coll] = [x for x in data[coll] if isinstance(x, dict)]
    seen = {"node": set(), "gate": set(), "activity": set()}

    def ident(kind, space, item):
        i = item.get("id")
        if not isinstance(i, str) or not DOC_ID.match(i) or i in (".", ".."):
            errors.append("%s needs an id of letters, digits and - _ (got %r)" % (kind, i))
            return
        if i in seen[space]:
            errors.append("duplicate %s id %r" % (kind, i))
        seen[space].add(i)
        if space == "node" and (i.startswith("rm-") or i in RESERVED or i.startswith("comment-")):
            warnings.append("id %r clashes with names the page or claude.ai uses; use p1, p1-2 ..." % i)

    def owner(kind, item):
        if item.get("owner") and item["owner"] not in owners:
            warnings.append("%s %s: owner %r is not a key in meta.owners" % (kind, item.get("id"), item["owner"]))

    phase_ids, codes = set(), set()
    for p in data["phases"]:
        ident("phase", "node", p)
        phase_ids.add(p.get("id"))
        if not p.get("title"):
            errors.append("phase %s needs a title" % p.get("id"))
        code = str(p.get("code") or "")
        if not code:
            errors.append("phase %s needs a code (P1, W2 ...)" % p.get("id"))
        elif len(code) > 3:
            warnings.append("phase code %r is longer than 3 characters and may crowd the station badge" % code)
        if code and code in codes:
            errors.append("duplicate phase code %r" % code)
        codes.add(code)
        if len(str(p.get("short") or p.get("title") or "")) > 16:
            warnings.append("phase %s: a short name of 16 characters or fewer fits the station label" % p.get("id"))
        if "scope" in p and not (isinstance(p["scope"], list) and all(isinstance(x, str) for x in p["scope"])):
            errors.append("phase %s: scope must be a list of strings" % p.get("id"))
        if p.get("status") and p["status"] not in PHASE_STATUS:
            warnings.append("phase %s: unknown status %r" % (p.get("id"), p["status"]))
        if "order" not in p:
            warnings.append("phase %s has no order, so it sorts by id" % p.get("id"))
        owner("phase", p)
    if len(data["phases"]) > 7:
        warnings.append("%s; a high-level roadmap reads best with 3 to 7, so consider grouping" % plural(len(data["phases"]), "phase"))
    per_phase, active = {}, 0
    for s in data["steps"]:
        ident("step", "node", s)
        if s.get("phase") not in phase_ids:
            errors.append("step %s points at unknown phase %r" % (s.get("id"), s.get("phase")))
        per_phase[s.get("phase")] = per_phase.get(s.get("phase"), 0) + 1
        if not s.get("label"):
            errors.append("step %s needs a label" % s.get("id"))
        st = s.get("status", "todo")
        if st not in STEP_STATUS:
            warnings.append("step %s: unknown status %r" % (s.get("id"), st))
        active += st == "active"
        if "order" not in s:
            warnings.append("step %s has no order, so it sorts by id" % s.get("id"))
        when("step %s at" % s.get("id"), s.get("at"))
        owner("step", s)
    for p in data["phases"]:
        n = per_phase.get(p.get("id"), 0)
        if n and p.get("status") in ("done", "active", "planned"):
            warnings.append("phase %s has steps, so leave its status off; the page works it out from them" % p.get("id"))
        if n > 8:
            warnings.append("phase %s has %d steps; a high-level roadmap reads best with 2 to 6 per phase" % (p.get("id"), n))
    if active > 1:
        warnings.append("%d steps are active; 'you are here' marks the first one in route order" % active)
    for g in data["gates"]:
        ident("gate", "gate", g)
        if not g.get("text"):
            errors.append("gate %s needs text" % g.get("id"))
        if not g.get("code"):
            warnings.append("gate %s has no code (D1, G1, R1), so its id shows instead" % g.get("id"))
        if g.get("status", "open") not in GATE_STATUS:
            warnings.append("gate %s: unknown status %r" % (g.get("id"), g.get("status")))
        ph = g.get("phases", [])
        if not isinstance(ph, list):
            errors.append("gate %s: phases must be a list of phase codes, such as [\"P2\"]" % g.get("id"))
        else:
            for c in ph:
                if c not in codes and c not in phase_ids:
                    warnings.append("gate %s holds up %r, which is not a phase code" % (g.get("id"), c))
        owner("gate", g)
    taken = {a["id"] for a in data["activity"] if isinstance(a.get("id"), str)}
    for a in data["activity"]:
        if not a.get("text") or not a.get("at"):
            errors.append("activity entry %s needs at and text" % (a.get("id") or a.get("text") or "?"))
        when("activity %s at" % (a.get("id") or a.get("text", "")[:30]), a.get("at"))
        if not a.get("id"):
            digits = re.sub(r"\D", "", str(a.get("at") or ""))
            base = "a-" + (digits[:8] + ("-" + digits[8:14] if len(digits) >= 14 else "") if len(digits) >= 8 else "entry")
            i, n = base, 2
            while i in taken:
                i, n = "%s-%d" % (base, n), n + 1
            a["id"] = i
            taken.add(i)
        ident("activity entry", "activity", a)
    return errors, warnings


def dump(data, escape=True):
    """One record per line, so a later change is a one-line edit. In a page, '<' is escaped so text can't end the script tag."""
    keys = ["meta"] + [k for k in COLLECTIONS if k in data]
    lines = ["{"]
    for i, k in enumerate(keys):
        comma = "," if i < len(keys) - 1 else ""
        if k == "meta":
            lines.append('"meta": %s%s' % (json.dumps(data.get("meta", {}), ensure_ascii=False, indent=1), comma))
        else:
            rows = data[k]
            lines.append('"%s": [' % k)
            lines += [json.dumps(r, ensure_ascii=False) + ("," if j < len(rows) - 1 else "") for j, r in enumerate(rows)]
            lines.append("]" + comma)
    lines.append("}")
    out = "\n".join(lines)
    return out.replace("<", "\\u003c") if escape else out


def page(tpl, data, live, document):
    m = data["meta"]
    out = tpl.replace("{{TITLE}}", html.escape(m["title"], quote=False)).replace("{{EYEBROW}}", html.escape(m.get("eyebrow", ""), quote=False))
    empty = DATA_OPEN + "null</script>"
    if empty not in out:
        sys.exit("error: the template's data block is missing")
    out = out.replace(empty, DATA_OPEN + ("null" if live else "\n" + dump(data) + "\n") + "</script>")
    if document:
        head, body = out.split('<div class="wrap">', 1)
        out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
               '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
               '<style>html,body{margin:0;padding:0}</style>\n' + head.strip() + '\n</head>\n<body>\n<div class="wrap">' + body + "</body>\n</html>\n")
    return out


def seed(data, out_dir):
    writes = []

    def put(coll, doc_id, body):
        path = os.path.abspath(os.path.join(out_dir, coll, doc_id + ".json"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False, indent=1)
        writes.append({"op": "set", "collection": coll, "doc_id": doc_id, "file_path": path})

    put("meta", "summary", data["meta"])
    for coll in COLLECTIONS:
        for item in data[coll]:
            put(coll, item["id"], {k: v for k, v in item.items() if k != "id"})
    total = (len(writes) + 49) // 50
    for n in range(0, len(writes), 50):
        chunk = writes[n:n + 50]
        print("\nArtifactData batch %d of %d (%d writes), pass this list as `writes`:" % (n // 50 + 1, total, len(chunk)))
        print("[\n" + ",\n".join(json.dumps(w, ensure_ascii=False) for w in chunk) + "\n]")


def extract(path):
    text = Path(path).read_text(encoding="utf-8")
    start = text.find(DATA_OPEN)
    if start < 0:
        sys.exit("error: no roadmap data block in %s" % path)
    start += len(DATA_OPEN)
    raw = text[start:text.find("</script>", start)].strip()
    data = json.loads(raw)
    if data is None:
        sys.exit("error: this is a live page; its data is in the artifact's database. Export it with ArtifactData "
                 "(out_dir) and use --collect.")
    return data


def collect(folder):
    """Rebuild roadmap data from an ArtifactData export: <dir>/meta/summary.json and <dir>/<collection>/<id>.json."""
    root = Path(folder)
    meta_file = root / "meta" / "summary.json"
    data = {"meta": json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}}
    for coll in COLLECTIONS:
        rows = []
        for f in sorted((root / coll).glob("*.json")) if (root / coll).is_dir() else []:
            row = {"id": f.stem}
            row.update(json.loads(f.read_text(encoding="utf-8")))
            rows.append(row)
        if coll == "activity":
            rows.sort(key=lambda r: str(r.get("at", "")))
        else:
            rows.sort(key=lambda r: (str(r.get("phase", "")), float(r.get("order") or 0), r["id"]) if coll == "steps"
                      else (float(r.get("order") or 0), r["id"]))
        data[coll] = rows
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", nargs="?", help="roadmap.json")
    ap.add_argument("out", nargs="?", help="the page to write")
    ap.add_argument("--live", action="store_true", help="leave the data block null; the page reads the artifact's db")
    ap.add_argument("--document", action="store_true", help="wrap in a full HTML document")
    ap.add_argument("--seed-dir", help="with --live: write one JSON file per db document and print the batch writes")
    ap.add_argument("--template", default=str(TEMPLATE), help="page template (default: ../assets/template.html)")
    ap.add_argument("--extract", metavar="PAGE", help="print the roadmap data embedded in a static page")
    ap.add_argument("--collect", metavar="DIR", help="print roadmap data rebuilt from an ArtifactData out_dir export")
    a = ap.parse_args()
    if a.extract or a.collect:
        print(dump(extract(a.extract) if a.extract else collect(a.collect), escape=False))
        return
    if not a.data or not a.out:
        ap.error("give roadmap.json and the page to write, or --extract / --collect")
    tpl = Path(a.template).read_text(encoding="utf-8")
    with open(a.data, encoding="utf-8") as f:
        data = json.load(f)
    errors, warnings = check(data)
    for w in warnings:
        print("warning: " + w)
    if errors:
        for e in errors:
            print("error: " + e)
        sys.exit(1)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page(tpl, data, a.live, a.document))
    print("wrote %s (%s; %s, %s, %s, %s)" % (
        a.out, "live" if a.live else ("standalone file" if a.document else "static"), plural(len(data["phases"]), "phase"),
        plural(len(data["steps"]), "step"), plural(len(data["gates"]), "gate"), plural(len(data["activity"]), "activity entry")))
    if a.seed_dir:
        if not a.live:
            print("note: --seed-dir is for live pages; a static page already carries its data")
        else:
            seed(data, a.seed_dir)


if __name__ == "__main__":
    main()
