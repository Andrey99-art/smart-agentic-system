#!/usr/bin/env python3
"""Stop hook: before Claude finishes, require one code review per new set of changes.

Fingerprints each uncommitted code file (git status + content hash). Files whose
fingerprint differs from their last reviewed one trigger a Stop "block" decision
that names only those files and tells Claude to delegate to the code-reviewer.
On the follow-up stop (stop_hook_active) it records the post-fix state silently,
so fixes made in the same turn are not re-reviewed (the reviewer runs in the
foreground for this). Backstop: at most MAX_BLOCKS_PER_FILE requests per file
per session, after which changes to that file are accepted silently.

Usage: review_gate.py <state-dir>   (state dir: ${CLAUDE_PLUGIN_DATA}; env fallback)
Opt out for a session: AK_REVIEW_GATE=off.
Fails OPEN by design: on errors it exits 1 (shown to the user as a hook error)
instead of trapping the session.

Does NOT cover: non-git folders, changes made outside the repo, docs-only
changes, and the quality of the review itself.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Changed files matching this are not code; a docs-only change needs no review.
NON_CODE = re.compile(r"(?i)\.(md|rst|txt|png|jpe?g|gif|svg|ico|webp|pdf|lock)$|(^|/)STATE\.md$")
OPT_OUT_ENV = "AK_REVIEW_GATE"
MAX_LISTED = 8  # changed files named in the block reason
# Backstop against endless review→fix rounds (inbox 2026-10-10: rounds 2-3 still found real bugs).
MAX_BLOCKS_PER_FILE = 3
REASON = (
    "Code changed since the last review ({count} file(s): {files}). Before finishing: "
    "delegate to the ak:code-reviewer agent with these files; fix every bug or "
    "warning it confirms (normal permissions apply); then tell the user in 2-3 lines what "
    "was found and fixed. If the change is trivial (formatting, comments), say so and stop."
)


def git_status(repo: Path) -> list[tuple[str, str]]:
    """(status, path) for every uncommitted file, untracked included."""
    out = subprocess.run(["git", "-C", str(repo), "status", "--porcelain=v1", "-z",
                          "--untracked-files=all"],
                         capture_output=True, text=True, timeout=15, check=True).stdout
    entries, items, i = [], out.split("\0"), 0
    while i < len(items):
        item = items[i]
        if len(item) > 3:
            entries.append((item[:2], item[3:]))
            if "R" in item[:2] or "C" in item[:2]:
                i += 1  # renames and copies are followed by the original path
        i += 1
    return entries


def file_hash(path: Path) -> str:
    if not path.is_file():
        return "absent"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprints(repo: Path, entries: list[tuple[str, str]]) -> dict[str, str]:
    """path -> 'status:content-hash' for each uncommitted code file."""
    return {rel: f"{status}:{file_hash(repo / rel)}" for status, rel in entries}


def state_file(state_dir: Path, repo: Path) -> Path:
    key = hashlib.sha256(str(repo).encode()).hexdigest()[:16]
    return state_dir / "review-gate" / f"{key}.json"


def save(path: Path, reviewed: dict[str, str], session: str, blocks: dict[str, int]) -> None:
    """Persist reviewed fingerprints and this session's block counts (other sessions dropped)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"reviewed": reviewed, "blocks": {session: blocks}}))
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written state


def load(path: Path, session: str) -> tuple[dict[str, str], dict[str, int]]:
    """(reviewed fingerprints, this session's block counts); empty for missing/old formats."""
    try:
        state = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}, {}
    reviewed = state.get("reviewed") if isinstance(state, dict) else None
    blocks = state.get("blocks", {}).get(session, {}) if isinstance(state, dict) else {}
    return (reviewed if isinstance(reviewed, dict) else {},
            blocks if isinstance(blocks, dict) else {})


def read_input() -> tuple[dict, Path]:
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise TypeError("hook input is not a JSON object")
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not raw_dir:
        raise ValueError("no state directory: pass ${CLAUDE_PLUGIN_DATA} as the argument")
    return data, Path(raw_dir)


def run() -> int:
    data, state_dir = read_input()
    if os.environ.get(OPT_OUT_ENV, "").lower() == "off":
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd")
    if not isinstance(root, str) or not root:
        raise ValueError("no project directory (CLAUDE_PROJECT_DIR or cwd)")
    repo = Path(root).resolve()
    try:
        entries = [e for e in git_status(repo) if not NON_CODE.search(e[1])]
    except subprocess.CalledProcessError:
        return 0  # not a git repo: nothing to compare against
    if not entries:
        return 0
    current, path = fingerprints(repo, entries), state_file(state_dir, repo)
    session = str(data.get("session_id") or "")
    reviewed, blocks = load(path, session)
    if data.get("stop_hook_active"):  # follow-up stop after a review: accept the fixes
        save(path, {**reviewed, **current}, session, blocks)
        return 0
    # Only files whose content changed since their last review need a new one, and
    # a file is not re-requested more than MAX_BLOCKS_PER_FILE times in one session.
    names = sorted(rel for rel, mark in current.items()
                   if reviewed.get(rel) != mark and blocks.get(rel, 0) < MAX_BLOCKS_PER_FILE)
    blocks.update({rel: blocks.get(rel, 0) + 1 for rel in names})
    save(path, {**reviewed, **current}, session, blocks)
    if not names:
        return 0
    listed = ", ".join(names[:MAX_LISTED]) + (" …" if len(names) > MAX_LISTED else "")
    print(json.dumps({"decision": "block",
                      "reason": REASON.format(count=len(names), files=listed)}))
    return 0


def main() -> int:
    try:
        return run()
    except Exception as exc:  # fail open, visibly: a broken gate must not trap the session
        print(f"review-gate: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
