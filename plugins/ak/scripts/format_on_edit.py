#!/usr/bin/env python3
"""PostToolUse hook for Edit|Write: format the edited file with the project's formatter.

Reads <project>/.claude/format.json: {"<glob>": ["cmd", "arg", ...], ...}. The first
glob matching the file (relative to the project) wins; the file path is appended.
Only commands in ALLOWED_FORMATTERS run, matched exactly: a cloned repo or an agent
must not be able to make this hook run arbitrary programs after every edit.
  no format.json / no match / outside project -> exit 0, nothing happens
  formatted                                   -> exit 0
  refused, missing or failing formatter       -> exit 1, message on stderr (non-blocking;
                                                 the edit itself stays)
Malformed input or format.json -> exit 1 with the reason.

Does NOT cover: files changed through Bash, notebooks, formatters not installed.
Needs Python 3.13+ (PurePath.full_match for ** globs).
"""
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

CONFIG = Path(".claude") / "format.json"
# Exact commands only; extra arguments (plugins, configs) could run project code.
ALLOWED_FORMATTERS = {
    ("ruff", "format"), ("uv", "run", "ruff", "format"),
    ("black",), ("uv", "run", "black"),
    ("rustfmt", "--edition", "2021"), ("rustfmt", "--edition", "2024"),
    ("prettier", "--write"), ("npx", "--no-install", "prettier", "--write"),
    ("ktlint", "-F"),
}
TIMEOUT_SECONDS = 20  # a formatter on one file should be near-instant
MAX_ERROR_LINES = 5


def load_config(project: Path) -> dict[str, list[str]]:
    path = project / CONFIG
    if not path.is_file():
        return {}
    config = json.loads(path.read_text())
    valid = isinstance(config, dict) and all(
        isinstance(cmd, list) and cmd and all(isinstance(a, str) for a in cmd)
        for cmd in config.values())
    if not valid:
        raise ValueError(f"{CONFIG} must map globs to non-empty lists of strings")
    return config


def edited_file(data: dict, project: Path) -> PurePosixPath | None:
    """Path of the edited file relative to the project, or None if outside it."""
    tool_input = data.get("tool_input")
    raw = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(raw, str) or not raw:
        raise ValueError("tool_input.file_path is missing")
    path = Path(raw) if Path(raw).is_absolute() else project / raw
    path = path.resolve()
    if not path.is_relative_to(project):
        return None
    return PurePosixPath(path.relative_to(project).as_posix())


def run_formatter(cmd: list[str], target: Path, project: Path) -> int:
    if tuple(cmd) not in ALLOWED_FORMATTERS:
        print(f"format-on-edit: refused {cmd} from {CONFIG}: not an allowed formatter "
              "command (see ALLOWED_FORMATTERS).", file=sys.stderr)
        return 1
    try:
        result = subprocess.run([*cmd, str(target)], cwd=project, capture_output=True,
                                text=True, timeout=TIMEOUT_SECONDS)
    except FileNotFoundError:
        print(f"format-on-edit: formatter not installed: {cmd[0]}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        tail = "\n".join((result.stderr or result.stdout).splitlines()[:MAX_ERROR_LINES])
        print(f"format-on-edit: {' '.join(cmd)} failed on {target.name}:\n{tail}",
              file=sys.stderr)
        return 1
    return 0


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise TypeError("hook input is not a JSON object")
        root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd")
        if not isinstance(root, str) or not root:
            raise ValueError("no project directory (CLAUDE_PROJECT_DIR or cwd)")
        project = Path(root).resolve()
        config = load_config(project)
        rel = edited_file(data, project) if config else None
        if rel is None:
            return 0
        cmd = next((c for glob, c in config.items() if rel.full_match(glob)), None)
        return run_formatter(cmd, project / rel, project) if cmd else 0
    except Exception as exc:  # PostToolUse cannot undo the edit: report and carry on
        print(f"format-on-edit: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
