#!/usr/bin/env bash
# Build a tiny NoCloud config ISO: volume label "cidata", user-data = the
# Ignition JSON, meta-data empty.
# Usage: tools/make_cidata_iso.sh <vm.ign> <out.iso>
#
# xorriso runs in a throwaway container from the already-pulled Podman image
# pinned in tools/images.env (podman if installed, else docker); the package is
# installed with dnf inside the container, so nothing is installed on this
# machine. The input is mounted read-only and is the only mount. No image is
# pulled: if the image is missing, the script stops and says so. The finished
# ISO is read back by tools/check_cidata_iso.py and used only if it holds
# exactly the input.
set -euo pipefail

IMAGE="$({ grep -m1 '^PODMAN_IMAGE=' "$(dirname "$0")/images.env" || true; } | cut -d= -f2-)"
MAX_BYTES=$((8 * 1024 * 1024))

die() { echo "make_cidata_iso: $*" >&2; exit "${2:-1}"; }

[[ $# -eq 2 ]] || die "usage: $0 <vm.ign> <out.iso>" 2
ign="$1"
out="$2"

[[ -f "$ign" && -r "$ign" ]] || die "$ign is not a readable file" 2
[[ ! -e "$out" && ! -L "$out" ]] || die "$out already exists; not overwriting" 2
[[ -d "$(dirname "$out")" ]] || die "folder for $out does not exist" 2
size="$(stat -c %s "$ign")"
(( size > 0 && size <= MAX_BYTES )) || die "$ign must be between 1 byte and $MAX_BYTES bytes" 2

runtime="$(command -v podman || command -v docker || true)"
[[ -n "$runtime" ]] || die "needs podman or docker" 3
[[ -n "$IMAGE" ]] || die "PODMAN_IMAGE is missing in tools/images.env" 3
"$runtime" image inspect "$IMAGE" >/dev/null 2>&1 \
    || die "image $IMAGE is not pulled; pull it once yourself (nothing is downloaded for you): $runtime pull $IMAGE" 3

stage="" log="" work=""
trap 'rm -rf "${stage:-}" "${work:-}"; rm -f "${log:-}"' EXIT  # set first: a failing mktemp below leaves nothing behind
stage="$(mktemp -d)"
log="$(mktemp)"
# A private folder (mode 0700) beside the output: nobody else can swap the file between the check and its
# placement, and the final link is on the same filesystem.
work="$(mktemp -d "$(dirname "$out")/.cidata-XXXXXX")" || die "cannot create a work folder beside $out" 1
tmp_out="$work/out.iso"

cp -- "$ign" "$stage/user-data"
: >"$stage/meta-data"
chmod 0755 "$stage"
chmod 0644 "$stage/user-data" "$stage/meta-data"

# Container output is shown only if the build fails.
if ! "$runtime" run --rm --pull=never --user root --security-opt no-new-privileges \
        -v "$stage:/in:ro,z" "$IMAGE" \
        sh -c 'dnf -y install xorriso >&2 && xorriso -as mkisofs -quiet -V cidata -J -r -o /tmp/o.iso /in >&2 && cat /tmp/o.iso' \
        >"$tmp_out" 2>"$log"; then
    tail -n 5 "$log" >&2 || true
    die "building the ISO failed (is the network reachable for dnf?)" 1
fi
[[ -s "$tmp_out" ]] || die "the ISO came out empty" 1
# The container installed its tool at run time and its output becomes the VM's first-boot configuration, so
# read the finished file back here, with the standard library only: it must hold exactly the input.
python3 "$(dirname "$0")/check_cidata_iso.py" "$tmp_out" "$ign" >/dev/null || die "the ISO does not match the input; not using it" 1

chmod 0600 "$tmp_out"
# A hard link, not a move: it fails if $out has appeared in the meantime instead of skipping silently. Where
# the filesystem has no hard links, a move that never overwrites is used instead, and checked.
if ! why="$(ln -- "$tmp_out" "$out" 2>&1)"; then
    [[ ! -e "$out" && ! -L "$out" ]] || die "$out appeared while the ISO was being built; not overwriting" 1
    mv -n -- "$tmp_out" "$out" 2>/dev/null && [[ ! -e "$tmp_out" ]] \
        || die "could not place $out ($why)" 1
fi
echo "make_cidata_iso: wrote $out (label cidata, user-data $size bytes)"
