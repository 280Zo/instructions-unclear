"""Test-only launcher: run tools/virtualization/proxmox.py's CLI against a local fake server.

The tool itself has no way to change its API endpoint. This wrapper patches the
base-URL resolver in-process and then calls pve.main(). It never touches an
owner's workspace: it builds its own temporary workspace holding a fixed FAKE
token, passes that path explicitly, and deletes it afterwards. It refuses
--workspace and any --host other than the test host (exit 2), and it ignores
FCOS_WORKSPACE and the remembered workspace.

FCOS_TEST_FAKE_URL is read here, never in tools/.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from virtualization import proxmox as pve  # noqa: E402

HOST = "host-a"
FAKE_PRINCIPAL = "fcos-agent@pve!fcos-bootstrap"
FAKE_SECRET = "-".join(["00000000", "0000", "0000", "0000", "000000000000"])
SITE = f"""\
hosts:
  {HOST}:
    name: test-host
    node: pve-a
    address: 192.0.2.21
    storage: local-lvm
    snippets_storage: coreos
    iso_storage: isos
    bridge: vmbr0
    max_cores: 4
    max_ram_mib: 8192
"""


def refused(argv: list[str]) -> str | None:
    for index, arg in enumerate(argv):
        if arg == "--workspace" or arg.startswith("--workspace="):
            return "this test launcher always uses its own temporary workspace; --workspace is not allowed"
        if arg == "--host" or arg.startswith("--host="):
            value = arg.split("=", 1)[1] if "=" in arg else (argv[index + 1] if index + 1 < len(argv) else "")
            if value != HOST:
                return f"this test launcher only knows host {HOST}"
    return None


def make_workspace() -> Path:
    ws = Path(tempfile.mkdtemp(prefix="pve-fake-ws-"))
    (ws / "site.yaml").write_text(SITE, encoding="utf-8")
    secrets = ws / "secrets"
    secrets.mkdir()
    secrets.chmod(0o700)
    fd = os.open(secrets / f"proxmox-{HOST}.token", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f"{FAKE_PRINCIPAL}={FAKE_SECRET}\n")
    return ws


def main(argv: list[str]) -> int:
    problem = refused(argv)
    if problem:
        print(f"run_pve_against_fake: {problem}", file=sys.stderr)
        return 2
    fake_url = os.environ["FCOS_TEST_FAKE_URL"]
    pve._api_base = lambda host, cfg: fake_url + pve.API_PREFIX
    ws = make_workspace()
    try:
        return pve.main([*argv, "--workspace", str(ws)])
    finally:
        shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
