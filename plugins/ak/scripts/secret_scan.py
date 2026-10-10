#!/usr/bin/env python3
"""PreToolUse guard for Bash: blocks `git commit` when the changes hold secrets.

Scans staged file names and added lines (plus tracked working-tree changes for
`commit -a` / `commit <paths>`). A secret, or a commit that cannot be scanned,
-> exit 2 with file:line: pattern on stderr; values are never printed.

Does NOT cover: secrets already in history, commits made outside Claude (terminal,
IDE), unlisted formats, encoded or split secrets, binaries, scripts or git aliases.
"""
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell_split  # noqa: E402

CREDENTIAL = "hard-coded credential"
# Patterns for ADDED lines; the key is the name shown in the block message.
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_\w{50,})"),
    "Anthropic API key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    "OpenAI-style API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Stripe live key": re.compile(r"\b[rs]k_live_[A-Za-z0-9]{20,}"),
    # name = "literal" for credential-like names (Django SECRET_KEY, DB passwords, …).
    CREDENTIAL: re.compile(
        r"(?i)\b(?:password|passwd|secret(?:_key)?|api_?key|access_?token|auth_?token)\b"
        r"['\"]?\s*[:=]\s*['\"]([^'\"\s]{8,})['\"]"),
}
# Literal values that are obviously not real credentials.
PLACEHOLDER = re.compile(r"(?i)change.?me|example|dummy|placeholder|your[_-]|x{4,}|\*{4,}"
                         r"|<[^>]*>|\$\{|^test")
# Files that hold secrets by convention, whatever their content.
SECRET_FILES = re.compile(r"(?:^|/)(?:\.env(?:\.[^/]*)?|id_(?:rsa|ed25519|ecdsa|dsa)"
                          r"|[^/]*\.(?:pem|key|p12|pfx|jks|keystore)"
                          r"|keystore\.properties|local\.properties)$")
# Committed .env templates are expected and safe.
SECRET_FILE_TEMPLATES = re.compile(r"\.env\.(?:example|sample|template|dist)$")
# Quick pre-filter: commands without this word cannot commit.
COMMIT_WORD = re.compile(r"\bcommit\b")
# git commit options that consume the next word as their value.
COMMIT_VALUE_FLAGS = {"-m", "-F", "-c", "-C", "-t", "--author", "--date", "--message",
                      "--file", "--template", "--fixup", "--squash", "--cleanup", "--trailer"}
# git global options that consume the next word.
GIT_VALUE_OPTIONS = {"-c", "--git-dir", "--work-tree", "--namespace"}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")  # new-file line number of a diff hunk
MAX_SHOWN = 10  # findings listed in the block message


@dataclass(frozen=True)
class Commit:
    repo: str
    all_files: bool
    paths: tuple[str, ...]


def short_cluster(arg: str) -> tuple[bool, bool]:
    """(-a inside?, next word is a value?) for a short-flag cluster such as -am."""
    flags = arg[1:]
    for k, flag in enumerate(flags):
        if flag in "mFcCt":  # value-taking flag: the rest of the word or the next word
            return "a" in flags[:k], k == len(flags) - 1
    return "a" in flags, False


def parse_commit_args(rest: list[str]) -> tuple[bool, list[str]]:
    """(-a given?, pathspecs) from the words after `git commit`."""
    all_files, paths, j = False, [], 0
    while j < len(rest):
        arg = rest[j]
        if arg == "--":
            return all_files, paths + rest[j + 1:]
        takes_value = arg in COMMIT_VALUE_FLAGS
        if arg.startswith("-") and not arg.startswith("--") and not takes_value:
            has_all, takes_value = short_cluster(arg)
            all_files |= has_all
        all_files |= arg == "--all"
        if not arg.startswith("-"):
            paths.append(arg)
        j += 2 if takes_value else 1
    return all_files, paths


def parse_git_commit(argv: list[str], repo: str) -> Commit | None:
    if argv[0] != "git":
        return None
    args, i = argv[1:], 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            repo = os.path.normpath(os.path.join(repo, os.path.expanduser(args[i + 1])))
        i += 2 if args[i] == "-C" or args[i] in GIT_VALUE_OPTIONS else 1
    if i >= len(args) or args[i] != "commit":
        return None
    all_files, paths = parse_commit_args(args[i + 1:])
    return Commit(repo, all_files, tuple(paths))


def find_commits(command: str, cwd: str) -> list[Commit]:
    """Every `git commit` in command, with its repo; [] if none or unparseable."""
    try:
        text, _ = shell_split.extract_heredocs(command)
        segments, _ = shell_split.split_segments(text)
        commits, repo = [], cwd
        for _, segment in segments:
            for argv in shell_split.candidate_argvs(shell_split.words(segment)):
                if argv[0] == "cd" and len(argv) > 1:
                    repo = os.path.normpath(os.path.join(repo, os.path.expanduser(argv[1])))
                commit = parse_git_commit(argv, repo)
                if commit:
                    commits.append(commit)
        return list(dict.fromkeys(commits))
    except ValueError:
        return []


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          errors="replace", timeout=15, check=True).stdout


def secret_names(text: str) -> list[str]:
    names = []
    for name, pattern in SECRET_PATTERNS.items():
        match = pattern.search(text)
        if match and not (name == CREDENTIAL and PLACEHOLDER.search(match.group(1))):
            names.append(name)
    return names


def scan_diff(diff: str) -> list[str]:
    """'file:line: pattern' for each added line that matches a secret pattern."""
    findings, path, line = [], "", 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else raw[4:]
        elif raw.startswith("@@"):
            match = HUNK.match(raw)
            line = int(match.group(1)) if match else 0
        elif raw.startswith("+"):
            findings += [f"{path}:{line}: {name}" for name in secret_names(raw[1:])]
            line += 1
    return findings


def scan(commit: Commit) -> list[str]:
    diff_opts = ["-U0", "--no-color", "--no-ext-diff"]
    names = git(commit.repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    diff = git(commit.repo, "diff", "--cached", *diff_opts)
    if commit.all_files or commit.paths:
        pathspec = ["--", *commit.paths] if commit.paths else []
        names += "\0" + git(commit.repo, "diff", "--name-only", "--diff-filter=ACMR", "-z", *pathspec)
        diff += git(commit.repo, "diff", *diff_opts, *pathspec)
    files = [f"{n}: secret file" for n in names.split("\0")
             if n and SECRET_FILES.search(n) and not SECRET_FILE_TEMPLATES.search(n)]
    return files + scan_diff(diff)


def report(findings: list[str]) -> int:
    unique = list(dict.fromkeys(findings))
    if not unique:
        return 0
    shown = "\n".join(f"  - {f}" for f in unique[:MAX_SHOWN])
    print(f"secret-scan: commit blocked, {len(unique)} possible secret(s):\n{shown}\n"
          "Unstage them (git restore --staged <file>) or move values to an untracked .env. "
          "If this is a false positive, ask the user to commit manually.", file=sys.stderr)
    return 2


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict) or not isinstance(data.get("tool_input"), dict):
            raise TypeError("hook input is not a JSON object with a tool_input object")
        command, cwd = data["tool_input"].get("command"), data.get("cwd")
        if not isinstance(command, str) or not isinstance(cwd, str) or not cwd:
            raise TypeError("tool_input.command or cwd is missing or not a string")
        if not COMMIT_WORD.search(command):
            return 0
        commits = find_commits(command, cwd)
        if commits:  # a real commit: any scan failure blocks it
            return report([f for c in commits for f in scan(c)])
        try:  # "commit" hidden in bash -c, an alias, or text: best-effort scan of cwd
            return report(scan(Commit(cwd, False, ())))
        except (subprocess.CalledProcessError, OSError):
            return 0  # not a git repo, so nothing can be committed from here
    except Exception as exc:  # fail closed: never let a broken scan pass a commit
        print(f"secret-scan: cannot check this commit ({type(exc).__name__}: {exc}); "
              "blocking to be safe.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
