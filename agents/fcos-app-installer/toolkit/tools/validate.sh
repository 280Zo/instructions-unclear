#!/usr/bin/env bash
# Render every template with a test values file into a scratch folder, then
# run the same checks a real VM build runs (tools/build-vm.sh). Then generate
# every service fixture (tests/fixtures/services/*.yaml) and the login front
# end with the test site (tests/fixtures/site.yaml), and build each of those.
# Usage: tools/validate.sh <values-file>
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 <values-file>" >&2
    exit 2
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
values="$(realpath "$1")"
# A private folder made for this run: a fixed path in a shared /tmp could be pre-created by someone else.
work="$(mktemp -d "${TMPDIR:-/tmp}/fcos-validate.XXXXXX")"
out="$work/$(basename "$values" .values)"
gen="$work/$(basename "$values" .values)-generated"
site="$root/tests/fixtures/site.yaml"

mkdir -p "$out" "$gen"
failures=0

templates=()
if [[ -d "$root/templates" ]]; then
    mapfile -t templates < <(cd "$root/templates" && find . -type f -name '*.tmpl' | sort)
fi
echo "validate: ${#templates[@]} templates"
if [[ ${#templates[@]} -gt 0 ]]; then
    for rel in "${templates[@]}"; do
        dest="$out/${rel%.tmpl}"
        mkdir -p "$(dirname "$dest")"
        python3 "$root/tools/render.py" "$root/templates/$rel" "$values" >"$dest"
    done
    bash "$root/tools/build-vm.sh" "$out" || failures=$((failures + 1))
fi

# Generated output: each service fixture on its own, then the login front end
# with the fixtures behind the login page (a fixture named like one of the
# chosen login front end modules' own services is a stand-alone example and
# would clash with it).
own_names="$(python3 "$root/tools/modules.py" services "$site")" || exit 1
mapfile -t own <<<"$own_names"
routed=()
for spec in "$root"/tests/fixtures/services/*.yaml; do
    name="$(basename "$spec" .yaml)"
    echo "validate: generate service fixture $name"
    if python3 "$root/tools/gen_service.py" "$spec" "$site" "$gen/$name" >/dev/null \
        && bash "$root/tools/build-vm.sh" "$gen/$name/rendered"; then
        :
    else
        failures=$((failures + 1))
    fi
    if [[ " ${own[*]} " != *" $name "* ]]; then
        routed+=("$spec")
    fi
done
echo "validate: generate the login front end"
if python3 "$root/tools/login_frontend.py" "$site" "$gen/login-frontend" "${routed[@]}" >/dev/null \
    && bash "$root/tools/build-vm.sh" "$gen/login-frontend/rendered"; then
    :
else
    failures=$((failures + 1))
fi

if [[ $failures -gt 0 ]]; then
    echo "validate: $failures build(s) failed; the files are kept in $work"
    exit 1
fi
rm -rf "$work"
echo "validate: all builds passed"
