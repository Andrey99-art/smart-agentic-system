"""End-to-end tests for scripts/agent_write_guard.py.

HOME is pointed at a temp dir, so the memory paths used here are throwaway.
Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "scripts" / "agent_write_guard.py"
REVIEWER = "ak:code-reviewer"


class AgentWriteGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name, "home")
        self.project = Path(self.tmp.name, "project")
        self.memory = self.home / ".claude" / "agent-memory" / "ak-code-reviewer"
        self.memory.mkdir(parents=True)
        self.project.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, file_path: str, agent: str | None = REVIEWER, tool: str = "Write",
              stdin: str | None = None) -> subprocess.CompletedProcess:
        payload = {"tool_name": tool, "tool_input": {"file_path": file_path, "content": "x"},
                   "cwd": str(self.project)}
        if agent:
            payload["agent_type"] = agent
        env = dict(os.environ, HOME=str(self.home))
        return subprocess.run([sys.executable, str(HOOK)], input=stdin or json.dumps(payload),
                              text=True, capture_output=True, env=env, timeout=10)

    def test_reviewer_may_write_own_memory(self) -> None:
        result = self.write(str(self.memory / "MEMORY.md"))
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_reviewer_blocked_in_project_and_elsewhere(self) -> None:
        other_memory = self.memory.parent / "ak-prompt-engineer" / "MEMORY.md"
        escape = str(self.memory / ".." / "evil.md")  # resolves outside its folder
        for target in (str(self.project / "app.py"), "relative.py", str(other_memory), escape):
            for tool in ("Write", "Edit"):
                with self.subTest(target=target, tool=tool):
                    result = self.write(target, tool=tool)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("read-only", result.stderr)

    def test_main_thread_and_other_agents_untouched(self) -> None:
        for agent in (None, "general-purpose", "ak:frontend"):
            with self.subTest(agent=agent):
                result = self.write(str(self.project / "app.py"), agent=agent)
                self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_malformed_input_fails_closed(self) -> None:
        cases = ["not json", "[]",
                 json.dumps({"agent_type": REVIEWER, "tool_name": "Write", "tool_input": "x"}),
                 json.dumps({"agent_type": REVIEWER, "tool_name": "Edit", "tool_input": {}})]
        for stdin in cases:
            with self.subTest(stdin=stdin):
                self.assertEqual(self.write("", stdin=stdin).returncode, 2)


if __name__ == "__main__":
    unittest.main()
