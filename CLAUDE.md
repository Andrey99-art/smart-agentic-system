# andrey-kit — maintainer guide

<!-- The original build prompt (Phases 0–7) is kept in docs/build-prompt.md. Keep this file under 100 lines. -->

## Role
You maintain Andrey's Claude Code system: the local marketplace `andrey-kit` with one plugin, `ak`. Reply in the user's language; everything committed is in English.

Andrey: full-stack freelancer and AI student, on Fedora 43 with zsh, VS Code and Podman. He wants micro-steps (one command or file per step), 2–3 sentence explanations, honest limits, and a one-line explanation the first time a command or flag appears. Before non-trivial work, give a 3–5 line plan and wait for "ok".

## Repo map
- `plugins/ak/`: the plugin.
  - `skills/` (engineering, start, commit, handoff, retro, learn);
  - `agents/` (code-reviewer, prompt-engineer);
  - `hooks/hooks.json` + `scripts/*.py`;
  - `templates/project/`;
  - `skills/start/references/stacks/` (stack guides);
  - `tests/`, `evals/`.
- `.claude-plugin/marketplace.json`: the marketplace. The plugin loads **in place**, so `/reload-plugins` applies edits.
- `docs/decisions.md`: the decision log. Do not reopen a decision without new evidence.
- `docs/architecture.md`: the design. `docs/notes/`: verified platform facts. `docs/inbox/`: proposals from projects (process them with `/inbox`).
- `STATE.md`: where work stands. `README.md`: install, use and safety coverage. `CHANGELOG.md`: releases.

## Hard rules
- **Verify stale-prone facts** (flags, settings keys, hook protocol, frontmatter) against the live docs, `code.claude.com/docs` (index `llms.txt`), or with the `claude-code-guide` agent. Label results ✅ / ⚠️ / ❓. When a guide and the docs disagree, the docs win.
- **"Works" means ran and passed.** Show the decisive output line.
- **Rules that must always hold are hooks, not skill text.** Every hook:
  - is Python 3 stdlib only;
  - has unit tests for block, allow and malformed input;
  - states what it does NOT cover.
  - Guards fail **closed** (exit 2). Stop and SessionStart hooks fail open, visibly.
- **Files** ≤ 200 lines, functions ≤ ~60, cognitive complexity ≤ 15; patterns are named constants with a comment saying why.
- **Distill, don't grow.** `tests/test_budgets.py` enforces size budgets for skills, agents, guides and templates. A new lesson replaces or merges older lines; raising a limit needs a recorded decision.
- **Model-invoked skills stay few and narrow;** commands are manual (`disable-model-invocation: true`). No top-level `bin/`.
- **`~/.claude/`:** read freely; write only after an explicit yes and a backup in `~/.claude/backups/`.
- **Never destructive commands;** move files to `_to_delete/` instead. Stage by explicit path. Never push without being asked.

## Change workflow
1. Branch for anything beyond a one-file fix.
2. Change, then run `python3 -m unittest discover -s plugins/ak/tests`, `claude plugin validate plugins/ak --strict` and `claude plugin validate . --strict`.
3. Bump `version` in `plugins/ak/.claude-plugin/plugin.json` (patch for fixes, minor for features) and add a `CHANGELOG.md` entry.
4. Commit (conventional message, explicit paths), then merge `--ff-only` into main after a yes.
5. Record new decisions in `docs/decisions.md`; update `STATE.md` with `/ak:handoff`.

## Gotchas learned here
- **Skill injection lines** (`` !`cmd` ``) are permission-checked before running. A shell variable such as `$f` or `$?`, or a read outside the project, silently aborts the whole skill. Use plain commands that end with `; true`.
- **`${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_SKILL_DIR}`** are substituted in SKILL.md and agent bodies, **not** in reference files. Pass paths from SKILL.md.
- **Reading plugin files** from a project needs `allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)`. Subagents cannot read them without a prompt, so paste the text into the delegation instead.
- **Plugin agents** report `agent_type` as `ak:<name>`; their `memory: user` folder is `~/.claude/agent-memory/ak-<name>/`. `disallowedTools` wins over `memory`, so read-only agents keep Write/Edit and are confined by `agent_write_guard.py`.
- **Inside the Bash sandbox:**
  - protected names (`.bashrc`, `.mcp.json`, `.claude/hooks`, …) appear as `/dev/null` devices, so `git add -A` fails;
  - `~/.claude` is not writable, so `claude plugin install/uninstall` and nested `claude -p` runs need `dangerouslyDisableSandbox` (the user approves).
- **`claude plugin eval`** needs API credits; the subscription does not cover it.
- **Exact allow rules only** (`Bash(pytest -q)`, not `Bash(pytest *)`): wildcards let flags like `--basetemp` or paths like `.env` through.
