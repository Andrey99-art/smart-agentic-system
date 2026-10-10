"""Split a Bash command line into the simple commands that would actually run.

guard.py matches rules against command words, not raw text, so a commit
message that mentions "rmdir" is not mistaken for an rmdir command.
This is a conservative approximation of Bash, not a full parser; guard.py
lists what it does NOT cover.
"""
import os
import re
import shlex

# Characters that end a simple command when they appear outside quotes.
SEPARATOR_CHARS = ";&|\n"
# Two-character operators, checked before the single-character ones.
DOUBLE_OPERATORS = ("&&", "||", "|&", ";;")
# Pipe operators: needed to spot `curl ... | sh`.
PIPES = {"|", "|&"}
# Heredoc start (<<EOF, <<-EOF, <<'EOF'), but not a here-string (<<<).
HEREDOC = re.compile(r"(?<!<)<<-?(?!<)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
# NAME=value words before a command set its environment; they are not the command.
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Shell grammar words that can precede the real command in a segment.
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{", "}", "(", ")"}
# Commands that run another command taken from their own arguments.
WRAPPERS = {"nohup", "time", "command", "builtin", "exec", "nice", "ionice",
            "timeout", "stdbuf", "env", "xargs"}


def extract_heredocs(cmd: str) -> tuple[str, list[str]]:
    """Remove heredoc bodies from cmd; return the remaining text and the bodies.

    A body whose closing delimiter never appears is left in place, so a stray
    "<<word" inside quotes cannot hide the lines after it from the guard.
    """
    lines = cmd.split("\n")
    kept: list[str] = []
    bodies: list[str] = []
    i = 0
    while i < len(lines):
        kept.append(lines[i])
        i += 1
        for match in HEREDOC.finditer(kept[-1]):
            delimiter = match.group(2)
            end = next((j for j in range(i, len(lines)) if lines[j].strip() == delimiter), None)
            if end is None:
                continue
            bodies.append("\n".join(lines[i:end]))
            i = end + 1
    return "\n".join(kept), bodies


def _substitution_end(cmd: str, start: int) -> int:
    """Index of the character closing the substitution that opens at start."""
    if cmd[start] == "`":
        j = start + 1
        while j < len(cmd):
            if cmd[j] == "\\":
                j += 2
                continue
            if cmd[j] == "`":
                return j
            j += 1
        raise ValueError("unclosed backtick substitution")
    depth, quote, j = 0, "", start + 1
    while j < len(cmd):
        char = cmd[j]
        if char == "\\" and quote != "'":
            j += 2
            continue
        if quote:
            quote = "" if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise ValueError("unclosed $( ) or <( ) substitution")


def _is_redirect(cmd: str, i: int) -> bool:
    """True when the & or | at i belongs to a redirection (2>&1, &>, >|)."""
    prev = cmd[i - 1] if i > 0 else ""
    nxt = cmd[i + 1] if i + 1 < len(cmd) else ""
    if cmd[i] == "&":
        return (prev != "" and prev in "<>") or nxt == ">"
    return cmd[i] == "|" and prev == ">"


def split_segments(cmd: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Split cmd on unquoted ; & | and newlines.

    Returns (segments, substitutions): segments are (operator_before, text);
    substitutions are bodies of $( ), ` `, <( ), >( ), which run on their own.
    """
    segments: list[tuple[str, str]] = []
    subs: list[str] = []
    buf: list[str] = []
    op, quote, i = "", "", 0
    while i < len(cmd):
        char = cmd[i]
        if char == "\\" and quote != "'":
            buf.append(cmd[i:i + 2])
            i += 2
            continue
        if quote == "'":
            quote = "" if char == "'" else quote
            buf.append(char)
            i += 1
            continue
        if cmd.startswith(("$(", "<(", ">("), i) or char == "`":
            end = _substitution_end(cmd, i)
            subs.append(cmd[i + (1 if char == "`" else 2):end])
            buf.append(cmd[i:end + 1])
            i = end + 1
            continue
        if quote == '"' or char in "'\"":
            quote = "" if char == quote else (quote or char)
            buf.append(char)
            i += 1
            continue
        if char in SEPARATOR_CHARS and not _is_redirect(cmd, i):
            new_op = cmd[i:i + 2] if cmd[i:i + 2] in DOUBLE_OPERATORS else char
            text = "".join(buf)
            if text.strip():
                segments.append((op, text))
                op = new_op
            elif op not in PIPES:  # keep a pipe across blank lines: "curl x |\n sh"
                op = new_op
            buf = []
            i += len(new_op)
            continue
        buf.append(char)
        i += 1
    if quote:
        raise ValueError("unbalanced quote")
    if "".join(buf).strip():
        segments.append((op, "".join(buf)))
    return segments, subs


def words(segment: str) -> list[str]:
    """Shell words of one segment, quotes removed. Raises ValueError if unparseable."""
    return shlex.split(segment, comments=True, posix=True)


def _normalize(word: str) -> str:
    """Command name without subshell/brace prefix or directory: '(/usr/bin/rm' -> 'rm'."""
    return os.path.basename(word.lstrip("({"))


def candidate_argvs(segment_words: list[str]) -> list[list[str]]:
    """Argv lists that may run: the command itself and, after a wrapper, every suffix.

    Checking every suffix after a wrapper (timeout, xargs, env, …) avoids
    knowing each wrapper's options; it may over-match, never under-match.
    """
    i = 0
    while i < len(segment_words) and (segment_words[i] in KEYWORDS
                                      or ASSIGNMENT.match(segment_words[i])):
        i += 1
    argv = list(segment_words[i:])
    if not argv:
        return []
    argv[0] = _normalize(argv[0])
    candidates = [argv]
    if argv[0] in WRAPPERS:
        candidates += [[_normalize(argv[k])] + argv[k + 1:]
                       for k in range(1, len(argv)) if not argv[k].startswith("-")]
    return candidates
