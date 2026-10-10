---
name: publish
description: Prepare a public release of this repo. Audit main for secrets and personal data, then add main's current files to the history-free `public` branch as one noreply commit. The user pushes.
disable-model-invocation: true
argument-hint: "[commit subject]"
---

# Publish

`main` keeps the private history (personal email in commit headers). `public` is a separate history with only noreply-authored snapshot commits; GitHub `main` tracks it.

## 1. Audit main (all must be clean; show each count)
- Tracked tree is committed: `git status --short` shows no ` M` or `A ` lines (sandbox `??` placeholders don't matter).
- Secrets: `git grep -nE "AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9_-]{20}|gh[pousr]_[A-Za-z0-9]{36}|xox[abprs]-[A-Za-z0-9-]{10}"` finds nothing.
- Personal data in files: with `PRIVATE=$(git log -1 --format=%ae main)` (the private author email; never write it into any file), `git grep -n -e "/home/" -e "$PRIVATE" -e "${PRIVATE%@*}"` finds nothing.
- Tests and validation pass: `python3 -m unittest discover -s plugins/ak/tests`, `claude plugin validate plugins/ak --strict`, `claude plugin validate . --strict`.

Stop and report if anything fails.

## 2. Snapshot onto `public` (never touches the working tree)
Write the message (subject: the argument, or the latest main subject; plus the attribution trailer) to `$TMPDIR/publish-msg.txt`, then run:
```
NEW=$(GIT_AUTHOR_NAME=Andrey99-art GIT_AUTHOR_EMAIL=211805472+Andrey99-art@users.noreply.github.com GIT_COMMITTER_NAME=Andrey99-art GIT_COMMITTER_EMAIL=211805472+Andrey99-art@users.noreply.github.com git commit-tree "main^{tree}" -p public -F "$TMPDIR/publish-msg.txt") && git update-ref refs/heads/public "$NEW"
```
Do **not** use `git checkout main -- .` (the guard blocks it, rightly: it can discard uncommitted work).

## 3. Verify, then hand over
- `git diff --stat main public` is empty.
- `git log -p public | grep -c "${PRIVATE%@*}"` is `0` (headers and content).
- Show `git log --oneline -3 public`, then tell the user to run, in their own terminal: `git push origin public:main`. Never push yourself.
