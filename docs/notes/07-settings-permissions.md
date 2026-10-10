# 07 — Settings and permissions

Source: live docs, fetched 2026-10-09. [settings](https://code.claude.com/docs/en/settings), [permissions](https://code.claude.com/docs/en/permissions), [permission-modes](https://code.claude.com/docs/en/permission-modes), [sandboxing](https://code.claude.com/docs/en/sandboxing)

## Facts we use
- ✅ **Precedence:** managed > `--settings` > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`. ❓ Whether arrays merge across scopes is unconfirmed; check with `/permissions`.
- ✅ **Rule order is deny → ask → allow,** and the first match wins. An allow can't override a deny. A hook's `allow` doesn't skip deny or ask rules, and a hook's exit 2 blocks before any rule runs. [permissions#manage-permissions](https://code.claude.com/docs/en/permissions#manage-permissions)
- ✅ **Bash rule syntax.**
  - `Bash(git status *)` also matches bare `git status`.
  - Compound commands (`&&`, `;`, `|`, …) are split, and **every part** must be allowed.
  - Wrappers like `timeout` and `nice` are stripped before matching.
  - [#compound-commands](https://code.claude.com/docs/en/permissions#compound-commands)
- ⚠️ **Rules are text matches.** `Bash(git push *)` does **not** catch `git -C . push`. The hook's regex (with git global options) and the sandbox close that gap.
- ✅ **Path rules.** `//abs` is absolute, `~/` is home, `/x` is relative to the settings file, `./x` is relative to cwd. They use gitignore syntax, so `.env` matches at any depth.
- ⚠️ **`acceptEdits` is broader than "edits".** It also auto-approves `mkdir`, `touch`, **`rm`, `rmdir`, `mv`, `cp`, `sed`** inside the project. Other Bash still prompts. [#auto-approve-file-edits-with-acceptedits-mode](https://code.claude.com/docs/en/permission-modes#auto-approve-file-edits-with-acceptedits-mode)
- ✅ **Built-in read-only commands need no rules:** `ls`, `cat`, `grep`, `find`, `diff`, read-only `git` and similar. Some combinations still prompt, such as `cd` followed by `git`. [#read-only-commands](https://code.claude.com/docs/en/permissions#read-only-commands)
- ✅ **Mode settings.** `permissions.defaultMode` sets the starting mode. Project settings can't set `auto` or `bypassPermissions`. Turn off bypass with `disableBypassPermissionsMode: "disable"`.
- ✅ **Sandbox** (`sandbox.enabled`, or `/sandbox`).
  - On Linux it needs `bubblewrap` and `socat`.
  - It covers only Bash, not Read/Edit or hooks.
  - Network is closed by default, and `~/.ssh` stays readable unless you add `filesystem.denyRead`.
- ✅ **Trust.** Project allow rules apply only after you trust the workspace. `settings.local.json` needs no trust.
- ✅ **Other keys we use:** `env`, `attribution` (replaces the deprecated `includeCoAuthoredBy`), `autoMemoryEnabled`, `promptCacheTtl`, `skillOverrides`, `cleanupPeriodDays` (default 30).

## Environment check (2026-10-09)
- ✅ `bwrap` installed. ✅ `socat` **missing**, so the sandbox can't run yet. Fix with `sudo dnf install socat` (needs a yes).

## Impact on design
- **Balanced template:**
  - `defaultMode: acceptEdits`;
  - allow-list only the stack checks (`cargo check *`, `python manage.py check *`, …), since read-only commands are built in;
  - ask for git writes, network, `podman` and installs.
- **Keep the `rm`/`rmdir` deny rules.** Without them, `acceptEdits` deletes single files silently. Your user settings already have them. The template states this requirement, and the guard hook backs it up.
- **The hook remains the main guard against bypasses** (`git -C`, quoting tricks). The sandbox is an optional extra for Phase 6, after `socat` is installed. It would conflict with podman and network use ❓, so test it before enabling.
- **First run of a new project:** `start` reminds you to trust the folder, or the project allow rules won't apply.

## Commands you'll use
- `/permissions` shows every rule in effect and which file it came from.
- `Shift+Tab` cycles Manual → acceptEdits → plan.
- `/sandbox` turns the Bash sandbox on or off once `socat` is installed.
