---
root: true
targets: ["*"]
description: "Communication: assumptions, completion summaries and full file paths"
---

# Communication

* State material assumptions.
* In replies to the user, write every file path in full, never relative to the working directory. For anything under the home folder, strongly prefer `~/...` or `$HOME/...` over the expanded `/home/<user>/...`; use an absolute path only for locations outside the home folder. In commands you hand the user, use `$HOME`, because `~` doesn't expand inside quotes or after `=`. This covers replies only: paths inside files you write, Markdown links and tool arguments such as `git add -- <paths>` follow that file's or tool's own convention.
* At completion, summarize:

  * Files changed
  * Behavioral changes
  * Checks run and their results
  * Remaining risks or unverified behavior
