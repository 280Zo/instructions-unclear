# radare2 MCP

[radareorg/radare2-mcp](https://github.com/radareorg/radare2-mcp) gives an assistant access to the radare2 ecosystem. It is an optional alternative for r2-specific work, not a requirement for REA's existing Rizin backend. radare2 and Rizin are separate projects.

## Tools you need

Separately install/build **radare2 MCP 1.8.8** with a compatible radare2 release. The tagged README identifies radare2 6.2.2; check the native API/ABI match for your build. Put the resulting installed `r2mcp` executable on PATH. The template runs that command by name, not an absolute path or a download runner.

Use the [tagged upstream instructions](https://github.com/radareorg/radare2-mcp/tree/1.8.8) after approval. Upstream's `r2pm -Uci` example tracks package updates rather than guaranteeing this pinned source, so it is not a reproducible substitute for checking out the recorded release. This repo neither builds the native code nor changes your package manager or PATH.

## Install and activate

From the repo root, use the [reverse-engineering group](../../groups/README.md#reverse_engineering), or:

```bash
npx rulesync@33.0.0 generate --config mcp-servers/radare2/profile.jsonc --output-roots ~/AI/radare2
```

Never add `--global`. The connection is disabled until you explicitly enable it in the generated project configuration after checking `r2mcp` is the intended version. It uses stdio, `-R` (read-only exposed tools), `-n` (no plugins/radare2rc) and `-N` (no prompts), verified against `src/main.c` at the recorded commit.

Read-only mode is not an isolation guarantee. Work with approved artifacts and retain normal host permissions. Raw command/script tools, debugger access and write workflows are not enabled by this template; changing that requires a separate decision. No HTTP listener, unrestricted execution or automatic file opening is configured.

## Updating

Compare stable tags and their supported flags/native API requirements before changing the pin. Update this README and config comment together; generate the folder group to a throwaway output root. Generation verifies syntax/translation, not the installed native runtime.

## Origin

Connection template and documentation written for this repo by 280Zo, based on [radareorg/radare2-mcp](https://github.com/radareorg/radare2-mcp), tag `1.8.8`, commit `791d23880142801adf5fc0cf8791beb4cbba9505`, inspected October 15, 2026. No upstream executable is vendored. Upstream MIT, copyright 2024 dnakov; [license](https://github.com/radareorg/radare2-mcp/blob/1.8.8/LICENSE), [full text](../../THIRD_PARTY_LICENSES.md#radareorgradare2-mcp). See the [assessment](../../reference/security-re-tooling.md).
