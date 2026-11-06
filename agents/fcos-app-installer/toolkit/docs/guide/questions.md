# Questions the agent asks

The agent asks these in plain language, grouped with the question tool, in this
order. It never shows the owner a config key, a field path or an internal name.
Options are built from what the agent already found (an earlier install, a
discovery command's output, the app's official docs); it never assumes a
network, storage or hardware value.

Each question below gives its exact wording, its options, what the answer
fills (in words), and when it is skipped because the answer is already known.

When the answer is a value to type (a number, a name, an address), the
question says to pick "Other" and type it: that is the question tool's only
text box. No option ever means "type it", because choosing one sends only its
label.

## 1. Where to keep the files

**Asked:** "Where should I keep this install's files? They hold your real
names and addresses, so they stay outside the agent's folder."

**Options:** the folder used last time (if any); a new folder in your home;
your own path. A folder whose name contains `fcos-` (such as
`~/fcos-workspace`) is opened without asking each time; any other folder
works too, but every file in it needs your approval. The `secrets` folder
inside is never opened either way.

**Fills:** the private folder for this install (the workspace).

**Skipped when:** never; the remembered folder is offered first.

## 2. Earlier installs

**Asked:** "Do you have a folder with earlier installs I can use to fill in
details?"

**Options:** yes, with its path; no.

**Fills:** nothing directly. The agent reads the earlier site file and app
specs, and then shows every value it would reuse (servers, network, file
server, domain, user numbers, ports, web names) for you to confirm. Secrets
are never copied.

**Skipped when:** the current folder already holds a finished site file.

## 3. Which systems you use

**Asked:** "Which virtualization platform runs your machines? Which router or
firewall? Which file server holds your shared folders? Who hosts the DNS for
your domain's certificates?"

**Options:** the products the agent has adapters for; "something else" (then
the agent uses general steps and offers to write an adapter as you go). For
the certificate's DNS, the provider's adapter carries an `acme` block (the
certificate client's provider code and the variable for the token); a provider
without an adapter gets one drafted with that block, from the provider's own
documentation.

**Fills:** which set of owner steps the agent shows you for each part.

**Skipped when:** already answered in the site file or an earlier install.

## 4. Access to the virtualization platform

**Asked:** "Do you have a limited access token for the agent on this server?"

**Options:** yes (the agent tests it and shows what it may do); no (the agent
shows the setup script's steps for you to run); this platform has no API.

**Fills:** whether the agent can create and start machines itself, or gives
you the commands.

**Skipped when:** a token already works for this server.

## 5. Which server

**Asked:** "Which server should it run on?"

**Options:** your servers by the names you gave them, each marked "always
running" or "sometimes switched off".

**Fills:** the server for the new machine or app.

**Skipped when:** never; the agent always asks, even if it thinks it knows.

## 6. An existing machine or a new one

**Asked:** "Add it to an existing machine, or create a new one?"

**Options:** the machines the agent can see on that server (with their
apps); a new machine.

**Fills:** where the app runs.

**Skipped when:** never.

## 7. A new machine's size, disks and network

**Asked:** after the read-only discovery step has saved the server's facts
(or, on another platform, you ran the read-only commands and pasted the output),
one question at a time, with options taken from that output: "How many CPU
cores and how much memory?", "Which disk storage?", "Which network (bridge),
which VLAN, which MTU?"

**Options:** only values the discovery output shows exist. For cores, memory
and disk, the question says how much is free with every machine and container
on the server running (stopped ones counted too; the discovery output adds it
up), less what the platform itself needs according to its docs (cores are
shared, not used up, so for them it says how many are assigned next to how
many the server has); what the
app's official docs recommend for each resource, or that they state none;
and recommends the lowest amount the agent judges safe for that software,
with the reason. Each machine is sized when it is planned, for what will run
on it. For
the network, each option shows its comment, port and whether it handles
VLANs, so the internet-facing one is easy to tell apart. Only the network to
use is asked: the agent's tool and the token's permissions refuse every other.

Then every other machine setting (CPU type and flags, firmware, board, disk
cache and I/O, network queues, random-number device, start order, and the
rest; guide 2.3) is shown as one table: the setting, what the agent will use,
why, and the source. You change any you want; the rest are used as shown.

**Fills:** the new machine's size, disks, network and every other setting.

**Skipped when:** the app goes on an existing machine.

## 8. The machine's address

**Asked:** "Which address should this machine get? You'll reserve it in your
router for the machine's network card after it's created, before its first
start."

**Options:** a free address you choose on that network.

**Fills:** the address the machine, its firewall rules and the login page's
routes use.

**Skipped when:** the machine already exists.

## 9. Behind the login page

**Asked:** "Put this app behind the login page? Then you sign in once, and
the same account works for all your apps."

**Options:** yes (recommended); no, it uses only its own login, with a reason
you give: it still gets its HTTPS web address, without the login page in
front, and its own password protects it. It also shows as a link on your login
page's app dashboard.

**Fills:** whether the app's web address goes through the login page.

**Skipped when:** never. If no login page exists yet, the agent also asks:
"Set the login page up first?"

## 10. Paths that skip the login page

**Asked:** "Desktop and phone apps can't use a web login. The app's official
docs say these paths are for them: (list). Leave them open to the app's own
password?"

**Options:** yes, all of them; only some; none.

**Fills:** the paths that skip the login page.

**Skipped when:** the app is not behind the login page, or its docs name no
such paths.

## 11. User and group numbers

**Asked:** "Which user and group number should the app's account have? If it
uses your file server, it must match the account there."

**Options:** the next free number the agent found (`tools/check_workspace.py`
names one when a number is taken); the number of an existing file server
account. Numbers run from 1000 to 24608; 1000 and 1001 are kept for the VM's
admin account. A file server account at 1000, 1001 or above 24608 can't be
matched: say so and offer a new account on the file server instead.

**Fills:** the app's account on the machine (and on the file server).

**Skipped when:** an earlier install already set it.

## 12. More than 5 GB of local data

**Asked:** "This app's data on the machine's own disk is expected to grow past
5 GB. Grow the machine's data disk, or keep it on the file server?" For a
database it adds: "A database on the file server can be corrupted if the
connection drops."

**Options:** grow the data disk (to a size you give); keep it on the file
server and record the risk.

**Fills:** where the data lives, and the recorded risk if you accept one.

**Skipped when:** the expected local data is 5 GB or less.

## 13. An app that must start as root

**Asked:** "This image starts as root inside its container (its docs say so).
It still runs without host root rights, with only the listed capabilities.
Use it, or look for another image?"

**Options:** use it, with the capabilities listed; look for another image.

**Fills:** how the container starts and which capabilities it gets.

**Skipped when:** the image runs as an ordinary user.

## 14. Facts the official docs don't state

**Asked:** "The app's official docs don't say (the fact). What should I use?"

**Options:** what a forum or issue says, labelled as such; a value you give;
stop and look it up together.

**Fills:** that one fact, marked with where it came from.

**Skipped when:** the docs state everything needed.

## 15. Secrets you keep

**Asked:** "These secrets must stay the same after a rebuild (a database
password, a signing key). Create them in your password manager, then paste
each one at the hidden prompt. OK?"

**Options:** yes; I already have them.

**Fills:** nothing the agent sees. You create each secret on the machine
from a hidden prompt; the agent only lists their names.

**Skipped when:** the app has no secret that data depends on.
