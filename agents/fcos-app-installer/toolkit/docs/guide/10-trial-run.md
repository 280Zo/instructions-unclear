# 10. Trial run after installing

The repository's tests check the files: the agents, rules, skills, tools and
templates. A few things only a live OpenCode can show: that it loads the
rules, sees the skills and lets the agent start its helper. Run these checks
once on each machine you install the toolkit on, then add one real service as
a trial.

## 10.1 [Manual] The toolkit itself

In the folder you installed the toolkit into:

```fish
# desktop (fish)
cd <toolkit folder>
python3 tools/check_requirements.py
python3 -m unittest discover tests
python3 tools/publish_check.py
```

Expected: an `ok` line for each requirement (OpenCode 2.1.3 or newer, Python 3
with PyYAML, podman or docker, and the launch folder), `OK` from the tests, and
`0 hit(s)` from the publish check.

## 10.2 [Manual] What OpenCode loads

Start OpenCode in the toolkit folder and pick the `fcos-app-installer` agent.
Each check below makes it do something whose result you can see in the
session; a model could answer a question about itself from memory, but it
can't fake a tool call or a refusal. Nothing on your systems changes.

| Ask it to | Expected |
|---|---|
| Quote the rule "Commands in full, in the message" (the Manual steps rule in `AGENTS.md`) | The rule's text, with no file read shown before it. A read tool call first means the rules aren't loading: check that `AGENTS.md` is in the folder you started OpenCode in (rulesync writes it; README.md "Install") |
| Load the skill of your hypervisor's adapter (`adapter-<product>`), then `researching-apps-for-self-hosting` | Two skill tool calls that succeed, each followed by the skill's steps |
| Load the skill `eli5` | Refused by permission (the skill filter works) |
| Start the `adapter-drafter` subagent and have it run only `python3 tools/adapters.py show --role file_server`, then report | A subagent session starts and reports the file server steps (`nfs_export`, `service_user`, `backup_folder`). If it can't be started, the agent's `subagent` permission isn't taking effect |
| Run `ssh localhost true` | Refused by permission (OpenCode's `build` agent would ask instead: the agent's own rules are in effect) |
| Run `python3 tools/vmssh.py run <any vm> -- 'journalctl -n 1'` | Refused, naming `vmssh.py logs` instead (no key is needed to see the refusal) |
| Run `python3 tools/check_updates.py > .opencode/skills/x.md` | Refused by permission: nothing may write into the skills from the shell. The tests check this rule with a stand-in for OpenCode's matching, so this is the live check |
| Run `python3 tools/adapters.py draft --role file_server --provider x --from /tmp/opencode/none.json --workspace ~/.opencode/skills` | Refused by permission (the command names `.opencode/`); the tool refuses it too: a draft never goes into a skill folder |

Report back: each result that differs from the expected one.

## 10.3 [Manual] Trial: add one service

Run `/add-service <service>` and let the agent work. Along the way, check each
of these as it happens:

| When | Check |
|---|---|
| A new hypervisor token | The setup script prints only the secret; storing it (`store_api_token`) comes as its own next step |
| File server folders | One table from `file-server.md` (folder, user, group, mode), then the how-to steps once |
| Secrets | One table from `secrets.md` (secret, used by, what to enter, keep it), then the commands |
| Any command for you | Complete in the message that asks for it, with its machine and shell as the first line |
| Reading the app's log | Only through `vmssh.py logs`; anything secret-looking shows `[hidden]` |
| The end of the run | `<workspace>/AGENTS.md` rebuilt; the report includes the service's `backups.md`; the agent's VM key revoked (`vmssh.py revoke`) |
| When you're done with the agent | The teardown step removes the agent's hypervisor access and leaves the VMs running, without asking anything |

Report back to whoever maintains the toolkit: every check that didn't hold,
with what happened instead.
