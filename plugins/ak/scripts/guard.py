#!/usr/bin/env python3
"""PreToolUse guard for Bash: blocks destructive commands, asks for risky ones.

Reads the hook JSON on stdin.
  deny -> exit 2, reason on stderr (Claude sees it; JSON allow cannot override)
  ask  -> exit 0, JSON permissionDecision "ask"
  none -> exit 0, no output (normal permission rules apply)
Any internal error -> exit 2 (fail closed: other non-zero exits would let the call run).

Does NOT cover: commands inside scripts or binaries it runs (./clean.sh),
obfuscation (base64 | sh, variables holding commands, aliases), inline code in
languages other than the listed interpreters, `cd` into a variable, and tools
other than Bash (Read/Edit/MCP). Not a security boundary: git is the safety net.
"""
import json
import os
import re
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard_rules as rules  # noqa: E402
import shell_split  # noqa: E402

# Nested shells deeper than this are refused rather than half-checked.
MAX_DEPTH = 5
# Shells and interpreters that execute whatever is piped into them.
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
PIPE_SINKS = SHELLS | {"python", "python3", "perl", "ruby", "node"}
FETCHERS = {"curl", "wget"}
# Downloaded content executed through process or command substitution.
FETCH_EXEC = re.compile(r"(<\(|\$\(|`)\s*(curl|wget)\b")
# Default ESP32 runner setup: `cargo run` flashes the board.
CARGO_CONFIG = Path(".cargo") / "config.toml"


def script_argument(argv: list[str]) -> str | None:
    """Inline script run by a shell (-c) or eval; None if there is none."""
    if argv[0] == "eval":
        return " ".join(argv[1:])
    if argv[0] in SHELLS:
        for i, arg in enumerate(argv[1:-1], start=1):
            if arg.startswith("-") and not arg.startswith("--") and "c" in arg:
                return argv[i + 1]
    return None


def next_cwd(argv: list[str], ctx: rules.Context) -> rules.Context:
    """Track `cd` so later relative paths resolve correctly; unknown -> '/'."""
    target = argv[1] if len(argv) > 1 else "~"
    if target == "-" or "$" in target:
        return replace(ctx, cwd=Path("/"))  # unknown: relative writes count as outside
    path = Path(os.path.expanduser(target))
    return replace(ctx, cwd=(path if path.is_absolute() else ctx.cwd / path).resolve())


def command_findings(argv: list[str], segment: str, fetch_piped: bool,
                     ctx: rules.Context, depth: int) -> list[rules.Finding]:
    """Findings for one command, including the inline script it runs."""
    findings: list[rules.Finding] = []
    if argv[0] in PIPE_SINKS and (fetch_piped or FETCH_EXEC.search(segment)):
        findings.append((rules.DENY, "downloaded content executed by a shell"))
    inner = script_argument(argv)
    if inner is not None:
        findings += analyze(inner, ctx, depth + 1)
    return findings + rules.check(argv, ctx)


def analyze(cmd: str, ctx: rules.Context, depth: int = 0) -> list[rules.Finding]:
    """Findings for every command that cmd would run, including nested ones."""
    if depth > MAX_DEPTH:
        return [(rules.DENY, "command nesting too deep to check")]
    text, heredoc_bodies = shell_split.extract_heredocs(cmd)
    segments, substitutions = shell_split.split_segments(text)
    findings: list[rules.Finding] = []
    fetch_in_pipe, names = False, set()
    for op, segment in segments:
        argvs = shell_split.candidate_argvs(shell_split.words(segment))
        piped = op in shell_split.PIPES
        for argv in argvs:
            findings += command_findings(argv, segment, piped and fetch_in_pipe, ctx, depth)
        names.update(argv[0] for argv in argvs)
        first = argvs[0][0] if argvs else ""
        fetch_in_pipe = first in FETCHERS or (fetch_in_pipe and piped)
        if first == "cd":
            ctx = next_cwd(argvs[0], ctx)
    # Heredoc bodies are code only when a shell reads them; otherwise data.
    nested = substitutions + (heredoc_bodies if names & (SHELLS | {"eval"}) else [])
    for code in nested:
        findings += analyze(code, ctx, depth + 1)
    return findings


def read_input(data: object) -> tuple[str, rules.Context]:
    """Validate hook JSON; raise on anything unexpected (caller fails closed)."""
    if not isinstance(data, dict) or not isinstance(data.get("tool_input"), dict):
        raise TypeError("hook input is not a JSON object with a tool_input object")
    command = data["tool_input"].get("command")
    if not isinstance(command, str):
        raise TypeError("tool_input.command is missing or not a string")
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd")
    if not isinstance(root, str) or not root:
        raise ValueError("no project directory (CLAUDE_PROJECT_DIR or cwd)")
    project = Path(root).resolve()
    cwd = Path(data.get("cwd") or root).resolve()
    scratch = data.get("scratchpad_dir")
    config = project / CARGO_CONFIG
    flashes = config.is_file() and "espflash" in config.read_text(errors="replace")
    return command, rules.Context(project, cwd, Path(scratch).resolve() if scratch else None,
                                  flashes)


def decide(findings: list[rules.Finding]) -> int:
    """Print the decision and return the exit code."""
    denies = list(dict.fromkeys(r for d, r in findings if d == rules.DENY))
    if denies:
        print(f"guard: blocked ({'; '.join(denies)}). Ask the user to run it manually, "
              "or move files to _to_delete/ instead of deleting.", file=sys.stderr)
        return 2
    asks = list(dict.fromkeys(r for d, r in findings if d == rules.ASK))
    if asks:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"guard: {'; '.join(asks)}",
        }}))
    return 0


def main() -> int:
    try:
        command, ctx = read_input(json.load(sys.stdin))
        return decide(analyze(command, ctx))
    except Exception as exc:  # fail closed: a broken guard must never allow a call
        print(f"guard: cannot check this command ({type(exc).__name__}: {exc}); "
              "blocking to be safe.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
