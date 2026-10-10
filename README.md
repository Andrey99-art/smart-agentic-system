# andrey-kit

A personal Claude Code system, built for daily freelance work and shared as-is: one local marketplace (`andrey-kit`) with one plugin (`ak`). It provides a guided project workflow, review agents, and layered safety. Each project gets its own conventions, generated from its real code.

## Daily use

```
/ak:start          set up a new project, or continue from STATE.md
                   (while you work: guard, sandbox, auto-review and auto-format run on their own)
/ak:commit         explicit staging, conventional message, commits after your yes, never pushes
/ak:handoff        save STATE.md before leaving
/ak:retro          turn lessons into fixes; general ones go to docs/inbox/ here
/ak:learn <topic>  any time: an answer verified against today's live docs
/ak:feedback       draft a redacted feedback issue for this plugin; you submit it yourself
```
Back within an hour? `claude --continue` reuses the warm cache and is cheaper than a fresh start.

## Install on a new machine

Requirements: Claude Code, `git`, Python ≥ 3.13 (system `python3`; hooks run outside any venv), and `bubblewrap` and `socat` for the sandbox (`sudo dnf install bubblewrap socat`).

```
git clone <this repo> ~/dev/agentic-system
claude plugin marketplace add ~/dev/agentic-system
claude plugin install ak@andrey-kit
```
The plugin loads **in place** from `plugins/ak`, so edits apply after `/reload-plugins` with no reinstall.

Recommended user settings (`~/.claude/settings.json`). Back up the file first:
- `"sandbox": { "enabled": true, "autoAllowBashIfSandboxed": false, "failIfUnavailable": true, "excludedCommands": ["podman *"], "filesystem": { "denyRead": ["~/.ssh", "~/.aws", "**/.env", "**/.env.*", …] } }`. **Keep `autoAllowBashIfSandboxed: false`**: the default `true` silently approves every sandboxed command.
- `rm *` and `rmdir *` under `permissions.ask`, not `deny`, so they ask instead of always failing.
- `"skillOverrides": { "anthropic-skills:andrey-engineering": "off" }`, if the claude.ai-synced copy exists; `ak:engineering` replaces it in Claude Code.

## Make it yours
- **Profile:** edit the "Profile" block at the top of `plugins/ak/skills/engineering/SKILL.md` (your languages, explanation style, build and flashing habits).
- **Stack defaults:** `plugins/ak/skills/start/references/stacks/*.md` (Django defaults to uv) and `plugins/ak/templates/project/stack-allow.json` (commands that run without asking).
- **Safety and settings:** the sandbox and permission examples above; turn the review gate off for one session with `AK_REVIEW_GATE=off`.
- Then run the tests (see Maintain). Your edits load in place after `/reload-plugins`.

## Per project
`/ak:start` in a new or existing repo:
1. It reads the repo and asks at most 6 questions.
2. `ak:prompt-engineer` drafts the project files: `CLAUDE.md`, `.claude/rules/*.md` (conventions taken from the code), role agents in `.claude/agents/`, Balanced `.claude/settings.json`, `.claude/format.json` (only for installed formatters), `.gitignore` additions and `STATE.md`.
3. You accept, change or reject each file; nothing is overwritten without a diff.

After setup, trust the folder when Claude Code asks, and restart once so the new agents load. Stack knowledge lives in `plugins/ak/skills/start/references/stacks/`; Django exists, and other stacks get a guide when their first real project arrives.

## What protects you, and what does not

| Layer | Blocks or asks | Does NOT cover |
|---|---|---|
| `guard.py` (Bash) | Blocks: recursive or wildcard `rm`, `git clean`, `reset --hard`, force push, `checkout -- .`, podman/docker prune and volume rm, `chmod -R 777`, `curl … \| sh`, `sudo`, disk tools. Asks: plain `rm`/`rmdir`, `espflash`, serial ports, `cargo run` with an espflash runner, writes outside the project. Fails closed. | Code inside scripts it runs, obfuscated commands, non-Bash tools |
| `secret_scan.py` | Blocks `git commit` with keys, tokens, hard-coded credentials, or `.env`/key files staged | Secrets already in history; commits made outside Claude |
| `agent_write_guard.py` | Read-only agents can write only their own memory folder | Writes through Bash (those prompt under Balanced) |
| `review_gate.py` | Before finishing, asks for one `ak:code-reviewer` pass per changed file (at most 3 per file per session) | Non-git folders, docs-only changes, the quality of the review |
| `format_on_edit.py` | Formats edited files with exact allow-listed formatter commands from `.claude/format.json` | Files changed by Bash; formatters not installed |
| `session_context.py` | Adds ≤ 1,500 chars of project status at session start | Does not start `/ak:start` by itself |
| Permission rules | Balanced: edits automatic; `rm`, `mv`, `cp`, `sed`, `git push`, installs, network and most shell commands ask | Rules match text, so `git -C . push` slips past `Bash(git push *)` (the guard catches it) |
| Bash sandbox | Shell commands write only to the project and temp folders, cannot read secrets, and need approval for each new network domain | Excluded `podman`; Read/Edit/Write tools; MCP servers |

None of this is a security boundary on its own. **The real safety net is git**: commit after each step, and use branches or worktrees for risky work.

## Limits
- User-scope plugins do not load in claude.ai cloud sessions or Cowork; this setup is for local VS Code and CLI.
- `claude plugin eval` needs API credits, so the `ak:engineering` skill's triggering is unverified (the suite is in `plugins/ak/evals/`).
- Inside the sandbox, `git add -A` fails on placeholder device files; stage by path (`/ak:commit` does).
- Git config changes (`git remote add`, `git config`) fail inside the sandbox by design; run them yourself or approve an unsandboxed run.

## Maintain
- Tests: `python3 -m unittest discover -s plugins/ak/tests`. Validate: `claude plugin validate plugins/ak --strict` and `claude plugin validate . --strict`.
- Proposals from projects land in `docs/inbox/`; process them with `/inbox` in this repo.
- Releases: bump `version` in `plugins/ak/.claude-plugin/plugin.json` and add a `CHANGELOG.md` entry.
- Design and history: `docs/architecture.md`, `docs/decisions.md`, `docs/notes/`.

## Feedback
Run `/ak:feedback` in Claude Code. It drafts an issue from your session, redacts secrets, paths and project names, and gives you the link to the [feedback form](https://github.com/Andrey99-art/smart-agentic-system/issues/new?template=feedback.yml). Nothing is sent automatically: you review the draft and submit it yourself. The plugin collects no usage data.

## License
Apache-2.0, see [LICENSE](LICENSE). You may use, modify and share it with attribution. The license includes a patent grant from contributors.
