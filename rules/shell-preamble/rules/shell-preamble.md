---
root: true
targets: ["*"]
description: "RULE 0: describe every non-exempt shell command before running it"
---

# RULE 0 — Shell Preamble (check before EVERY shell command)

Run this test on the command string. It is mechanical. Do not reason around it.

EXEMPT only if ALL THREE are true:
  (a) it contains NO `&&`, `;`, `||`, `|`, `&`, `>`, `<`, `$(`, backtick, or
      newline; AND
  (b) the single command only reads: `ls` `pwd` `cat` `head` `tail` `wc` `stat`
      `file` `which` `rg` `grep` `find` `git status` `git log` `git diff`
      `git show` `git branch` `date` `echo`, and it uses none of these arguments:
      `find` with `-delete` `-exec` `-execdir` `-ok` `-okdir` `-fprint`
      `-fprint0` `-fprintf` `-fls`; `rg` with `--pre`; `git log`, `git diff` or
      `git show` with `--output`; `git branch` with anything except `-a` `-r`
      `-v` `-vv` `--list` `--show-current`; `date` with `-s` or `--set`; AND
  (c) it names no secret-bearing file (listed below).

Anything else is NON-EXEMPT. This includes read-only commands that are piped or
chained. `strings x | grep y` is NON-EXEMPT. `wc -c a && rg b c` is NON-EXEMPT.
`node -e '...'` is NON-EXEMPT. `env` and `printenv` are NON-EXEMPT because they
print every secret in the environment. `mkdir` `rm` `mv` `cp` `touch` `tee` and
every install/build/network command are NON-EXEMPT.

Examples that are ALWAYS NON-EXEMPT: `git ls-remote`, `git fetch`, `find -exec`,
and `sd` (including a chain of `sd` calls). Read-only intent does not exempt a
network call, an executed helper, or a chained command.

For a NON-EXEMPT command, emit 1–2 sentences of ordinary assistant text
IMMEDIATELY BEFORE the tool call, stating:
  1. what the command does;
  2. what it creates, modifies or deletes — or explicitly that it only reads;
  3. if the command names a secret-bearing file (`.env` `.pem` `.key` `id_rsa`
     `id_ed25519` `.ssh/` `credentials.json` `.credentials.json` `auth.json`
     `.claude.json` `.npmrc` `.netrc` `.tfstate` `.kdbx` `.cred`), say so
     and say why you need it.

Constraints:
* Final check before sending the tool call: is the required ordinary text
  already in the assistant message immediately before it? If not, do not send
  the call. Write the preamble first. A later explanation cannot satisfy it.
* Never emit a NON-EXEMPT shell call without its preamble already written.
* One preamble per tool call. Do not batch several calls under one preamble.
* A todo list, a heading, or a sentence about your plan is NOT a preamble. It
  must describe THAT command.
* Uncertain whether something is exempt? It is not. Write the preamble.
* If you catch yourself having skipped it, stop, say so, and write it before
  continuing.
