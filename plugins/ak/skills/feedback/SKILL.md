---
name: feedback
description: Draft a feedback issue for the ak plugin from this session (what worked, what broke, ideas), redacted for privacy. The user reviews it and submits it themselves; nothing is sent automatically.
disable-model-invocation: true
argument-hint: "[what to report]"
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# Feedback

## Facts (collected before you read this)
- ak version: read `"version"` from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`
- OS: !`uname -sr 2>/dev/null; true`
- The user's note: $ARGUMENTS

## 1. Decide what to report
If the note is empty, ask one question (AskUserQuestion): **Something broke** / **Worked well** / **Idea** / **Retro lesson**, plus which command or component. Use this session as the evidence: commands run, decisive output lines, hook messages, review findings.

## 2. Draft the issue
Match the fields of the repo's issue form:
- **Kind**;
- **Command or component**;
- **What happened** (steps, plus the decisive output line quoted);
- **What you expected**;
- **Proposed fix** (optional, in the form Evidence → Root cause → Fix → Verify);
- **Versions** (ak, Claude Code if known from this session, OS).

Title: `[feedback] <short summary>`.

## 3. Redact before showing it
Remove or generalize:
- secrets and tokens;
- emails;
- absolute paths (use `~/…` or `<project>/…`);
- hostnames;
- client and project names;
- source code beyond a minimal snippet.
Say what you redacted in one line.

## 4. Hand it to the user
Show the draft. Then give the link to open the form, where the user pastes and submits:
`https://github.com/Andrey99-art/smart-agentic-system/issues/new?template=feedback.yml`
**Never** submit it yourself: no `gh issue create`, no network calls. Sharing is the user's decision.
