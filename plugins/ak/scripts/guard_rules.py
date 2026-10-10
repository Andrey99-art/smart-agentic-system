"""Per-command rules for guard.py. Each rule takes (name, args) of one command."""
import os
import re
from dataclasses import dataclass
from pathlib import Path

DENY, ASK = "deny", "ask"
Finding = tuple[str, str]

# Privilege escalation is never automatic.
PRIVILEGE = {"sudo", "doas", "su", "pkexec"}
# Wildcards in rm arguments delete an unknown set of files.
GLOB = re.compile(r"[*?\[]")
# find actions that run a deleting command per match.
FIND_EXEC = {"-exec", "-execdir", "-ok", "-okdir"}
DELETERS = {"rm", "rmdir", "shred", "unlink"}
# git global options that take a separate value (git -C dir push ...).
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
# Pathspecs that mean "everything" for checkout/restore.
ALL_PATHS = {".", ":/", "*", ":/*"}
# chmod modes that make files world-writable.
WORLD_WRITABLE = {"777", "0777", "a+rwx", "ugo+rwx", "a+w", "o+w"}
# Disk-level destruction; no legitimate use inside a project session.
DISK_WIPERS = {"shred", "wipefs", "fdisk", "parted"}
# Inline code that deletes trees: same damage as rm -rf.
RECURSIVE_DELETE_CODE = re.compile(r"rmtree|rimraf|removedirs|fs\.rm\w*\(|rm_rf|remove_dir_all")
# Inline code that deletes single files: same as plain rm, so ask.
DELETE_CODE = re.compile(r"os\.remove|unlink|os\.rmdir|fs\.rmdir|remove_file")
# Serial devices used to flash or monitor boards (ESP32 over USB-UART).
SERIAL_DEVICE = re.compile(r"/dev/tty(USB|ACM)\d*")
# Flashing tools: never automatic (wrong firmware can brick a board; a human decides).
FLASH_TOOLS = {"espflash", "cargo-espflash", "espmonitor", "esptool", "esptool.py"}
# Commands that write to every path argument / to the last path argument.
WRITE_ALL_ARGS = {"rm", "rmdir", "touch", "mkdir", "chmod", "chown", "truncate", "tee"}
WRITE_LAST_ARG = {"cp", "mv", "install", "rsync", "ln"}
# Output redirection words after shlex: '>', '2>>', '&>file', '>|file'.
REDIRECT = re.compile(r"^(?:\d|&)?>{1,2}\|?(.*)$")
# Device files that are safe redirect targets.
SAFE_DEVICES = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"}


@dataclass(frozen=True)
class Context:
    project: Path
    cwd: Path
    scratch: Path | None
    cargo_runs_espflash: bool  # .cargo/config.toml uses espflash as the runner


def _short_flags(args: list[str]) -> str:
    """All single-letter flags joined: ['-rf', '-v'] -> 'rfv'."""
    return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))


def privilege_rule(name: str, args: list[str]) -> list[Finding]:
    return [(DENY, f"privilege escalation ({name})")] if name in PRIVILEGE else []


def rm_rule(name: str, args: list[str]) -> list[Finding]:
    if name == "rmdir":
        return [(ASK, "rmdir needs manual approval")]
    if name != "rm":
        return []
    if "--recursive" in args or "r" in _short_flags(args).lower():
        return [(DENY, "recursive rm")]
    if any(GLOB.search(a) for a in args if not a.startswith("-")):
        return [(DENY, "rm with a wildcard")]
    return [(ASK, "rm needs manual approval")]


def find_rule(name: str, args: list[str]) -> list[Finding]:
    if name != "find":
        return []
    if "-delete" in args:
        return [(DENY, "find -delete")]
    for i, arg in enumerate(args[:-1]):
        if arg in FIND_EXEC and os.path.basename(args[i + 1]) in DELETERS:
            return [(DENY, f"find {arg} {args[i + 1]}")]
    return []


def git_rule(name: str, args: list[str]) -> list[Finding]:
    if name != "git":
        return []
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in GIT_VALUE_OPTIONS else 1
    sub, rest = (args[i], args[i + 1:]) if i < len(args) else ("", [])
    if sub == "clean":
        return [(DENY, "git clean")]
    if sub == "reset" and "--hard" in rest:
        return [(DENY, "git reset --hard")]
    if sub == "push" and ("f" in _short_flags(rest) or any(
            a.startswith("--force") or a.startswith("+") for a in rest)):
        return [(DENY, "git force push")]
    staged_only = sub == "restore" and "--staged" in rest and "--worktree" not in rest
    if sub in ("checkout", "restore") and ALL_PATHS & set(rest) and not staged_only:
        return [(DENY, f"git {sub} of all files discards uncommitted work")]
    return []


def container_rule(name: str, args: list[str]) -> list[Finding]:
    if name not in ("podman", "docker"):
        return []
    plain = [a for a in args if not a.startswith("-")]
    if "prune" in plain or plain[:2] == ["system", "reset"]:
        return [(DENY, f"{name} prune/reset")]
    if plain[:2] in (["volume", "rm"], ["volume", "remove"]):
        return [(DENY, f"{name} volume rm")]
    forced = "--force" in args or "f" in _short_flags(args)
    if forced and (plain[:1] in (["rm"], ["rmi"]) or plain[:2] == ["container", "rm"]):
        return [(DENY, f"{name} rm -f")]
    return []


def chmod_rule(name: str, args: list[str]) -> list[Finding]:
    recursive = "--recursive" in args or "R" in _short_flags(args)
    if name == "chmod" and recursive and WORLD_WRITABLE & set(args):
        return [(DENY, "recursive world-writable chmod")]
    return []


def disk_rule(name: str, args: list[str]) -> list[Finding]:
    if name in DISK_WIPERS or name.startswith("mkfs"):
        return [(DENY, f"disk-level command ({name})")]
    if name == "dd" and any(a.startswith("of=/dev/") and a not in ("of=/dev/null",) for a in args):
        return [(DENY, "dd onto a device")]
    return []


def interpreter_rule(name: str, args: list[str]) -> list[Finding]:
    if not name.startswith(("python", "node", "perl", "ruby")):
        return []
    code = " ".join(args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-c", "-e"))
    if RECURSIVE_DELETE_CODE.search(code):
        return [(DENY, f"recursive delete via {name}")]
    if DELETE_CODE.search(code):
        return [(ASK, f"file delete via {name} needs manual approval")]
    return []


def flash_rule(name: str, args: list[str], ctx: Context) -> list[Finding]:
    cargo_flash = name == "cargo" and args[:1] in (["espflash"], ["run"], ["r"]) and (
        args[:1] == ["espflash"] or ctx.cargo_runs_espflash)
    if name in FLASH_TOOLS or cargo_flash or any(SERIAL_DEVICE.search(a) for a in args):
        return [(ASK, "flashing or serial access needs manual approval")]
    return []


def write_targets(name: str, args: list[str]) -> list[str]:
    """Paths this command writes to: redirections plus known writer arguments."""
    targets, plain, skip = [], [], False
    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        match = REDIRECT.match(arg)
        if match:
            target = match.group(1) or (args[i + 1] if i + 1 < len(args) else "")
            skip = not match.group(1)
            if target and not target.startswith("&"):
                targets.append(target)
        elif not arg.startswith("-"):
            plain.append(arg)
    if name in WRITE_ALL_ARGS:
        targets += plain if name not in ("chmod", "chown") else plain[1:]
    elif name in WRITE_LAST_ARG and plain:
        targets.append(plain[-1])
    return targets


def is_outside(target: str, ctx: Context) -> bool:
    if target in SAFE_DEVICES:
        return False
    if "$" in target:  # unresolvable variable: cannot prove it stays inside
        return True
    path = Path(os.path.expanduser(target))
    path = (path if path.is_absolute() else ctx.cwd / path).resolve()
    roots = [ctx.project, Path("/tmp")] + ([ctx.scratch] if ctx.scratch else [])
    return not any(path == r or path.is_relative_to(r) for r in roots)


def check(argv: list[str], ctx: Context) -> list[Finding]:
    """All findings for one command argv."""
    name, args = argv[0], argv[1:]
    findings: list[Finding] = []
    for rule in (privilege_rule, rm_rule, find_rule, git_rule, container_rule,
                 chmod_rule, disk_rule, interpreter_rule):
        findings += rule(name, args)
    findings += flash_rule(name, args, ctx)
    outside = [t for t in write_targets(name, args) if is_outside(t, ctx)]
    if outside:
        findings.append((ASK, f"writes outside the project: {', '.join(outside)}"))
    return findings
