#!/usr/bin/env bash
# Remove the FCOS agent's Proxmox access after an install (run as root on the host).
#
#   teardown-agent-access.sh [--move-to <pool>] [--create-pool] [--check]
#
# Moves every guest still in pool fcos-agent into <pool> (so it keeps running
# and stays managed), then removes the agent's ACLs, token, user, roles
# (FCOSAgentVM, FCOSAgentISO) and the emptied pool. A role also granted to
# others is kept; only the agent's grants of it are removed. Without --move-to
# it refuses while the pool has members. Safe to
# re-run: pieces already gone are skipped, and a clean host reports
# "nothing to remove".
#
# Exit codes: 0 done, 1 validation failure, 2 usage error.
# FCOS_ALLOW_NONROOT=1 is test-only (see lib.sh); never set it on a real host.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

TARGET=''
CREATE_POOL=0

usage() {
  cat <<'EOF'
usage: teardown-agent-access.sh [--move-to <pool>] [--create-pool] [--check] [--host-key <key>]

  --move-to <pool>  move the agent's remaining VMs into this pool first
  --create-pool     create <pool> if it does not exist
  --check           show what would be moved and removed; change nothing
  --host-key <key>  the workspace's name for this server; names the token file
                    to delete on the desktop (default: this host's name)
  -h, --help        show this help

Run as root on the Proxmox host, once the install is verified.
EOF
}

usage_error() {
  printf 'error: %s\n\n' "$1" >&2
  usage >&2
  exit 2
}

while (( $# > 0 )); do
  case "$1" in
    --move-to)
      if (( $# < 2 )) || [[ "$2" == --* ]]; then
        usage_error "--move-to needs a pool name"
      fi
      TARGET=$2
      shift 2
      ;;
    --host-key)
      if (( $# < 2 )) || [[ "$2" == --* ]]; then
        usage_error "--host-key needs a value"
      fi
      HOST_KEY=$2
      shift 2
      ;;
    --create-pool) CREATE_POOL=1; shift ;;
    --check) CHECK=1; shift ;;
    -h | --help) usage; exit 0 ;;
    *) usage_error "unknown option: $1" ;;
  esac
done
if (( CREATE_POOL )) && [[ -z "$TARGET" ]]; then
  usage_error "--create-pool needs --move-to <pool>"
fi
if [[ -n "$HOST_KEY" ]]; then
  validate_name "host key" "$HOST_KEY" 64
fi
if [[ -n "$TARGET" ]]; then
  validate_name "pool" "$TARGET" 64
  [[ "$TARGET" != "$POOL" ]] || usage_error "--move-to must be a different pool than ${POOL}"
fi

require_root
require_commands pveum pvesh perl

# 1. Read what exists.
POOLS=$(pvesh get /pools --output-format json | json_field poolid)
MEMBERS=''
if contains "$POOLS" "$POOL"; then
  MEMBERS=$(pvesh get "/pools/${POOL}" --output-format json | json_pool_members | sort -nu | paste -sd, -)
fi
ROLE_NAMES=$(pvesh get /access/roles --output-format json | json_field roleid)
USERS=$(pvesh get /access/users --output-format json | json_field userid)
KEYS=''
if contains "$USERS" "$PVE_USER"; then
  KEYS=$(pvesh get "/access/users/${PVE_USER}/token" --output-format json | json_field tokenid)
fi
# Every grant held by the agent's user or token, whichever path it is on.
ACLS=$(pvesh get /access/acl --output-format json | json_acls)
ACL_PATHS=()
ACL_ROLES=()
ACL_KINDS=()
ACL_WHO=()
while IFS=$'\t' read -r path kind who role; do
  if [[ ( "$kind" == user && "$who" == "$PVE_USER" ) || ( "$kind" == token && "$who" == "$KEY_ID" ) ]]; then
    ACL_PATHS+=("$path")
    ACL_ROLES+=("$role")
    ACL_KINDS+=("$kind")
    ACL_WHO+=("$who")
  fi
done <<<"$ACLS"

# 2. Decide, and refuse before changing anything.
target_exists=0
if [[ -n "$TARGET" ]] && contains "$POOLS" "$TARGET"; then
  target_exists=1
fi
if [[ -n "$MEMBERS" ]]; then
  if [[ -z "$TARGET" ]]; then
    die 1 "pool ${POOL} still holds guests (VMIDs: ${MEMBERS//,/ }); rerun with --move-to <your pool> to move them first"
  fi
  if (( ! target_exists && ! CREATE_POOL )); then
    die 1 "pool '${TARGET}' does not exist; create it first or add --create-pool"
  fi
fi

have_pool=0; contains "$POOLS" "$POOL" && have_pool=1
have_role=0; contains "$ROLE_NAMES" "$ROLE" && have_role=1
have_iso_role=0; contains "$ROLE_NAMES" "$ISO_ROLE" && have_iso_role=1
# A role someone else also holds stays (only the agent's grants of it go):
# deleting a role in Proxmox also drops every other grant of it.
KEPT=''
for r in "$ROLE" "$ISO_ROLE"; do
  holders=$(other_holders "$r" "$ACLS")
  if [[ -n "$holders" ]]; then
    warn "role ${r} is also granted to others ($(join_lines <<<"$holders")); keeping the role"
    KEPT="${KEPT:+${KEPT}, }${r}"
    if [[ "$r" == "$ROLE" ]]; then have_role=0; else have_iso_role=0; fi
  fi
done
have_user=0; contains "$USERS" "$PVE_USER" && have_user=1
have_token=0; contains "$KEYS" "$KEY_NAME" && have_token=1

host=${HOST_KEY:-$(short_host)}  # the workspace's name for this server names the token file
if (( CHECK )); then
  info "Check only: nothing will be changed."
fi

if (( ! have_pool && ! have_role && ! have_iso_role && ! have_user && ! have_token && ${#ACL_PATHS[@]} == 0 )); then
  if [[ -n "$KEPT" ]]; then
    info "The agent's access is already gone: nothing to remove (no pool, user, token or grants; shared roles kept: ${KEPT})."
  else
    info "The agent's access is already gone: nothing to remove (no pool, roles, user, token or grants)."
  fi
else
  # 3. Move the guests out, then remove the access.
  if [[ -n "$MEMBERS" ]]; then
    if (( ! target_exists )); then
      change "create pool ${TARGET}" pveum pool add "$TARGET"
    fi
    change "move guests ${MEMBERS//,/ } from ${POOL} to ${TARGET}" pveum pool modify "$TARGET" --vms "$MEMBERS" --allow-move 1
  fi
  for (( i = 0; i < ${#ACL_PATHS[@]}; i++ )); do
    flag="--${ACL_KINDS[$i]}s"
    change "remove ${ACL_ROLES[$i]} on ${ACL_PATHS[$i]} from ${ACL_KINDS[$i]} ${ACL_WHO[$i]}" \
      pveum acl delete "${ACL_PATHS[$i]}" --roles "${ACL_ROLES[$i]}" "$flag" "${ACL_WHO[$i]}"
  done
  if (( have_token )); then
    change "remove token ${KEY_ID}" pveum user token remove "$PVE_USER" "$KEY_NAME"
  fi
  if (( have_user )); then
    change "remove user ${PVE_USER}" pveum user delete "$PVE_USER"
  fi
  if (( have_role )); then
    change "remove role ${ROLE}" pveum role delete "$ROLE"
  fi
  if (( have_iso_role )); then
    change "remove role ${ISO_ROLE}" pveum role delete "$ISO_ROLE"
  fi
  if (( have_pool )); then
    change "remove pool ${POOL}" pveum pool delete "$POOL"
  fi
  if (( CHECK )); then
    info "Check complete: ${PENDING} change(s) would be made."
  else
    info "Teardown complete."
  fi
fi

printf '%s\n' \
  "" \
  "Delete the token file on your desktop (fish); replace <workspace> with your workspace folder:" \
  "" \
  "  rm -f <workspace>/secrets/proxmox-${host}.token"
