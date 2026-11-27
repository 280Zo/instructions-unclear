"""Opt-in check before changing the rulesync pin: compare two rulesync CLIs on every group.

Generates each group in groups/ with both CLIs into a fresh folder under /tmp/opencode. Home-folder
groups run with --global inside a throwaway HOME; folder groups run with --output-roots, once with
their own targets and once for Claude Code, Codex CLI, Gemini CLI and Cursor. It then merges the
default group into a seeded opencode.jsonc with each CLI and reports which seeded settings survive.
It reports every differing path. Nothing is downloaded, and live settings are never read or written.

    python3 tests/compare_rulesync_versions.py OLD_CLI NEW_CLI

Each CLI is an existing rulesync dist/cli/index.js. Exit status 1 means a generate run failed, the
outputs differ, or the merged opencode.jsonc files differ. The warning counts are lines containing
"warn" in each run's output, a rough signal. It refuses to run while rulesync.local.jsonc exists,
because that file could change what a group selects.
"""

import argparse
import filecmp
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parent.parent
HOME_GROUPS = ("default", "work")
OTHER_TARGETS = "claudecode,codexcli,geminicli,cursor"
SEED = """{
  // seed comment
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/seed-model",
  "plugins": ["seed-plugin@1.0.0"],
  "permission": { "bash": "ask" },
  "mcp": {
    "timeout": 45000,
    "servers": { "obsolete-seed": { "type": "local", "command": ["true"] } }
  }
}
"""
SEEDED = {
    "comment": "// seed comment",
    "model": '"anthropic/seed-model"',
    "plugins": '"seed-plugin@1.0.0"',
    "permission": '"bash": "ask"',
    "mcp.timeout": "45000",
    "obsolete server": "obsolete-seed",
}


def home_env(home):
    return {"PATH": os.environ["PATH"], "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_DATA_HOME": str(home / ".local/share"), "XDG_STATE_HOME": str(home / ".local/state"),
            "XDG_CACHE_HOME": str(home / ".cache")}


def run(cli, args, env, log):
    result = subprocess.run(["node", str(cli), "generate", *args], cwd=REPO, env=env,
                            capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr)
    warnings = sum("warn" in line.lower() for line in (result.stdout + result.stderr).splitlines())
    return result.returncode, warnings


def generate_all(cli, out):
    """One output folder per group and target set; returns {name: (exit, warnings)}."""
    status = {}
    for config in sorted((REPO / "groups").glob("*.jsonc")):
        group = config.stem
        if group in HOME_GROUPS:
            home = out / group
            home.mkdir(parents=True)
            status[group] = run(cli, ["--config", f"groups/{group}.jsonc", "--global"], home_env(home),
                                out / f"{group}.log")
            continue
        for name, extra in ((group, []), (f"{group}+other-tools", ["--targets", OTHER_TARGETS])):
            folder = out / name
            folder.mkdir(parents=True)
            env = {"PATH": os.environ["PATH"], "HOME": str(out / ".home")}
            status[name] = run(cli, ["--config", f"groups/{group}.jsonc", "--output-roots", str(folder), *extra],
                               env, out / f"{name}.log")
    return status


def merge(cli, out):
    """Generate default over a seeded opencode.jsonc; returns (exit, merged text)."""
    home = out / "merge"
    config = home / ".config/opencode/opencode.jsonc"
    config.parent.mkdir(parents=True)
    config.write_text(SEED)
    code, _ = run(cli, ["--config", "groups/default.jsonc", "--global"], home_env(home), out / "merge.log")
    return code, config.read_text()


def files(root):
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file() and ".cache" not in p.relative_to(root).parts}


def differing(left, right):
    """Paths present on one side only or whose bytes differ."""
    old, new = files(left), files(right)
    changed = {p for p in old & new if not filecmp.cmp(left / p, right / p, shallow=False)}
    return sorted(str(p) for p in (old ^ new) | changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("old_cli", type=Path, help="Existing rulesync dist/cli/index.js for the current pin")
    parser.add_argument("new_cli", type=Path, help="Existing rulesync dist/cli/index.js for the candidate")
    args = parser.parse_args()
    for cli in (args.old_cli, args.new_cli):
        if not cli.is_file():
            parser.error(f"{cli} does not exist")
    if (REPO / "rulesync.local.jsonc").exists():
        parser.error("rulesync.local.jsonc exists and could change each group's selection; move it aside first")
    Path("/tmp/opencode").mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="rulesync-compare-", dir="/tmp/opencode"))
    print(f"Evidence directory: {root}", flush=True)

    status, merged = {}, {}
    for side, cli in (("old", args.old_cli.resolve()), ("new", args.new_cli.resolve())):
        status[side] = generate_all(cli, root / side / "groups")
        merged[side] = merge(cli, root / side)

    failed = False
    for name in status["old"]:
        old, new = status["old"][name], status["new"][name]
        diff = differing(root / "old/groups" / name, root / "new/groups" / name)
        ok = old[0] == new[0] == 0 and not diff
        failed |= not ok
        print(f"{'PASS' if ok else 'FAIL'} {name}: exit {old[0]}/{new[0]}, warnings {old[1]}/{new[1]}, "
              f"{len(diff)} differing paths", flush=True)
        for path in diff[:15]:
            print(f"    {path}")

    for side in ("old", "new"):
        code, text = merged[side]
        kept = [k for k, needle in SEEDED.items() if needle in text]
        dropped = [k for k in SEEDED if k not in kept]
        print(f"merge {side}: exit {code}; kept {', '.join(kept) or 'nothing'}; "
              f"dropped {', '.join(dropped) or 'nothing'}", flush=True)
    same = merged["old"][1] == merged["new"][1]
    failed |= not same
    print(f"{'PASS' if same else 'FAIL'} merged opencode.jsonc is {'identical' if same else 'different'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
