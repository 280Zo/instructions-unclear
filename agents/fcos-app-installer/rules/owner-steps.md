# Owner steps

How to hand work to the owner: the steps they do on systems the agent never
touches, and how to wait for them. Owner, 2026-11-04.

- **The agent never touches** the file server, the router, the hypervisor's
  shell, the DNS provider or remote-access consoles, and never runs commands
  as root on a server. Those are owner steps.
- **Each owner step** gives the exact steps with every value filled in, says
  which machine and shell each command runs in, and lists what to report back.
- **One step per answer block.** When a step's output leads to another step,
  the agent shows that next step itself, on its own: never a step hidden
  inside another step's output.
- **Commands in full, in the message.** Every command the owner should run is
  in the message that asks for it, complete and ready to paste, never "the
  command from earlier".
- **Several items of one kind are one table**: folders, secrets, accounts,
  rules or addresses go in a table with one row each, never in paragraphs.
- **Waiting.** When the owner does something themselves, the agent ends its
  turn and waits until they say it's done.
- **Shells.** Commands the owner runs on their desktop are fish syntax.
  Commands on a server or a VM are bash. Every code block starts with a
  comment naming its machine and shell, for example `# desktop (fish)` or
  `# vm apps (bash, <admin>)`. When the agent runs a fish block itself in its
  own bash shell, it runs the bash equivalent (`&&`/`||` for fish's
  `; and`/`; or`, `$(...)` for `(...)`).
