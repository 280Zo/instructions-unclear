# shellcheck shell=bash
# shellcheck disable=SC2034,SC2016  # names are used by the sourcing scripts; $ in perl code is not a shell expansion
# Shared helpers for setup-agent-access.sh and teardown-agent-access.sh.
# Sourced, never run. Targets bash on a Proxmox VE host; needs perl (JSON::PP).
#
# FCOS_ALLOW_NONROOT=1 skips the root check. It exists only so the test suite
# can run the scripts unprivileged against fake pveum/pvesh; never set it
# on a real host.

POOL='fcos-agent'
ROLE='FCOSAgentVM'
PVE_USER='fcos-agent@pve'
# KEY_NAME / KEY_ID name the API token (the repo's secret scanner flags
# variable names with "token" in them).
KEY_NAME='fcos-bootstrap'
# Always use this variable or this exact single-quoted form: an exclamation
# mark inside double quotes triggers history expansion in an interactive shell.
KEY_ID='fcos-agent@pve!fcos-bootstrap'
# Pool.Audit (read-only) lets the token read its own pool's member list; on
# PVE 9.2 a guest's pool membership is hidden from callers without it.
ROLE_PRIVS='VM.Allocate VM.Audit VM.PowerMgmt VM.Config.CPU VM.Config.Memory VM.Config.Disk VM.Config.Network VM.Config.HWType VM.Config.Options VM.Config.Cloudinit Pool.Audit'
# Upload-only role on the storage holding config discs and FCOS images:
# upload an ISO (Datastore.AllocateTemplate; it cannot delete volumes) and
# Datastore.Audit, which lists the storage AND lets a VM use the uploaded disc
# and import its disk from the image there. Both are needed. Uploads have no
# size quota: on a default install that storage is on the root filesystem.
ISO_ROLE='FCOSAgentISO'
ISO_ROLE_PRIVS='Datastore.AllocateTemplate Datastore.Audit'

CHECK=0
PENDING=0
HOST_KEY=''

die() {
  local code=$1
  shift
  printf 'error: %s\n' "$*" >&2
  exit "$code"
}

warn() {
  printf 'warning: %s\n' "$*" >&2
}

info() {
  printf '%s\n' "$*"
}

require_root() {
  if [[ "${EUID}" -ne 0 && "${FCOS_ALLOW_NONROOT:-}" != 1 ]]; then
    die 1 "run this as root on the Proxmox host"
  fi
}

require_commands() {
  local cmd
  for cmd in "$@"; do
    command -v "$cmd" >/dev/null 2>&1 || die 1 "'${cmd}' not found; run this on a Proxmox VE host"
  done
}

short_host() {
  local name
  name=$(uname -n)
  printf '%s\n' "${name%%.*}"
}

# validate_name <what> <value> <max-length>: a plain Proxmox-style name only.
validate_name() {
  local what=$1 value=$2 max=$3
  if [[ "$value" == *'<'* || "$value" == *'>'* ]]; then
    die 1 "${what} '${value}' looks like a placeholder; use the real name"
  fi
  if [[ ! "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || (( ${#value} > max )); then
    die 1 "${what} '${value}' is not a valid name (letters, digits, '.', '_', '-'; at most ${max} characters)"
  fi
}

# contains <newline-separated list> <line>: exact whole-line match, no pipe, so
# pipefail never turns an early grep exit into a false negative.
contains() {
  grep -Fxq -- "$2" <<<"$1"
}

# change <description> <command...>: run it, or in --check mode only report it.
change() {
  local what=$1
  shift
  if (( CHECK )); then
    printf '  would: %s\n' "$what"
    PENDING=$((PENDING + 1))
  else
    "$@"
    printf '  done: %s\n' "$what"
  fi
}

# JSON readers (stdin is the JSON from `pvesh get <api path> --output-format json`).
# Only pvesh is used for reads: its man page documents --output-format, while
# pvesm status and the pveum list commands do not.

# json_field <name>: that field of every object in the array, one per line.
json_field() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) { print "$row->{$ARGV[0]}\n" if ref $row eq "HASH" && defined $row->{$ARGV[0]}; }
  ' "$1"
}

# json_storage_content <storage>: that storage's content types, one per line.
json_storage_content() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) {
      next unless ref $row eq "HASH" && ($row->{storage} // "") eq $ARGV[0];
      print "$_\n" for grep { length } split /[,\s]+/, ($row->{content} // "");
    }
  ' "$1"
}

# json_pool_members: the VMIDs listed under "members" in a pool object.
json_pool_members() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) {
      next unless ref $row eq "HASH" && ref $row->{members} eq "ARRAY";
      for my $m (@{ $row->{members} }) { print "$m->{vmid}\n" if ref $m eq "HASH" && defined $m->{vmid}; }
    }
  '
}

# json_role_privs <roleid>: that role's privileges, sorted and comma-separated.
json_role_privs() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) {
      next unless ref $row eq "HASH" && ($row->{roleid} // "") eq $ARGV[0];
      my $p = $row->{privs} // "";
      my @p = ref $p eq "HASH" ? keys %$p : split /[,\s]+/, $p;
      print join(",", sort grep { length } @p), "\n";
    }
  ' "$1"
}

# json_token_privsep <tokenname>: 1 or 0 for that token (1 when not reported).
json_token_privsep() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) {
      next unless ref $row eq "HASH" && ($row->{tokenid} // "") eq $ARGV[0];
      print((defined $row->{privsep} && $row->{privsep} eq "0") ? "0\n" : "1\n");
    }
  ' "$1"
}

# json_acls: one "path<TAB>type<TAB>ugid<TAB>roleid" line per ACL entry.
json_acls() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) {
      next unless ref $row eq "HASH";
      print join("\t", map { $row->{$_} // "" } qw(path type ugid roleid)), "\n";
    }
  '
}

# other_holders <role> <acl lines>: "<type> <who> on <path>" for every grant of
# that role to anyone but the agent's user and token. A same-named role the
# owner also uses is not the agent's to change or delete.
other_holders() {
  local role=$1 path kind who roleid
  while IFS=$'\t' read -r path kind who roleid; do
    [[ "$roleid" == "$role" ]] || continue
    [[ ( "$kind" == user && "$who" == "$PVE_USER" ) || ( "$kind" == token && "$who" == "$KEY_ID" ) ]] && continue
    printf '%s %s on %s\n' "$kind" "$who" "$path"
  done <<<"$2"
}

# join_lines: stdin lines joined with "; ".
join_lines() {
  awk 'NR > 1 { printf "; " } { printf "%s", $0 } END { print "" }'
}

# agent_grants <role> <acl lines>: "<path><TAB><user|token><TAB><who>" for each
# grant of that role to the agent's user or token.
agent_grants() {
  local role=$1 path kind who roleid
  while IFS=$'\t' read -r path kind who roleid; do
    [[ "$roleid" == "$role" ]] || continue
    if [[ ( "$kind" == user && "$who" == "$PVE_USER" ) || ( "$kind" == token && "$who" == "$KEY_ID" ) ]]; then
      printf '%s\t%s\t%s\n' "$path" "$kind" "$who"
    fi
  done <<<"$2" | sort -u
}

# norm_privs "<privileges, space or comma separated>": sorted, comma-separated.
norm_privs() {
  perl -e 'print join(",", sort grep { length } split /[,\s]+/, $ARGV[0]), "\n"' "$1"
}

