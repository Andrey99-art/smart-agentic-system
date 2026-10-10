#!/usr/bin/env python3
"""SessionStart hook: inject a short project status so work can continue cheaply.

startup / clear / compact -> additionalContext (<= MAX_CHARS): head of STATE.md,
  git branch and uncommitted-file count; or a hint to run /ak:start.
resume -> nothing (the resumed conversation already holds the context; extra
  text would only cost tokens).
Errors -> exit 1 with a message (SessionStart cannot block; it only adds text).

Does NOT cover: starting /ak:start by itself, and STATE.md content
quality (that is the handoff skill's job).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

STATE_FILE = "STATE.md"
MAX_CHARS = 1500  # keep every session start cheap (docs cap is 10,000)
STATE_LINES = 25  # head of STATE.md that is injected
# Sources where the conversation lacks project state and the status helps.
INJECT_SOURCES = {"startup", "clear", "compact"}
NOT_SET_UP = ("andrey-kit: this project has no STATE.md, so it is not set up yet. "
              "If the user wants to start work here, suggest running /ak:start once.")
SET_UP = ("andrey-kit project status (from {state}; the user may run /ak:start "
          "to plan the next step):\n{git}{head}")


def git_line(project: Path) -> str:
    """'Branch: x; uncommitted files: n' or '' when git is unavailable."""
    try:
        def git(*args: str) -> str:
            return subprocess.run(["git", "-C", str(project), *args], capture_output=True,
                                  text=True, timeout=10, check=True).stdout
        # --show-current also works before the first commit; empty means detached HEAD.
        branch = git("branch", "--show-current").strip() or "(detached HEAD)"
        changed = [line for line in git("status", "--porcelain").splitlines() if line]
        return f"Branch: {branch}; uncommitted files: {len(changed)}\n"
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return ""  # not a repo, no commits yet, or git missing: status still useful


def build_context(project: Path) -> str:
    state = project / STATE_FILE
    if not state.is_file():
        return NOT_SET_UP
    lines = state.read_text(errors="replace").splitlines()
    head = "\n".join(lines[:STATE_LINES])
    if len(lines) > STATE_LINES:
        head += f"\n… ({len(lines) - STATE_LINES} more lines in {STATE_FILE})"
    text = SET_UP.format(state=STATE_FILE, git=git_line(project), head=head)
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS - 1] + "…"


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise TypeError("hook input is not a JSON object")
        if data.get("source", "startup") not in INJECT_SOURCES:
            return 0
        root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd")
        if not isinstance(root, str) or not root:
            raise ValueError("no project directory (CLAUDE_PROJECT_DIR or cwd)")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_context(Path(root).resolve()),
        }}))
        return 0
    except Exception as exc:  # SessionStart cannot block: report and carry on
        print(f"session-context: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
