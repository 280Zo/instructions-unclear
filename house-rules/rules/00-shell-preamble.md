---
root: true
targets: ["*"]
description: "RULE 0: describe every non-exempt shell command before running it"
---

# RULE 0 — Shell Preamble (check before EVERY bash call)

Run this test on the command string. It is mechanical. Do not reason around it.

EXEMPT only if BOTH are true:
  (a) it contains NO `&&`, NO `;`, NO `||`, NO `|`, and NO newline; AND
  (b) the single command only reads: `ls` `pwd` `cat` `head` `tail` `wc` `stat`
      `file` `which` `rg` `grep` `find` `git status` `git log` `git diff`
      `git show` `git branch` `env` `printenv` `date` `echo`.

Anything else is NON-EXEMPT. This includes read-only commands that are piped or
chained. `strings x | grep y` is NON-EXEMPT. `wc -c a && rg b c` is NON-EXEMPT.
`node -e '...'` is NON-EXEMPT. `mkdir` `rm` `mv` `cp` `touch` `tee` and every
install/build/network command are NON-EXEMPT.

For a NON-EXEMPT command, emit 1–2 sentences of ordinary assistant text
IMMEDIATELY BEFORE the tool call, stating:
  1. what the command does;
  2. what it creates, modifies or deletes — or explicitly that it only reads;
  3. if the command names a secret-bearing file (`.env` `.pem` `.key` `id_rsa`
     `credentials.json` `.npmrc` `.netrc` `.tfstate` `.kdbx` `.cred`), say so
     and say why you need it.

Constraints:
* Never emit a NON-EXEMPT bash call without its preamble already written.
* One preamble per tool call. Do not batch several calls under one preamble.
* A todo list, a heading, or a sentence about your plan is NOT a preamble. It
  must describe THAT command.
* Uncertain whether something is exempt? It is not. Write the preamble.
* If you catch yourself having skipped it, stop, say so, and write it before
  continuing.
