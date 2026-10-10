"""End-to-end tests for scripts/context_nudge.py with synthetic transcripts.

Run: python3 -m unittest discover -s plugins/ak/tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

NUDGE = Path(__file__).resolve().parent.parent / "scripts" / "context_nudge.py"
sys.path.insert(0, str(NUDGE.parent))
import context_nudge  # noqa: E402


def assistant(context: int, sidechain: bool = False) -> dict:
    usage = {"input_tokens": 2, "cache_read_input_tokens": context - 1002,
             "cache_creation_input_tokens": 1000, "output_tokens": 50}
    return {"type": "assistant", "isSidechain": sidechain, "message": {"usage": usage}}


class ContextNudgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.transcript = Path(self.tmp.name, "session.jsonl")
        self.state = Path(self.tmp.name, "state")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, *records: object, raw: str = "") -> None:
        lines = [json.dumps(r) for r in records]
        self.transcript.write_text(raw + "\n".join(lines) + "\n")

    def submit(self, env_extra: dict | None = None, stdin: str | None = None,
             args: list[str] | None = None, prompt: str = "next step") -> subprocess.CompletedProcess:
        payload = {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": prompt,
                   "transcript_path": str(self.transcript)}
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PLUGIN_DATA", "AK_CONTEXT_NUDGE")}
        env.update(env_extra or {})
        argv = [sys.executable, str(NUDGE)] + (args if args is not None else [str(self.state)])
        return subprocess.run(argv, input=stdin if stdin is not None else json.dumps(payload),
                              text=True, capture_output=True, env=env, timeout=30)

    def assert_silent(self, result: subprocess.CompletedProcess) -> None:
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def assert_nudged(self, result: subprocess.CompletedProcess, k: str) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        message = output["systemMessage"]
        self.assertIn(f"~{k}k tokens", message)
        self.assertIn("/ak:handoff", message)
        specific = output["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
        self.assertTrue(specific["additionalContext"].endswith(message))

    def test_quiet_below_threshold(self) -> None:
        self.write(assistant(150_000))
        self.assert_silent(self.submit())

    def test_nudges_once_per_step(self) -> None:
        self.write(assistant(210_000))
        self.assert_nudged(self.submit(), "210")
        self.write(assistant(260_000))
        self.assert_silent(self.submit())  # same 100k step: no repeat
        self.write(assistant(310_000))
        self.assert_nudged(self.submit(), "310")

    def test_drop_below_threshold_rearms(self) -> None:
        self.write(assistant(220_000))
        self.assert_nudged(self.submit(), "220")
        self.write(assistant(40_000))  # after /compact
        self.assert_silent(self.submit())
        self.write(assistant(205_000))
        self.assert_nudged(self.submit(), "205")

    def test_unmeasurable_tail_keeps_state(self) -> None:
        self.write(assistant(210_000))
        self.assert_nudged(self.submit(), "210")
        huge = {"type": "user", "pad": "x" * (context_nudge.TAIL_BYTES + 10)}
        self.write(assistant(212_000), huge)  # tail holds no usage: size unknown
        self.assert_silent(self.submit())
        self.write(assistant(215_000))
        self.assert_silent(self.submit())  # same step: no second nudge

    def test_negative_or_bool_usage_does_not_rearm(self) -> None:
        self.write(assistant(250_000))
        self.assert_nudged(self.submit(), "250")
        odd = {"type": "assistant", "message": {"usage": {"input_tokens": -1,
                                                          "cache_read_input_tokens": True}}}
        self.write(assistant(250_000), odd)
        self.assert_silent(self.submit())
        self.write(assistant(255_000))
        self.assert_silent(self.submit())

    def test_corrupt_state_recovers(self) -> None:
        self.write(assistant(230_000))
        self.assert_nudged(self.submit(), "230")
        for state in self.state.glob("context-nudge/*.json"):
            state.write_bytes(b"\xff\xfe{")
        self.assert_nudged(self.submit(), "230")  # corrupt state counts as "never nudged"
        self.assert_silent(self.submit())

    def test_uses_latest_main_record(self) -> None:
        self.write(assistant(250_000), assistant(90_000), assistant(400_000, sidechain=True),
                   {"type": "user", "message": {"content": "hi"}})
        self.assert_silent(self.submit())  # newest main-conversation size is 90k

    def test_slash_command_prompt_is_skipped(self) -> None:
        self.write(assistant(230_000))
        self.assert_silent(self.submit(prompt="  /ak:handoff"))
        self.assert_nudged(self.submit(), "230")  # level was not consumed by the command

    def test_path_first_prompt_is_not_a_command(self) -> None:
        self.write(assistant(230_000))
        self.assert_nudged(self.submit(prompt="/var/log/app/error.log -- why does this fail?"), "230")

    def test_env_threshold_with_k_suffix(self) -> None:
        self.write(assistant(60_000))
        self.assert_nudged(self.submit({"AK_CONTEXT_NUDGE": "50k"}), "60")

    def test_env_off_disables(self) -> None:
        self.write(assistant(500_000))
        self.assert_silent(self.submit({"AK_CONTEXT_NUDGE": "off"}))

    def test_bad_env_fails_open_visibly(self) -> None:
        self.write(assistant(500_000))
        result = self.submit({"AK_CONTEXT_NUDGE": "lots"})
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("context-nudge: skipped", result.stderr)

    def test_missing_transcript_is_quiet(self) -> None:
        self.assert_silent(self.submit())

    def test_garbage_lines_are_skipped(self) -> None:
        self.write(assistant(230_000), raw="not json\n")
        self.transcript.write_text(self.transcript.read_text() + "{truncated\n")
        self.assert_nudged(self.submit(), "230")

    def test_malformed_input_fails_open(self) -> None:
        for stdin in ("not json", "[1, 2]"):
            with self.subTest(stdin=stdin):
                result = self.submit(stdin=stdin)
                self.assertEqual((result.returncode, result.stdout), (1, ""))
                self.assertIn("context-nudge: skipped", result.stderr)

    def test_missing_state_dir_fails_open(self) -> None:
        self.write(assistant(230_000))
        result = self.submit(args=[])
        self.assertEqual(result.returncode, 1)
        self.assertIn("no state directory", result.stderr)


class TailTest(unittest.TestCase):
    def test_cut_first_line_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "t.jsonl")
            filler = json.dumps({"type": "user", "pad": "x" * context_nudge.TAIL_BYTES})
            path.write_text(json.dumps(assistant(999_000)) + "\n" + filler + "\n"
                            + json.dumps(assistant(210_000)) + "\n")
            self.assertEqual(context_nudge.last_context(path), 210_000)

    def test_no_usage_in_tail(self) -> None:
        self.assertIsNone(context_nudge.context_size({"type": "assistant", "message": "x"}))
        self.assertIsNone(context_nudge.context_size(["not", "a", "dict"]))


if __name__ == "__main__":
    unittest.main()
