#!/usr/bin/env python3
"""PreToolUse guard for Edit|Write: read-only agents may write only their own memory.

`memory: user` needs Write/Edit, so read-only agents keep those tools and this
hook confines them to ~/.claude/agent-memory/<plugin>-<agent>/.
  read-only agent writing elsewhere -> exit 2, reason on stderr
  any other caller                  -> exit 0, no output
Any internal error -> exit 2 (fail closed).

Does NOT cover: writes through Bash (redirects, sed -i, cp; under Balanced
those prompt the user), and agents not listed in READ_ONLY_AGENTS.
"""
import json
import os
import sys
from pathlib import Path

# agent_type values (plugin-scoped) that must never change project files.
READ_ONLY_AGENTS = {"ak:code-reviewer", "ak:prompt-engineer"}
# Where Claude Code keeps `memory: user` notes; folder = agent_type with ':' -> '-'.
MEMORY_ROOT = Path.home() / ".claude" / "agent-memory"
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def memory_dir(agent_type: str) -> Path:
    return (MEMORY_ROOT / agent_type.replace(":", "-")).resolve()


def target_path(tool_input: dict, cwd: str) -> Path:
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str) or not raw:
        raise ValueError("write tool input has no file_path")
    path = Path(os.path.expanduser(raw))
    return (path if path.is_absolute() else Path(cwd) / path).resolve()


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise TypeError("hook input is not a JSON object")
        agent = data.get("agent_type")
        if agent not in READ_ONLY_AGENTS or data.get("tool_name") not in WRITE_TOOLS:
            return 0
        tool_input = data.get("tool_input")
        if not isinstance(tool_input, dict):
            raise TypeError("tool_input is not an object")
        target, allowed = target_path(tool_input, data.get("cwd") or "."), memory_dir(agent)
        if target == allowed or target.is_relative_to(allowed):
            return 0
        print(f"agent-write-guard: {agent} is read-only; it may write only its memory "
              f"({allowed}), not {target}. Report the change to the main session instead.",
              file=sys.stderr)
        return 2
    except Exception as exc:  # fail closed: an unreadable write request is refused
        print(f"agent-write-guard: cannot check this write ({type(exc).__name__}: {exc}); "
              "blocking to be safe.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
