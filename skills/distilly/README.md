# Distilly

`distilly` turns what you know about a person into a reusable skill that thinks and answers the way they do. It handles three kinds of people:

| Kind | From | You get |
|---|---|---|
| Public figures (authors, founders, thinkers) | Their writing, interviews and talks, researched on the web along six lines: works, conversations, phrasing, outside views, decisions, timeline | Their mental models, decision rules and voice, with sources |
| Colleagues and mentors | Messages, documents and notes you provide (it can collect from Slack, Lark and DingTalk) | How they work, their standards and judgment, as a work skill plus persona |
| People you know | Chat exports and notes you provide | How they talk, what sets them off, how they make up |

Its instructions are in English, and it replies in the language you write in.

## Install

1. Install the skill from the repo root:

   ```bash
   npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/distilly
   ```

    Swap `--targets` for your tools. To keep it in your regular install, add `skills/distilly` to `inputRoots` in your `rulesync.local.jsonc`.

2. Set up Python with uv in the installed skill folder. For OpenCode:

   ```bash
   cd ~/.config/opencode/skills/distilly
   uv venv .venv
   uv pip install --python .venv/bin/python -r requirements.txt
   source .venv/bin/activate
   ```

   For another assistant, use its installed Distilly folder instead. Run its
   Python helpers from the activated environment. Start your coding tool from
   that shell so child processes inherit it, or invoke helpers explicitly with
   `.venv/bin/python`; shell activation may not persist between agent tool calls.
   Distilly ships scripts and
   requirements files rather than an installable CLI package, so a local venv
   fits better than `uv tool install`.

3. Only if you need the Slack, Lark or DingTalk collectors, install their extras
   into the same environment:

   ```bash
   uv pip install --python .venv/bin/python -r requirements-optional.txt
   ```

   Browser-based collectors also need their browser runtime set up separately.
   Recheck requirements after updating the skill. These commands install Python
   dependencies; rulesync itself only copies the skill and helper files.

## Use

- "Distill Paul Graham", "make a skill of how Richard Feynman thinks" (public figure, researched for you)
- "Make a skill of my old manager from these Slack exports" (colleague, from your material)
- "I have new material on Feynman" or "he wouldn't say that": it updates and corrects an existing profile
- "Show my skills", or roll one back or delete it

New skills are saved under `./skills/<kind>/<name>/` in the folder you're working in, through its own `tools/skill_writer.py`. Use one with `/<kind>-<name>` or by asking for that person's view.

Credentials for the message collectors never go through the conversation: you run each collector's `--setup` or `--login` in your own terminal.

"Set up my profile" interviews you so a personal agent knows who it works for. That only supports Claude Code, and it writes a short summary between markers into `~/.claude/CLAUDE.md`. Installing rules from this repo for Claude Code replaces that file, so set the profile up after installing, and again after each reinstall.

## Origin

[titanwings/distilly](https://github.com/titanwings/distilly) (formerly colleague-skill): `SKILL.md`, `prompts/`, `tools/` and the two requirements files from the repo root, which is what its npm package ships as the skill. Commit `0afc45c29c360ba7bc8260f1bb0bf34e9155f4fa`, copied 2026-10-14. One change: its Claude Code-only settings (`argument-hint`, `user-invocable`, `allowed-tools`) moved under `claudecode:` so rulesync keeps them. [MIT](../../THIRD_PARTY_LICENSES.md#titanwingsdistilly), © 2026 titanwings. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
