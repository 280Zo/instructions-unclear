---
root: true
targets: ["*"]
description: "Shell habits that keep permission rules matching, and when to load the permission-tuning skill"
---

# Shell habits

* Permission rules match the raw command string, so write commands they can recognize, and prefer tools to the shell:
  * Use `read`, `grep`, `glob` to inspect files and `edit`/`write` to change them. Do not rewrite files with Python heredocs, `sed -i`, `tee` or redirects.
  * No `VAR=value` prefixes (they defeat allow and deny rules); for Python use `python3 -B`. No wrappers: `env`, `bash -c`, `sh -c`, `xargs`, `time`, `nice`, or `timeout` (except `timeout 60|120|300 python3 -m unittest ...`).
  * Run tests as `python3 -m unittest ...` or `python3 -m pytest ...` (optionally `-B`, optionally piped to `tail`/`rg`/`cut`). Stage with `git add -- <paths>`. No `python3 -` heredocs or `python3` scripts you wrote in `/tmp`.
  * Never suggest or click "Always" on a broad prefix (`python3 *`, `bash *`, `rm *`, `edit *`) or on a prompt a protected-file guard raised; propose a precise rule instead. Agents cannot edit any `opencode.json(c)` (policy); give the user exact snippets to apply by hand.
  * When the same category of prompt recurs more than three times in a session, load the `permission-tuning` skill and follow it. Security outranks fewer prompts.
