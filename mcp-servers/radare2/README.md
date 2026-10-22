# radare2 MCP

[radareorg/radare2-mcp](https://github.com/radareorg/radare2-mcp) gives an assistant access to the radare2 ecosystem. It is an optional alternative for r2-specific work, not a requirement for REA's existing Rizin backend. radare2 and Rizin are separate projects.

## Tools you need

Separately install/build **radare2 MCP 1.9.0** with a compatible radare2 release. The tagged README identifies **radare2 6.2.4**; check the native API/ABI requirements for your build rather than assuming an earlier version still matches. Put the resulting installed `r2mcp` executable on PATH. The template runs that command by name, not an absolute path or a download runner.

Use the [tagged upstream instructions](https://github.com/radareorg/radare2-mcp/tree/1.9.0) and [release notes](https://github.com/radareorg/radare2-mcp/releases/tag/1.9.0), reviewed October 20, 2026, after approval. Upstream's `r2pm -Uci` example tracks package updates rather than guaranteeing this pinned source, so it is not a reproducible substitute for checking out the recorded release. This repo neither builds the native code nor changes your package manager or PATH.

## Install and activate

From the repo root, use the [reverse-engineering group](../../groups/README.md#reverse_engineering), or:

```bash
npx rulesync@38.0.0 generate --config mcp-servers/radare2/profile.jsonc --output-roots ~/AI/radare2
```

Never add `--global`. The connection is disabled until you explicitly enable it in the generated project configuration after checking `r2mcp` is the intended version. It uses stdio, `-R` (read-only exposed tools), `-n` (no plugins/radare2rc) and `-N` (no prompts), verified against `src/main.c` at the recorded commit.

Read-only mode is not an isolation guarantee. Work with approved artifacts and retain normal host permissions. Raw command/script tools, debugger access and write workflows are not enabled by this template; changing that requires a separate decision. No HTTP listener, unrestricted execution or automatic file opening is configured.

## For agents: install and verify

Follow the [shared backend installation procedure](../../agents/reverse-engineering/README.md#for-agents-installing-and-verifying-backends). This is optional; do not install it just because a REA native backend is missing.

1. Inspect existing radare2 and `r2mcp` installations and their provenance. Resolve the native dependency/API requirements against **radare2 MCP 1.9.0** and the tagged **radare2 6.2.4** baseline above. Use the official tagged build instructions, checking OS/architecture and compiler dependencies. Do not replace Rizin or silently upgrade an existing radare2 installation.
2. Propose exact pinned download/build/install commands, checksum/signature checks, output paths, dependencies and PATH changes. Obtain approval before executing them. Prefer an isolated install prefix when upstream supports it. Do not substitute an updating `r2pm` recipe for a reviewed tag or run build/install steps with elevated privileges without explicit approval.
3. Verify the installed versions and the pinned release's supported `r2mcp` options. Inspect the generated connection and preserve `-R`, `-n`, `-N`, stdio and its disabled state until activation is approved. Do not enable script/debug/write capabilities or relax host permissions to make tests pass.
4. Smoke test catalog discovery, then a read-only inspection of a benign local fixture using the exposed tool schema; verify an expected string or symbol without executing the fixture. Include package acquisition and connection startup in the approved test scope. A catalog alone does not verify native analysis.
5. Use the shared handoff/rollback checklist. Record the executable actually used by the assistant, both versions, fixture evidence and any remaining limitations. Stop only test-owned processes and keep disabled if compatibility or verification fails.

## Updating

Compare stable tags and their supported flags/native API requirements before changing the pin. Update this README and config comment together; generate the folder group to a throwaway output root. Generation verifies syntax/translation, not the installed native runtime.

## Origin

Connection template and documentation written for this repo by 280Zo, based on [radareorg/radare2-mcp](https://github.com/radareorg/radare2-mcp), tag `1.9.0`, commit `562c0cf23c42b65b3052f0b294d8778c20facbde`, verified October 20, 2026. No upstream executable is vendored or runtime upgrade performed. Upstream MIT, copyright 2024 dnakov; [license](https://github.com/radareorg/radare2-mcp/blob/1.9.0/LICENSE), [full text](../../THIRD_PARTY_LICENSES.md#radareorgradare2-mcp). See the [assessment](../../reference/security-re-tooling.md).
