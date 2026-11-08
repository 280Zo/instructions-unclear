#!/usr/bin/env python3
"""The agent's own setup key for one VM, used while it sets services up, then revoked.

The agent never uses the user's SSH key. It gets a
separate key that the user adds beside their own, and removes it when the
services work:

  keygen <vm>                     new key in <workspace>/secrets/agent-ssh/<vm>/;
                                  prints the manual step that adds it to the VM
  trust <vm> --fingerprint FP     pin the VM's host key, only if it matches the
                                  fingerprint the user read on the VM
  run <vm> -- <command>           run a command as the admin, with only this key;
                                  its output is redacted (tools/redact.py) and it
                                  refuses direct reads of logs, environments and
                                  secret stores
  logs <vm> <unit> [-n N] [--system]
                                  the last N (default 30) journal lines of one
                                  user (or system) unit, redacted: the only way
                                  the agent reads a log
  revoke <vm>                     remove the key from the VM, prove the login now
                                  fails, then delete the key here
  reinstall <vm>                  after a rebuild: print the manual step again for
                                  the same key, and drop the old pinned host key

The private key stays in the secrets folder, which the agent may not read; this
tool only hands its path to ssh. ssh runs with no config file, no ssh-agent and
no other identity, so the user's keys can never be used.
"""
from __future__ import annotations

import argparse
import ipaddress
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workspace  # noqa: E402
from redact import redact_text  # noqa: E402
from workspace import WorkspaceError  # noqa: E402

NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
USER = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
PUBKEY = re.compile(r"^ssh-ed25519 [A-Za-z0-9+/=]+ fcos-agent-setup-[a-z0-9-]+$")
VM_KEY_FILE = "~/.ssh/authorized_keys.d/fcos-agent"
UNIT = re.compile(r"^[a-z0-9][a-z0-9@_.-]{0,120}\.service$")
# An app printed a generated secret into its log at first start, and a
# log check showed it to the agent. Logs go through `logs` (redacted); these reads are refused.
DIRECT_READS = re.compile(r"\bjournalctl\b|\b(?:podman|docker)\b[^|;&]*\blogs\b|\bsecret\s+inspect\b"
                          r"|--showsecret|\bprintenv\b|(?:^|[\s;&|(])env(?:\s|$)|/environ\b|\.log\b"
                          r"|(?:^|[\s/])\.env\b|/run/secrets\b|secretsdata|\becho\s+[\"']?\$\{?[A-Z_]"
                          r"|\bsystemctl\b[^|;&]*\bstatus\b")


class VmSshError(Exception):
    pass


def _target(site: dict, vm: str) -> tuple[str, str]:
    """(admin user, VM address) from the site file."""
    if not NAME.match(vm):
        raise VmSshError(f"invalid VM name {vm!r}")
    admin = site.get("admin_user")
    if not isinstance(admin, str) or not USER.match(admin) or admin == "root":
        raise VmSshError("site.yaml admin_user must be a normal account name (never root)")
    for entry in site.get("vms") or []:
        if isinstance(entry, dict) and entry.get("name") == vm:
            try:
                ip = ipaddress.IPv4Address(str(entry.get("ip")))
            except ValueError:
                raise VmSshError(f"site.yaml vms: {vm} has no valid ip") from None
            return admin, str(ip)
    raise VmSshError(f"VM {vm} is not in site.yaml vms")


def _key_dir(ws: Path, vm: str, create: bool = False) -> Path:
    vault = ws / "secrets"
    try:
        info = vault.lstat()
    except OSError:
        raise VmSshError(f"no secrets folder at {vault}; create the workspace first") from None
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise VmSshError(f"{vault} must be a real folder owned by you")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise VmSshError(f"{vault} has mode {stat.S_IMODE(info.st_mode):04o}; run: chmod 700 {vault}")
    folder = vault / "agent-ssh" / vm
    if create:
        for part in (vault / "agent-ssh", folder):
            part.mkdir(mode=0o700, exist_ok=True)
            part.chmod(0o700)
    return folder


def _known_hosts(ws: Path, vm: str) -> Path:
    # Beside the key in secrets/, where the agent can't edit it.
    return _key_dir(ws, vm) / "known_hosts"


def _clean_env() -> dict:
    """No ssh-agent: the user's unlocked keys must never be offered."""
    env = dict(os.environ)
    for var in ("SSH_AUTH_SOCK", "SSH_AGENT_PID", "SSH_ASKPASS"):
        env.pop(var, None)
    return env


def _ssh_args(ws: Path, vm: str, admin: str, ip: str) -> list[str]:
    key = _key_dir(ws, vm) / "id_ed25519"
    if not key.is_file():
        raise VmSshError(f"no agent key for {vm}; run: python3 tools/vmssh.py keygen {vm}")
    kh = _known_hosts(ws, vm)
    if not kh.is_file():
        raise VmSshError(f"{vm}'s host key isn't pinned; run: python3 tools/vmssh.py trust {vm} --fingerprint <FP>")
    return ["ssh", "-F", "none", "-i", str(key),
            "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none", "-o", "BatchMode=yes",
            "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
            "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={kh}",
            "-o", "GlobalKnownHostsFile=none",
            "-o", "ConnectTimeout=10", "-l", admin, ip]


def cmd_keygen(ws: Path, site: dict, args) -> int:
    _target(site, args.vm)
    folder = _key_dir(ws, args.vm, create=True)
    key = folder / "id_ed25519"
    if key.exists() or key.with_name("id_ed25519.pub").exists():
        raise VmSshError(f"an agent key for {args.vm} already exists; revoke it first")
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"fcos-agent-setup-{args.vm}",
                    "-f", str(key)], check=True, env=_clean_env(), stdin=subprocess.DEVNULL)
    key.chmod(0o600)
    _print_manual_step(key, args.vm, _target(site, args.vm)[0])
    return 0


def _print_manual_step(key: Path, vm: str, admin: str) -> None:
    pub = key.with_name("id_ed25519.pub").read_text(encoding="utf-8").strip()
    if not PUBKEY.match(pub) or not pub.endswith(f"fcos-agent-setup-{vm}"):
        raise VmSshError("the agent's public key has an unexpected form; nothing to add")
    args = argparse.Namespace(vm=vm)
    print(f"### Add the agent's setup key to VM {args.vm}\n")
    print("It goes in its own file beside your key, and `python3 tools/vmssh.py revoke "
          f"{args.vm}` removes it again when the services work.\n")
    # The block stops by itself on any other machine: pasted on the wrong one, it would
    # overwrite that machine's agent key or put the key on a hypervisor.
    print("```bash")
    print(f"# vm {args.vm} (bash, {admin}): run this ONLY on {args.vm}")
    print(f'if [ "$(hostnamectl hostname)" = "{args.vm}" ]; then')
    print("  install -d -m 0700 ~/.ssh/authorized_keys.d")
    print(f"  printf '%s\\n' '{pub}' > {VM_KEY_FILE}")
    print(f"  chmod 0600 {VM_KEY_FILE}")
    print("  ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub")
    print("else")
    print(f'  echo "STOP: this is not {args.vm}, it is $(hostnamectl hostname); nothing was changed"')
    print("fi")
    print("```\n")
    print("Report back: the fingerprint line (256 SHA256:...).")


def cmd_reinstall(ws: Path, site: dict, args) -> int:
    """After a rebuild: the VM lost the key file and has a new host key; the key here stays."""
    admin, _ = _target(site, args.vm)
    key = _key_dir(ws, args.vm) / "id_ed25519"
    if not key.is_file():
        raise VmSshError(f"no agent key for {args.vm}; run: python3 tools/vmssh.py keygen {args.vm}")
    _known_hosts(ws, args.vm).unlink(missing_ok=True)
    _print_manual_step(key, args.vm, admin)
    print(f"Then pin the new host key: python3 tools/vmssh.py trust {args.vm} --fingerprint <SHA256:...>")
    return 0


def cmd_trust(ws: Path, site: dict, args) -> int:
    _admin, ip = _target(site, args.vm)
    if not (_key_dir(ws, args.vm) / "id_ed25519").is_file():
        raise VmSshError(f"no agent key for {args.vm}; run: python3 tools/vmssh.py keygen {args.vm}")
    scan = subprocess.run(["ssh-keyscan", "-T", "5", "-t", "ed25519", ip], capture_output=True, text=True,
                          env=_clean_env(), timeout=30)
    lines = [ln for ln in scan.stdout.splitlines() if ln.strip() and not ln.startswith("#")]
    if len(lines) != 1:
        raise VmSshError(f"could not read one ed25519 host key from {ip}")
    printed = subprocess.run(["ssh-keygen", "-lf", "-"], input=lines[0] + "\n", capture_output=True, text=True,
                             env=_clean_env(), timeout=30).stdout.split()
    if len(printed) < 2 or printed[1] != args.fingerprint:
        raise VmSshError(f"the host key at {ip} does not match {args.fingerprint}; nothing pinned "
                         "(check the address, or read the fingerprint on the VM again)")
    kh = _known_hosts(ws, args.vm)
    kh.write_text(lines[0] + "\n", encoding="utf-8")
    kh.chmod(0o600)
    print(f"pinned {args.vm}'s host key ({args.fingerprint})")
    return 0


def _run_redacted(ssh: list[str], command: str) -> int:
    done = subprocess.run(ssh + ["--", command], env=_clean_env(), capture_output=True, text=True,
                          errors="replace")
    sys.stdout.write(redact_text(done.stdout))
    sys.stderr.write(redact_text(done.stderr))
    return done.returncode


def cmd_run(ws: Path, site: dict, args) -> int:
    admin, ip = _target(site, args.vm)
    if not args.command:
        raise VmSshError("nothing to run: give the command after --")
    command = " ".join(args.command)
    if DIRECT_READS.search(command):
        raise VmSshError("refused: logs, environments and secret stores are read only with "
                         "`python3 tools/vmssh.py logs <vm> <unit>`, which hides secrets; never read "
                         "them another way")
    return _run_redacted(_ssh_args(ws, args.vm, admin, ip), command)


def cmd_logs(ws: Path, site: dict, args) -> int:
    admin, ip = _target(site, args.vm)
    if not UNIT.match(args.unit):
        raise VmSshError("the unit must be a unit name ending in .service, e.g. myapp-app.service")
    if not 1 <= args.lines <= 500:
        raise VmSshError("-n must be between 1 and 500")
    field = "_SYSTEMD_UNIT" if args.system else "_SYSTEMD_USER_UNIT"
    return _run_redacted(_ssh_args(ws, args.vm, admin, ip),
                         f"sudo journalctl {field}={args.unit} -n {args.lines} --no-pager -o short-iso")


def cmd_revoke(ws: Path, site: dict, args) -> int:
    admin, ip = _target(site, args.vm)
    ssh = _ssh_args(ws, args.vm, admin, ip)
    removed = subprocess.run(ssh + ["--", f"rm -f {VM_KEY_FILE} && ! test -e {VM_KEY_FILE}"],
                             env=_clean_env(), stdin=subprocess.DEVNULL)
    if removed.returncode != 0:
        raise VmSshError(f"removing the key on {args.vm} failed (exit {removed.returncode}); the key is kept here")
    check = subprocess.run(ssh + ["--", "true"], env=_clean_env(), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True)
    if check.returncode == 0:
        raise VmSshError(f"the agent key still logs in to {args.vm}; it is kept here. Check "
                         "~/.ssh/authorized_keys and ~/.ssh/authorized_keys.d/ on the VM for fcos-agent-setup")
    # Only a refused key proves it; a timeout or network error proves nothing.
    if check.returncode != 255 or "Permission denied (publickey" not in check.stderr:
        raise VmSshError(f"could not confirm the key is refused by {args.vm} (exit {check.returncode}); "
                         "it is kept here; run revoke again when the VM answers")
    shutil.rmtree(_key_dir(ws, args.vm))
    print(f"revoked: the agent key no longer logs in to {args.vm}, and its key files are deleted here")
    return 0


COMMANDS = {"keygen": cmd_keygen, "trust": cmd_trust, "run": cmd_run, "logs": cmd_logs,
            "revoke": cmd_revoke, "reinstall": cmd_reinstall}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="name", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("vm")
        p.add_argument("--workspace")
        if name == "trust":
            p.add_argument("--fingerprint", required=True)
        if name == "logs":
            p.add_argument("unit")
            p.add_argument("-n", dest="lines", type=int, default=30)
            p.add_argument("--system", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # "run <vm> --workspace W -- cmd": everything after "--" is the remote command.
    remote: list[str] = []
    if "--" in argv:
        i = argv.index("--")
        argv, remote = argv[:i], argv[i + 1:]
    args = build_parser().parse_args(argv)
    if args.name == "run":
        args.command = remote
    elif remote:
        print("vmssh: only run takes a command after --", file=sys.stderr)
        return 1
    try:
        ws = workspace.resolve_workspace(args.workspace)
        site = workspace.load_site(ws)
        return COMMANDS[args.name](ws, site, args)
    except (VmSshError, WorkspaceError) as exc:
        print(f"vmssh: {exc}", file=sys.stderr)
        return 1
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"vmssh: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
