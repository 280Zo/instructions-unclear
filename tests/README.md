# Offline context packaging checks

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

These stdlib tests check collection completeness, native plugin resource paths, reviewed MCP launch definitions, disabled templates, group roots, unique skill names, global-default separation and published status. They do not import helper dependencies, contact targets, access devices or start native MCP backends. The former IoTHackBot patch assertions were retired with the patched packaging; its complete upstream layout is checked instead.

`test_openai_skills.py` checks that the seven pinned OpenAI skills retain their runtime references/scripts, licenses and interface metadata, and that the selected groups discover them without name collisions.

`test_documents_skill.py` runs the packaged `documents` validator on its four bundled fixtures (PDF, DOCX, XLSX, PPTX) and checks that the complete family skill and its references are present in the groups that select it. It does not render documents or need Python libraries beyond the standard library.

Changes to source roots must also be generated with pinned rulesync into throwaway output folders. Compare installed support assets and translated configuration against the source; unit tests alone do not prove generation or native runtime compatibility.

Native-owned collections require a separate isolated installation/discovery check followed by rulesync generation. The October 20, 2026 refresh validated Claude Code plugin packaging and preservation, not model-driven security workflows or Codex execution. Do not run native hooks, scanners, hardware workflows or dependency installers merely to run this suite.

## Origin

Written for this repo by 280Zo.
