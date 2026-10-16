---
name: ableton-mcp
description: Controls Ableton Live through the AbletonMCP Remote Script. Use when creating or editing MIDI clips, loading instruments and effects, building drum patterns or basslines or chord progressions, arranging sections, controlling playback and tempo, or browsing Ableton's device library. Use when asked to "make a beat", "write a bassline", "create a track", "load a synth", "set the tempo", or anything that changes the state of a live Ableton session. Also covers diagnosing a dead AbletonMCP connection.
---

# AbletonMCP — Driving Ableton Live

Ableton runs a socket server inside Live (a MIDI Remote Script) on **port 9877**.
You send JSON commands over TCP and it mutates the live session in real time.

**The user is looking at Ableton while you work.** Every command is immediately
visible and audible to them. There is no dry-run.

## Preflight — always, before anything else

```bash
lsof -nP -iTCP:9877 -sTCP:LISTEN
```

Nothing listening → the Remote Script isn't loaded. **Stop and fix that first**
(see `reference.md` § Connection). Do not attempt musical work against a dead socket.

## Two ways in

**Raw socket (always works).** Preferred when the MCP server isn't registered in
the client, or the client hasn't been restarted since config changes:

```python
import sys; sys.path.insert(0, "<skill_dir>/scripts")
from ableton import cmd, N, write_clip, find_preset, check_mix
cmd("get_session_info")
```

**MCP tools** (`mcp_AbletonMCP_*`) if they're exposed in the current session.
Same protocol underneath. The socket path is strictly more capable — a few
commands have no MCP tool wrapper.

---

# THE CRITICAL PART: don't generate mud

Music theory alone produces technically-correct output that **sounds terrible**.
These are the failure modes, all of which are detectable *before* you play anything.
Run `check_mix()` on your parts and resolve every warning before firing a clip.

### 1. Never pick presets by name

`find_preset("sounds/Pad", "pad")` returning `"Analog Slow Sweep Pad"` is a trap.
A slow-attack pad at 128 BPM never reaches its peak — it just smears. The name
tells you the *category*, never the *envelope* or the *spectrum*.

- Need rhythmic stabs → short attack. Prefer names with `Stab`, `Pluck`, `Poly`.
- Need sustained texture → only if notes are ≥ 2 bars.
- **When in doubt, ask the user to audition it**, or load 2–3 options on separate
  tracks and let them choose. That costs one message and saves a rebuild.

### 2. Keep bass out of the kick's fundamental

A kick's fundamental sits around **45–70 Hz**. Bass roots in that band are mud —
this is the single most common way generated EDM fails.

- MIDI 29–36 (F1–C2) = 44–65 Hz = **directly inside the kick**. Avoid.
- Put bass roots at **MIDI 40–52** (E2–C4), or sidechain, or high-pass.
- `check_mix()` flags this automatically.

### 3. Budget your voice leading

Root-position chords everywhere means every voice leaps on every change.
**Total motion between consecutive chords should be ≤ 12 semitones.** Use inversions.

`Am–F–C–G` in root position costs 52 semitones. The same progression voiced
`[57,60,64] → [57,60,65] → [55,60,64] → [55,59,62]` costs 8 and sounds smooth.

### 4. Match note duration to the patch envelope

A percussive stab held for a full beat gets cut off mid-note. A slow pad given
a 16th note never speaks. Decide the patch first, then write durations for it.

### 5. Leave room in the midrange

≥ 7 semitones (ideally an octave) between the top of the chords and the bottom
of the lead. Otherwise they mask each other and both turn to sludge.

### 6. Vary velocity

Identical velocities across a part sound like a machine. Accent downbeats,
ghost the offbeats.

### Honest limits

Static analysis catches masking, voice leading, range collisions and envelope
mismatch. It **cannot** tell you whether a hook is any good. Get the technical
issues to zero, then **put the user in the loop early** — build 4 bars, let them
listen, iterate. Never build 32 bars before the first playback.

---

## Workflow

1. **Preflight** the socket.
2. `get_session_info` → tempo, track_count, is_playing. `get_track_info` per track.
3. **Ask what you don't know**: genre, reference artist, key, BPM. "EDM" is not a
   spec — it spans 120 BPM house and 174 BPM DnB.
4. **Append new tracks** (`create_midi_track` with `index: -1`). Never overwrite
   the user's existing tracks or clips without explicit permission.
5. Load instruments, name tracks.
6. Compose notes in memory → **`check_mix()`** → resolve all warnings.
7. `write_clip` per part.
8. `fire_clip` each, then `start_playback`.
9. Confirm `is_playing: true` and report what you built.
10. **Ask how it sounds.** You cannot hear it. Their ears are the only verification.

## Note format

```python
{"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100, "mute": False}
```

- `start_time`/`duration` are **beats**, not seconds or ticks.
- 4 bars of 4/4 = 16 beats.
- Drum rack: 36 kick · 38 snare · 39 clap · 42 closed hat · 46 open hat.
- The slot must be **empty** — `create_clip` fails on an occupied slot.

## Guardrails

- **Additive by default.** Appending tracks is safe; overwriting is not.
- Mutations are undoable in Live with `⌘Z` — tell the user that when you finish.
- `set_tempo` changes the whole song. Confirm before changing an existing project's tempo.
- Loading instruments takes time; use a generous socket timeout (60–90s).
- If a command fails, read the `message` field — the Remote Script returns real
  Python exception text, which is usually the exact answer.

See `reference.md` for the full command table, browser paths and connection repair.
