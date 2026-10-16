# AbletonMCP Reference

## Command table

Protocol: `{"type": <command>, "params": {...}}` over TCP to `localhost:9877`.
Response: `{"status": "success"|"error", "result": {...}, "message": "..."}`.

### Session & transport
| Command | Params | Notes |
|---|---|---|
| `get_session_info` | — | tempo, track_count, return_track_count, master_track, is_playing, song_length, loop info |
| `get_track_info` | `track_index` | name, clip_slots, devices, volume, panning |
| `set_tempo` | `tempo` (float) | Affects the whole song |
| `start_playback` / `stop_playback` | — | Global transport |
| `set_current_song_time` | `time` (beats) | Moves the playhead |
| `switch_to_arrangement_view` | — | |

### Tracks
| Command | Params | Notes |
|---|---|---|
| `create_midi_track` | `index` | **`-1` appends to the end.** Returns the new index |
| `set_track_name` | `track_index`, `name` | |

### Clips
| Command | Params | Notes |
|---|---|---|
| `create_clip` | `track_index`, `clip_index`, `length` (beats) | **Fails if the slot is occupied** |
| `add_notes_to_clip` | `track_index`, `clip_index`, `notes[]` | Clip must already exist |
| `set_clip_name` | `track_index`, `clip_index`, `name` | |
| `fire_clip` / `stop_clip` | `track_index`, `clip_index` | |
| `create_audio_clip` | `track_index`, `clip_index`, `path` | Audio tracks only; needs Live ≥ 12.0.5 |

### Arrangement
| Command | Params | Notes |
|---|---|---|
| `duplicate_session_clip_to_arrangement` | `track_index`, `clip_index`, `destination_time` (beats) | Call once per placement |
| `get_arrangement_clips` | `track_index` | name, start_time, end_time, length |

### Browser
| Command | Params | Notes |
|---|---|---|
| `get_browser_items_at_path` | `path` | Primary discovery method |
| `get_browser_tree` | `category_type` | `all`/`instruments`/`sounds`/`drums`/`audio_effects`/`midi_effects` |
| `get_browser_item` | `uri`, `path` | |
| `load_browser_item` | `track_index`, `item_uri` | Loads onto a track |
| `load_instrument_or_effect` | `track_index`, `uri` | Equivalent for instruments/effects |

### Known broken (upstream)
- **`get_browser_categories`** — dispatched but the method doesn't exist.
  Fails with `'AbletonMCP' object has no attribute '_get_browser_categories'`.
  Use `get_browser_items_at_path` instead.

## Browser paths

Verified working top-level paths: `drums`, `instruments`, `sounds`,
`audio_effects`, `midi_effects`.

| Path | Contains |
|---|---|
| `drums` | Drum Rack, plus kits: `909 Core Kit.adg`, `808 Core Kit.adg`, `707`, `606`, `505`, `AG Techno Kit` … |
| `instruments` | Analog, Collision, Drift, Electric, Operator, Wavetable (folders) + DS Kick/Snare/HH/Clap (loadable) |
| `instruments/Analog` | `Bass`, `Brass`, `Pad`, `Piano & Keys`, `Strings` … |
| `sounds` | `Bass`, `Pad`, `Synth Lead`, … (category folders) |
| `sounds/Bass` | `Acid Bass.adv`, `808 Pure.adg`, `Abel Bass.adg` … |
| `sounds/Pad` | `Analog Slow Sweep Pad.adv`, `After Glow Pad.adg` … |
| `sounds/Synth Lead` | `Analog Stab Lead.adv`, `Acceleration Lead.adg` … |

URIs look like `query:Drums#FileId_5447` or `query:Sounds#Bass:FileId_6933`.
They are **installation-specific** — always discover them at runtime, never hardcode.

---

## Connection

### Repair checklist

1. **Socket check** — `lsof -nP -iTCP:9877 -sTCP:LISTEN`
2. **Is Live running?** — `pgrep -f "MacOS/Live"`
3. **Is the script on disk?**
   - Active: `/Applications/Ableton Live <N> <Ed>.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP/__init__.py`
   - Spare: `~/Music/Ableton/User Library/Remote Scripts/AbletonMCP/__init__.py`
4. **Is the Control Surface selected?** Live 12: `⌘,` → **Tempo & MIDI** → Control
   Surface row 1 → `AbletonMCP`, Input/Output = **None**.
5. **Restart Live.** It scans remote scripts at **launch only**.

### Version-specific gotchas

- **Live 12 renamed the dialog** to *Settings* (was *Preferences*), and split the
  old *Link, Tempo & MIDI* page — the Control Surface grid now lives on
  **Tempo & MIDI**. Project READMEs written for Live 10/11 give the wrong path.
- **`~/Library/Preferences/Ableton/Live X.X.X/User Remote Scripts/` is NOT for
  Python control-surface scripts.** That folder is for `UserConfiguration.txt`
  and instant-mapping. Ableton's documented location for third-party scripts is
  `~/Music/Ableton/User Library/Remote Scripts/`.
- **Verify the running version** before touching preference folders — stale
  folders for uninstalled versions are common. Trust
  `defaults read "<app>/Contents/Info.plist" CFBundleShortVersionString`, or
  `lsof -p <live_pid> | grep Preferences/Ableton`, **not** the highest-numbered folder.
- Scripts placed inside the `.app` bundle **are wiped by Ableton updates**.
  Keep the User Library copy as the recovery source.

### Proving which copy Live loaded

Live writes `__pycache__/__init__.cpython-*.pyc` next to the `__init__.py`
it actually imported, at the moment the Control Surface is **selected**
(not at scan). Sibling scripts that were never selected have no `.pyc` —
so a fresh `.pyc` is a reliable fingerprint of the loaded copy.

### MCP server dependency bug

`ableton-mcp` (PyPI, v1.2.0) declares `mcp[cli]>=1.3.0` with **no upper bound**.
Resolvers pick `mcp 2.0.0`, which removed `mcp.server.fastmcp`, so `uvx ableton-mcp`
dies with `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`.

Pin it:

```bash
uvx --with "mcp[cli]<2" ableton-mcp
```

Client config (opencode uses `environment`; Claude Desktop uses `env`):

```json
{
  "AbletonMCP": {
    "type": "local",
    "command": ["/path/to/uvx", "--with", "mcp[cli]<2", "ableton-mcp"],
    "environment": { "ABLETON_MCP_DISABLE_TELEMETRY": "true" },
    "timeout": 60000
  }
}
```

- Use an **absolute path to `uvx`** — GUI apps don't inherit your shell `PATH`.
- Default MCP timeout (5 s in opencode) is too short for loading instruments; raise it.
- The server posts anonymous telemetry to a Supabase endpoint unless
  `ABLETON_MCP_DISABLE_TELEMETRY=true` is set.

## Musical constants

- 4/4: 1 bar = 4 beats. 4 bars = 16 beats.
- Drum rack: 36 kick · 37 rim · 38 snare · 39 clap · 42 closed hat · 44 pedal hat · 46 open hat · 49 crash.
- `hz(midi) = 440 * 2**((midi-69)/12)`
- Kick fundamental ≈ 45–70 Hz → MIDI 29–37. Keep sustained bass out of it.
- Middle C = MIDI 60 (C3 in Ableton's display, which is one octave lower than
  the scientific-pitch convention — say "MIDI 60" to avoid ambiguity).
