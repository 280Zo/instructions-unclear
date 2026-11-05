# 11. Move and update

Three changes that come up after the first install: using the toolkit on
another computer, updating the toolkit, and moving one service to a new
release line of its app.

## 11.1 [Owner] Use the toolkit on another computer

Your installs live in their workspace folders, not in the toolkit, so moving
means taking the workspaces with you and making new access on the new
computer. The old computer's agent access is never copied.

1. Install the toolkit on the new computer and run its checks there:
   `python3 tools/check_requirements.py`, then guide 10 (`10-trial-run.md`).
2. Copy your workspace folders (for example `~/fcos-installs/`) to the new
   computer, **without** each workspace's `secrets/` folder. It holds the
   hypervisor token and the agent's VM keys, which belong to the old computer.
3. Point the agent at the workspace once:
   `python3 tools/workspace.py init <workspace>`. It remembers the folder in
   `~/.config/fcos-agent/workspace` on the new computer, and adds anything the
   folder is missing.
4. New access, as on a first install:
   - a new hypervisor token, with virtualization `create_api_access`, then
     `store_api_token`. If the old token still exists, the setup's replacement
     blocks swap it, and the old copy stops working;
   - the agent's VM key: `python3 tools/vmssh.py keygen <vm>` for each VM it
     needs, which you add as before (guide 2.7);
   - app API tokens: created again in the app when the agent needs one
     (guide 3.12).
5. Secrets on the VMs stay where they are. The ones a rebuild needs are in
   your password manager, not in any folder you copy.

Report back: the requirement check's lines, and that the agent shows your
install (`python3 tools/workspace.py where`).

## 11.2 [Owner] Update the toolkit

1. Get the newer toolkit the way you installed it (README.md "Install"), into
   a new folder next to the old one. In the new folder run
   `python3 tools/check_requirements.py` and the tests:
   `python3 -m unittest discover tests`. Start OpenCode in the new folder.
2. Run `python3 tools/check_updates.py`. For anything it reports, follow
   README.md "Updating".
3. If the hypervisor's host scripts changed, their checksum changed with
   them, and the new toolkit carries the new pinned list
   (`host-scripts.sha256`): the next virtualization step (such as
   `create_api_access`) shows the new checksum, so check it again before
   running the script, as on a first install.
4. Keep the previous folder until the new one passes these checks, so you can
   go back to it. Your workspaces are in neither folder, so nothing in them
   changes.

## 11.3 Move a service to a new release line

The services update themselves within their image's tag: every container has
`AutoUpdate=registry`, and the VM's update timer pulls each fix. A new release
line (for example `2026.8` to `2026.11`) is a planned change.

1. **[Agent]** Read the app's official release notes for every release line
   between the current one and the new one, and write what changes into
   `<workspace>/services/<svc>/research.md`, with links. Look for:
   - an upgrade order: some apps must move **one release line at a time**,
     never skipping (Authentik says so in its upgrade docs);
   - a database major version change: a new major version of the database
     can't read the old one's data until it is converted (for example with
     `pg_dumpall` and a restore), so it needs a planned dump and restore, not
     just a new tag;
   - settings that are renamed or removed.
2. **[Agent]** Show the owner the plan, release line by release line, and
   wait for their yes.
3. **[Agent]** Make a fresh backup and check it (guide 4, Check a backup).
4. **[Agent]** Change `image:` in the service's spec to the next release
   line, regenerate with `python3 tools/gen_service.py` (guide 3.6), build,
   push (guide 3.7) and restart the service.
5. **[Agent]** Run the verify checklist (guide 3.10). If the app needs more
   release lines, repeat steps 3 to 5 for each.
6. **[Owner]** If something breaks: go back to the previous `image:`,
   regenerate and push, then guide 4, Restore, with the backup from step 3.
   You lose at most what changed since that backup.

Report back: the release lines moved through, and each verify checklist.
