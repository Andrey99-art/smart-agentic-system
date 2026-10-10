"""End-to-end tests for scripts/session_context.py.

Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "scripts" / "session_context.py"
MAX_CHARS = 1500


class SessionContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def start(self, source: str = "startup", stdin: str | None = None,
              home: Path | None = None) -> subprocess.CompletedProcess:
        payload = json.dumps({"hook_event_name": "SessionStart", "source": source,
                              "cwd": str(self.project)})
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        if home is not None:
            env["HOME"] = str(home)
        return subprocess.run([sys.executable, str(HOOK)], input=stdin or payload, text=True,
                              capture_output=True, env=env, timeout=30)

    def context(self, result: subprocess.CompletedProcess) -> str:
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertLessEqual(len(output["additionalContext"]), MAX_CHARS)
        return output["additionalContext"]

    def git_repo(self) -> None:
        subprocess.run(["git", "-C", str(self.project), "init", "-q", "-b", "main"], check=True)

    def test_project_without_state_suggests_start(self) -> None:
        self.git_repo()
        text = self.context(self.start())
        self.assertIn("not set up", text)
        self.assertIn("/ak:start", text)

    def test_state_head_and_git_status_are_injected(self) -> None:
        self.git_repo()
        (self.project / "STATE.md").write_text("# State\nNext: add login form\n")
        (self.project / "app.py").write_text("x = 1\n")
        text = self.context(self.start())
        self.assertIn("Next: add login form", text)
        self.assertIn("Branch: main", text)
        self.assertIn("uncommitted files: 2", text)

    def test_long_state_is_truncated(self) -> None:
        (self.project / "STATE.md").write_text("".join(f"line {i} " + "x" * 80 + "\n"
                                                       for i in range(200)))
        text = self.context(self.start())  # length asserted inside context()
        self.assertNotIn("line 30 ", text)

    def test_clear_and_compact_inject_resume_does_not(self) -> None:
        (self.project / "STATE.md").write_text("Next: deploy\n")
        for source in ("clear", "compact"):
            with self.subTest(source=source):
                self.assertIn("Next: deploy", self.context(self.start(source)))
        result = self.start("resume")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_non_git_folder_still_reports_state(self) -> None:
        (self.project / "STATE.md").write_text("Next: deploy\n")
        text = self.context(self.start())
        self.assertIn("Next: deploy", text)
        self.assertNotIn("Branch:", text)

    def test_home_folder_warns_instead_of_status(self) -> None:
        (self.project / "STATE.md").write_text("Next: deploy\n")
        result = self.start(home=self.project)
        self.assertIn("home folder", json.loads(result.stdout)["systemMessage"])
        text = self.context(result)
        self.assertIn("Open a project folder", text)
        self.assertNotIn("Next: deploy", text)

    def test_project_folder_has_no_warning(self) -> None:
        result = self.start(home=self.project / "elsewhere")
        self.assertNotIn("systemMessage", json.loads(result.stdout))
        self.assertIn("/ak:start", self.context(result))

    def test_errors_exit_1_without_context(self) -> None:
        for stdin in ("not json", "[]", json.dumps({"source": "startup"})):
            with self.subTest(stdin=stdin):
                result = self.start(stdin=stdin)
                self.assertEqual((result.returncode, result.stdout), (1, ""))
                self.assertIn("session-context: skipped", result.stderr)


if __name__ == "__main__":
    unittest.main()
