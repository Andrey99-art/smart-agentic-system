"""Skill injection lines (!`cmd`) must pass Claude Code's permission pre-check.

A line that fails the pre-check (a shell variable, a loop) or exits non-zero
aborts the whole skill silently, as /ak:start once did with `$f`.
Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
REPO = PLUGIN.parent.parent
SKILL_GLOBS = [PLUGIN / "skills", REPO / ".claude" / "skills"]
# !`cmd` at the start of a line or after ": " / "- " (how skills write facts).
INJECTION = re.compile(r"!`([^`]+)`")
# Substituted by Claude Code before the command is checked, so they are allowed.
SUBSTITUTED = re.compile(r"\$\{CLAUDE_(?:PLUGIN_ROOT|SKILL_DIR)\}")
LOOP = re.compile(r"\b(?:for|while|until)\s")


def problems(command: str) -> list[str]:
    """Reasons this injection command would fail or abort; empty if fine."""
    found = []
    if "$" in SUBSTITUTED.sub("", command):
        found.append("contains a shell variable ($), which fails the permission pre-check")
    if LOOP.search(command):
        found.append("contains a loop")
    if not command.rstrip().endswith("true"):
        found.append("does not end with `true`, so a non-zero exit aborts the skill")
    return found


def injection_commands() -> list[tuple[Path, str]]:
    commands = []
    for root in SKILL_GLOBS:
        for skill in sorted(root.glob("*/SKILL.md")):
            commands += [(skill, cmd) for cmd in INJECTION.findall(skill.read_text())]
    return commands


class SkillInjectionTest(unittest.TestCase):
    def test_skills_have_injection_lines_to_check(self) -> None:
        self.assertGreaterEqual(len(injection_commands()), 5, "glob found too few lines")

    def test_every_injection_line_is_safe(self) -> None:
        for skill, command in injection_commands():
            with self.subTest(skill=str(skill.relative_to(REPO)), command=command):
                self.assertEqual(problems(command), [])

    def test_checker_rejects_known_bad_lines(self) -> None:
        cases = {
            'for f in a b; do [ -e "$f" ] && echo "$f"; done; true': 2,  # the /ak:start bug
            "ls $HOME; true": 1,
            "git status --short": 1,
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(len(problems(command)), expected, problems(command))

    def test_checker_accepts_substituted_placeholders(self) -> None:
        self.assertEqual(problems("ls -d ${CLAUDE_PLUGIN_ROOT}/x 2>/dev/null; true"), [])


if __name__ == "__main__":
    unittest.main()
