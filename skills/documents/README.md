# documents

[Magnus Hedemark's documents skill](https://github.com/magnus919/agent-skills/tree/92c327e525da69c9ad3812fd223a1770e977c2e3/documents): one shared authoring workflow for **PDF, Word (`.docx`), Excel (`.xlsx`) and PowerPoint (`.pptx`)**, with per-format references, planning templates, fixtures, tests and a structural smoke validator. The complete upstream folder is preserved unchanged.

## Install context

Included in `default`, `work` and `writing_reporting`. To install this skill alone, run from the repo root:

```bash
npx rulesync@41.0.0 generate --global --features skills --input-roots skills/documents
```

This copies context and helpers, not Python libraries, native renderers or other skills. It does not replace rules or MCP settings.

### Upstream installation ownership

Upstream documents a selective `skills` CLI install. Before importing here, the pinned checkout was installed with **skills CLI 1.7.4**, selecting only `documents`, using a fake home with networking disabled and declining its unrelated `find-skills` offer. The installed payload matched the 18 upstream files and their modes. No additional plugin hooks or configuration are needed for that skill-only installation.

For native installation instead of rulesync, follow the [upstream options](https://github.com/magnus919/agent-skills#installation), selecting only `documents`, your intended harness and scope. Use a reviewed checkout pinned to `92c327e525da69c9ad3812fd223a1770e977c2e3` rather than silently following `main`. The installed CLI can add that local checkout without downloading source again. Package/installer operations still need approval; do not copy upstream's full-catalog or automatic-confirmation examples blindly.

Choose **one owner per assistant/destination**. Skills CLI 1.7.4 uses `~/.agents/skills` for Codex/OpenCode, while rulesync 38's OpenCode output uses `~/.config/opencode/skills`; installing both can leave duplicate discovery roots. The isolated matched Codex destination is used to check subsequent generation. Review existing copies before separately approving any live migration or deletion. No live assistant was changed by this import.

## Python setup — prefer uv

Use the task project's existing environment first. For a new approved task-local environment, the common authoring libraries can be installed with:

```bash
uv venv .venv
uv pip install --python .venv/bin/python python-docx openpyxl python-pptx weasyprint
```

Install only the libraries needed for the chosen format. On Windows select `.venv\Scripts\python.exe`. These commands create an environment and download dependencies; do not run them automatically in this context repo. They are repo-authored `uv` equivalents for upstream's Python tooling, not an upstream-tested dependency lock. No npm `docx` package is required.

| Format | Authoring path | Optional rendering |
|---|---|---|
| Word | `python-docx` or Pandoc | LibreOffice, then a PDF renderer |
| Excel | `openpyxl` | LibreOffice; separate formula recalculation is needed |
| PowerPoint | `python-pptx` | LibreOffice, then a PDF renderer |
| PDF | HTML/CSS with WeasyPrint, Chromium or LaTeX | Poppler (`pdftoppm`), MuPDF or Ghostscript |

WeasyPrint can require platform libraries/fonts. Python package installation does not install LibreOffice, Poppler or a TeX/browser toolchain. Approve needed native tools separately; never weaken filesystem/device permissions or bypass access controls. The skill pin fixes context, not these runtime dependencies.

## Use and verification limits

Ask to create or edit an Office/PDF deliverable, then inspect the relevant format reference. The templates are content/layout briefs, not executable generators. Resolve scripts relative to the installed skill directory.

`scripts/validate-documents.py --json <files...>` checks basic PDF/OOXML structure using Python's standard library. `--render-check` optionally invokes external renderers. **Inspect the JSON status, not just the exit code:** missing renderers can report `unavailable` with exit code 0, and unsupported extensions can be skipped successfully. PDF rendering generally probes the first page; this is not proof that every page looks correct. Office conversion is not proof of layout fidelity or correct formulas.

The validator does not establish formula caches/calculation, complete relationship resolution, all worksheet/slide XML correctness, accessibility, overflow, font fidelity or content accuracy. Review the final rendered pages/sheets/slides and calculation results separately. External rendering processes untrusted files and is not sandboxed by this script; use the project's approved isolation. Retain **Docling for OCR, extraction and structured conversion**; this skill adds authoring/smoke validation rather than replacing that role.

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default), [`work`](../../groups/README.md#work) and [`writing_reporting`](../../groups/README.md#writing_reporting) groups install it globally. For this folder alone, use the command under [Install context](#install-context) above.
- Pick one owner per tool: rulesync or the upstream skills CLI, not both (see [Upstream installation ownership](#upstream-installation-ownership)).
- rulesync doesn't install Python libraries, LibreOffice, Poppler, WeasyPrint's system libraries or a TeX or browser toolchain. Set up only what the chosen format needs, with approval, as [Python setup](#python-setup--prefer-uv) describes.
- To verify, start a new session and confirm the skills list includes `documents`. If the user wants a further check, run `scripts/validate-documents.py --json` from the installed skill folder on a bundled fixture such as `fixtures/sample.pdf`, without `--render-check`, and read the JSON status, not just the exit code.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `documents` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name.

- The skills CLI may have put another copy in `~/.agents/skills/documents`, which is also where rulesync writes Codex skills. Find out which installer owns each copy before deleting.
- Task `.venv` folders, LibreOffice and other renderers, and documents it made stay.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating and origin](#updating-and-origin), where the pinned revision is recorded. Test the native install and later rulesync generation in isolation before adopting a new revision, then follow the routing bullets below.

## For agents: routing and updates

- Roles in [`rules/routing`](../../rules/routing/rules/routing.md): "**Office and PDF files** to create or edit (Word, Excel, PowerPoint, PDF): `documents`", and editable `.pptx` decks ("An editable `.pptx` uses the Presenton MCP when it is enabled, otherwise `documents`"). Presenton wins only when the user has it running and enabled.
- It does not own reading documents (convert, OCR, extract text or tables, describe images): that is the Docling MCP. Browser decks go to `frontend-slides`; slides inside a page stay with `visual-explainer`.
- Why: `documents` and Docling both covered extraction, and slides were claimed by `documents`, `frontend-slides`, `visual-explainer` and Presenton.
- When a `theme-factory` theme is in use, it replaces this skill's default palette and fonts.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns (for example OCR or extraction), or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Updating and origin

Full `documents/` from [magnus919/agent-skills](https://github.com/magnus919/agent-skills), revision **`92c327e525da69c9ad3812fd223a1770e977c2e3`**, checked/imported October 20, 2026. Payload unchanged, including all references, templates, fixtures, eval scenarios and tests. Compare the complete folder, test the selective native installation and subsequent rulesync generation in isolation, and update groups/counts/provenance together before adopting another revision.

**MIT, © 2026 Magnus Hedemark**, verified from upstream `LICENSE.md`; [full license text](../../THIRD_PARTY_LICENSES.md#magnus919agent-skills--documents). Wrapper and `uv` setup guidance written for this repo by 280Zo. Packaging and fixture checks are not evidence of a real-world document-generation/rendering workflow.
