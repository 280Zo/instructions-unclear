#!/usr/bin/env python3
"""The agent's one way to talk to the hypervisor's API.

Usage:
  hypervisor.py check  [--host KEY]
  hypervisor.py list   [--host KEY]
  hypervisor.py create <vm.yaml> [--dry-run] [--host KEY]
  hypervisor.py start  <vm> [--host KEY]
  hypervisor.py status <vm> [--host KEY]
  (each also takes --workspace PATH; the default is FCOS_WORKSPACE or the remembered one)

It reads the product from the site file (roles.virtualization.provider), loads that adapter's tool
(`code:` in its adapter.yaml, a file in tools/virtualization/) and hands it the arguments unchanged. The
tool has only these verbs; anything that deletes or needs root stays a manual step from the adapter.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workspace  # noqa: E402
from adapters import AdapterError, TOOL_VERBS, load_adapter, load_tool  # noqa: E402
from workspace import WorkspaceError  # noqa: E402

ROLE = "virtualization"


def _provider(site) -> str:
    roles = site.get("roles") if isinstance(site, dict) else None
    entry = roles.get(ROLE) if isinstance(roles, dict) else None
    provider = entry.get("provider") if isinstance(entry, dict) else None
    if provider in (None, "ASK"):
        raise AdapterError("site.yaml: roles.virtualization.provider is not set; ask the user which hypervisor "
                           "runs the machines, then name its adapter (python3 tools/adapters.py show --role "
                           "virtualization --provider <name>)")
    return provider


def _load_site(ws: Path) -> dict:
    """The site file, with a one-line error for a missing, unreadable or invalid one."""
    try:
        return workspace.load_site(ws)
    except (workspace._yaml().YAMLError, UnicodeDecodeError):
        raise WorkspaceError("site.yaml can't be read as YAML; fix it first (python3 tools/workspace.py where "
                             "shows the workspace)") from None
    except OSError as error:
        raise WorkspaceError(f"can't read {Path(ws) / 'site.yaml'} ({error.strerror}); is this the right "
                             "workspace? (python3 tools/workspace.py where)") from None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    verbs = TOOL_VERBS[ROLE]
    if argv[:1] in (["-h"], ["--help"]):
        print((__doc__ or "").strip())
        return 0
    if not argv or argv[0] not in verbs:
        print(f"usage: hypervisor.py <{'|'.join(verbs)}> [arguments] [--workspace PATH]\n"
              "run it with a verb; the adapter's tool does the rest (see this file's header)", file=sys.stderr)
        return 2
    where = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    where.add_argument("--workspace")
    known, _rest = where.parse_known_args(argv[1:])
    try:
        ws = workspace.resolve_workspace(known.workspace)
        tool = load_tool(load_adapter(ROLE, _provider(_load_site(ws))))
    except (AdapterError, WorkspaceError) as error:
        print(f"hypervisor: {error}", file=sys.stderr)
        return 1
    return tool.main(argv)


if __name__ == "__main__":
    sys.exit(main())
