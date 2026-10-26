# report

A skill that writes up material you've already gathered (files, notes, a talk, scan results) as a report that anchors every claim to its source and states who it's for.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/report
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/report` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Type `/report`, or ask it to "write up" what you've gathered, optionally "for the board" or "as slides". It renders through [`visual-explainer`](../visual-explainer/), [`diagram-design`](../diagram-design/), [`frontend-slides`](../frontend-slides/), `theme-factory` ([`anthropic-design`](../anthropic-design/)) or [Presenton](../../mcp-servers/presenton/), saving to `Clanker_Crayon_Box/reports/` in the current folder. Without those installed it can still gather and check the evidence, but not render it.

To learn something new rather than write it up, use [`eli5`](../eli5/).

## Notes

Claude Code's `allowed-tools` sits under a `claudecode:` section so other tools ignore it.

## For agents: install, remove and update

To install, use the `default`, `work` or `writing_reporting` group, or the single-folder command above. Rendering needs the skills or Presenton server listed in [Use](#use); without them it only gathers and checks evidence. To verify, start a new session and check that `report` is listed among the skills.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `report` skill folder behind; delete it with approval. Reports already saved under `Clanker_Crayon_Box/reports/` are the user's files and stay unless the user asks. If the user keeps `rules/routing`, its line still names `report`, so tell them.

To update, there is no upstream: the skill is written for this repo and changes in place. The next section says what to keep in step with `rules/routing`.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Write-up** of material already gathered: `report`". Teaching something unfamiliar is `eli5`'s job.
- It gathers and checks evidence but doesn't own rendering: pages go to `visual-explainer`, diagrams to `diagram-design`, browser decks to `frontend-slides`, editable `.pptx` to `documents` or Presenton, and the shared look to `theme-factory`.
- Why: on 2026-10-21 the user replaced the per-skill rules with one routing rule because several skills' descriptions and rules claimed the same jobs. `report` delegates rendering to those skills, so it has to follow the same owners as everything else.
- The skill is written for this repo, so its own text can be adjusted to match routing, but `rules/routing` stays the single source: change the rule first and keep this skill consistent with it.
- Don't add a per-skill routing rule to this folder. When a renderer it uses is added, removed or refreshed and its job changes, update `rules/routing`, this skill's references to that renderer and this section in the same change, and tell the user.

## Origin

Written for this repo. [MIT](../../LICENSE).
