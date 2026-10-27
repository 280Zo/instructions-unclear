# speech

OpenAI text-to-speech using built-in voices. Included in `default`, `work` and `infosec`; independently selectable.

## Install context

From the repo root:

```bash
npx rulesync@41.0.0 generate --global --features skills --input-roots skills/speech
```

This includes the complete upstream script, references and interface assets. It does not install dependencies or generate audio.

## Runtime setup — prefer uv

Use the task project's existing environment first. For a new approved task-local environment:

```bash
uv venv .venv
uv pip install --python .venv/bin/python openai
```

On Windows select `.venv\Scripts\python.exe`. These commands download a dependency into the selected environment; do not run them automatically in this context repo. Invoke `scripts/text_to_speech.py` with that interpreter and the actual installed skill path. Some references assume `$CODEX_HOME/skills` (normally `~/.codex/skills`); rulesync 38's global Codex output is `~/.agents/skills`, and other hosts differ. Do not globally change `CODEX_HOME` or rewrite the payload merely to hide that mismatch. Choose one installation owner per destination.

Supply `OPENAI_API_KEY` through an approved process environment/secret mechanism, not a committed value or chat. Text is sent to OpenAI and calls can incur costs. Approve data sharing and paid operations first, and disclose the resulting voice as AI-generated. The retained Codex network reference is not permission to disable approvals, enable network access or weaken sandbox settings. No API calls were made to verify packaging. The skill pin does not lock runtime libraries or API model availability.

## For agents: install, remove and update

To install, use the `default`, `work` or `infosec` group, or the single-folder command above. rulesync doesn't install the `openai` Python package (see [Runtime setup](#runtime-setup--prefer-uv)) or supply `OPENAI_API_KEY`; the user sets that variable themselves. To verify, start a new session and check that `speech` is listed among the skills. Don't generate audio as a test, because it sends text to OpenAI and can cost money.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `speech` skill folder behind; delete it with approval. Task environments with the `openai` package, audio already generated and the user's OpenAI account and key stay unless the user asks.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The pinned commit is in [Updating and origin](#updating-and-origin); the update bullets in the next section say what to recheck.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): no other installed skill does text to speech, so its description is enough.
- It does not own speech to text (`transcribe`). Installing its Python client follows `package-management`.
- Why: Generating voice overlapped with `visual-explainer`'s narration features, so the rule gives audio to `speech` and `transcribe`.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/.curated/speech/` from [OpenAI's skills repository](https://github.com/openai/skills), pinned to `49f948faa9258a0c61caceaf225e179651397431`, imported October 20, 2026. Upstream is deprecated. Its installer was verified in isolation before import; compare complete folders/modes and generated resources when updating, and review live duplicates separately rather than deleting automatically.

Publisher: OpenAI. Apache-2.0; the license retains unfilled copyright-example boilerplate, not a named holder. Original [LICENSE.txt](skills/speech/LICENSE.txt) and [consolidated terms](../../THIRD_PARTY_LICENSES.md#openaiskills) are retained. Wrapper written for this repo by 280Zo.
