# Init flow — set up a project

Paths below ("Templates", "Role guide", "Stack guides") are the ones listed in SKILL.md.

## 1. Read before asking (no questions yet)
- Manifests that exist: `pyproject.toml`, `requirements*.txt`, `manage.py`, `package.json`, `Cargo.toml`, `src-tauri/`, `build.gradle(.kts)`, `.cargo/config.toml`; README (first 40 lines); `git log --oneline -5`; `git remote -v`.
- Detect the stack:
  - **django**: `manage.py`, or `django` in requirements/pyproject.
  - **android**: `build.gradle(.kts)` with an Android plugin, or `AndroidManifest.xml`.
  - **tauri**: `src-tauri/`, or `tauri` in `Cargo.toml`.
  - **esp32**: `esp-hal`/`esp-idf` in `Cargo.toml`, or `espflash` in `.cargo/config.toml`.
  - Several match → ask which is primary. Nothing matches (empty repo) → ask.
  - A stack without a guide in Stack guides still works: drafting then relies on the repo's own code alone. Say so, and suggest `/ak:retro` later to add a guide.

## 2. Ask (AskUserQuestion, ≤ 6 questions in total, up to 4 per call)
Ask only what step 1 could not answer:
1. **Goal**: what the project is for, 1–2 sentences (skip if the README states it).
2. **Stack**: only if not detected.
3. **Roles** (multi-select): derive roles from this project's work using the Role guide (§1). They are not a fixed list. Propose 2–3 with one-line reasons, recommended first; the user may rename, add or drop any. More than 4 needs a stated reason, because each agent costs a cold-cache spawn.
4. **Git policy**: remote and branching (feature branches? commit after each accepted step?), only if unclear from `git remote -v`.
5. **Never automate**: anything beyond the defaults (flashing, deploys, production migrations, …).
6. **Constraints** worth knowing: deadline, hosting, client rules. Optional; skip when the user is brief.

## 3. Draft (one delegation)
Delegate once to `ak:prompt-engineer` with: goal, stack, all answers, the list of existing setup files, chosen roles, and the **full text** of the Role guide, of the stack's guide (if one exists) and of `Templates/CLAUDE.md.template` (the skeleton; the project file is named `CLAUDE.md`). Paste the text: the agent cannot read plugin files without a permission prompt. Ask for drafts of: CLAUDE.md, `.claude/rules/<area>.md` files derived from the repo's **actual code** (the stack guide says what to look for; the code decides), and one agent per chosen role.

## 4. Approve each file
For every draft, in this order: each agent → rules → CLAUDE.md (CLAUDE.md lists the agents, so it comes last).
- If a role is rejected, remove its references from the remaining drafts and reassign its owned paths to the closest remaining role; show those edits in the diffs that follow.
- Show the path and the full content (or a diff if the file exists).
- AskUserQuestion: **Accept** / **Change** (the user says what) / **Reject**.
- Write only accepted files. Apply requested changes yourself, then show them again.

## 5. Settings, ignore list, state
- **`.claude/settings.json`**: start from `Templates/settings.json`.
  - Add the stack's `allow` entries from `Templates/stack-allow.json`.
  - If the file exists: merge, keeping all of the user's entries and never removing anything.
  - Show the diff and write it after a yes.
- **`.claude/format.json`**: only for a formatter the stack guide names **and** that runs on this machine (check its `--version` first). Example: `{"**/*.py": ["uv", "run", "ruff", "format"]}`. The `format_on_edit` hook accepts only its exact allowed commands. Show it and write it after a yes; skip it when no formatter qualifies.
- **`.gitignore`**: append the missing lines from `Templates/gitignore-additions`: the "always" block plus the `# stack: <stack>` block for the detected stack (diff, then a yes).
- **`STATE.md`**: fill `Templates/STATE.md`:
  - Goal;
  - Next: the first concrete step;
  - Decisions: from the answers.
  - Show it and write it after a yes.

## 6. Finish
- Offer one commit of the setup files (`chore: set up project for andrey-kit`). Git writes ask anyway; never push.
- Tell the user, only the items that apply:
  - New `.claude/agents/` folder → **restart once**: CLI `claude --continue`; VS Code: open a new Claude session. New agents load only after a restart.
  - Project settings apply after the workspace is **trusted** (Claude Code asks on the next start).
  - Record how to run and verify the app: suggest `/run-skill-generator`.
- End with the three-line summary from SKILL.md.
