"""Opt-in runtime check: install the FCOS app installer for real and run its tests in the result.

Uses an already-downloaded rulesync CLI, Node, Python and PyYAML; nothing is downloaded. It
installs the toolkit's own files with agents/fcos-app-installer/install.py, adds rulesync's output
for groups/fcos_app_installer.jsonc, checks that what rulesync wrote carries the sources' permission
lists and bodies, and then runs the toolkit's whole test suite inside the installed folder, which is
the layout the toolkit's tests are written for. The installed folder is left in place (under
/tmp/opencode when that exists) and its path is printed; it is never deleted.

    python3 tests/check_fcos_app_installer.py /path/to/rulesync-41/node_modules/rulesync/dist/cli/index.js
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "agents" / "fcos-app-installer"
SKILLS = ["adapter-duckdns", "adapter-generic", "adapter-opnsense", "adapter-proxmox", "adapter-truenas",
          "authgw-authentik", "ingress-traefik", "researching-apps-for-self-hosting"]
AGENTS = ["adapter-drafter", "fcos-app-installer"]
problems = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        problems.append(what)


def split(path: Path):
    head, body = path.read_text(encoding="utf-8").split("\n---\n", 1)
    return yaml.safe_load(head[4:]), " ".join(body.split())


def main(argv):
    if len(argv) != 1 or not Path(argv[0]).is_file():
        print(__doc__)
        return 2
    cli = argv[0]
    scratch = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None
    target = Path(tempfile.mkdtemp(prefix="fcos-installed-", dir=scratch))
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    installed = subprocess.run([sys.executable, str(FOLDER / "install.py"), str(target), "--apply"],
                               capture_output=True, text=True, cwd=ROOT, env=env)
    check(installed.returncode == 0, "install.py --apply succeeds")
    generated = subprocess.run(["node", cli, "generate", "--config", "groups/fcos_app_installer.jsonc",
                                "--output-roots", str(target)], capture_output=True, text=True, cwd=ROOT, env=env)
    check(generated.returncode == 0, "rulesync generate succeeds" + ("" if generated.returncode == 0 else
                                                                    "\n" + generated.stdout + generated.stderr))

    check((target / "AGENTS.md").is_file(), "the rules are in AGENTS.md")
    check(not (target / ".opencode" / "opencode.json").exists(), "no opencode.json (no instructions list)")
    found = sorted(p.parent.name for p in (target / ".opencode" / "skills").rglob("SKILL.md"))
    check(found == SKILLS, "the eight skills are siblings under .opencode/skills, and the only skills")
    agents = sorted(p.stem for p in (target / ".opencode" / "agents").glob("*.md"))
    check(agents == AGENTS, "the only agents are the installer and its helper")
    check(sorted(p.stem for p in (target / ".opencode" / "commands").glob("*.md")) == ["add-service"],
          "the only command is /add-service")
    check(all(p.parent.parent == target / ".opencode" / "skills"
              for p in (target / ".opencode" / "skills").rglob("SKILL.md")),
          "every skill is a direct child of the skills folder")

    for name in ("fcos-app-installer", "adapter-drafter"):
        before_meta, before_body = split(FOLDER / "subagents" / f"{name}.md")
        after_meta, after_body = split(target / ".opencode" / "agents" / f"{name}.md")
        check(before_meta["opencode"]["permissions"] == after_meta["permissions"],
              f"{name}: the permission list is unchanged ({len(after_meta['permissions'])} rules)")
        check(before_body == after_body, f"{name}: the instructions are unchanged")
        check(before_meta["opencode"]["mode"] == after_meta["mode"], f"{name}: the mode is kept")
        check(before_meta["description"] == after_meta["description"], f"{name}: the description is kept")
        check(before_meta["opencode"].get("color") == after_meta.get("color"), f"{name}: the color is kept")
    rules_text = " ".join((target / "AGENTS.md").read_text(encoding="utf-8").split())
    for rule in sorted((FOLDER / "rules").glob("*.md")):
        body = " ".join(rule.read_text(encoding="utf-8").split("\n---\n", 1)[1].split())
        check(body in rules_text, f"AGENTS.md holds the whole text of rules/{rule.name}")
    for skill in SKILLS:
        before_meta, before_body = split(FOLDER / "skills" / skill / "SKILL.md")
        after_meta, after_body = split(target / ".opencode" / "skills" / skill / "SKILL.md")
        check(before_meta == after_meta and before_body == after_body, f"{skill}: SKILL.md is unchanged")
        others = [p.relative_to(FOLDER / "skills" / skill) for p in (FOLDER / "skills" / skill).rglob("*")
                  if p.is_file() and p.name != "SKILL.md"]
        check(all((target / ".opencode" / "skills" / skill / o).read_bytes() == (FOLDER / "skills" / skill / o).read_bytes()
                  and (target / ".opencode" / "skills" / skill / o).stat().st_mode & 0o111
                  == (FOLDER / "skills" / skill / o).stat().st_mode & 0o111 for o in others),
              f"{skill}: its other files are unchanged, with their modes")
    command, _ = split(target / ".opencode" / "commands" / "add-service.md")
    source_command, _ = split(FOLDER / "commands" / "add-service.md")
    check(command.get("description") == source_command["description"], "the command's description is kept")
    check(command.get("agent") == "fcos-app-installer", "/add-service still runs in fcos-app-installer")

    requirement = subprocess.run([sys.executable, "tools/check_requirements.py"], capture_output=True, text=True,
                                 cwd=target, env=env)
    check(any(line.startswith("ok") and "launch folder" in line for line in requirement.stdout.splitlines()),
          "check_requirements.py reports the launch folder ok")

    print("running the toolkit's tests in the installed folder (a few minutes)...")
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], capture_output=True, text=True,
                           cwd=target, env=dict(env, PYTHONDONTWRITEBYTECODE="1"))
    summary = [line for line in tests.stderr.splitlines() if line.startswith(("Ran ", "OK", "FAILED"))]
    print("  " + " / ".join(summary))
    check(tests.returncode == 0, "the toolkit's tests pass in the installed folder")
    if tests.returncode:
        print(tests.stderr[-3000:])
    print(f"installed folder left at {target}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
