# permission-tuning

A skill for tuning OpenCode permissions without giving up security, and a rule that holds the shell habits that keep permission rules matching. The skill covers the workflow (evidence, classification, root cause, lowest-risk fix, review, canaries), what never to allowlist, and how to audit saved "Always" approvals. The rule tells the agent to write recognizable commands and to load the skill when the same prompt keeps coming back.

| File | What it is |
|---|---|
| `skills/permission-tuning/SKILL.md` | The tuning workflow and the verified facts about OpenCode V2 permissions |
| `rules/shell-habits.md` | The shell habits, plus the instruction to load the skill after more than three repeated prompts |

## Install

This folder is for the `ai_research` folder group, not for your home folder. The rule lands in the folder's own `AGENTS.md`, so it only applies when you start your tool there. From the repo root:

```bash
mkdir -p ~/AI/ai_research
npx rulesync@41.0.0 generate --config groups/ai_research.jsonc --output-roots ~/AI/ai_research
```

Never add `--global`. The `default`, `work` and `writing_reporting` groups don't include this folder, so your global instructions file doesn't get the shell habits.

## Use

Start OpenCode in the folder. When permission prompts keep recurring, or before you change permission rules, policies or saved approvals, the agent loads the skill. You can also say "Use permission-tuning".

In OpenCode, the `ai-research` agent and the `build` family can load the skill; the other specialist agents can't.

## For agents: install, remove and update

Install. Use the [`ai_research` group](../../groups/README.md#ai_research). It writes the folder's `AGENTS.md`, replacing any existing one in that folder, so tell the user before the live run. The skill needs no programs; its saved-approvals commands use `opencode`, `jq` and `sqlite3`, which the user already has or installs under the `package-management` skill. To verify, start OpenCode in the folder, check that `AGENTS.md` starts with the "Shell habits" section and that `permission-tuning` is listed among the skills. Don't change any permission as a test.

Remove. Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component) inside the chosen folder. Regenerating without this folder rewrites `AGENTS.md` without the rule; `delete: false` leaves `.opencode/skills/permission-tuning/` behind, which you delete with approval. Remove the `ai-research` agent's allow for this skill by taking `permission-tuning` out of that agent's bundles in `agents/generate.py`.

Update. There is no upstream: the skill and rule are written for this repo and change in place. Keep the facts in `SKILL.md` verified against the OpenCode docs; describe the current behavior, not a history of tuning rounds, and keep personal paths, project names and backlogs out of it. When the shell habits change in the user's setup, change `rules/shell-habits.md` to match.

## Origin

Written for this repo. [MIT](../../LICENSE).
