# teach

`teach` runs a course over several sessions. It treats the folder you start it in as a teaching workspace and keeps your progress there, so each session picks up from the last:

| File or folder | What it holds |
|---|---|
| `MISSION.md` | Why you want to learn the topic. Every lesson ties back to it |
| `RESOURCES.md` | Trusted sources and communities it found for the topic |
| `lessons/*.html` | Short, self-contained lessons, each with one tangible win |
| `reference/*.html` | Cheat sheets and glossaries distilled from the lessons |
| `learning-records/*.md` | What you've learned, used to pick the next lesson |
| `assets/` | Shared styles and quiz widgets the lessons reuse |
| `NOTES.md` | Your stated preferences about how you want to be taught |

It researches before it teaches, uses retrieval practice and spacing, and points you to communities for real-world practice. It only runs when you call it.

## Install

From the repo root:

```bash
npx rulesync@38.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/teach
```

Swap `--targets` for your tools. The `default`, `work` and `writing_reporting` groups include it. The skill's `*-FORMAT.md` files must stay beside `SKILL.md`; rulesync copies them.

## Use

Make a folder for the topic, start your coding tool there, and run:

- `/teach Rust ownership`
- `/teach` with no topic to continue the course already in the folder

It writes into the current folder, so don't start it in a project you don't want lesson files in. It opens lessons in a browser when it can; your [preferences rule](../../rules/preferences/) says Firefox.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): it's user-invoked only (`disable-model-invocation`), so the model never chooses it and a routing line would only cost tokens (removed 2026-10-24). Its lessons are its own pages, not `visual-explainer`'s; the skill's text says so once invoked.
- It does not own one-off teaching: explaining one unfamiliar thing in a single sitting is `eli5`. Its lesson and reference pages are its own output; don't hand them to `visual-explainer`.
- Why: added on 2026-10-21 after an overlap check. `eli5` was the only neighbor; it teaches one subject in one conversation or page, while `teach` keeps state across sessions, so the user approved both.
- Its research follows the web-research rule (Exa `search` for discovery). Opening a lesson follows the preferences rule.
- The skill is user-invoked only (`disable-model-invocation: true`, kept under the `claudecode:` and `opencode:` sections). Don't remove it.
- On upstream updates, copy the whole folder unchanged, including every `*-FORMAT.md` file, keep the tool sections, and record the new commit below. Don't edit the upstream text to change routing. If the new description claims a job another skill owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

[mattpocock/skills](https://github.com/mattpocock/skills), path `skills/productivity/teach/`, commit `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, copied 2026-10-21. Unchanged except that `disable-model-invocation` and `argument-hint` moved from the top-level frontmatter into the `claudecode:` (both) and `opencode:` (`disable-model-invocation`) sections. [MIT](../../THIRD_PARTY_LICENSES.md#mattpocockskills), © 2026 Matt Pocock. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
