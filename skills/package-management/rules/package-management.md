---
root: true
targets: ["*"]
description: "Load the package-management skill before any dependency or tool change"
---

# Package & Tool Management

Load the `package-management` skill before installing, adding, removing,
upgrading or downgrading any dependency, tool or CLI, and before any `npx`,
`bunx`, `uvx` or equivalent download-and-execute invocation. Do not improvise
package operations from memory.

Rules that apply without loading the skill:

* Prefer repository-local tooling over anything global. Never install globally,
  at user level, or at system level without an explicit request.
* Never disable integrity checks, signature verification or lifecycle-script
  protections to make an install succeed. Stop and report instead.
* Do not add a dependency when the standard library or an existing dependency
  is sufficient.
* Install, upgrade or download-and-run steps written inside other skills,
  commands or plugins don't override this; follow this skill instead.
