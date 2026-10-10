# 04 — Hooks

Source: live docs, fetched 2026-10-09. [hooks](https://code.claude.com/docs/en/hooks), [hooks-guide](https://code.claude.com/docs/en/hooks-guide)

## Facts we use
- ✅ **Plugin config.** Plugins put hooks in `hooks/hooks.json`, nested as event → `matcher` → `hooks[]`.
  - Matchers: `Bash` matches exactly; `Edit|Write` is a list; any other string is treated as a regex.
  - `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` and `${CLAUDE_PROJECT_DIR}` are substituted in the command.
  - ✅ Substitution works inside the `args` array (ran 2026-10-09 with `--plugin-dir`). `${CLAUDE_PLUGIN_DATA}` became `~/.claude/plugins/data/andrey-core-inline/`. An installed plugin gets a different id, so `--plugin-dir` test state is not shared with real use.
  - ✅ Hooks from user settings and from the plugin both run on the same event. Debug logs: `claude -p --debug-file <path>`.
- ✅ **Exec form.** With `"command"` plus `"args": [...]`, the hook runs without a shell. Default timeout is 600 s for command hooks.
- ✅ **PreToolUse exit codes.**
  - Exit 2 blocks the call, and stderr becomes the reason. A JSON `allow` can't override it.
  - **Any other non-zero exit is a non-blocking error, so the call proceeds.**
- ✅ **PreToolUse JSON output.** `hookSpecificOutput.permissionDecision` is `allow`, `deny`, `ask` or `defer`, plus a `permissionDecisionReason`.
  - When hooks disagree: deny > defer > ask > allow.
  - `ask` forces a prompt even in auto mode. ❓ Under `acceptEdits` it's unconfirmed; test in Phase 3.
  - ❓ `allow` probably doesn't override deny or ask rules in settings.
- ✅ **Input fields:** `tool_name`, `tool_input` (Bash: `command`), `cwd`, `permission_mode`, `effort`, `session_id`, `transcript_path`. Inside subagents, also `agent_id` and `agent_type`.
- ✅ **SessionStart.**
  - `source` is `startup`, `resume`, `clear`, `compact` or `fork`.
  - `additionalContext` (or stdout) injects text, capped at 10,000 chars.
  - Only `command` and `mcp_tool` hook types are allowed here.
  - ❓ `initialUserMessage` might auto-start work; read it before relying on it.
- ✅ **Stop and SubagentStop.** `{"decision":"block","reason":…}` or exit 2 keeps Claude working, and the reason becomes its next instruction.
  - Check `stop_hook_active` to avoid loops.
  - The cap is 8 consecutive continuations.
- ✅ **Hook types:** `command`, `http`, `mcp_tool`, `prompt`, `agent`. ❓ Which events accept which type is unread.
- ✅ **Gaps and controls.**
  - PreToolUse does not fire for `@`-referenced files, so keep the `Read` deny rules for `.env` and keys.
  - `disableAllHooks` and `allowManagedHooksOnly` exist.
  - `/hooks` is a read-only browser.

## Impact on design
- **Bug in the current `guard.py`, confirmed by running it** (2026-10-09: `{"tool_input":"x"}` gives `exit=1`).
  - Malformed `tool_input`, such as a non-dict value, raises an uncaught exception.
  - That exits with code 1, which is non-blocking, so the guard **fails open**.
  - The port to `andrey-core` wraps `main` so that any error exits with code 2.
- **False positive in the current `guard.py`** (2026-10-09). It matches the whole command text, so a commit message containing `rmdir` was blocked. The port must ignore quoted strings and heredoc bodies, or match only command positions.
- **espflash and serial access:** PreToolUse `ask` works. Test it in `acceptEdits` mode.
- **Session start:**
  - A SessionStart hook on `startup|resume` injects a short project status (aim for under 1,500 chars) and suggests `/andrey-core:start`.
  - It can't run the skill by itself unless `initialUserMessage` turns out to.
- **"Reviewer always checks":** a Stop hook blocks once when the git diff has changed since the last review, and asks Claude to run `code-reviewer` on it.
  - A diff hash stored in `${CLAUDE_PLUGIN_DATA}` prevents a re-review loop.
  - It costs one review per turn that changed code, not per message.

## Commands you'll use
- `/hooks` shows which hooks are active and where they come from.
- `/reload-plugins` applies hook edits.
- `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | python3 guard.py; echo $?` tests a hook by hand.
