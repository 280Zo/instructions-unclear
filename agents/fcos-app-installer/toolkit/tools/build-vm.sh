#!/usr/bin/env bash
# Build and check one VM folder of rendered Butane fragments:
#   - config.bu merges base-config first (the admin account's UID)
#   - Butane --strict on every fragment (*.bu except config.bu) -> igns/
#   - Butane --strict on config.bu (merges igns/) -> <vm>.ign
#   - nft -c on the firewall the VM would load
#   - Quadlet -dryrun on every Quadlet the VM would get
#   - every Quadlet volume under a root its require-mounts check covers
#   - no secret-looking values in any rendered or embedded file
# Usage: tools/build-vm.sh <vm-dir>
set -euo pipefail

if [[ $# -ne 1 || ! -d "$1" ]]; then
    echo "usage: $0 <vm-dir>" >&2
    exit 2
fi

dir="$(realpath "$1")"
vm="$(basename "$dir")"

# Ignition creates users in merge order, and useradd gives an account without
# a fixed UID the next one above every existing user. base-config (the admin
# account) must merge first, so the admin gets 1000/1001, the numbers
# tools/check_workspace.py keeps free, and never one an app may claim later.
if [[ -f "$dir/config.bu" ]]; then
    first="$( { grep -m1 -E '^[[:space:]]*- local: ' "$dir/config.bu" || true; } | sed -E 's/^[[:space:]]*- local: //')"
    if [[ "$first" != "igns/base-config.ign" ]]; then
        echo "FAIL  merge order: config.bu must merge igns/base-config.ign first (found: ${first:-nothing})"
        exit 1
    fi
fi
if command -v podman >/dev/null 2>&1; then
    runtime=podman
elif command -v docker >/dev/null 2>&1; then
    runtime=docker
else
    echo "build-vm: need podman or docker" >&2
    exit 1
fi
# The pinned images, read (never executed) from tools/images.env.
pin() { { grep -m1 "^$1=" "$(dirname "$0")/images.env" || true; } | cut -d= -f2-; }
butane_image="$(pin BUTANE_IMAGE)"
podman_image="$(pin PODMAN_IMAGE)"
# Nothing is downloaded for you: a missing image stops the build with the command to pull it.
for image in "$butane_image" "$podman_image"; do
    if [[ -z "$image" ]] || ! "$runtime" image inspect "$image" >/dev/null 2>&1; then
        echo "build-vm: image ${image:-(missing in tools/images.env)} is not here; pull it once yourself:" >&2
        echo "  $runtime pull $image" >&2
        exit 1
    fi
done

rm -rf "$dir/igns" "$dir/.rootfs" "$dir/.quadlet" "$dir/$vm.ign"
mkdir -p "$dir/igns"
failures=0

butane() {
    "$runtime" run --rm -i --pull=never -v "$dir:/files:ro,z" "$butane_image" \
        --strict --pretty --files-dir /files
}

mapfile -t fragments < <(cd "$dir" && find . -type f -name '*.bu' ! -name 'config.bu' | sort)
for rel in "${fragments[@]}"; do
    name="$(basename "$rel" .bu)"
    if butane <"$dir/$rel" >"$dir/igns/$name.ign"; then
        echo "ok    butane  $rel"
    else
        echo "FAIL  butane  $rel"
        failures=$((failures + 1))
    fi
done

config="$(cd "$dir" && find . -type f -name 'config.bu' | sort | head -n 1)"
if [[ -n "$config" ]]; then
    if butane <"$dir/$config" >"$dir/$vm.ign"; then
        echo "ok    butane  $config -> $vm.ign"
    else
        echo "FAIL  butane  $config"
        failures=$((failures + 1))
    fi
fi

# Unpack every file the Ignition configs would write into a scratch rootfs.
rootfs="$dir/.rootfs"
python3 - "$dir/igns" "$rootfs" <<'EOF'
import base64, gzip, json, os, sys, urllib.parse
igns, rootfs = sys.argv[1], sys.argv[2]
for name in sorted(os.listdir(igns)):
    config = json.load(open(os.path.join(igns, name)))
    for entry in config.get("storage", {}).get("files", []):
        source = entry.get("contents", {}).get("source")
        if not source or not source.startswith("data:"):
            continue
        head, body = source.split(",", 1)
        raw = base64.b64decode(body) if head.endswith(";base64") else urllib.parse.unquote_to_bytes(body)
        if entry["contents"].get("compression") == "gzip":
            raw = gzip.decompress(raw)
        dest = os.path.join(rootfs, entry["path"].lstrip("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(raw)
EOF

if [[ -f "$rootfs/etc/sysconfig/nftables.conf" ]]; then
    if "$runtime" run --rm --pull=never --cap-add NET_ADMIN -v "$rootfs:/r:ro,z" "$podman_image" sh -c \
        'mkdir -p /etc/nftables.d && cp /r/etc/nftables.d/*.nft /etc/nftables.d/ 2>/dev/null; nft -c -f /r/etc/sysconfig/nftables.conf' \
        >"$dir/.nft.txt" 2>&1; then
        echo "ok    nft     /etc/sysconfig/nftables.conf"
    else
        echo "FAIL  nft     (see $dir/.nft.txt)"
        failures=$((failures + 1))
    fi
fi

containers=()
if [[ -d "$rootfs/etc/containers/systemd" ]]; then
    mapfile -t containers < <(find "$rootfs/etc/containers/systemd" -type f \
        \( -name '*.container' -o -name '*.network' -o -name '*.volume' -o -name '*.pod' \) | sort)
fi
if [[ ${#containers[@]} -gt 0 ]]; then
    mkdir -p "$dir/.quadlet"
    for path in "${containers[@]}"; do
        cp "$path" "$dir/.quadlet/"
    done
    if "$runtime" run --rm --pull=never -v "$dir/.quadlet:/etc/containers/systemd:ro,z" "$podman_image" \
        /usr/libexec/podman/quadlet -dryrun >"$dir/.quadlet.txt" 2>&1 \
        && ! grep -qiE 'error|unsupported key|converting .*:|was not found' "$dir/.quadlet.txt"; then
        echo "ok    quadlet ${#containers[@]} file(s)"
    else
        echo "FAIL  quadlet (see $dir/.quadlet.txt)"
        failures=$((failures + 1))
    fi
    # Every Volume= host path must sit under a root its require-mounts line checks.
    if python3 "$(dirname "$0")/check_mount_roots.py" "$dir/.quadlet" >"$dir/.mounts.txt" 2>&1; then
        echo "ok    mounts  every volume under a checked mount root"
    else
        echo "FAIL  mounts  (see $dir/.mounts.txt)"
        cat "$dir/.mounts.txt"
        failures=$((failures + 1))
    fi
fi

# Scans rendered files and, through .rootfs/, every file the Ignition
# configs embed. Exit 1 = hits, anything else = the scanner itself broke.
scan_rc=0
python3 "$(dirname "$0")/secret_scan.py" "$dir" || scan_rc=$?
if [[ $scan_rc -eq 0 ]]; then
    echo "ok    secret scan"
else
    echo "FAIL  secret scan (lines above, exit $scan_rc)"
    failures=$((failures + 1))
fi

if [[ $failures -gt 0 ]]; then
    echo "build-vm: $failures failure(s)"
    exit 1
fi
echo "build-vm: all checks passed ($dir/$vm.ign)"
