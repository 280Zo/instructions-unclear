# Runs INSIDE the Authentik worker container, passed to `ak shell -c` (guide 3.9);
# not on the desktop. Waits until every rules file in <blueprints_dir>/custom/ is
# applied as it is now, and prints one line per file.
#
# Authentik 2026.8.5 (blueprints/models.py, blueprints/v1/tasks.py): each file has a
# BlueprintInstance with `status` (successful, warning, error, orphaned, unknown);
# a successful apply stores sha512 of the file's text in `last_applied_hash`. The
# worker records an invalid file only as status "error" (no log line), so this
# checks the status, not the log.
#   ok      <path>            applied, and the file hasn't changed since
#   pending <path> ...        not applied as it is now yet (waits, then fails)
#   error   <path>            still refused at the deadline: see System > Blueprints
# Passed as an argument (ak shell -c), never piped: Django's shell falls back to
# its interactive mode when stdin has no data yet.
import time
from hashlib import sha512
from pathlib import Path

from authentik.blueprints.models import BlueprintInstance
from authentik.lib.config import CONFIG
from authentik.tenants.models import Tenant

try:
    SLEEP
except NameError:
    SLEEP = time.sleep
try:
    DEADLINE_S
except NameError:
    DEADLINE_S = 300
# {"custom/<file>": sha512 hex} computed on the VM (guide 3.9): `podman exec` runs without the
# worker's extra group, so it can't list the rules folder itself (trial VM 2026-11-03).
try:
    EXPECTED
except NameError:
    EXPECTED = None


def _rows():
    root = Path(CONFIG.get("blueprints_dir"))
    rows = []
    if EXPECTED is not None:
        files = sorted(EXPECTED.items())
    else:
        files = [(str(path.relative_to(root)), sha512(path.read_text(encoding="utf-8").encode()).hexdigest())
                 for path in sorted((root / "custom").glob("*.yaml"))]
    for tenant in Tenant.objects.filter(ready=True):
        with tenant:
            for rel, digest in files:
                instance = BlueprintInstance.objects.filter(path=rel).first()
                if instance is None:
                    rows.append(("pending", rel, "(not registered: Authentik ignored this file: bad YAML, "
                                                 "version or instantiate label)"))
                elif instance.status == "error":
                    rows.append(("error", rel, ""))
                elif instance.status == "successful" and instance.last_applied_hash == digest:
                    rows.append(("ok", rel, ""))
                else:
                    rows.append(("pending", rel, f"(status {instance.status}, not applied as it is now)"))
    return rows


def _main() -> int:
    waited = 0
    while True:
        rows = _rows()
        # An error can be left from an earlier push until the restarted worker has
        # re-applied the file, so wait for "ok" until the deadline; only then report.
        if (rows and all(state == "ok" for state, _, _ in rows)) or waited >= DEADLINE_S:
            if not rows:
                print("error   no rules files found to check (none passed in, and the folder can't be listed)")
            for state, rel, note in rows:
                print(f"{state:<7} {rel} {note}".rstrip())
            return 0 if rows and all(state == "ok" for state, _, _ in rows) else 1
        SLEEP(5)
        waited += 5


raise SystemExit(_main())
