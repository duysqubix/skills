# bw-secrets — Reference

Detailed tables, JSON payloads, and gotchas for create / modify / remove of Bitwarden
items via the `bw` CLI. SKILL.md is the entry point; read this for the exact mechanics.

## 1. Type & field enums

### Item type (`type`)

| Value | Meaning | Sub-object key |
|-------|---------|----------------|
| 1 | Login | `login` |
| 2 | Secure Note | `secureNote` (`{"type":0}`) |
| 3 | Card | `card` |
| 4 | Identity | `identity` |

App-registration / API-key style secrets are usually **type 2 (Secure Note)** with the
real values in custom `fields[]`.

### Custom field type (`fields[].type`)

| Value | Meaning | Visible? |
|-------|---------|----------|
| 0 | Text | yes |
| 1 | Hidden | masked — **use for secret values** |
| 2 | Boolean | yes |
| 3 | Linked | links to another field |

### Targeting (where the item lives)

| Goal | JSON keys |
|------|-----------|
| Shared org "folder" | `"organizationId": "<org>"`, `"collectionIds": ["<col>"]` |
| Personal folder | `"folderId": "<folder>"` (or `""`/`null` = No Folder) |
| Both | org item can also have a personal `folderId` for the owner's view |

Discover ids:

```bash
bw list organizations      # -> organizationId
bw list collections        # -> collectionIds (shared "folders")
bw list folders            # -> folderId (personal). "" id == No Folder
```

## 2. Session / unlock handling

`bw status` returns one of `unauthenticated` | `locked` | `unlocked`.

- **unauthenticated** → user must `bw login` (interactive; needs email + master pw + 2FA).
  Do NOT attempt to log in on their behalf or store creds.
- **locked** → user runs `bw unlock`, which prints a session key. Either:
  - they `export BW_SESSION="<key>"` in the shell you use, or
  - pass `--session "<key>"` to each command.
- **unlocked** → proceed. (In this environment `bw` was already unlocked.)

Never write the master password or session key to a file or to chat.

## 3. CREATE — JSON payload

Mirror a sibling item, then build payload. Example (Secure Note app-registration in a
shared collection):

```json
{
  "organizationId": "44cdfe27-....",
  "collectionIds": ["8340c76d-...."],
  "folderId": null,
  "type": 2,
  "name": "My App (Dev)",
  "notes": "Azure AD App Registration: MyApp (Dev)",
  "favorite": false,
  "secureNote": { "type": 0 },
  "fields": [
    { "name": "Tenant ID",       "value": "....", "type": 0 },
    { "name": "App (Client) ID", "value": "....", "type": 0 },
    { "name": "Secret Value",    "value": "....", "type": 1 }
  ]
}
```

Create:

```bash
bw encode < payload.json | bw create item
# or capture: ENC=$(bw encode < payload.json); bw create item "$ENC"
```

`bw create item` requires `organizationId` AND `collectionIds` together for org items —
one without the other errors. A personal item omits both (use `folderId` or nothing).

## 4. MODIFY — edit patterns

`bw edit item <id>` **replaces the entire item** with the JSON you pass. There is no
partial patch — you must send the full object. Safe pattern: get → mutate → put.

```bash
# Change one field value, preserving everything else
bw get item <ID> | python3 -c "
import sys, json
it = json.load(sys.stdin)
for f in it.get('fields', []):
    if f['name'] == 'Secret Value':
        f['value'] = 'NEW_SECRET'      # value comes from a var/stdin, not argv ideally
it.pop('revisionDate', None)
print(json.dumps(it))
" | bw encode | bw edit item <ID>
```

Common mutations:

| Task | Mutation in the get→put script |
|------|--------------------------------|
| Rotate secret | set the type-1 field's `value` |
| Add a field | `it['fields'].append({"name":..,"value":..,"type":..})` |
| Rename item | `it['name'] = "..."` |
| Move to collection | set `it['collectionIds']` (org item) — needs `bw edit item-collections` |
| Move personal folder | `it['folderId'] = "<id>"` |

Moving an org item between collections may require:
`bw edit item-collections <ID> <<< "$(echo '["<col1>","<col2>"]' | bw encode)"`.

## 5. REMOVE — delete patterns

```bash
bw delete item <ID>              # SOFT delete -> Trash (restorable in vault UI)
bw delete item <ID> --permanent  # HARD delete -> unrecoverable (only when user insists)
```

Default to soft delete. For org items the deleter needs manage/edit rights on the
collection. After delete: `bw get item <ID>` should fail ("Not found") — that's the proof.

Restore a soft-deleted item: `bw restore item <ID>`.

## 6. Verification gate (MANDATORY)

Create/edit are not "done" until read-back matches. Delete is not done until get fails.

```bash
bw sync >/dev/null
bw get item <ID> | python3 -c "
import sys, json
d = json.load(sys.stdin)
expected = {'Tenant ID':'....', 'App (Client) ID':'....', 'Secret Value':'....'}
got = {f['name']: f['value'] for f in d.get('fields', [])}
ok = True
for k, v in expected.items():
    m = got.get(k) == v
    ok &= m
    shown = '<hidden, len %d>' % len(v) if 'secret' in k.lower() else (v if m else 'GOT '+repr(got.get(k)))
    print(('PASS' if m else 'FAIL'), k, '=>', shown)
print('ALL MATCH:', ok)
"
```

## 7. Gotchas

- **"Shared folder" ≠ personal folder.** It's an org *collection*. Using `folderId` for a
  shared item silently makes it personal. Always `bw list collections`.
- **`bw list items --search` can miss freshly-synced items** — run `bw sync` first; if still
  empty, search a broader term or `bw list items` and filter in python.
- **`bw edit` is full-replace** — never hand-write a partial object; always get→mutate→put,
  and drop `revisionDate` before re-encoding.
- **Secret hygiene** — pass secret values via stdin/env, not shell argv (argv shows in
  `ps`/history). Delete temp JSON holding plaintext immediately after.
- **Org write rights** — create/edit/delete in a collection needs the right org role;
  a "you do not have permission" error means ask the user to grant access, not retry.
- **Don't print secrets** — redact to `<hidden, len N>` in all chat/log output.
