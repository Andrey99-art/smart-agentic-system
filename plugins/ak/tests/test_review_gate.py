"""End-to-end tests for scripts/review_gate.py in throwaway git repos.

Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().parent.parent / "scripts" / "review_gate.py"


class ReviewGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name, "repo")
        self.state = Path(self.tmp.name, "state")
        self.repo.mkdir()
        subprocess.run(["git", "-C", str(self.repo), "init", "-q"], check=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def stop(self, active: bool = False, cwd: Path | None = None,
             env_extra: dict | None = None, stdin: str | None = None,
             args: list[str] | None = None, session: str = "test") -> subprocess.CompletedProcess:
        payload = {"hook_event_name": "Stop", "stop_hook_active": active,
                   "cwd": str(cwd or self.repo), "session_id": session}
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_DATA", "AK_REVIEW_GATE")}
        env.update(env_extra or {})
        argv = [sys.executable, str(GATE)] + (args if args is not None else [str(self.state)])
        return subprocess.run(argv, input=stdin if stdin is not None else json.dumps(payload),
                              text=True, capture_output=True, env=env, timeout=30)

    def write(self, name: str, content: str) -> None:
        Path(self.repo, name).write_text(content)

    def assert_silent(self, result: subprocess.CompletedProcess) -> None:
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def assert_review_requested(self, result: subprocess.CompletedProcess, file: str) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        decision = json.loads(result.stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("code-reviewer", decision["reason"])
        self.assertIn(file, decision["reason"])

    def test_clean_repo_is_silent(self) -> None:
        self.assert_silent(self.stop())

    def test_non_git_folder_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as plain:
            self.assert_silent(self.stop(cwd=Path(plain)))

    def test_code_change_requests_review_once(self) -> None:
        self.write("app.py", "x = 1\n")
        self.assert_review_requested(self.stop(), "app.py")
        self.assert_silent(self.stop())  # same state: no second review

    def test_follow_up_stop_accepts_fixes_without_re_review(self) -> None:
        self.write("app.py", "x = 1\n")
        self.assert_review_requested(self.stop(), "app.py")
        self.write("app.py", "x = 2  # fixed by reviewer finding\n")
        self.assert_silent(self.stop(active=True))  # stop_hook_active: record the fix
        self.assert_silent(self.stop())  # next normal stop: fixes already accepted

    def test_new_change_after_review_requests_again(self) -> None:
        self.write("app.py", "x = 1\n")
        self.stop()
        self.write("util.py", "y = 2\n")
        result = self.stop()
        self.assert_review_requested(result, "util.py")
        # Regression (first real run): unchanged, already-reviewed files are not listed again.
        self.assertNotIn("app.py", json.loads(result.stdout)["reason"])

    def test_edit_of_reviewed_file_requests_review_of_that_file_only(self) -> None:
        self.write("app.py", "x = 1\n")
        self.write("util.py", "y = 2\n")
        self.stop()
        self.write("app.py", "x = 3\n")
        reason = json.loads(self.stop().stdout)["reason"]
        self.assertIn("1 file(s): app.py", reason)

    def test_cap_three_requests_per_file_per_session(self) -> None:
        for round_no in range(1, 5):  # fixes arrive in later turns (background reviewer case)
            self.write("app.py", f"x = {round_no}\n")
            result = self.stop()
            if round_no <= 3:
                self.assert_review_requested(result, "app.py")
            else:
                self.assert_silent(result)  # 4th change in the same session: accepted
        self.write("app.py", "x = 5\n")
        self.assert_review_requested(self.stop(session="new-session"), "app.py")

    def test_docs_only_change_is_silent(self) -> None:
        self.write("README.md", "# notes\n")
        self.write("STATE.md", "Done: x\n")
        self.assert_silent(self.stop())

    def test_opt_out_env_is_silent(self) -> None:
        self.write("app.py", "x = 1\n")
        self.assert_silent(self.stop(env_extra={"AK_REVIEW_GATE": "off"}))

    def test_state_dir_from_env(self) -> None:
        self.write("app.py", "x = 1\n")
        result = self.stop(args=[], env_extra={"CLAUDE_PLUGIN_DATA": str(self.state)})
        self.assert_review_requested(result, "app.py")

    def test_errors_fail_open_visibly(self) -> None:
        self.write("app.py", "x = 1\n")
        for label, result in {"not json": self.stop(stdin="not json"),
                              "json list": self.stop(stdin="[]"),
                              "no state dir": self.stop(args=[])}.items():
            with self.subTest(case=label):
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")  # never a block decision on error
                self.assertIn("review-gate: skipped", result.stderr)


if __name__ == "__main__":
    unittest.main()
