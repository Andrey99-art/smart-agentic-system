#!/usr/bin/env python3
"""UserPromptSubmit hook: tell the user when the conversation context has grown expensive.

Every request re-sends the whole context, so long sessions dominate cost
(measured 2026-10-10: requests above 250k tokens were 26% of requests but ~43%
of spend). This hook reads the latest main-conversation `usage` from the tail of
the transcript and, once the context passes the threshold, suggests /ak:handoff
then /clear: as a `systemMessage` and as one line of context asking Claude to
pass it on (a Stop `systemMessage` alone went unseen in the 2026-10-10 live test;
~60 tokens per nudge). It nudges again only after each further STEP_TOKENS of
growth; a drop below a level (after /compact) re-arms it. It never blocks the
prompt (that would need exit 2) and skips prompts that are slash commands.

Usage: context_nudge.py <state-dir>   (state dir: ${CLAUDE_PLUGIN_DATA}; env fallback)
Threshold: AK_CONTEXT_NUDGE=<tokens> (e.g. 150000 or 150k); AK_CONTEXT_NUDGE=off disables.
Fails OPEN by design: on errors it exits 1 (shown to the user as a hook error).

Does NOT cover: subagent contexts, the first prompt of a session (no usage
yet), and anything beyond the last TAIL_BYTES of the transcript (no usage
there means no nudge).
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ENV = "AK_CONTEXT_NUDGE"
DEFAULT_THRESHOLD = 200_000  # where cost per turn clearly outgrows a fresh start from STATE.md
STEP_TOKENS = 100_000  # re-nudge spacing: one reminder per 100k of growth, not every turn
TAIL_BYTES = 256 * 1024  # transcripts reach several MB; the latest usage sits at the end
MESSAGE = ("ak: context is ~{k}k tokens and every turn re-sends it. Cheaper from here: "
           "/ak:handoff, then /clear (STATE.md carries the work over). "
           f"Tune with {ENV}=<tokens> or {ENV}=off.")
FOR_CLAUDE = "Before answering, tell the user this in one line: "
# One command word (/ak:handoff, /clear) then space or end; a path like /var/log/a.log is a question.
SLASH_COMMAND = re.compile(r"/[\w:.-]+(\s|$)")


def threshold() -> int | None:
    """Tokens at which to nudge, or None when disabled."""
    raw = os.environ.get(ENV, "").strip().lower()
    if not raw:
        return DEFAULT_THRESHOLD
    if raw in ("off", "0"):
        return None
    value = int(raw[:-1]) * 1000 if raw.endswith("k") else int(raw)
    if value <= 0:
        raise ValueError(f"{ENV} must be a positive token count or 'off'")
    return value


def context_size(record: object) -> int | None:
    """Prompt size of one main-conversation assistant record, else None."""
    if not isinstance(record, dict) or record.get("type") != "assistant" or record.get("isSidechain"):
        return None
    message = record.get("message")
    usage = message.get("usage") if isinstance(message, dict) else None
    if not isinstance(usage, dict):
        return None
    keys = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    # type() rather than isinstance(): bools are ints; negatives would fake a drop and re-arm.
    return sum(v for v in (usage.get(k) for k in keys) if type(v) is int and v >= 0)


def last_context(transcript: Path) -> int | None:
    """Context size from the newest assistant record in the transcript tail."""
    with transcript.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        start = max(0, handle.tell() - TAIL_BYTES)
        handle.seek(start)
        lines = handle.read().split(b"\n")
    if start:
        lines = lines[1:]  # the first line is cut in the middle
    for line in reversed(lines):
        try:
            size = context_size(json.loads(line))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # a partial or foreign line must not hide older records
        if size:
            return size
    return None


def state_file(state_dir: Path, session: str) -> Path:
    key = hashlib.sha256(session.encode()).hexdigest()[:16]
    return state_dir / "context-nudge" / f"{key}.json"


def load_level(path: Path) -> int:
    try:
        level = json.loads(path.read_text()).get("level")
    except (OSError, ValueError, AttributeError):  # missing or corrupt: start over, then overwrite
        return -1
    return level if isinstance(level, int) else -1


def save_level(path: Path, level: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"level": level}))
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written state


def read_input() -> tuple[dict, Path]:
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise TypeError("hook input is not a JSON object")
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not raw_dir:
        raise ValueError("no state directory: pass ${CLAUDE_PLUGIN_DATA} as the argument")
    return data, Path(raw_dir)


def run() -> None:
    data, state_dir = read_input()
    limit = threshold()
    transcript = data.get("transcript_path")
    prompt = data.get("prompt")
    if isinstance(prompt, str) and SLASH_COMMAND.match(prompt.lstrip()):
        return  # a command such as /ak:handoff: the user is already acting
    if limit is None or not isinstance(transcript, str) or not Path(transcript).is_file():
        return  # disabled, or nothing to measure yet
    size = last_context(Path(transcript))
    if size is None:
        return  # unknown is not "small": keep the state, or the same step would nudge twice
    path = state_file(state_dir, str(data.get("session_id") or transcript))
    level = (size - limit) // STEP_TOKENS if size >= limit else -1
    previous = load_level(path)
    if level != previous:
        save_level(path, level)  # also lowers the level after /compact, re-arming the nudge
    if level > previous:
        message = MESSAGE.format(k=round(size / 1000))
        print(json.dumps({"systemMessage": message, "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": FOR_CLAUDE + message}}))


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:  # fail open, visibly: a broken nudge must not trap the session
        print(f"context-nudge: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
