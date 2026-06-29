#!/usr/bin/env bash
# bw-secret.sh — create / edit / delete a Bitwarden item with built-in verify.
# Secret VALUES are read via prompt or stdin (never argv) and never echoed.
#
# Usage:
#   bw-secret.sh create
#   bw-secret.sh edit   <ITEM_ID>
#   bw-secret.sh delete <ITEM_ID> [--permanent]
#
# Notes:
#   - Requires `bw` unlocked (BW_SESSION exported or vault unlocked). Run `bw status`.
#   - For create/edit it mirrors a sibling item's structure; you supply field values.
#   - Always reads the item back and prints PASS/FAIL per field (secret shown as length).
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

have bw      || die "bw CLI not found in PATH"
have python3 || die "python3 required for JSON build/verify"

# --- preflight: vault must be unlocked ---
STATUS=$(bw status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))' 2>/dev/null || echo "?")
[ "$STATUS" = "unlocked" ] || die "vault status='$STATUS'. Run 'bw login' / 'bw unlock' and export BW_SESSION first."

CMD="${1:-}"; shift || true

prompt() { # prompt VAR_NAME "label" [hidden]
  local __var="$1" __label="$2" __hidden="${3:-}" __val=""
  if [ -n "$__hidden" ]; then read -rsp "$__label: " __val; echo; else read -rp "$__label: " __val; fi
  printf -v "$__var" '%s' "$__val"
}

verify_item() { # verify_item <ID>  (reads expected field name=value pairs on stdin as JSON dict)
  local id="$1" expected_json="$2"
  bw sync >/dev/null 2>&1 || true
  bw get item "$id" 2>/dev/null | EXP="$expected_json" python3 -c '
import sys, json, os
d = json.load(sys.stdin)
exp = json.loads(os.environ["EXP"])
got = {f["name"]: f.get("value") for f in d.get("fields", [])}
ok = True
print("name      :", d.get("name"))
print("type      :", d.get("type"))
print("collection:", d.get("collectionIds"))
print("--- fields ---")
for k, v in exp.items():
    m = got.get(k) == v
    ok = ok and m
    shown = ("<hidden, len %d>" % len(v)) if ("secret" in k.lower() or "password" in k.lower()) and m else (v if m else "GOT "+repr(got.get(k)))
    print(("PASS" if m else "FAIL"), k, "=>", shown)
print("ALL MATCH:", ok)
sys.exit(0 if ok else 1)
'
}

build_fields() { # interactive field collection -> emits JSON array on stdout; also writes EXPECTED env file
  local n="" name="" val="" ftype="" arr="[]" exp="{}"
  read -rp "How many custom fields? " n
  for ((i=1;i<=n;i++)); do
    prompt name "  field #$i name"
    read -rp "  field #$i type (0=text,1=hidden/secret) [0]: " ftype; ftype="${ftype:-0}"
    if [ "$ftype" = "1" ]; then prompt val "  field #$i value (hidden)" 1; else prompt val "  field #$i value"; fi
    arr=$(NAME="$name" VAL="$val" FT="$ftype" ARR="$arr" python3 -c '
import os,json
a=json.loads(os.environ["ARR"]); a.append({"name":os.environ["NAME"],"value":os.environ["VAL"],"type":int(os.environ["FT"])}); print(json.dumps(a))')
    exp=$(NAME="$name" VAL="$val" EXP="$exp" python3 -c '
import os,json
e=json.loads(os.environ["EXP"]); e[os.environ["NAME"]]=os.environ["VAL"]; print(json.dumps(e))')
  done
  printf '%s' "$arr" > "$FIELDS_TMP"
  printf '%s' "$exp" > "$EXPECTED_TMP"
}

case "$CMD" in
  create)
    FIELDS_TMP=$(mktemp); EXPECTED_TMP=$(mktemp); PAYLOAD_TMP=$(mktemp)
    trap 'rm -f "$FIELDS_TMP" "$EXPECTED_TMP" "$PAYLOAD_TMP"' EXIT
    echo "== CREATE =="
    read -rp "Item name: " ITEM_NAME
    read -rp "Type (1=Login,2=SecureNote) [2]: " ITYPE; ITYPE="${ITYPE:-2}"
    read -rp "Notes (optional): " NOTES
    read -rp "Organization ID (blank = personal): " ORG
    read -rp "Collection ID (blank = none; required if org set): " COL
    read -rp "Folder ID (blank = No Folder): " FOLDER
    build_fields
    ITEM_NAME="$ITEM_NAME" ITYPE="$ITYPE" NOTES="$NOTES" ORG="$ORG" COL="$COL" FOLDER="$FOLDER" \
    FIELDS_FILE="$FIELDS_TMP" python3 -c '
import os, json
fields = json.load(open(os.environ["FIELDS_FILE"]))
item = {
  "type": int(os.environ["ITYPE"]),
  "name": os.environ["ITEM_NAME"],
  "notes": os.environ["NOTES"] or None,
  "favorite": False,
  "fields": fields,
}
if int(os.environ["ITYPE"]) == 2: item["secureNote"] = {"type": 0}
if int(os.environ["ITYPE"]) == 1: item["login"] = {}
org = os.environ["ORG"].strip(); col = os.environ["COL"].strip(); fld = os.environ["FOLDER"].strip()
if org: item["organizationId"] = org
if col: item["collectionIds"] = [col]
item["folderId"] = fld or None
print(json.dumps(item))
' > "$PAYLOAD_TMP"
    echo "-- creating --"
    NEW_ID=$(bw encode < "$PAYLOAD_TMP" | bw create item | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
    echo "Created id: $NEW_ID"
    echo "-- verify --"
    verify_item "$NEW_ID" "$(cat "$EXPECTED_TMP")" || die "verification FAILED for $NEW_ID"
    echo "OK: created + verified $NEW_ID"
    ;;

  edit)
    ID="${1:-}"; [ -n "$ID" ] || die "usage: bw-secret.sh edit <ITEM_ID>"
    EXPECTED_TMP=$(mktemp); CUR_TMP=$(mktemp); NEW_TMP=$(mktemp)
    trap 'rm -f "$EXPECTED_TMP" "$CUR_TMP" "$NEW_TMP"' EXIT
    bw get item "$ID" > "$CUR_TMP" 2>/dev/null || die "item $ID not found"
    echo "== EDIT $ID (get -> mutate -> put) =="
    read -rp "Field name to set/add: " FNAME
    read -rp "Field type (0=text,1=hidden) [keep existing or 1]: " FT
    if [ "${FT:-1}" = "1" ]; then prompt FVAL "New value (hidden)" 1; else prompt FVAL "New value"; fi
    FNAME="$FNAME" FVAL="$FVAL" FT="${FT:-1}" CUR="$CUR_TMP" python3 -c '
import os, json
it = json.load(open(os.environ["CUR"]))
it.pop("revisionDate", None)
name, val, ft = os.environ["FNAME"], os.environ["FVAL"], int(os.environ["FT"])
it.setdefault("fields", [])
for f in it["fields"]:
    if f["name"] == name:
        f["value"] = val; f["type"] = ft; break
else:
    it["fields"].append({"name": name, "value": val, "type": ft})
print(json.dumps(it))
' > "$NEW_TMP"
    bw encode < "$NEW_TMP" | bw edit item "$ID" >/dev/null
    printf '{"%s": %s}' "$FNAME" "$(printf '%s' "$FVAL" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')" > "$EXPECTED_TMP"
    echo "-- verify --"
    verify_item "$ID" "$(cat "$EXPECTED_TMP")" || die "verification FAILED for $ID"
    echo "OK: edited + verified $ID"
    ;;

  delete)
    ID="${1:-}"; [ -n "$ID" ] || die "usage: bw-secret.sh delete <ITEM_ID> [--permanent]"
    PERM="${2:-}"
    bw get item "$ID" >/dev/null 2>&1 || die "item $ID not found (already gone?)"
    if [ "$PERM" = "--permanent" ]; then
      read -rp "PERMANENT (unrecoverable) delete of $ID. Type 'yes': " C; [ "$C" = "yes" ] || die "aborted"
      bw delete item "$ID" --permanent
    else
      bw delete item "$ID"   # soft delete -> trash
    fi
    bw sync >/dev/null 2>&1 || true
    if bw get item "$ID" >/dev/null 2>&1; then
      # soft-deleted items still resolve via get on some versions; check deletedDate
      DEL=$(bw get item "$ID" 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("deletedDate") or "")' 2>/dev/null || echo "")
      [ -n "$DEL" ] && { echo "OK: $ID soft-deleted (in trash, restorable)"; exit 0; }
      die "verification FAILED: $ID still present and not marked deleted"
    fi
    echo "OK: $ID deleted/verified gone"
    ;;

  *)
    die "usage: bw-secret.sh {create | edit <ID> | delete <ID> [--permanent]}"
    ;;
esac
