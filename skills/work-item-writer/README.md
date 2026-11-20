# work-item-writer

A skill that turns notes into epics, features and user stories a team can pick up: project notes, meeting notes, research, AI session recaps or a brain dump. It works with any tracker, and has a reference for Azure DevOps on the Agile process, including a CSV file for bulk import.

Every user story gets a title, a description in Mike Cohn's "As a …, I want …, so that …" form, and acceptance criteria as Gherkin scenarios (Given, When, Then). The skill writes only what the notes support:

- Scenarios restate the behavior and limits the notes describe. Anything else, such as error states, validation or formats, becomes a proposed refinement or an open question.
- Engineering, infrastructure and spike work stays a Task, never an "As a developer" story.
- Story points, priority, area and iteration paths, tags and owners appear only when the notes give them.
- It never aims for a number of stories, and it asks instead of writing when a note is too thin.
- Every item links back to the note it came from.
- Decisions become context, and admin chores, remarks about people and secrets are left out.

After the items comes a story review. For each story it gives:

- a readiness label: Ready for refinement, Needs clarification, Needs splitting or Ready for implementation
- an INVEST check (Independent, Negotiable, Valuable, Estimable, Small, Testable), naming the criteria that fail or can't be judged
- suggested smaller stories when a story holds several outcomes
- its assumptions and proposed refinements

The open questions come at the end of the review. The items hold only what the notes document, so you can paste them as they are.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/work-item-writer
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/work-item-writer` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Give it a note and ask for work items: "write user stories from my project note", "turn this meeting note into ADO work items", "give me a CSV I can import into Azure DevOps". Items come back in one Markdown block, ready to paste, followed by a second block with the story review and open questions. A CSV comes back as its own block, followed by the review.

| Ask | You get |
|---|---|
| User stories, epics or features | Items in tool-neutral Markdown, plus the story review |
| ADO work items | Items using Azure DevOps field names (Epic, Feature, User Story, Task; Acceptance Criteria in its own field) |
| A CSV for ADO import | A file with indented `Title 1`, `Title 2`, `Title 3` columns for the hierarchy, no `ID` column, Gherkin scenarios as HTML, and spikes as Tasks tagged `Spike` |
| Tasks | Technical work from the notes always; stories broken into tasks only when you ask |

The ADO reference, `reference/ado-agile.md`, records the facts the skill relies on, each with its Microsoft source. Field names can differ between organizations, so export a few existing items first and compare the columns before a large import.

To turn raw material into notes first, use [`md-note-organizer`](../md-note-organizer/).

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default) and [`work`](../../groups/README.md#work) groups install it globally. For this folder alone, use the command under [Install](#install) above; it skips `rules/routing`.
- It needs no other software. It writes items and files; it doesn't connect to a tracker.
- In OpenCode's default install, the `build`, `plan` and `general` agents can load it.
- To verify, start a new session and confirm the skills list includes `work-item-writer`.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `work-item-writer` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name.

### Update

The skill is written for this repo, so there is no upstream commit to check. Recheck `reference/ado-agile.md` against its Microsoft sources when Azure DevOps changes its work item types, fields, CSV import or Markdown support.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Work items** (epics, features, user stories, acceptance criteria) from notes: `work-item-writer`". Writing the notes themselves is `md-note-organizer`'s job.
- Don't add a per-skill routing rule to this folder. If its job changes, update `rules/routing`, this section and `md-note-organizer`'s routing section in the same change, and tell the user.

## Origin

Written for this repo. [MIT](../../LICENSE), © 280Zo. Two upstream skills shaped it. Their ideas are rewritten here, and no text is copied.

- Its Azure DevOps hierarchy and field handling draw on [charlesjones-dev's `ado-work-items`](https://github.com/charlesjones-dev/ai-agent-plugins/blob/ebeb8eeb0bd368f506aa28fb4e58d604130b8b8c/plugins/ai-ado/skills/ado-work-items/SKILL.md) (commit `ebeb8eeb0bd368f506aa28fb4e58d604130b8b8c`). [MIT](../../THIRD_PARTY_LICENSES.md#charlesjones-devai-agent-plugins), © 2026 Charles Jones.
- Its user story and acceptance criteria structure draws on [AWS konductor's `user-story-writing`](https://github.com/aws-solutions/konductor/blob/7de51bfaef8479e267e870445cb3732bfbe2d768/skills/user-story-writing/SKILL.md) (commit `7de51bfaef8479e267e870445cb3732bfbe2d768`). [Apache 2.0](../../THIRD_PARTY_LICENSES.md#aws-solutionskonductor), © Amazon.com, Inc. or its affiliates.
