---
name: bw-secrets
description: >
  Create, modify, or remove secrets (credentials, API keys, app registrations, notes)
  in Bitwarden using the `bw` CLI, including items in shared organization collections.
  Handles unlock/session state, mirrors an existing item as a template, builds the JSON
  payload safely, writes via `bw encode | bw create/edit`, and verifies by reading back.
  Use when asked to "add a secret to bitwarden", "store creds in bw", "create/update/delete
  a bitwarden item", "add an entry to the shared <X> folder", "put this in the vault", or
  any create/modify/remove of a Bitwarden login, secure note, or org-collection item.
---

# bw-secrets

Safely create / modify / remove Bitwarden items via the `bw` CLI, including shared
org collections. Always **mirror an existing sibling item** for structure, and always
**read back to verify** before declaring done.

## Quick start

```bash
# 0. Preflight: CLI present + vault unlocked (status must be "unlocked")
bw --version && bw status

# 1. Sync, then find a sibling item to use as the structural template
bw sync
bw list collections        # shared "folders" are ORG COLLECTIONS, not personal folders
bw list items --search "<sibling name>"
bw get item <SIBLING_ID>   # copy type, fields[], collectionIds, organizationId

# 2. CREATE (helper builds JSON, encodes, creates, reads back & verifies)
scripts/bw-secret.sh create

# 3. MODIFY / REMOVE
scripts/bw-secret.sh edit <ITEM_ID>
scripts/bw-secret.sh delete <ITEM_ID>     # soft-delete (trash) by default
```

The helper never echoes secret VALUES; it confirms by length + PASS/FAIL match.

## Mental model (do not skip)

| Concept | Reality |
|---------|---------|
| "shared folder" | an **org Collection** → `collectionIds` + `organizationId`, NOT `folderId` |
| personal "folder" | `folderId` (empty `""` / `null` = No Folder) |
| item type | `1`=Login, `2`=SecureNote, `3`=Card, `4`=Identity |
| custom field type | `0`=text, `1`=hidden, `2`=boolean, `3`=linked |
| secret VALUE | field type `1` (hidden). Never print it. |

## Workflow (every operation)

1. **Preflight** — `bw status`. If `locked`/`unauthenticated`, STOP and ask the user to
   `bw unlock` / `bw login` (see REFERENCE.md for session-token handling). Never store creds.
2. **Sync** — `bw sync` so org collections/items are fresh.
3. **Template** — find a sibling item (`bw list items --search`), `bw get item <id>`, and
   mirror its `type`, `fields[]`, `collectionIds`, `organizationId`.
4. **Resolve target** — `bw list collections` for the shared folder id; `bw list folders`
   for personal. Confirm name→id before writing.
5. **Confirm gaps** — if the user gives fewer fields than the template has, ASK whether to
   include empty placeholders or drop them, and confirm the item NAME.
6. **Build + write** — use the helper or `bw encode < payload.json | bw create item` /
   `bw edit item <id>`. For delete: `bw delete item <id>` (add `--permanent` only if asked).
7. **Verify (MANDATORY)** — `bw sync` then `bw get item <id>`; assert every field matches
   (secret by length). For delete: assert `bw get item <id>` now fails / item gone.
8. **Cleanup** — `rm -f` any temp JSON that held plaintext secrets.

## Safety rules (BLOCKING)

- Writing to a **shared collection** affects the whole org → confirm collection + name first.
- **Delete is destructive** → default to trash (soft delete); only `--permanent` when the
  user explicitly says permanent/hard delete. State it's reversible-from-trash or not.
- Never paste secret values into chat output, logs, or git. Redact to `<hidden, len N>`.
- Always `bw sync` after a write so other org members see it.

## See also

- [REFERENCE.md](REFERENCE.md) — item/field type tables, JSON payloads for each op, edit
  patterns (merge vs replace fields), session-token handling, full verification snippet.
- [scripts/bw-secret.sh](scripts/bw-secret.sh) — interactive create/edit/delete + verify.
