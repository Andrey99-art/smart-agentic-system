"""Size budgets: the system must get sharper, not bigger.

Every line of a skill, agent, guide or template is loaded into context somewhere,
so lessons from /ak:retro must fit the budget by merging or replacing older lines.
A failing test here means: distill, do not raise the limit without a decision.
Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
# path glob (relative to the plugin) -> max lines; values from docs/architecture.md and CLAUDE.md
LINE_BUDGETS = {
    "skills/*/SKILL.md": 120,                      # docs allow 500; ours stay far below
    "skills/*/references/*.md": 100,
    "skills/start/references/stacks/*.md": 80,
    "agents/*.md": 60,
    "templates/project/CLAUDE.md.template": 100,
    "templates/project/STATE.md": 60,
    "scripts/*.py": 200,
}
# Descriptions are listed in context on every turn (skills) or at delegation (agents).
MAX_DESCRIPTION_CHARS = 400
DESCRIPTION = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


class BudgetTest(unittest.TestCase):
    def test_line_budgets(self) -> None:
        for pattern, limit in LINE_BUDGETS.items():
            files = sorted(PLUGIN.glob(pattern))
            self.assertTrue(files, f"budget pattern matches nothing: {pattern}")
            for path in files:
                with self.subTest(file=str(path.relative_to(PLUGIN))):
                    lines = len(path.read_text().splitlines())
                    self.assertLessEqual(lines, limit, f"{lines} lines > budget {limit}")

    def test_description_budgets(self) -> None:
        for path in sorted([*PLUGIN.glob("skills/*/SKILL.md"), *PLUGIN.glob("agents/*.md")]):
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                match = DESCRIPTION.search(path.read_text())
                self.assertIsNotNone(match, "frontmatter has no description")
                self.assertLessEqual(len(match.group(1)), MAX_DESCRIPTION_CHARS)


if __name__ == "__main__":
    unittest.main()
