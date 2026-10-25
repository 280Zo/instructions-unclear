---
root: true
targets: ["*"]
description: "Which skill owns each job when several installed skills could do it"
---

# Routing

Several installed skills can do the same job. Use the owner below. If the owner isn't installed, use the closest one that is and say so.

* **Page** (explanation, plan, review or comparison shown as a page): `visual-explainer`.
* **Diagram** on its own: `diagram-design`. A page built around figures: `visual-explainer`, with the figures drawn by `diagram-design`.
* **Slides**: a deck that runs in a browser uses `frontend-slides`. An editable `.pptx` uses the Presenton MCP when it is enabled, otherwise `documents`. Use `visual-explainer` slides only as part of a page it is already making.
* **Office and PDF files** to create or edit (Word, Excel, PowerPoint, PDF): `documents`.
* **One shared look** across several visual outputs: `theme-factory`. Its theme replaces each renderer's default palette and fonts.
* **UI and frontend design**: `frontend-design`.
* **Write-up** of material already gathered: `report`. **Teaching** one unfamiliar thing: `eli5`.
* **Prose people will read** (READMEs, docs, commit messages, pull requests): `humanizer`.
* **Security**: threat model → `security-threat-model`; security review or secure-by-default help → `security-best-practices`; scanner setup → `sast-configuration`. Use `/security-hardening` only when asked for by name.
