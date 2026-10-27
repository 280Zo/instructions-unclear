# Offline context packaging checks

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

These stdlib tests check collection completeness, native plugin resource paths, reviewed MCP launch definitions, disabled templates, group roots, unique skill names, global-default separation and published status. They do not import helper dependencies, contact targets, access devices or start native MCP backends. IoTHackBot's complete upstream layout is checked.

`test_openai_skills.py` checks that the pinned OpenAI skills retain their runtime references/scripts, licenses and interface metadata, that the selected groups discover them without name collisions, and that Microsoft's `playwright-cli` replaced OpenAI's deprecated `playwright` copy everywhere.

`test_rules.py` checks the routing, preference and precedence rules, including that folder-only collections keep their routing in their own folder.

`test_opencode_agents.py` checks that every file `agents/generate.py` writes is current: the six specialists, the `build`, `plan`, `general` and `explore` files, the blocks in `second-opinion` and `local-model`, the README hero (both SVGs, which must be accessible images with no external fonts or links) and `docs/agents-map.html`. It also checks one file per agent folder with no leftover `.portable` files, that specialists carry their instructions and matching Claude Code MCP denies for every tool, and that the four OpenCode-only files have empty bodies and only deny. It confirms that specialists start from a skill deny, that agent file names are unique across `default`, and that every repo MCP server has a permission pattern. It verifies that `default` installs every agent's skills once without REA.

`test_user_invoked_skills.py` checks that `handoff`, `teach` and `wait-what` are separate folders with all their supporting files, keep their invocation fields in tool sections, and are selected, routed and licensed.

`test_documents_skill.py` runs the packaged `documents` validator on its four bundled fixtures (PDF, DOCX, XLSX, PPTX) and checks that the complete family skill and its references are present in the groups that select it. It does not render documents or need Python libraries beyond the standard library.

Changes to source roots must also be generated with pinned rulesync into throwaway output folders. Compare installed support assets and translated configuration against the source; unit tests alone do not prove generation or native runtime compatibility.

Native-owned collections require a separate isolated installation/discovery check followed by rulesync generation. These checks cover Claude Code plugin packaging and preservation, not model-driven security workflows or Codex execution. Do not run native hooks, scanners, hardware workflows or dependency installers merely to run this suite.

## OpenCode permission regression

`test_rulesync_version.py` keeps repo-owned install commands pinned to 41.0.0. Historical version references stay unchanged.

`check_opencode_permissions.py` is a separate, opt-in runtime test. It uses an already-downloaded rulesync CLI, the installed `opencode`, Node, and Python's standard library. It generates agents in a fresh home under `/tmp/opencode`, starts a password-protected private OpenCode server and a localhost model stub, and requests native `skill` calls. The stub supplies calls only; OpenCode executes or denies them. No real model, credentials, live settings, package downloads or MCP backends are needed. Private servers stop afterward; generated files and `results.json` remain in the printed evidence directory.

Point these fish variables at existing package files. Downloading packages is a separate, approved operation:

```fish
set cli41 /path/to/rulesync-41/node_modules/rulesync/dist/cli/index.js
set cli38 /path/to/rulesync-38/node_modules/rulesync/dist/cli/index.js
python3 tests/check_opencode_permissions.py "$cli41"
python3 tests/check_opencode_permissions.py "$cli38" --legacy
```

Checked with OpenCode 2.1.3:

| Native skill call | rulesync 38.0.0 | rulesync 41.0.0 |
|---|---|---|
| Design loads `eli5` | Loaded despite deny | Permission denied |
| Design loads `humanizer` | Loaded | Loaded |
| Build loads `eli5` | Loaded despite deny | Permission denied |

This checks real native tool enforcement with dummy skills, not a model's claimed skill list. It does not verify live session reloads, MCP execution or every permission action. For the rulesync upgrade, all eight groups also generated successfully with 38 and 41 in isolation.

`check_opencode_agents.py` is the same kind of opt-in test for the real `default` group. It first generates the specialists for Claude Code, Codex, Copilot, Copilot CLI and Cursor, parses each file (including the Codex TOML) and confirms OpenCode's four built-in agents don't reach those tools; the tools aren't run. In the OpenCode output it checks each specialist carries its instructions and no Claude Code section. It then generates `default` without MCP output, so no real MCP server starts, and adds three harmless local stub servers (`tests/fixtures/mcp_stub.py`) named `zap`, `codebase-memory-mcp` and `freecad`. It also copies one real `SKILL.md` from each native plugin in `NATIVE_PLUGINS` (Trail of Bits and IoTHackBot) into the test home, as if the plugin were installed; nothing else from the plugin is copied or run. It checks every agent's mode and Explore's resolved read-only policy. For each primary-capable agent it compares the skills, MCP servers and subagents shown to the model with `agents/generate.py`, then makes sample skill, MCP (through Code Mode) and delegation calls:

```fish
python3 tests/check_opencode_agents.py "$cli41"
```

Checked with OpenCode 2.1.3. Every list matched exactly; counts are repo skills the model sees, plus the planted plugin skill for `security` and `reverse-engineering`. Superpowers isn't installed in the test home, and user-invoked skills never reach the model:

| Agent | Skills | Agent | Skills |
|---|---|---|---|
| `build`, `plan` | 24 | `security` | 17 |
| `design` | 32 | `reverse-engineering` | 16 |
| `career` | 33 | `3d-modeling` | 11 |
| `ai-research` | 107 | `second-opinion` / `local-model` | 3 / 5 |

Design and security were denied `resume-tailor` and `binary-triage`, and build was denied `typography`. Career, reverse-engineering and ai-research loaded `resume-tailor`, `binary-triage` and `humanizer`. Security loaded the Trail of Bits skill and reverse-engineering the IoTHackBot skill; build was denied the first and security the second. Security reached the ZAP stub, build reached the codebase-memory stub, and 3d-modeling reached the FreeCAD stub; design and build were blocked from servers they don't list, and those servers were absent from their Code Mode catalogs. Design couldn't delegate to `security-auditor` and career couldn't delegate to `evaluator`; security, build and second-opinion delegated to `security-auditor`, `career` and `evaluator`. Real MCP backends weren't started. File counts matched; differences were confined to OpenCode agent frontmatter and MCP config. A synthetic V2 config retained shared MCP timeouts and unrelated settings while its server list was replaced.

## Origin

Written for this repo by 280Zo.
