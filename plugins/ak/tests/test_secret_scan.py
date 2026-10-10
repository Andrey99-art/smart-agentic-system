"""End-to-end tests for scripts/secret_scan.py in throwaway git repos.

Fake secrets are assembled at runtime so this source file never contains a
string that looks like a real key. No command string here is run by a shell;
each is passed to secret_scan.py as text.

Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCAN = Path(__file__).resolve().parent.parent / "scripts" / "secret_scan.py"
FAKE_AWS_KEY = "AKIA" + "Z" * 16
FAKE_PRIVATE_KEY = "-----BEGIN " + "RSA PRIVATE KEY-----\nabc\n"
FAKE_DJANGO_KEY = "SECRET_KEY = '" + "q8" * 12 + "'\n"
PLACEHOLDER_KEY = "SECRET_KEY = '" + "change-me-please" + "'\n"


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.com",
                    *args], check=True, capture_output=True)


class SecretScanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def stage(self, name: str, content: str) -> None:
        path = Path(self.repo, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        git(self.repo, "add", name)

    def scan(self, command: str, cwd: str | None = None) -> subprocess.CompletedProcess:
        payload = {"tool_name": "Bash", "tool_input": {"command": command},
                   "cwd": cwd or self.repo}
        return self.run_raw(json.dumps(payload))

    @staticmethod
    def run_raw(stdin: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCAN)], input=stdin, text=True,
                              capture_output=True, timeout=30)

    def assert_blocked(self, result: subprocess.CompletedProcess, *expected: str) -> None:
        self.assertEqual(result.returncode, 2, result.stderr)
        for text in expected:
            self.assertIn(text, result.stderr)

    def test_clean_commit_passes(self) -> None:
        self.stage("app.py", "print('hello')\n")
        self.assertEqual(self.scan('git commit -m "add app"').returncode, 0)

    def test_secret_in_staged_line_is_blocked_and_masked(self) -> None:
        self.stage("config.py", f"x = 1\nKEY = '{FAKE_AWS_KEY}'\n")
        result = self.scan('git commit -m "config"')
        self.assert_blocked(result, "config.py:2: AWS access key")
        self.assertNotIn(FAKE_AWS_KEY, result.stderr)

    def test_private_key_and_django_secret_are_blocked(self) -> None:
        self.stage("deploy/key.txt", FAKE_PRIVATE_KEY)
        self.stage("settings.py", FAKE_DJANGO_KEY)
        self.assert_blocked(self.scan("git commit -m x"), "private key", "hard-coded credential")

    def test_placeholder_credential_passes(self) -> None:
        self.stage("settings.py", PLACEHOLDER_KEY)
        self.assertEqual(self.scan("git commit -m x").returncode, 0)

    def test_env_file_blocked_but_template_allowed(self) -> None:
        self.stage(".env.example", "DEBUG=1\n")
        self.assertEqual(self.scan("git commit -m x").returncode, 0)
        self.stage(".env", "DEBUG=1\n")
        self.assert_blocked(self.scan("git commit -m x"), ".env: secret file")

    def test_commit_all_scans_unstaged_tracked_changes(self) -> None:
        self.stage("app.py", "x = 1\n")
        git(self.repo, "commit", "-qm", "init")
        Path(self.repo, "app.py").write_text(f"x = '{FAKE_AWS_KEY}'\n")
        self.assertEqual(self.scan("git commit -m x").returncode, 0)  # nothing staged
        self.assert_blocked(self.scan('git commit -am "update"'), "app.py:1")

    def test_repo_found_through_cd_and_dash_c(self) -> None:
        self.stage("config.py", f"KEY = '{FAKE_AWS_KEY}'\n")
        outside = str(Path(self.repo).parent)
        name = Path(self.repo).name
        self.assert_blocked(self.scan(f"cd {name} && git commit -m x", cwd=outside))
        self.assert_blocked(self.scan(f"git -C {name} commit -m x", cwd=outside))

    def test_commit_hidden_in_bash_c_still_scanned(self) -> None:
        self.stage("config.py", f"KEY = '{FAKE_AWS_KEY}'\n")
        self.assert_blocked(self.scan("bash -c 'git commit -m x'"), "AWS access key")

    def test_non_commit_commands_are_ignored(self) -> None:
        self.stage("config.py", f"KEY = '{FAKE_AWS_KEY}'\n")
        self.assertEqual(self.scan("git status").returncode, 0)
        with tempfile.TemporaryDirectory() as not_repo:
            self.assertEqual(self.scan('echo "commit"', cwd=not_repo).returncode, 0)

    def test_commit_outside_a_repo_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as not_repo:
            self.assert_blocked(self.scan("git commit -m x", cwd=not_repo), "cannot check")

    def test_malformed_input_fails_closed(self) -> None:
        for stdin in ["not json", "[]", json.dumps({"tool_input": "x", "cwd": self.repo}),
                      json.dumps({"tool_input": {"command": "git commit"}})]:
            with self.subTest(stdin=stdin):
                self.assertEqual(self.run_raw(stdin).returncode, 2)


if __name__ == "__main__":
    unittest.main()
