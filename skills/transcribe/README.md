# transcribe

OpenAI audio transcription with optional speaker identification. Included in `default`, `work` and `infosec`; independently selectable.

## Install context

From the repo root:

```bash
npx rulesync@38.0.0 generate --global --features skills --input-roots skills/transcribe
```

The complete upstream helper, references and interface assets accompany the skill. This installs no Python packages and starts no API calls.

## Runtime setup — prefer uv

Use the task project's existing environment first. For a new approved task-local environment:

```bash
uv venv .venv
uv pip install --python .venv/bin/python openai
```

On Windows select `.venv\Scripts\python.exe`. These commands create an environment and download a dependency; do not automatically run them in this context repo. Invoke the bundled `scripts/transcribe_diarize.py` with that environment's Python, resolving its actual installed directory. Upstream examples assume `$CODEX_HOME/skills` (normally `~/.codex/skills`); rulesync 38's Codex output is `~/.agents/skills`, and other hosts differ. Do not globally change `CODEX_HOME` or rewrite upstream files to hide a path mismatch. Use one install owner per destination.

Supply `OPENAI_API_KEY` through an approved process environment/secret mechanism, never a value in this repo or chat. Audio and any known-speaker samples are uploaded to OpenAI and can incur costs: get data-sharing and paid-operation approval first. No live API behavior is established by context-generation tests. The skill pin does not lock the client library or API model availability.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): no other installed skill does speech to text, so its description is enough (line removed 2026-10-24 to save tokens).
- It does not own text to speech (`speech`) or reading text from documents and images (Docling MCP). Installing its Python client follows `package-management`.
- Why: on 2026-10-21 the user replaced the per-skill rules with one routing rule because several skills' descriptions and rules claimed the same jobs. Here, the audio jobs overlapped with `visual-explainer`'s narration features, so the rule gives audio to `transcribe` and `speech`.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/.curated/transcribe/` from [OpenAI's skills repository](https://github.com/openai/skills), pinned to `49f948faa9258a0c61caceaf225e179651397431`, imported October 20, 2026. Upstream is deprecated. Its installer was verified in isolation before import; preserve all scripts/references/assets and modes when reviewing a new revision, and recheck generated resource paths. Do not automatically remove existing live copies.

Publisher: OpenAI. Apache-2.0; the license retains unfilled copyright-example boilerplate, not a named holder. Original [LICENSE.txt](skills/transcribe/LICENSE.txt) and [consolidated terms](../../THIRD_PARTY_LICENSES.md#openaiskills) are retained. Wrapper written for this repo by 280Zo.
