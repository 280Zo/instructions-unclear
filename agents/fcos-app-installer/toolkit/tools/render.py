#!/usr/bin/env python3
"""Fill {{KEY}} placeholders in a template from a flat KEY=value file.

Usage: render.py <template> <values-file>   (writes to stdout)
"""

import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
KEY = re.compile(r"^[A-Z][A-Z0-9_]*$")
SECRET_SUFFIXES = ("_TOKEN", "_PASSWORD", "_SECRET", "_KEY")


class RenderError(Exception):
    pass


def _networks(key: str, value: str) -> str:
    """A *_CIDR value: a comma-separated list of distinct, non-overlapping IPv4
    networks (host bits zero, never /0), written back as "a, b". These values
    land inside firewall rules, so nothing else may pass."""
    import ipaddress
    items = [item.strip() for item in value.split(",")]
    nets = []
    for item in items:
        try:
            net = ipaddress.IPv4Network(item, strict=True)
        except ValueError:
            raise RenderError(f"{key}: {item!r} is not an IPv4 network like 192.0.2.0/24") from None
        # Home networks only: a public range (or halves that add up to every
        # address) never belongs in these rules. Private LANs and the shared
        # address space 100.64.0.0/10 (used by some VPN overlays) are not
        # global, so they pass.
        if net.prefixlen < 8 or net.is_global or net.is_loopback or net.overlaps(ipaddress.IPv4Network("0.0.0.0/8")):
            raise RenderError(f"{key}: {item} is not a home network (private, shared 100.64.0.0/10 or documentation range)")
        nets.append(net)
    for i, a in enumerate(nets):
        for b in nets[i + 1:]:
            if a.overlaps(b):
                raise RenderError(f"{key}: {a} and {b} overlap; list each network once")
    return ", ".join(str(n) for n in nets)


def _number(key: str, value: str, low: int, high: int) -> str:
    """A *_PORT or *_KEEP value: a whole number in range (they land in nft and shell arithmetic)."""
    text = value.strip()
    if not re.fullmatch(r"[0-9]+", text) or not low <= int(text) <= high:  # ASCII digits only
        raise RenderError(f"{key}: {value!r} must be a whole number from {low} to {high}")
    return str(int(text))


def _address(key: str, value: str) -> str:
    """A *_IP value: one IPv4 address, nothing else."""
    import ipaddress
    try:
        return str(ipaddress.IPv4Address(value.strip()))
    except ValueError:
        raise RenderError(f"{key}: {value!r} is not one IPv4 address") from None


def render(template: str, values: dict[str, str]) -> str:
    # A malformed placeholder ({{ svc }}, {{svc}}, a lone {{ or }}) would pass
    # through to the output unnoticed; refuse the template instead.
    leftover = PLACEHOLDER.sub("", template)
    if "{{" in leftover or "}}" in leftover:
        raise RenderError("malformed placeholder in template (only {{KEY}} with capital letters, digits, _)")

    def substitute(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise RenderError(f"missing value for {{{{{key}}}}}")
        value = values[key]
        if "{{" in value:
            raise RenderError(f"value for {key} contains '{{{{'")
        if key.endswith("_CIDR"):
            return _networks(key, value)
        if key.endswith("_IP"):
            return _address(key, value)
        if key.endswith("_PORT"):
            return _number(key, value, 1, 65535)
        if key.endswith("_KEEP"):
            return _number(key, value, 1, 100000)
        return value

    return PLACEHOLDER.sub(substitute, template)


def load_values(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for number, raw in enumerate(handle, start=1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, sep, value = line.partition("=")
            key = key.strip()
            if not sep or not KEY.match(key):
                raise RenderError(f"{path}:{number}: expected KEY=value")
            if key.endswith(SECRET_SUFFIXES) and value:
                raise RenderError(
                    f"{path}:{number}: {key} looks like a secret; "
                    "secrets never go in values files (use a Podman secret)"
                )
            values[key] = value.replace("\\n", "\n")
    return values


def _under(path: Path, roots: list[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def _checked_paths(template: str, values: str) -> tuple[Path, Path]:
    """The two files, resolved (symlinks and ..) and checked. This tool runs without asking, so it may not be
    turned into a way to print any readable file: a template comes from templates/ and a values file from the
    workspace, the test fixtures or the scratch folder."""
    toolkit = Path(__file__).resolve().parent.parent
    template_path, values_path = Path(template).resolve(), Path(values).resolve()
    if not _under(template_path, [toolkit / "templates"]):
        raise RenderError("the template must be a file under the toolkit's templates/ folder")
    roots = [toolkit / "tests" / "fixtures", Path("/tmp/opencode").resolve()]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import workspace
        roots.append(workspace.resolve_workspace().resolve())
    except Exception:  # no workspace set (or one that can't be used): the other folders still work
        pass
    if not _under(values_path, roots):
        raise RenderError("the values file must be in the workspace, tests/fixtures or /tmp/opencode")
    return template_path, values_path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        template_path, values_path = _checked_paths(argv[1], argv[2])
        with open(template_path, encoding="utf-8") as handle:
            sys.stdout.write(render(handle.read(), load_values(str(values_path))))
    except (RenderError, OSError) as error:
        print(f"render: {argv[1]}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
