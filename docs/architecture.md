# Architecture (Phase 2 draft, 2026-10-09)

Status: **approved 2026-10-09** (Q1–Q4 resolved as recommended). Facts come from `docs/notes/00–08`. Labels: ✅ verified, ⚠️ likely (test in Phase 3/4), ❓ open.

## 1. Shape

```
agentic-system/                         # git repo = marketplace "andrey-kit"
├── .claude-plugin/marketplace.json     # sources: ./plugins/<name>
├── plugins/
│   ├── ak/                    # user scope, always on
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/{engineering,start,handoff,retro}/SKILL.md (+ references/)
│   │   ├── skills/start/references/stacks/<stack>.md   # stack guides, read only by /start
│   │   ├── agents/{prompt-engineer,code-reviewer}.md
│   │   ├── hooks/hooks.json
│   │   ├── scripts/*.py                # hook scripts, stdlib only (no bin/)
│   │   ├── templates/project/          # copied/merged by /ak:start
│   │   └── tests/ evals/
│   └── (no stack plugins: dynamic per-project conventions, see §1a)
└── docs/{notes,guides,inbox}/ architecture.md decisions.md
```

### 1a. Dynamic stack support (amended 2026-10-10, replaces the four stack plugins)
- **Guides teach, projects decide.** A stack guide (≤ 80 lines: conventions, gotchas, checks, formatter) is general knowledge, read only during `/start`, so it has no session cost. `prompt-engineer` samples the repo's own code and writes the conventions it actually follows, with the guide as the fallback, as `.claude/rules/<area>.md` with `paths:` globs. The user approves each one.
- **Only "always" rules become hooks.** One generic `format_on_edit` hook formats edited files from a per-project `.claude/format.json`. `/start` writes it only for formatters installed on the machine.
- **New stack = one guide file.** `retro` improves guides centrally; existing projects pick up changes when `/start` offers a refresh.

A day in use:
1. Open Claude Code in a project.
2. SessionStart hook injects about 3 lines: is the project initialized, plus the head of `STATE.md`.
3. You type `/ak:start`.
   - **New project:** ≤6 questions → `prompt-engineer` drafts CLAUDE.md, rules and role agents → you approve each file as a diff → `.claude/format.json` for installed formatters → reminders to trust the folder and restart.
   - **Existing project:** reads `STATE.md`, `git log` since the last handoff and open TODOs → proposes the next step.
4. Work.
5. A Stop hook makes Claude call `code-reviewer` once per changed diff, and the main thread fixes the findings.
6. `/ak:handoff` before leaving updates `STATE.md`.

## 2. Components

| Component | Layer | Invocation | Why it exists | Reuses / replaces | Test |
|---|---|---|---|---|---|
| `engineering` skill (+ `references/code-quality.md`, `verification.md`) | core | model | Single source of truth for your working style (decision 3) | Migrates synced `andrey-engineering`; duplicate resolved in Phase 6 | `claude plugin eval`: ≥5 trigger / ≥5 no-trigger |
| `start` skill (+ `references/init.md`, `continue.md`, `roles.md`) | core | manual (`disable-model-invocation`) | Your "one command" entry point: init or continue | Replaces planned `project-init`; suggests bundled `/run-skill-generator` and doesn't rebuild it | `claude -p` on 2 fixture repos (empty, initialized): asserts files proposed, nothing overwritten |
| `handoff` skill | core | manual | Writes a ≤1-page `STATE.md` so continuing is cheap without old chat (notes/05) | None (Claude Code has no handoff file) | `claude -p` on fixture: STATE.md ≤60 lines, has Done/Next/Open |
| `prompt-engineer` agent | core | delegated by `start` | Drafts concise CLAUDE.md, rules and role agents (your request) | Its own isolated context keeps drafting noise out of main | Fixture: output under line limits, no duplication across layers |
| `code-reviewer` agent | core | Stop hook → delegated | Independent logic check on every change. Read-only; main thread fixes (decision, option 1) | Bundled `/code-review` and `engineering:code-review` run in main context, user-invoked. This agent is isolated and automatic, and preloads the `engineering` skill | Fixture diff with 5 planted bugs: ≥4 found |
| `guard.py` | core | PreToolUse `Bash` hook | Hard blocks + ask for flashing/removal (Autonomy_Balanced) | Ports `~/.claude/hooks/guard.py`, fixing fail-open and false positives | unittest: block / allow / malformed fixtures |
| `secret_scan.py` | core | PreToolUse `Bash` hook (acts only on `git commit`) | Blocks secrets and `.env` in staged diff | None | unittest: staged fixture repo with fake key → exit 2 |
| `review_gate.py` | core | Stop hook | Makes "reviewer always checks" true without your memory | None | unittest: diff unchanged → silent; changed → block once; `stop_hook_active` → silent |
| `session_context.py` | core | SessionStart hook | Cheap continuity: ≤1,500 chars of state | None | unittest: output length and content per fixture |
| Stack guides `start/references/stacks/<stack>.md` | core | read by `/start` only | General stack knowledge for generating project rules (§1a) | Replaces the four stack plugins | Trial: `/start` on one real repo per stack |
| `format_on_edit.py` hook | core | PostToolUse `Edit\|Write` | Auto-format with the project's own formatter, from `.claude/format.json` | Replaces per-stack formatter hooks | unittest + one trial on a branch |
| Project rules `.claude/rules/<area>.md` | project | load on matching `paths` | Conventions this repo actually follows | Generated by prompt-engineer; maintained by retro | Reviewed by you at creation (diff) |
| Project template | project | copied by `start` | Per-project differences live in the project | None | `start` fixture test above |
| Role agents (derived per project; e.g. frontend, backend, firmware) | project | delegated | Specialists per kind of work (your request); roles vary by project | Derived per project with the `roles.md` guide (method, required parts, safety defaults, examples); not shipped as plugin agents | Reviewed by you at creation (diff) |

Not built (reuse instead): debug → bundled `/debug`; manual deep review → `/code-review`; verify and run → `/verify`, `/run`, `/run-skill-generator`; architecture ADRs → `engineering:architecture`.

**Agent frontmatter policy:**
- **No `effort`:** your session choice applies (notes/05). ⚠️ Verify that inheritance with the logging hook.
- **No `model`:** inherit, except where a cheaper model is shown to be good enough.
- **Explicit `tools` lists.** `memory: project` for role agents.

## 3. Context budget (always-listed text)

| Item | Chars (est.) | Notes |
|---|---|---|
| `engineering` description | ≤400 | Model-invoked; must stay narrow enough to pass no-trigger evals |
| `start`, `handoff` | 0 ⚠️ | Manual skills; docs say the description isn't in context. Measure with `/context` |
| `prompt-engineer`, `code-reviewer` descriptions | ~2×250 | Agent budget (15k tokens), separate from the skills budget |
| Stack guides | 0 | Read only during `/start`; project rules load only for matching files |
| SessionStart injection | ≤1,500 | Once per session start or resume |
| **Total added per session** | **≈1.3k chars plus ≤1.5k injected ≈ 700 tokens** | |
| Removable today | ~470 | The synced `andrey-engineering` duplicate (Phase 6) |

Biggest existing cost is outside our control: the synced `anthropic-skills:*` (14) and `engineering:*` (10) descriptions. 📌 Phase 6: `skillOverrides: "off"` for unused synced skills, measured with `/context` before and after.

## 4. Hooks

| Hook | Event / matcher | Decision | Does NOT cover |
|---|---|---|---|
| `guard.py` | PreToolUse `Bash` | **deny** (exit 2): recursive or wildcard rm, find -delete, git clean/reset --hard/force push/`checkout -- .`, podman/docker prune/volume rm/rm -f, `chmod -R 777`, `curl\|wget … \| sh`, sudo, disk wipe. **ask**: plain rm/rmdir, espflash and serial devices, Bash writes outside project. Internal error → exit 2 | Commands inside scripts it runs, obfuscation (base64, eval, variables), Read/Edit tools, non-Bash MCP tools |
| `secret_scan.py` | PreToolUse `Bash`, acts on `git commit` | **deny** if staged diff matches secret patterns or adds `.env*`. Error → exit 2 | Secrets already committed, commits made outside Claude, custom formats not in patterns, `git commit -a` unstaged parts (⚠️ handle `-a` by scanning the working diff) |
| `review_gate.py` | Stop | **block once** per new diff hash (stored in `${CLAUDE_PLUGIN_DATA}`) with "delegate to code-reviewer, then fix" | Non-git dirs (skipped), changes made outside Claude, quality of the review itself. Fails **open** on error by design, so a broken gate can't trap the session |
| `session_context.py` | SessionStart `startup\|resume\|clear\|compact` | additionalContext ≤1,500 chars | Doesn't run `start` itself (❓ `initialUserMessage`, test in Phase 3). Fails open |
| `format_on_edit.py` | PostToolUse `Edit\|Write` | none (formats per `.claude/format.json`) | Files changed via Bash; formatters not installed; projects without `format.json` |

Limits stated in README: hooks and rules are not a security boundary. The real safety net is git with commits per step, plus branches or worktrees for risky work (Autonomy_Balanced).

## 5. Per-project template (`templates/project/`)

- `CLAUDE.md` skeleton (<100 lines, copied into every subagent):
  - Project and goal;
  - Stack;
  - Commands (run/test/lint);
  - Must-know rules;
  - Agents;
  - "Update STATE.md via `/ak:handoff`".
- `.claude/settings.json` (Balanced):
  - `defaultMode: acceptEdits`;
  - no `enabledPlugins` (ak is enabled at user scope; stacks are dynamic, §1a);
  - `allow`: stack checks only;
  - `ask`: `rm`, `rmdir`, `mv`, `cp`, `sed`, `git push`, `espflash` (ask beats the mode **and** any later "always allow");
  - `deny`: `Read` of `.env*`, keys and keystores.
  - Other Bash prompts by default in `acceptEdits`, so it needs no rules.
- `.claude/rules/` with `paths:`: conventions specific to this project, written with prompt-engineer.
- `STATE.md` at the project root (see Q3): Done / Next / Open / Decisions, ≤60 lines.
- `.gitignore` additions: `.env*`, `.claude/settings.local.json`, `CLAUDE.local.md`, `.claude/agent-memory-local/`.

`start` never overwrites. Existing files get a proposed diff; you accept or reject each.

## 6. Versioning and updates

- Semver `version` in each `plugin.json`, starting at `0.1.0`. A root `CHANGELOG.md` has one section per plugin.
- During development the local marketplace loads plugins in place, so no bump is needed; `/reload-plugins` picks up changes. A bump is needed only for releases to a remote or copied install.
- Before each release:
  - `claude plugin validate --strict` on every plugin;
  - all hook unit tests;
  - evals for changed skills.
- Phase 7: on a new Claude Code release, re-verify the affected notes, run `/doctor prompt-audit`, bump the version.

## 7. Resolved questions (owner chose the recommendations, 2026-10-09)

Custom commands: owner wants more typed commands. They are manual skills (`disable-model-invocation: true`, no listing cost). The list is chosen in Phase 6. ⚠️ Check whether typing `/start` finds `/ak:start` in the menu.


- **Q1.** Split Rust into `andrey-tauri` and `andrey-esp32`? Overlap is only rustfmt/clippy. Tauri adds a web frontend; ESP32 adds `no_std`, esp-hal and espflash. Recommended: split.
- **Q2.** Writes outside the project. CLAUDE.md says "hard block". Today Edit/Write outside the project already prompts (acceptEdits only covers the project), and guard **asks** for Bash writes outside. Recommended: ask, not block. Phase 6 needs writes to `~/.claude`, and you approve each one.
- **Q3.** State file `STATE.md` at the project root, not under `.claude/`. Writes in `.claude/` may prompt as a protected path ⚠️. Recommended: root.
- **Q4.** `handoff` as its own manual skill, instead of `start` doing it. Recommended: separate. It's one command when you leave, and costs zero listing.
