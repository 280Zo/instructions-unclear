# geo-sleuth

A skill that works out where (and when) a photo was taken, and shows its work: every conclusion points to the clue it used, the command it ran and the file that command produced. It reads metadata, runs text recognition, searches for similar images, and checks candidate places against maps, satellite imagery and skylines.

## Install

1. Have Python 3.10+, [uv](https://docs.astral.sh/uv/) and `curl`. Each script installs its own Python packages through `uv run` the first time.
2. Reverse image search needs Google Chrome or Playwright Chromium. Without either: `uvx playwright install chromium` (on Linux, add `--with-deps` if browser libraries are missing).
3. Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

   ```bash
   npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/geo-sleuth
   ```

   Swap `--targets` for your tools. To keep it in your regular install, add `skills/geo-sleuth` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

The first time, ask the agent to "run geo-sleuth's doctor check" and fix what it reports. Then:

- "Where was `/path/photo.jpg` taken?"
- "When was this photo taken?" (it uses the sun's position and shadows)
- "These three photos are from one trip; place each one"

It saves its working files in your current directory so you can check each step: `intake/` (crops, text it read, search results), `board.json` (the candidate places) and `.geo-cache/`. Image matching downloads a model the first time and uses a GPU if PyTorch finds one.

Use it on your own photos or ones you have permission to analyze, never to find people who haven't agreed to be found.

## Origin

[Oldcircle/geo-sleuth](https://github.com/Oldcircle/geo-sleuth), path `skills/geo-sleuth/`, commit `836d70eea196b194391017e6e018e04ccc85aaa4`, copied 2026-10-14. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#oldcirclegeo-sleuth), © 2026 Oldcircle. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
