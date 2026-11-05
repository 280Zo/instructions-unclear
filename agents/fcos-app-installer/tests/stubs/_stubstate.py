"""Shared state and logging for the fake pveum, pvesm and pvesh in this folder.

State lives in the JSON file named by $STUB_STATE. Keys: pools {name: [vmids]},
roles {name: "A,B,C"}, users [ids], tokens ["user!name"], tokens_no_privsep
[ids], acls [[path, kind, id, role]] (kind is "user" or "token"), storages
[ids], bridges [names]. Every call appends its argv as one JSON array per line
to $STUB_LOG.
"""

import json
import os
import sys

DEFAULTS = (
    ("pools", dict), ("roles", dict), ("users", list), ("tokens", list),
    ("tokens_no_privsep", list), ("acls", list), ("storages", list), ("bridges", list),
)


def log_call(argv):
    path = os.environ.get("STUB_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(argv) + "\n")


def load():
    with open(os.environ["STUB_STATE"], encoding="utf-8") as handle:
        state = json.load(handle)
    for key, kind in DEFAULTS:
        state.setdefault(key, kind())
    return state


def save(state):
    with open(os.environ["STUB_STATE"], "w", encoding="utf-8") as handle:
        json.dump(state, handle)


def fail(message, code=255):
    print(message, file=sys.stderr)
    sys.exit(code)


BUILTIN_ROLES = {"Administrator": "Sys.Audit", "PVEDatastoreUser": "Datastore.AllocateSpace,Datastore.Audit",
                 "PVESDNUser": "SDN.Audit,SDN.Use"}

# The FORMAT_OPTIONS of the Proxmox CLIs (pvesh man page, "FORMAT_OPTIONS").
FORMAT_OPTIONS = ("output-format", "human-readable", "noborder", "noheader", "quiet")


def parse(args, allowed, usage, positional=None, required=()):
    """Split args into positionals and {--name: value} options, like the real CLIs.

    `allowed` is the set of option names (without dashes) the real command
    documents in its man page; anything else fails as the real tool does:
    "Unknown option: <name>" then "400 unable to parse option" and the usage.
    `positional` is the exact number of positional arguments expected.
    """
    positionals, options = [], {}
    index = 0
    while index < len(args):
        if args[index].startswith("--"):
            name = args[index][2:]
            if name not in allowed:
                fail(f"Unknown option: {name}\n400 unable to parse option\n{usage}")
            if index + 1 >= len(args):
                fail(f"option '{args[index]}' needs a value", 2)
            options[args[index]] = args[index + 1]
            index += 2
        else:
            positionals.append(args[index])
            index += 1
    if positional is not None and len(positionals) != positional:
        fail(f"400 {'not enough' if len(positionals) < positional else 'too many'} arguments\n{usage}")
    for name in required:
        if f"--{name}" not in options:
            fail(f"400 Parameter verification failed.\n{name}: property is missing and it is not optional\n{usage}")
    return positionals, options
