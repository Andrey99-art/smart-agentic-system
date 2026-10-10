# 02 — Skills

Source: live docs, fetched 2026-10-08. Base URL: https://code.claude.com/docs/en/skills

## Facts we use
- ✅ **Plugin skills.**
  - A skill lives at `<plugin>/skills/<name>/SKILL.md` and is invoked as `/<plugin>:<name>`, so it never collides with personal or project skills. [#where-skills-live](https://code.claude.com/docs/en/skills#where-skills-live)
  - The folder name `synced` and the namespace `anthropic-skills` are reserved.
- ✅ **Precedence:** enterprise > personal `~/.claude/skills/` > project `.claude/skills/`. A skill beats a `commands/` file with the same name.
- ✅ **Frontmatter we'll use** ([#frontmatter-reference](https://code.claude.com/docs/en/skills#frontmatter-reference)):
  - `description` (front-load the trigger) and `when_to_use` (appended to it in the listing);
  - `disable-model-invocation: true` makes a skill manual-only, with no listing cost for auto-triggering;
  - `paths` restricts auto-activation to matching files, which suits stack conventions;
  - `allowed-tools` pre-approves tools for the invoking turn only;
  - `argument-hint` and `arguments` define parameters.
  - Also available: `context: fork` with `agent` (runs in a subagent), and `hooks` (active from invocation until the session ends).
- ⚠️ **Portability.** Outside Claude Code (claude.ai, the Skills API), only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools` are valid. Other keys are a hard error.
- ✅ **Size.** Keep SKILL.md under 500 lines. Detail goes into linked sibling files that load on demand. `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PLUGIN_ROOT}` point to bundled scripts. [#add-supporting-files](https://code.claude.com/docs/en/skills#add-supporting-files)
- ✅ **Arguments.** `$ARGUMENTS`, `$0..$N` and `$name`. If no placeholder is used, the arguments are appended.
- ✅ **Dynamic context.** `` !`cmd` `` runs before Claude reads the skill.
  - A non-zero exit aborts the whole invocation.
  - A deny rule also aborts it.
  - Turn it off with `disableSkillShellExecution`.
  - [#inject-dynamic-context](https://code.claude.com/docs/en/skills#inject-dynamic-context)
- ✅ **Budget.** Descriptions share 1% of the context window, and each is capped at 1,536 chars. Overflow drops the least-used descriptions first. Check with `/context` (Skills row), `/doctor` and `/skill-doctor` (v2.1.252+, and we have 2.1.287). [#skill-descriptions-are-cut-short](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short)
- ✅ **Reload.**
  - SKILL.md edits are picked up live.
  - A new skills directory needs `/reload-skills`.
  - Plugin hooks and agents need `/reload-plugins`.
  - [#live-change-detection](https://code.claude.com/docs/en/skills#live-change-detection)
- ✅ **Cloud/Cowork** sessions don't read `~/.claude/skills/` or plugins that are enabled only in user settings. This confirms the README caveat in CLAUDE.md.
- ✅ **Testing.**
  - `claude plugin eval` compares against a baseline run without the plugin.
  - Trigger checks use a `tool_used: Skill` grader.
  - `claude plugin validate` catches bad frontmatter.
  - skill-creator's `evals.json` is a different, incompatible format.
  - ❓ The eval page itself (`/docs/en/plugin-evals`) is still unread, so I'll read it before Phase 4.

## Impact on design
- **Core skill** becomes `/andrey-core:engineering`. While the synced `anthropic-skills:andrey-engineering` stays enabled, both descriptions are listed, so you pay twice. Phase 6 resolves this, and `skillOverrides: "off"` is one option.
- **Stack conventions:** a skill with `paths` globs (e.g. `**/*.py`, `**/*.kt`) stays quiet in other repos. `project-init` is manual and can use `` !`ls` `` to read the repo state safely.
- **Shared frontmatter:** if a skill should also work on claude.ai, it may use only the portable keys. Otherwise we use Claude Code keys freely.

## Commands you'll use
- `/context` shows what fills the context, including the Skills row.
- `/skill-doctor` finds skills that are unused or have weak descriptions.
- `/reload-plugins` applies plugin hook and agent changes without a restart.
