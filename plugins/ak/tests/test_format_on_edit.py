"""End-to-end tests for scripts/format_on_edit.py with fake formatters on PATH.

The fake `ruff` appends a marker line, so a test can see that it ran; PATH holds
only the fake bin dir, so real formatters on this machine never run.
Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "scripts" / "format_on_edit.py"
FAKE_RUFF = f"""#!{sys.executable}
import sys
path = sys.argv[-1]
text = open(path).read()
if "BAD" in text:
    print("error: cannot parse", file=sys.stderr)
    sys.exit(2)
open(path, "a").write("# formatted\\n")
"""


class FormatOnEditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name, "project")
        self.bin = Path(self.tmp.name, "bin")
        (self.project / ".claude").mkdir(parents=True)
        self.bin.mkdir()
        ruff = self.bin / "ruff"
        ruff.write_text(FAKE_RUFF)
        ruff.chmod(0o755)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def config(self, mapping: object) -> None:
        (self.project / ".claude" / "format.json").write_text(json.dumps(mapping))

    def edit(self, name: str, content: str = "x = 1\n", stdin: str | None = None,
             file_path: str | None = None) -> subprocess.CompletedProcess:
        target = self.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        payload = {"tool_name": "Edit", "cwd": str(self.project),
                   "tool_input": {"file_path": file_path or str(target)}}
        return subprocess.run([sys.executable, str(HOOK)], input=stdin or json.dumps(payload),
                              text=True, capture_output=True, timeout=30,
                              env={"PATH": str(self.bin)})

    def text(self, name: str) -> str:
        return (self.project / name).read_text()

    def test_matching_file_is_formatted(self) -> None:
        self.config({"**/*.py": ["ruff", "format"]})
        result = self.edit("app/views.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# formatted", self.text("app/views.py"))

    def test_non_matching_file_and_missing_config_are_untouched(self) -> None:
        self.assertEqual(self.edit("app.py").returncode, 0)  # no format.json yet
        self.assertNotIn("# formatted", self.text("app.py"))
        self.config({"**/*.py": ["ruff", "format"]})
        self.assertEqual(self.edit("README.md", "# hi\n").returncode, 0)
        self.assertNotIn("# formatted", self.text("README.md"))

    def test_disallowed_commands_are_refused(self) -> None:
        for cmd in (["sh", "-c", "touch pwned"], ["ruff", "format", "--config", "x"]):
            with self.subTest(cmd=cmd):
                self.config({"**/*.py": cmd})
                result = self.edit("app.py")
                self.assertEqual(result.returncode, 1)
                self.assertIn("refused", result.stderr)
                self.assertFalse((self.project / "pwned").exists())

    def test_file_outside_project_is_ignored(self) -> None:
        self.config({"**/*.py": ["ruff", "format"]})
        outside = Path(self.tmp.name, "outside.py")
        outside.write_text("x = 1\n")
        self.assertEqual(self.edit("app.py", file_path=str(outside)).returncode, 0)
        self.assertNotIn("# formatted", outside.read_text())

    def test_missing_and_failing_formatter_report_without_blocking(self) -> None:
        self.config({"**/*.py": ["black"]})
        result = self.edit("app.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not installed: black", result.stderr)
        self.config({"**/*.py": ["ruff", "format"]})
        result = self.edit("app.py", "BAD syntax\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot parse", result.stderr)

    def test_malformed_input_and_config_exit_1(self) -> None:
        self.config({"**/*.py": "ruff format"})  # string instead of list
        self.assertIn("must map globs", self.edit("app.py").stderr)
        self.config({"**/*.py": ["ruff", "format"]})
        for stdin in ("not json", "[]", json.dumps({"cwd": str(self.project), "tool_input": {}})):
            with self.subTest(stdin=stdin):
                self.assertEqual(self.edit("app.py", stdin=stdin).returncode, 1)


if __name__ == "__main__":
    unittest.main()
