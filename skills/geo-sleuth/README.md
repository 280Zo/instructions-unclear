# geo-sleuth

A skill that works out where (and when) a photo was taken, and shows its work: every conclusion points to the clue it used, the command it ran and the file that command produced. It reads metadata, runs text recognition, searches for similar images, and checks candidate places against maps, satellite imagery and skylines.

## Install

1. Have Python 3.10+, [uv](https://docs.astral.sh/uv/) and `curl`. Each script installs its own Python packages through `uv run` the first time.
2. Reverse image search needs Google Chrome or Playwright Chromium. Without either: `uvx playwright install chromium` (on Linux, add `--with-deps` if browser libraries are missing). The optional skyline detector in `references/skyline-fallback.md` downloads a 185 MB model and PyTorch on first run, so ask before using it.
3. Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

   ```bash
   npx rulesync@43.12.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/geo-sleuth
   ```

   Swap `--targets` for your tools. To keep it in your regular install, add `skills/geo-sleuth` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

The first time, ask the agent to "run geo-sleuth's doctor check" and fix what it reports. Then:

- "Where was `/path/photo.jpg` taken?"
- "When was this photo taken?" (it uses the sun's position and shadows)
- "These three photos are from one trip; place each one"

It saves its working files in your current directory so you can check each step: `intake/` (crops, text it read, search results), `board.json` (the candidate places) and `.geo-cache/`. Image matching downloads a model the first time and uses a GPU if PyTorch finds one.

Use it on your own photos or ones you have permission to analyze, never to find people who haven't agreed to be found.

## For agents: install, remove and update

### Install

- The [`default` group](../../groups/README.md#default) installs it globally. For this folder alone, use step 3 under [Install](#install) above.
- rulesync doesn't install Python 3.10+, uv, `curl`, or Chrome or Playwright Chromium. Install missing ones only with approval, following the `package-management` skill. The scripts install their own Python packages through `uv run` on first use.
- To verify, start a new session, confirm the skills list includes `geo-sleuth`, and run its doctor check (`uv run scripts/doctor.py` from the installed skill folder) without `--network`. It uploads no photos and loads no models, but uv may download its Playwright dependency on first use, so ask before running it.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `geo-sleuth` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name.

- Working files in the folders where it ran (`intake/`, `board.json`, `.geo-cache/`) stay unless the user explicitly asks.
- uv's package cache, the downloaded image-matching model, and Chromium stay. Offer to remove them separately.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The upstream commit is under [Origin](#origin). Copy the whole skill folder, including the region packs and tests, and rerun the doctor check after a refresh.

## Origin

[Oldcircle/geo-sleuth](https://github.com/Oldcircle/geo-sleuth), path `skills/geo-sleuth/`, commit `c27d5ee24ec4393633c5c3d5a3bbe0cebbe33d93`, copied 2026-11-24. Unchanged, including all 14 region packs and the upstream tests. [MIT](../../THIRD_PARTY_LICENSES.md#oldcirclegeo-sleuth), © 2026 Oldcircle. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
