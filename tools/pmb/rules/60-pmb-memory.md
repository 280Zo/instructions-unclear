---
root: true
targets: ["*"]
description: "When and how to use PMB project memory"
---

## PMB Memory

When PMB is available for the current project:

- Read before you write: `record_batch` is forbidden unless `prepare`, `recall`,
  `project_overview` or `session_brief` ran earlier this session.
- Call `prepare(<user's message>)` before the first modifying tool call, and before
  answering "where were we" / "what's next". Not a judgment call.
- A `_nudge` or below-target ratio is a failure: report it and correct it.
- PMB is local-only; project goal, tasks and status also belong in repo files.
- One `record_batch` per turn, scoped to the project. No secrets, and never the
  only copy of an exact value.
- For images, use Docling first; keep OCR and vision notes with the source path.
