---
name: bn-headless
description: Headless Binary Ninja CLI for decompiling and reverse-engineering compiled binaries without the GUI. Use when you need to decompile, disassemble, read pseudo-C/HLIL/MLIL, follow xrefs and callees, dump strings and the code that references them, enumerate imports/exports/sections, or hunt a vulnerability in any ELF/PE/Mach-O/raw binary across any architecture (x86, MIPS, ARM, aarch64, PPC, RISC-V).
---

# Binary Ninja Headless (bnhl)

You are helping the user reverse-engineer compiled binaries from the command line using Binary Ninja's headless API, with no GUI involved. This covers firmware executables, shared libraries, and any ELF/PE/Mach-O or raw binary across any architecture Binary Ninja lifts.

## Tool Overview

`bnhl` is a self-contained CLI wrapper (`scripts/bnhl.py`) around the Binary Ninja Python API. It loads any file on disk, runs full analysis, caches the result, and prints readable output to stdout. It is the right tool when you want to:

- Decompile functions to pseudo-C (or HLIL / MLIL / disassembly)
- List and filter functions by name
- Follow cross-references (callers) and callees
- Dump strings and jump straight to the code that references them
- Enumerate imports, exports, and sections
- Batch-analyze many binaries in a script, headless

For reading compiled code, `bnhl` is far more productive than raw `objdump`, `gdb`, or `radare2` because it gives you readable decompilation and a resolved call graph.

### When to use CLI vs the GUI

Use `bnhl` (CLI) for automated analysis, scripting, batch processing, headless/server environments, and any self-directed decompilation. Use the Binary Ninja GUI (or its MCP server) only for interactive, manual exploration when the user explicitly asks for it, because the GUI only sees the one binary an operator has loaded by hand.

## Prerequisites

- **A licensed Binary Ninja** (Commercial, Enterprise, or Ultimate). The free/demo edition does not ship the headless Python API. Binary Ninja is commercial software licensed separately from this toolkit; the skill is inert without it.
- A license that validates locally needs no enterprise-server checkout and runs fine alongside a running GUI instance.
- **Python 3**. The script locates the Binary Ninja Python API itself and injects it onto `sys.path`, so no `PYTHONPATH` setup is needed.

### Pointing the script at your Binary Ninja install

`bnhl` autodetects the API in these locations, in order:

1. `$BN_PYTHON` (your install's `python` directory), if set
2. `$BN_INSTALL_DIR/python`, if `BN_INSTALL_DIR` is set
3. `~/binaryninja/python`
4. `/opt/binaryninja/python`
5. `/Applications/Binary Ninja.app/Contents/Resources/python` (macOS)

If your install is elsewhere, set the env var once:

```bash
export BN_PYTHON="/path/to/binaryninja/python"
```

## Running It

Invoke through the `bnhl` shim in this repo's `bin/` (add `bin/` to your `PATH`):

```bash
bnhl <command> <bin> [args]
```

If `bnhl` is not on your `PATH`, call the script directly:

```bash
python3 skills/bn-headless/scripts/bnhl.py <command> <bin> [args]
```

## Commands

| Command | What it does |
|---|---|
| `info <bin>` | arch, platform, entry, function/string/import counts, sections |
| `functions <bin> [--filter REGEX] [--limit N]` | list functions (addr, size, name) |
| `decompile <bin> <func\|0xADDR> [more...] [--il pseudoc\|hlil\|mlil\|disasm]` | decompile one or more functions (default: pseudo-C) |
| `at <bin> <0xADDR>` | decompile whichever function contains an address |
| `xrefs <bin> <func\|0xADDR>` | callers + code references **to** the target |
| `callees <bin> <func\|0xADDR>` | functions the target calls |
| `strings <bin> [--filter REGEX] [--min N]` | dump strings |
| `grepstr <bin> <REGEX>` | strings matching REGEX **plus the functions that reference each** |
| `imports <bin>` / `exports <bin>` / `sections <bin>` | symbol / section inventory |

**func selector**: an exact symbol name, a unique substring of a name, or a hex address (`0x...`). Most commands also accept `--raw` for machine-readable JSON where supported.

## Typical RE Flow

```bash
bnhl info      ./libtarget.so                       # orient: arch, counts, sections
bnhl grepstr   ./libtarget.so 'password|secret|/dev' # interesting constants + their handlers
bnhl functions ./libtarget.so --filter -i auth       # find the auth functions
bnhl decompile ./libtarget.so handle_cmd             # read the pseudo-C
bnhl xrefs     ./libtarget.so is_privileged          # trace an authz gate's callers
bnhl decompile ./libtarget.so 0x823b1                # or decompile by address
```

### What to look for in decompiled code

- Command injection via `system()` / `popen()` / `exec*()` with attacker-influenced strings
- Hardcoded keys, credentials, and backdoor comparisons
- Stack buffer overflows (`strcpy`, `sprintf`, `memcpy` with unchecked lengths)
- Format string bugs (`printf`-family with a non-constant format argument)
- Integer overflows feeding allocation or copy sizes
- Missing or broken authentication/authorization checks
- Debug/diagnostic interfaces left enabled

## Performance & Caching

The first analysis of a binary is cached to a `.bndb` under `~/.cache/bnhl/` (override with `$BNHL_CACHE`), keyed by path + mtime + size. Repeat calls on the same binary are near-instant. A small `.so` analyzes in under a second cold; a few-hundred-KB daemon with ~1000 functions takes several seconds cold and under a second warm. Multi-MB binaries pay a proportional cost on the first call only.

## Notes & Gotchas

- Pseudo-C restored from a cached `.bndb` needs a one-time internal re-analysis to materialize the linear view; the tool does this automatically, so you may see a brief pause on the first `decompile` after a cold analysis. HLIL/MLIL/disassembly come straight from cache with no re-analysis.
- HLIL and pseudo-C reorder basic blocks relative to address order (cold-path branches often float to the bottom), so addresses within a function are not monotonic. This is normal Binary Ninja behavior, not corruption.
- Output goes to **stdout**; progress and counts go to **stderr**. Pipe stdout to a file when capturing.
- The tool disables Binary Ninja's default logging for clean, parseable output.
- Verify surprising findings in `disasm` (or cross-check with `objdump`) before reporting. Decompiled HLIL can rotate loops and rebase expressions, so a claim that hinges on exact control flow should be confirmed against the disassembly.

## Integration with IoTHackBot Tools

`bnhl` is the code-reading stage after you have a binary in hand:

1. **Firmware → executable → decompile**: use `ffind` to identify file types and extract filesystems from a firmware image, then point `bnhl` at the interesting ELF binaries (web daemons, update handlers, auth helpers) in the extracted rootfs.
2. **UEFI/BIOS**: use `chipsec` to inventory EFI executables from a BIOS dump, then decompile individual modules with `bnhl`.
3. **Binary → network testing**: decompile a device daemon to recover its protocol, endpoints, and command handlers, then exercise them with `iotnet`, `nmap`, `onvifscan`, or `telnetshell`.
4. **Companion app → firmware**: pair findings from `jadx` (Android app decompilation) with the matching device-side logic you read in `bnhl`.

## Security & Ethics

**IMPORTANT**: Only reverse-engineer binaries you own or are authorized to analyze.

- Respect software licenses and reverse-engineering terms where they apply
- Follow responsible disclosure for any vulnerabilities you find
- Use for authorized security testing and research only
