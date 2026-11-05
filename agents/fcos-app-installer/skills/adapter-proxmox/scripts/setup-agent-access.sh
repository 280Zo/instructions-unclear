#!/usr/bin/env bash
# Give the FCOS agent a pool-scoped Proxmox API token (run as root on the host).
#
#   setup-agent-access.sh --storage <id> --bridge <name> [--iso-storage <id>]
#                         [--zone localnetwork] [--node <name>] [--check] [--rotate]
#
# Creates pool fcos-agent, role FCOSAgentVM, user fcos-agent@pve (no password)
# and token fcos-bootstrap (privilege separation on), then grants the role on
# the pool, PVEDatastoreUser on the storage and PVESDNUser on the bridge to
# both the user and the token. With --iso-storage it also creates role
# FCOSAgentISO (upload ISOs, list the storage) and grants it on that storage,
# which must allow "iso" and "import" content. Safe to re-run: existing pieces are kept, all
# grants are re-applied, and the token secret is printed only when the token is
# created (or replaced with --rotate).
#
# Exit codes: 0 done, 1 validation failure, 2 usage error.
# FCOS_ALLOW_NONROOT=1 is test-only (see lib.sh); never set it on a real host.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

STORAGE=''
ISO_STORAGE=''
BRIDGE=''
ZONE='localnetwork'
NODE=''
ROTATE=0
SECRET_BLOCK=''

usage() {
  cat <<'EOF'
usage: setup-agent-access.sh --storage <id> --bridge <name> [options]

  --storage <id>   storage the agent may put VM disks on (see: pvesm status)
                   (it must be available on the node)
  --bridge <name>  network bridge the agent may attach VMs to (e.g. vmbr0)
  --iso-storage <id>
                   directory storage holding the FCOS image and the VMs'
                   config discs; must allow "iso" and "import" content.
                   Without it the agent cannot upload config discs
  --zone <name>    SDN zone holding the bridge (default: localnetwork)
  --node <name>    node name for the storage and bridge lookup (default: this host)
  --host-key <key> the workspace's name for this server; names the token file
                   in the printed store command (default: this host's name)
  --check          report what exists and what would change; change nothing
  --rotate         replace the token (use when the secret was lost)
  -h, --help       show this help

Run as root on the Proxmox host. Prints the token secret once, on creation.
EOF
}

usage_error() {
  printf 'error: %s\n\n' "$1" >&2
  usage >&2
  exit 2
}

while (( $# > 0 )); do
  case "$1" in
    --storage | --iso-storage | --bridge | --zone | --node | --host-key)
      if (( $# < 2 )) || [[ "$2" == --* ]]; then
        usage_error "$1 needs a value"
      fi
      case "$1" in
        --host-key) HOST_KEY=$2 ;;
        --storage) STORAGE=$2 ;;
        --iso-storage) ISO_STORAGE=$2 ;;
        --bridge) BRIDGE=$2 ;;
        --zone) ZONE=$2 ;;
        --node) NODE=$2 ;;
      esac
      shift 2
      ;;
    --check) CHECK=1; shift ;;
    --rotate) ROTATE=1; shift ;;
    -h | --help) usage; exit 0 ;;
    *) usage_error "unknown option: $1" ;;
  esac
done
[[ -n "$STORAGE" ]] || usage_error "--storage is required"
[[ -n "$BRIDGE" ]] || usage_error "--bridge is required"

if [[ -n "$HOST_KEY" ]]; then
  validate_name "host key" "$HOST_KEY" 64
fi
validate_name "storage" "$STORAGE" 64
if [[ -n "$ISO_STORAGE" ]]; then
  validate_name "iso storage" "$ISO_STORAGE" 64
fi
validate_name "bridge" "$BRIDGE" 15
validate_name "zone" "$ZONE" 64
if [[ -z "$NODE" ]]; then
  NODE=$(short_host)
fi
validate_name "node" "$NODE" 64

require_root
require_commands pveum pvesh perl

print_secret() {
  [[ -n "$SECRET_BLOCK" ]] || return 0
  printf '\nToken created. The secret below is shown only once; copy its value row now.\n\n%s\n\n' "$SECRET_BLOCK"
  printf '%s\n' "Don't paste it into the chat. The agent gives you the next step, which stores it on your desktop."
  SECRET_BLOCK=''
}

# If a later step fails after the token exists, still show the secret once.
on_exit() {
  local rc=$?
  trap - EXIT
  if [[ -n "$SECRET_BLOCK" ]]; then
    (( rc == 0 )) || warn "setup stopped early, but the token was already created; its secret is below"
    print_secret
  fi
  exit "$rc"
}
trap on_exit EXIT

info "Proxmox node: ${NODE}"
if (( CHECK )); then
  info "Check only: nothing will be changed."
fi

# 1. Validate the host facts before any change.
STORAGES_JSON=$(pvesh get "/nodes/${NODE}/storage" --output-format json)
STORAGES=$(json_field storage <<<"$STORAGES_JSON")
BRIDGES=$(pvesh get "/nodes/${NODE}/network" --type bridge --output-format json | json_field iface)
problems=0
if ! contains "$STORAGES" "$STORAGE"; then
  printf 'error: storage %s does not exist. Storages here:\n%s\n' "'${STORAGE}'" "$(sed 's/^/  /' <<<"$STORAGES")" >&2
  problems=1
fi
if [[ -n "$ISO_STORAGE" ]]; then
  if ! contains "$STORAGES" "$ISO_STORAGE"; then
    printf 'error: iso storage %s does not exist. Storages here:\n%s\n' "'${ISO_STORAGE}'" "$(sed 's/^/  /' <<<"$STORAGES")" >&2
    problems=1
  else
    ISO_CONTENT=$(json_storage_content "$ISO_STORAGE" <<<"$STORAGES_JSON")
    allowed=nothing
    if [[ -n "$ISO_CONTENT" ]]; then
      allowed=$(paste -sd, - <<<"$ISO_CONTENT")
    fi
    for needed in iso import; do
      if ! contains "$ISO_CONTENT" "$needed"; then
        printf 'error: storage %s does not allow content "%s" (it allows: %s); add it under Datacenter > Storage > %s > Content\n' \
          "'${ISO_STORAGE}'" "$needed" "$allowed" "$ISO_STORAGE" >&2
        problems=1
      fi
    done
  fi
fi
if ! contains "$BRIDGES" "$BRIDGE"; then
  printf 'error: bridge %s does not exist on node %s. Bridges here:\n%s\n' "'${BRIDGE}'" "'${NODE}'" "$(sed 's/^/  /' <<<"$BRIDGES")" >&2
  problems=1
fi
(( problems == 0 )) || exit 1

# 2. Read what exists.
POOLS=$(pvesh get /pools --output-format json | json_field poolid)
ROLES_JSON=$(pvesh get /access/roles --output-format json)
ROLE_NAMES=$(json_field roleid <<<"$ROLES_JSON")
USERS=$(pvesh get /access/users --output-format json | json_field userid)
USER_EXISTS=0
KEYS=''
KEY_PRIVSEP=1
if contains "$USERS" "$PVE_USER"; then
  USER_EXISTS=1
  KEYS_JSON=$(pvesh get "/access/users/${PVE_USER}/token" --output-format json)
  KEYS=$(json_field tokenid <<<"$KEYS_JSON")
  if contains "$KEYS" "$KEY_NAME"; then
    KEY_PRIVSEP=$(json_token_privsep "$KEY_NAME" <<<"$KEYS_JSON")
  fi
fi
ACLS=$(pvesh get /access/acl --output-format json | json_acls)

if contains "$KEYS" "$KEY_NAME" && [[ "$KEY_PRIVSEP" == 0 ]] && (( ! ROTATE )); then
  die 1 "token ${KEY_ID} exists without privilege separation (it has the user's full rights); rerun with --rotate to replace it"
fi

# A role of the same name that someone else also holds: never rewrite it (that
# would change their rights); with the expected privileges it is used as is.
check_shared_role() {
  local role=$1 privs=$2 holders
  contains "$ROLE_NAMES" "$role" || return 0
  holders=$(other_holders "$role" "$ACLS")
  [[ -n "$holders" ]] || return 0
  if [[ "$(json_role_privs "$role" <<<"$ROLES_JSON")" != "$(norm_privs "$privs")" ]]; then
    printf 'error: role %s exists with other privileges and is also granted to:\n%s\n' "$role" "$(sed 's/^/  /' <<<"$holders")" >&2
    printf 'It is not the agent'"'"'s to change. Remove those grants, or change or delete the role yourself, then run this again.\n' >&2
    exit 1
  fi
  warn "role ${role} is also granted to others ($(join_lines <<<"$holders")); teardown will keep it"
}
check_shared_role "$ROLE" "$ROLE_PRIVS"
if [[ -n "$ISO_STORAGE" ]]; then
  check_shared_role "$ISO_ROLE" "$ISO_ROLE_PRIVS"
fi

# 3. Create what is missing.
info "Creating or checking the agent's access:"
if contains "$POOLS" "$POOL"; then
  info "  ok: pool ${POOL} exists"
else
  change "create pool ${POOL}" pveum pool add "$POOL" --comment "FCOS agent VMs"
fi

if contains "$ROLE_NAMES" "$ROLE"; then
  have=$(json_role_privs "$ROLE" <<<"$ROLES_JSON")
  if [[ "$have" == "$(norm_privs "$ROLE_PRIVS")" ]]; then
    info "  ok: role ${ROLE} exists with the expected privileges"
  else
    change "reset role ${ROLE} to the expected privileges" pveum role modify "$ROLE" --privs "$ROLE_PRIVS"
  fi
else
  change "create role ${ROLE}" pveum role add "$ROLE" --privs "$ROLE_PRIVS"
fi

if [[ -n "$ISO_STORAGE" ]]; then
  if contains "$ROLE_NAMES" "$ISO_ROLE"; then
    have=$(json_role_privs "$ISO_ROLE" <<<"$ROLES_JSON")
    if [[ "$have" == "$(norm_privs "$ISO_ROLE_PRIVS")" ]]; then
      info "  ok: role ${ISO_ROLE} exists with the expected privileges"
    else
      change "reset role ${ISO_ROLE} to the expected privileges" pveum role modify "$ISO_ROLE" --privs "$ISO_ROLE_PRIVS"
    fi
  else
    change "create role ${ISO_ROLE}" pveum role add "$ISO_ROLE" --privs "$ISO_ROLE_PRIVS"
  fi
fi

if (( USER_EXISTS )); then
  info "  ok: user ${PVE_USER} exists"
else
  change "create user ${PVE_USER} (no password)" pveum user add "$PVE_USER" --comment "FCOS agent API user"
fi

create_token=0
if contains "$KEYS" "$KEY_NAME"; then
  if (( ROTATE )); then
    change "remove token ${KEY_ID} (rotate)" pveum user token remove "$PVE_USER" "$KEY_NAME"
    create_token=1
  else
    info "  ok: token already exists; secret not shown (use --rotate to replace)"
  fi
else
  create_token=1
fi
if (( create_token )); then
  if (( CHECK )); then
    info "  would: create token ${KEY_ID} with privilege separation"
    PENDING=$((PENDING + 1))
  else
    SECRET_BLOCK=$(pveum user token add "$PVE_USER" "$KEY_NAME" --privsep 1)
    info "  done: create token ${KEY_ID} with privilege separation"
  fi
fi

# 4. Grant the roles, to the user and to the token. Re-applied on every run.
grant() {
  local path=$1 role=$2 kind=$3 who=$4 flag
  flag="--${kind}s"
  if (( CHECK )); then
    # A replaced token loses its grants (Proxmox drops ACL entries of a removed
    # token), so under --rotate the token's grants are always "would".
    if ! { [[ "$kind" == token ]] && (( create_token )); } \
        && contains "$ACLS" "$(printf '%s\t%s\t%s\t%s' "$path" "$kind" "$who" "$role")"; then
      info "  ok: ${role} on ${path} for ${kind} ${who}"
    else
      info "  would: grant ${role} on ${path} to ${kind} ${who}"
      PENDING=$((PENDING + 1))
    fi
  else
    pveum acl modify "$path" --roles "$role" "$flag" "$who"
    info "  done: grant ${role} on ${path} to ${kind} ${who}"
  fi
}

info "Granting access:"
targets=("/pool/${POOL}|${ROLE}" "/storage/${STORAGE}|PVEDatastoreUser" "/sdn/zones/${ZONE}/${BRIDGE}|PVESDNUser")
if [[ -n "$ISO_STORAGE" ]]; then
  targets+=("/storage/${ISO_STORAGE}|${ISO_ROLE}")
fi
for target in "${targets[@]}"; do
  grant "${target%%|*}" "${target##*|}" user "$PVE_USER"
  grant "${target%%|*}" "${target##*|}" token "$KEY_ID"
done
# Upload grants from an earlier run stay (this script never removes a grant);
# name them, so the note below is true.
old_iso=$(agent_grants "$ISO_ROLE" "$ACLS" | awk -F'\t' -v keep="/storage/${ISO_STORAGE}" '$1 != keep')
if [[ -n "$old_iso" ]]; then
  info "Note: from an earlier run, the agent still holds ${ISO_ROLE} on:"
  cut -f1 <<<"$old_iso" | sort -u | sed 's/^/  /'
  info "  They stay until teardown-agent-access.sh removes the agent's access. To remove only these grants now:"
  while IFS=$'\t' read -r path kind who; do
    if [[ "$kind" == token ]]; then
      printf "    pveum acl delete %s --roles %s --tokens '%s'\n" "$path" "$ISO_ROLE" "$who"
    else
      printf '    pveum acl delete %s --roles %s --users %s\n' "$path" "$ISO_ROLE" "$who"
    fi
  done <<<"$old_iso"
elif [[ -z "$ISO_STORAGE" ]]; then
  info "Note: no --iso-storage given, so the agent cannot upload VM config discs or read images there."
fi

# 5. Show what the token can do.
if (( CHECK )) && { (( ! USER_EXISTS )) || (( create_token )) || (( ROTATE )); }; then
  info "Effective token permissions: not shown (the token does not exist yet or would be replaced)."
else
  info "Effective permissions of ${KEY_ID}:"
  pveum user token permissions "$PVE_USER" "$KEY_NAME"
fi

if (( CHECK )); then
  if (( PENDING == 0 )); then
    info "Check complete: everything is in place."
  else
    info "Check complete: ${PENDING} change(s) pending; run again without --check to apply."
  fi
else
  info "Setup complete. After the install is verified, run teardown-agent-access.sh to remove this access."
  print_secret
fi
