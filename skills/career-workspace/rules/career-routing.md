---
root: true
targets: ["*"]
description: "Which career skill owns each step of an application"
---

# Career routing

`career-start-application` starts an application from an existing master; `career-master-resume` builds or refreshes that master. `resume-version-manager` owns resume versions, archives and submission tracking; `career-intake` files source records and interview notes; `career-work-history` supplies official employment fields. Interview prep, practice, mock interviews, storybanks, debriefs, interview salary scripts and thank-you notes go to `interview-coach`; use `interview-prep-generator` only for a one-pass written prep sheet when the user doesn't want a coaching session, or for its sales-role questions. If a required career skill is missing, report the blocker rather than silently substituting another workflow.
