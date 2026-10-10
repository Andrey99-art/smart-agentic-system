---
name: learn
description: Explain a Claude Code feature, command, flag or setting in a few lines, verified against the live docs today, with the 2–3 commands worth knowing.
disable-model-invocation: true
argument-hint: "<topic>"
allowed-tools: WebFetch(domain:code.claude.com), Read(~/.claude/settings.json)
---

# Learn

Topic: $ARGUMENTS

Claude Code changes weekly, so answer from the **live docs, never from memory**.

1. If the topic is empty, ask one question: what to learn.
2. Find it: start at `https://code.claude.com/docs/llms.txt` (the index), then fetch the page or pages that cover the topic. If a `claude-code-guide` agent is available, one delegation to it is fine instead.
3. Answer in the user's language, in at most 15 lines:
   - **What it is**: 1–2 sentences.
   - **When to use it**: 1–2 sentences, tied to the user's setup (VS Code and CLI on Fedora, the `ak` plugin) when relevant.
   - **Commands / keys**: 2–3 lines, one-line explanation each.
   - **Gotcha**: one line, only if there is a real one.
   - **Source**: the doc URL, marked "✅ verified today".
4. If the docs do not cover it, say so plainly (❓) instead of guessing.
5. **Check against the user's setup.** When the topic involves settings, read the user's actual values (`~/.claude/settings.json`, the project's `.claude/settings.json`). If a docs recommendation conflicts with a deliberate choice, say so and do not recommend changing it. Example: ak keeps `sandbox.autoAllowBashIfSandboxed: false` so the sandbox adds no auto-approvals.
6. End with at most one offer, e.g. "Want to try it in this project?"
