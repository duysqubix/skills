"""
Minimal AbletonMCP client. Talks the raw JSON-over-TCP protocol on port 9877.

Works whether or not the MCP server is wired into your client - it speaks
directly to the Remote Script running inside Ableton Live.

Usage:
    from ableton import cmd, find_preset, notes_from, check_mix
    print(cmd("get_session_info"))
"""

import json
import socket

HOST, PORT = "localhost", 9877


class AbletonError(RuntimeError):
    pass


def cmd(command_type, params=None, timeout=90):
    """Send one command. Returns the parsed 'result'. Raises on error status."""
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    try:
        s.sendall(json.dumps({"type": command_type, "params": params or {}}).encode())
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            try:
                resp = json.loads(buf.decode())
                break
            except json.JSONDecodeError:
                continue  # partial JSON, keep reading
        else:
            resp = json.loads(buf.decode())
    finally:
        s.close()

    if resp.get("status") != "success":
        raise AbletonError(f"{command_type}: {resp.get('message')}")
    return resp.get("result", {})


def alive():
    """True if the Remote Script socket is reachable."""
    try:
        cmd("get_session_info", timeout=5)
        return True
    except Exception:
        return False


# ── browser ────────────────────────────────────────────────────────────────

def browse(path):
    """List browser items at a path, e.g. 'drums', 'sounds/Bass', 'instruments'."""
    r = cmd("get_browser_items_at_path", {"path": path})
    items = r.get("items", r)
    return items if isinstance(items, list) else []


def find_preset(path, *names):
    """First loadable item whose name contains one of `names` (in priority order).

    Returns (name, uri) or None. NOTE: matching on name tells you NOTHING about
    how the preset actually sounds - see the 'Preset selection' rules in SKILL.md.
    """
    items = browse(path)
    for want in names:
        for it in items:
            if it.get("is_folder"):
                continue
            if want.lower() in (it.get("name") or "").lower():
                return it.get("name"), it.get("uri")
    return None


# ── notes ──────────────────────────────────────────────────────────────────

def N(pitch, start, dur, vel=100):
    """Build one note dict. start/dur are in BEATS (not seconds, not ticks)."""
    return {
        "pitch": int(pitch),
        "start_time": float(start),
        "duration": float(dur),
        "velocity": int(vel),
        "mute": False,
    }


def write_clip(track_index, clip_index, length_beats, notes, name=None):
    """Create a clip and fill it. Slot must be EMPTY - create_clip fails otherwise."""
    cmd("create_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "length": float(length_beats),
    })
    if notes:
        cmd("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes,
        })
    if name:
        cmd("set_clip_name", {
            "track_index": track_index,
            "clip_index": clip_index,
            "name": name,
        })


# ── analysis: run BEFORE firing anything ───────────────────────────────────

def hz(midi):
    return 440.0 * (2 ** ((midi - 69) / 12))


def check_mix(parts, kick_fundamental=(45, 70)):
    """Static mix check. `parts` maps role -> list of note dicts.

    Catches the failure modes that make generated music sound like mud,
    without needing to hear anything. Returns a list of warning strings.
    """
    warn = []
    lo, hi = kick_fundamental

    bass = parts.get("bass") or []
    clashing = sorted({n["pitch"] for n in bass if lo <= hz(n["pitch"]) <= hi})
    if clashing:
        warn.append(
            f"BASS/KICK MASKING: pitches {clashing} land at "
            f"{[round(hz(p)) for p in clashing]} Hz, inside the kick fundamental "
            f"({lo}-{hi} Hz). Move the bass up an octave, or sidechain it."
        )

    chords, lead = parts.get("chords") or [], parts.get("lead") or []
    if chords and lead:
        gap = min(n["pitch"] for n in lead) - max(n["pitch"] for n in chords)
        if gap < 7:
            warn.append(
                f"MIDRANGE CROWDING: only {gap} semitones between chord top and "
                f"lead bottom. Aim for >= 7 (ideally an octave)."
            )

    # voice leading: total semitone motion between consecutive chord stacks
    if chords:
        by_start = {}
        for n in chords:
            by_start.setdefault(n["start_time"], []).append(n["pitch"])
        stacks = [sorted(v) for _, v in sorted(by_start.items())]
        for a, b in zip(stacks, stacks[1:]):
            if len(a) == len(b):
                motion = sum(abs(x - y) for x, y in zip(a, b))
                if motion > 12:
                    warn.append(
                        f"VOICE LEADING: {motion} semitones of motion between "
                        f"{a} -> {b}. Budget is <= 12; use an inversion."
                    )

    for role, ns in parts.items():
        if ns and len({n["velocity"] for n in ns}) == 1:
            warn.append(f"FLAT DYNAMICS: every '{role}' note has the same velocity.")

    return warn
