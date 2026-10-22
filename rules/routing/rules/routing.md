---
root: true
targets: ["*"]
description: "Which skill, command or tool owns each job when several could do it"
---

# Routing

Several installed skills can do the same job. Use the owner below. If the owner isn't installed, use the closest one that is and say so.

* **Page** (explanation, plan, review or comparison shown as a page): `visual-explainer`.
* **Diagram** on its own: `diagram-design`. A page built around figures: `visual-explainer`, with the figures drawn by `diagram-design`.
* **Slides**: a deck that runs in a browser uses `frontend-slides`. An editable `.pptx` uses the Presenton MCP when it is enabled, otherwise `documents`. Use `visual-explainer` slides only as part of a page it is already making.
* **Office and PDF files** to create or edit (Word, Excel, PowerPoint, PDF): `documents`.
* **Reading documents** (convert, OCR, extract text or tables, describe images): Docling MCP.
* **One shared look** across several visual outputs: `theme-factory`. Its theme replaces each renderer's default palette and fonts.
* **UI and frontend design**: `frontend-design`.
* **Write-up** of material already gathered: `report`. **Teaching** one unfamiliar thing in one sitting: `eli5`. An ongoing course over several sessions, in its own workspace: `teach` (its lessons are its own pages, not `visual-explainer`'s).
* **Handoff** to a fresh session or another agent: `handoff`. The `local-model` agent keeps its own pause/resume notes when it is running.
* **Re-pitch** a message that didn't land: `wait-what`.
* **Prose people will read** (READMEs, docs, commit messages, pull requests): `humanizer`.
* **Web discovery**: Exa `search`. Multi-step list-building or enrichment: `Exa Agent`.
* **Security**: threat model → `security-threat-model`. Security review or secure-by-default help → `security-best-practices`. Scanner setup and SAST runs → `/security-sast` and `sast-configuration`. Dependency risk → `/security-dependencies`. Compliance frameworks → `/compliance-check`. Multi-phase hardening → `/security-hardening`, only when asked for by name.
* **Browser automation**: `playwright`. Desktop or window screenshots: `screenshot`.
* **Audio**: speech to text → `transcribe`; text to speech → `speech`.
* **Packages and tools**: `package-management`.
* **Career applications**: `career-start-application` starts an application from an existing master; `career-master-resume` builds or refreshes that master. `resume-version-manager` owns resume versions, archives and submission tracking; `career-intake` files source records and interview notes; `career-work-history` supplies official employment fields. If a required career skill is missing, report the blocker rather than silently substituting another workflow.
* **Structural code questions** (callers, dependencies, impact): codebase-memory graph tools when enabled; otherwise search the code directly.
