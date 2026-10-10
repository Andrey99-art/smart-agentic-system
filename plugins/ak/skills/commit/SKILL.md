---
name: commit
description: Commit the current work. Stages files by explicit path, shows what goes in, writes a conventional message and commits after the user's yes. Never pushes.
disable-model-invocation: true
argument-hint: "[hint for the message]"
---

# Commit

## Facts (collected before you read this)
- Branch: !`git branch --show-current 2>/dev/null; true`
- Changes: !`git status --short 2>/dev/null | head -40; true`
- Already staged: !`git diff --cached --stat 2>/dev/null; true`
- Recent messages (match their style): !`git log --oneline -5 2>/dev/null; true`
- Hint from the user: $ARGUMENTS

## 1. Choose the files
- Take the work of this step: files changed in this session, or ones the user names. Unrelated changes → propose separate commits.
- **Never stage:**
  - `.env*`, keys and credentials;
  - build output and caches;
  - large binaries (unless the user asks).
  - **Sandbox placeholders:** inside the Bash sandbox, paths such as `.bashrc`, `.zshrc`, `.profile`, `.mcp.json`, `.gitconfig` and `.claude/hooks` can show up as untracked entries. They are `/dev/null` devices that exist only inside the sandbox. Before staging an unexpected untracked path, check it with `test -f <path>`; skip anything that is not a regular file.
- Stage only by explicit path: `git add <path> …` (or `git add -u` for tracked files only). Never `git add -A` or `git add .`.

## 2. Write the message
- Conventional Commits: `type(scope): summary`, at most 72 characters, imperative mood, English.
- Body only when the *why* is not obvious: 1–3 lines.
- Add the attribution trailer only if the session's instructions require one.

## 3. Confirm, then commit
1. Show the file list and the message. AskUserQuestion: **Commit** / **Change message** / **Cancel**.
2. On Commit: `git add <paths>`, then `git commit -m "<subject>" -m "<body>"`. Use `-m` flags, not `-F $TMPDIR/...`: commands with shell variables are rejected by the permission pre-check.
3. If a hook blocks the commit (for example the secret scan), show its reason and stop. Never use `--no-verify`, never amend unless asked, **never push**.
4. Report in one line: short hash and subject.
