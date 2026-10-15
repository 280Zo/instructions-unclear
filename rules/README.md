# Rules

How I want any AI coding tool to behave, split into topics you can install separately. Written for this repo.

| Folder | Rule |
|---|---|
| `shell-preamble/` | Explain every shell command that isn't a plain read before running it. Installed first |
| `scope-secrets-approvals/` | Where to work, what never to touch, what to ask before doing |
| `engineering/` | Inspect first, keep changes small, use `sd` for replacements, verify before claiming success |
| `secure-coding/` | The security mistakes AI-written code makes most often |
| `communication/` | State assumptions, summarize at the end, write prose with `humanizer`, use the visual skills |
| `shell-preamble-reminder/` | Repeat the preamble check at the end of the installed rules. Installed last |

## Install

rulesync installs rules by replacing your tool's whole instructions file, so pick every topic you want at once. Add them to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../README.md#install)), keeping `rules/shell-preamble` first and `rules/shell-preamble-reminder` last, then run your install command with `--features rules`. For example:

```jsonc
{
  "inputRoots": ["rules/shell-preamble", "rules/scope-secrets-approvals", "rules/engineering", "rules/communication", "rules/shell-preamble-reminder"]
}
```

Every rule installs into the same file (`~/.config/opencode/AGENTS.md`, `~/.claude/CLAUDE.md` and so on), in the order listed.

## Notes

- The secure-coding rule is based on OpenSSF's [Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html) (2025).
- Lines in `communication/` about a skill you haven't installed do nothing.
