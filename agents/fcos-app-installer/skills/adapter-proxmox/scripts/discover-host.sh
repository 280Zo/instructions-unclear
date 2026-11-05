#!/usr/bin/env bash
# Print the facts the FCOS agent builds its VM recommendations from (run as
# root on the Proxmox host). Read-only: only `pvesh get`, lsblk, pvs, lvs and
# /sys are read; nothing is created or changed.
#
#   discover-host.sh [--node <name>]
#
# Prints: Proxmox version; CPU (model, sockets, cores, threads) and NUMA nodes;
# memory; disks (rotational, transport) and what sits on them; LVM volume groups
# and thin pools; storages with type, content, size and free space, and where
# each keeps its data; bridges (VLAN-aware, allowed VLANs, MTU, comments); and
# each VM's and container's network cards. Storage settings are printed from an
# allow-list, so credentials (password, username, keys) never appear. It does
# hold free text (bridge comments) and addresses (bridge cidr, storage servers).
# Root is needed: pvesh runs locally as root, and reading a storage's settings
# needs Datastore.Allocate.
#
# Exit codes: 0 done, 1 validation failure, 2 usage error.
# FCOS_ALLOW_NONROOT=1 and FCOS_TEST_SYSFS are test-only (see lib.sh); never set
# them on a real host.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

NODE=''
SYSFS="${FCOS_TEST_SYSFS:-/sys}"
PROCFS="${FCOS_TEST_PROC:-/proc}"

usage() {
  cat <<'EOF'
usage: discover-host.sh [--node <name>]

  --node <name>  node to describe (default: this host)
  -h, --help     show this help

Run as root on the Proxmox host. Read-only. Save the output as
<workspace>/hosts/<host>/discovery.txt for the agent.
EOF
}

usage_error() {
  printf 'error: %s\n\n' "$1" >&2
  usage >&2
  exit 2
}

while (( $# > 0 )); do
  case "$1" in
    --node)
      if (( $# < 2 )) || [[ "$2" == --* ]]; then
        usage_error "--node needs a value"
      fi
      NODE=$2
      shift 2
      ;;
    -h | --help) usage; exit 0 ;;
    *) usage_error "unknown option: $1" ;;
  esac
done
if [[ -z "$NODE" ]]; then
  NODE=$(short_host)
fi
validate_name "node" "$NODE" 64

require_root
require_commands pvesh perl lsblk

get() {
  pvesh get "$@" --output-format json
}

# rows <field>...: one line per object of the JSON array (or object) on stdin,
# "field=value" for each listed field that is present. Only listed fields are
# printed: this is the allow-list that keeps credentials out.
rows() {
  perl -MJSON::PP -e '
    local $/; my $t = <STDIN>; $t = "[]" unless defined $t && $t =~ /\S/;
    my $d = decode_json($t); $d = [$d] if ref $d ne "ARRAY";
    for my $row (@$d) {
      next unless ref $row eq "HASH";
      my @out;
      for my $f (@ARGV) {
        next unless defined $row->{$f} && !ref $row->{$f};
        (my $v = $row->{$f}) =~ s/[\r\n]+/ /g;
        push @out, "$f=$v";
      }
      print "  ", join(" ", @out), "\n" if @out;
    }
  ' "$@"
}

# status_facts: CPU and memory from /nodes/<node>/status.
status_facts() {
  perl -MJSON::PP -e '
    local $/; my $d = decode_json(<STDIN>);
    my $c = $d->{cpuinfo} // {}; my $m = $d->{memory} // {};
    my $threads = ($c->{sockets} && $c->{cores}) ? $c->{cpus} / ($c->{sockets} * $c->{cores}) : "?";
    printf "  model=%s\n  sockets=%s cores=%s cpus=%s threads_per_core=%s\n",
      $c->{model} // "?", $c->{sockets} // "?", $c->{cores} // "?", $c->{cpus} // "?", $threads;
    printf "  memory_total_mib=%d memory_available_mib=%d\n",
      ($m->{total} // 0) / 1048576, ($m->{available} // $m->{free} // 0) / 1048576;
  '
}

# storages_facts: sizes in GiB next to the usage fields.
storage_facts() {
  perl -MJSON::PP -e '
    local $/; my $d = decode_json(<STDIN>); $d = [$d] if ref $d ne "ARRAY";
    for my $s (@$d) {
      next unless ref $s eq "HASH";
      printf "  storage=%s type=%s content=%s active=%s shared=%s total_gib=%d avail_gib=%d\n",
        map({ $s->{$_} // "?" } qw(storage type content active)), $s->{shared} // 0,
        ($s->{total} // 0) / 1073741824, ($s->{avail} // 0) / 1073741824;
    }
  '
}

section() {
  printf '\n== %s ==\n' "$1"
}

printf 'Proxmox host discovery for node %s (read-only)\n' "$NODE"

section "Proxmox"
get /version | rows version release

section "CPU and memory"
NODE_STATUS_JSON=$(get "/nodes/${NODE}/status")
status_facts <<<"$NODE_STATUS_JSON"
numa=0
for dir in "$SYSFS"/devices/system/node/node[0-9]*; do
  [[ -d "$dir" ]] && numa=$((numa + 1))
done
printf '  numa_nodes=%s\n' "$numa"
# CPU flags (first CPU; all cores of one host share them): VM CPU type and flag choices.
flags=$(grep -m1 '^flags' "$PROCFS/cpuinfo" | sed 's/^flags[[:space:]]*:[[:space:]]*//' || true)
printf '  cpu_flags=%s\n' "${flags:-not readable}"

section "Disks (ROTA 0 = SSD/NVMe, 1 = spinning; tree shows what sits on each)"
lsblk -o NAME,TYPE,SIZE,ROTA,TRAN,MODEL | sed 's/^/  /'

section "LVM volume groups (physical volume, group, size, free)"
if command -v pvs >/dev/null 2>&1; then
  # A report-only command; a warning exit (e.g. duplicate PVs) must not stop the rest.
  pvs --noheadings -o pv_name,vg_name,pv_fmt,pv_size,pv_free | sed 's/^ */  /' \
    || printf '  (pvs failed; its message is above)\n'
else
  printf '  (pvs not found)\n'
fi

section "LVM thin pools and volumes (name, group, attributes, size, data used %)"
if command -v lvs >/dev/null 2>&1; then
  lvs --noheadings -o lv_name,vg_name,lv_attr,lv_size,data_percent | sed 's/^ */  /' \
    || printf '  (lvs failed; its message is above)\n'
else
  printf '  (lvs not found)\n'
fi

section "Storages"
STORAGES_JSON=$(get "/nodes/${NODE}/storage")
storage_facts <<<"$STORAGES_JSON"
section "Where each storage keeps its data"
STORAGE_IDS=$(json_field storage <<<"$STORAGES_JSON")
while IFS= read -r id; do
  [[ -n "$id" ]] || continue
  printf '  storage=%s\n' "$id"
  # Settings from an allow-list only: never password, username, keys or fingerprints.
  # content-dirs: a changed folder layout moves e.g. the import folder.
  get "/storage/${id}" | rows type path content-dirs vgname thinpool pool server export share datastore nodes shared \
    | sed 's/^  /    /' || printf '    (settings not readable)\n'
done <<<"$STORAGE_IDS"

section "Bridges"
get "/nodes/${NODE}/network" --type any_bridge \
  | rows iface type active comments bridge_ports bridge_vlan_aware bridge_vids mtu cidr

section "Virtual machines and containers (network cards)"
all_mem=0
all_cores=0
no_limit=''
templates=''
for kind in qemu lxc; do
  # Captured first: a failed listing must stop the script (set -e), never pass
  # as "no guests" (a process substitution's failure would be ignored).
  GUESTS_JSON=$(get "/nodes/${NODE}/${kind}")
  GUESTS=$(perl -MJSON::PP -e '
    local $/; my $d = decode_json(<STDIN>);
    # \x1f, not a tab: tab is whitespace to bash read, so an empty name would shift the fields.
    for my $g (sort { $a->{vmid} <=> $b->{vmid} } grep { ref eq "HASH" } @$d) {
      print join("\x1f", $g->{vmid}, $g->{name} // "", $g->{status} // "", $g->{template} ? 1 : 0), "\n";
    }
  ' <<<"$GUESTS_JSON")
  while IFS=$'\x1f' read -r vmid name status template; do
    [[ -n "$vmid" ]] || continue
    name=${name:-vmid $vmid}
    printf '  %s vmid=%s name=%s status=%s%s\n' "$kind" "$vmid" "$name" "$status" \
      "$( (( template )) && printf ' template=1')"
    CONFIG_JSON=$(get "/nodes/${NODE}/${kind}/${vmid}/config")
    perl -MJSON::PP -e '
      local $/; my $c = decode_json(<STDIN>);
      for my $k (sort keys %$c) {
        next unless $k =~ /^(net\d+|cores|sockets|memory|numa|balloon|hostname|onboot|startup)$/;
        print "    $k=$c->{$k}\n";
      }
    ' <<<"$CONFIG_JSON"
    # "<memory MiB> <cores or ->": API schema defaults when unset: memory 512;
    # a VM has cores 1 x sockets 1; a container without cores may use all of them.
    read -r mem cores < <(perl -MJSON::PP -e '
      local $/; my $c = decode_json(<STDIN>); my $kind = $ARGV[0];
      my ($m) = (($c->{memory} // "512") =~ /(\d+)/); $m //= 512;
      my $n = $kind eq "qemu" ? ($c->{cores} // 1) * ($c->{sockets} // 1)
                              : (defined $c->{cores} ? $c->{cores} : "-");
      print "$m $n\n";
    ' "$kind" <<<"$CONFIG_JSON")
    if (( template )); then  # a template never runs
      templates="${templates:+${templates},}${name}"
      continue
    fi
    all_mem=$((all_mem + mem))
    if [[ "$cores" == - ]]; then
      no_limit="${no_limit:+${no_limit},}${name}"
    else
      all_cores=$((all_cores + cores))
    fi
  done <<<"$GUESTS"
done

section "If every machine and container runs at once (stopped ones counted too)"
total_mem=$(perl -MJSON::PP -e 'local $/; my $d = decode_json(<STDIN>); printf "%d\n", ($d->{memory}{total} // 0) / 1048576' \
  <<<"$NODE_STATUS_JSON")
printf '  all_guests_memory_mib=%s free_memory_if_all_run_mib=%s (before what Proxmox itself needs)\n' \
  "$all_mem" "$((total_mem - all_mem))"
host_cpus=$(perl -MJSON::PP -e 'local $/; my $d = decode_json(<STDIN>); print(($d->{cpuinfo}{cpus} // "?"), "\n")' \
  <<<"$NODE_STATUS_JSON")
# Cores are shared between guests, not used up: more assigned than the host has is normal.
printf '  assigned_cores=%s host_cpus=%s (shared, not used up) no_core_limit=%s\n' \
  "$all_cores" "$host_cpus" "${no_limit:-none}"
printf '  templates_not_counted=%s\n' "${templates:-none}"

printf '\nDone. Nothing was changed. Save this output as <workspace>/hosts/<host>/discovery.txt for the agent.\n'
