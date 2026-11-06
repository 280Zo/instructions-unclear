#!/usr/bin/env python3
"""Provider adapters: the user's steps for systems the agent never touches.

Each provider is a skill, <prefix>-<provider>/ in the skills folder (tools/layout.py), where the
prefix names the role (hypervisor-, router-, fileserver-, dns-): SKILL.md
says what the product is and when to use it, adapter.yaml holds its steps, and
scripts/ any host scripts. This tool is the one renderer for every adapter skill.
adapter.yaml:

  role, provider, name        which role it fills, and its display name
  docs                        official documentation links
  discovery                   what the agent can read, or must ask, about it
  capabilities                what the agent may do through an API (bools)
  defaults                    optional choices for the agent (e.g. ignition_method)
  manual_steps                 <step id>: {title, steps[], blocks[], uses[], report_back[]}
                              blocks: [{machine, code}]; machine names the machine
                              and shell, e.g. "<product> {{HOST}} (bash, root)"
  scripts                     host scripts it ships (paths in its skill folder); the
                              tool fills in each one's checksum as <FIRST WORD>_SHA256
                              (lib.sh: LIB_SHA256), the agent's folder as AGENT_REPO
                              and the skill's folder as SKILL_DIR; none may be passed in

Every role's adapter defines that role's steps (ROLE_STEPS). An unknown
provider gets adapter-generic's provider-neutral steps, marked
generic: true, so the agent can offer to draft an adapter as it goes.
Placeholders are {{KEY}}; every one a step uses is listed in its `uses`.
{{HOST}} is always the site file's hosts key for the server (it names the
token file and hosts/<HOST>/), never its display or node name; `render`
refuses any other value when a workspace is set.

Usage:
  adapters.py show --role <role> [--provider <name>]
      the adapter (or the generic fallback): capabilities, defaults, and each
      step with the values it uses
  adapters.py render --role <role> [--provider <name>] --step <id> --values <values.json>
      one manual step as Markdown with every value filled in (refuses unsafe values)
  adapters.py draft --role <role> --provider <name> --from <recorded.json> [--workspace <path>]
      writes <workspace>/adapters-draft/<prefix>-<provider>/ (adapter.yaml, SKILL.md, a small test)
"""

import argparse
import importlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import CHECKSUMS, SKILLS, SKILLS_DIR, adapter_skill  # noqa: E402
from render import RenderError, render  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
ADAPTERS = SKILLS
ROLE_STEPS = {
    "virtualization": ["download_image", "copy_ignition_snippet", "rebuild_os_disk", "create_api_access"],
    "router_firewall": ["reserve_ip", "dns_wildcard", "allow_flows"],
    "file_server": ["nfs_export", "service_user", "backup_folder"],
    "dns_certificates": ["api_token", "acme_provider"],
}
PROVIDER = re.compile(r"[a-z][a-z0-9-]{0,40}")
STEP_ID = re.compile(r"[a-z][a-z0-9_]{0,40}")
KEY = re.compile(r"[A-Z][A-Z0-9_]*")
ANY_PLACEHOLDER = re.compile(r"\{\{([^}]*)\}\}")
# Values go into commands the user runs as root. No value may hold spaces,
# quotes, $, ;, |, &, <, >, backticks, glob or brace characters (* ? [ ] { }),
# ~ or %, or start with - (an option). Checked by kind, from the key's name:
#   *_DIR, *_REPO, *_FOLDER  an absolute local path: no :, no .. segment, not /
#   *_OPTIONS                a comma list of key=value options
#   *_ISO_VOLUME             <storage>:iso/<file>.iso (a config disc, never another disk)
#   *_ADDRESS                a host name or IP address (no @ or :, so ssh can't be redirected)
#   anything else            a name, number, address, volume id or CIDR
#                            (no , or =, so it can't add options)
SAFE_VALUE = re.compile(r"[A-Za-z0-9/][A-Za-z0-9._:/@+-]{0,199}")
ISO_VOLUME_VALUE = re.compile(r"[a-z][a-z0-9_-]{0,63}:iso/[A-Za-z0-9][A-Za-z0-9._-]{0,120}\.iso")
ADDRESS_VALUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}")
PATH_VALUE = re.compile(r"/[A-Za-z0-9._/@+-]{1,199}")
OPTIONS_VALUE = re.compile(r"[a-z0-9_]+=[A-Za-z0-9._-]+(,[a-z0-9_]+=[A-Za-z0-9._-]+)*")
MACHINE = re.compile(r".+ \((bash|fish)(, [^)]+)?\)")
TOP_KEYS = {"role", "provider", "name", "docs", "discovery", "capabilities", "defaults", "manual_steps", "scripts",
            "draft", "notes", "acme", "code"}
# Roles whose adapter may ship a tool the agent runs (tools/<package>/<product>.py), with the verbs the
# generic entry point accepts. Only the virtualization role has one: tools/hypervisor.py.
TOOL_PACKAGES = {"virtualization": "virtualization"}
TOOL_VERBS = {"virtualization": ("check", "list", "create", "start", "status")}
# Manual steps an adapter with a tool must define besides the role's own: the guide tells the user to store the
# token the tool uses and to remove the access when the install is done.
TOOL_STEPS = {"virtualization": ("store_api_token", "teardown_api_access")}
TOOL_NAME = re.compile(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*")
ACME_KEYS = {"provider", "env", "store_as", "notes"}
ACME_PROVIDER = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
ACME_ENV = re.compile(r"[A-Z][A-Z0-9_]{0,60}")
ACME_STORE_AS = re.compile(r"[a-z][a-z0-9_]{0,60}")
ACME_ENV_REFUSED = {"PATH", "HOME", "USER", "SHELL", "IFS", "TMPDIR", "LANG", "PWD", "XDG_RUNTIME_DIR"}
STEP_KEYS = {"title", "steps", "blocks", "uses", "report_back"}


class AdapterError(Exception):
    pass


def _yaml():
    try:
        import yaml
    except ImportError:
        raise AdapterError("install PyYAML (python-yaml / python3-yaml)") from None
    return yaml


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def _check_step(where: str, step) -> None:
    if not isinstance(step, dict):
        raise AdapterError(f"{where}: a step must be a mapping")
    unknown = set(step) - STEP_KEYS
    if unknown:
        raise AdapterError(f"{where}: unknown field(s) {sorted(unknown)}")
    if not (isinstance(step.get("title"), str) and step["title"]):
        raise AdapterError(f"{where}: title is required")
    if not _strings(step.get("steps")):
        raise AdapterError(f"{where}: steps must be a list of sentences")
    for key in ("uses", "report_back"):
        if key in step and not (isinstance(step[key], list) and all(isinstance(v, str) for v in step[key])):
            raise AdapterError(f"{where}: {key} must be a list of strings")
    uses = step.get("uses", [])
    if not all(KEY.fullmatch(u) for u in uses):
        raise AdapterError(f"{where}: uses must list placeholder names like VM_IP")
    blocks = step.get("blocks", [])
    if not isinstance(blocks, list):
        raise AdapterError(f"{where}: blocks must be a list")
    texts = [step["title"], *step["steps"], *step.get("report_back", [])]
    for block in blocks:
        if not (isinstance(block, dict) and set(block) == {"machine", "code"}
                and isinstance(block["machine"], str) and isinstance(block["code"], str)):
            raise AdapterError(f"{where}: each block needs machine and code")
        if not MACHINE.fullmatch(block["machine"]):
            raise AdapterError(f"{where}: block machine must end in (bash...) or (fish...)")
        if block["machine"].startswith("desktop") and "(fish" not in block["machine"]:
            raise AdapterError(f"{where}: desktop commands are fish")
        texts += [block["machine"], block["code"]]
    for text in texts:
        for name in ANY_PLACEHOLDER.findall(text):
            if not KEY.fullmatch(name):
                raise AdapterError(f"{where}: placeholder {{{{{name}}}}} must be capital letters, digits, _")
            if name not in uses:
                raise AdapterError(f"{where}: {{{{{name}}}}} is used but not listed in uses")


def _check_acme(acme, role: str, where: str) -> None:
    """How a certificate client proves the domain through this DNS provider (dns_certificates only):
    its provider code, the environment variable that holds the token, and the name the token is stored under."""
    if role != "dns_certificates":
        raise AdapterError(f"{where}: acme is only for the dns_certificates role")
    if not (isinstance(acme, dict) and set(acme) <= ACME_KEYS and {"provider", "env", "store_as"} <= set(acme)):
        raise AdapterError(f"{where}: acme needs provider, env and store_as (and may have notes)")
    if not (isinstance(acme["provider"], str) and ACME_PROVIDER.fullmatch(acme["provider"])):
        raise AdapterError(f"{where}: acme provider must be the client's provider code (lowercase letters, digits, -)")
    if not (isinstance(acme["env"], str) and ACME_ENV.fullmatch(acme["env"])):
        raise AdapterError(f"{where}: acme env must be the environment variable that holds the token (capitals, digits, _)")
    if not (isinstance(acme["store_as"], str) and ACME_STORE_AS.fullmatch(acme["store_as"])):
        raise AdapterError(f"{where}: acme store_as must be the name the token is stored under (lowercase letters, digits, _)")
    if acme["env"] in ACME_ENV_REFUSED or acme["env"].startswith(("LD_", "SYSTEMD_", "PODMAN_", "CONTAINERS_")):
        raise AdapterError(f"{where}: acme env {acme['env']} would change how every program on the VM runs; "
                           "use the variable the DNS provider's documentation names for its token")
    note = acme.get("notes", "")
    if not (isinstance(note, str) and len(note) <= 300 and note.isprintable() and "{{" not in note):
        raise AdapterError(f"{where}: acme notes must be one printable line of at most 300 characters, with no {{ }}")


def _check_code(code, role: str, provider: str, where: str) -> None:
    """code names the adapter's tool: <package>.<product>, in the role's package and named like the provider."""
    package = TOOL_PACKAGES.get(role)
    if package is None:
        raise AdapterError(f"{where}: the {role} role has no tool contract, so the adapter can't name code")
    expected = f"{package}.{provider.replace('-', '_')}"
    if not (isinstance(code, str) and TOOL_NAME.fullmatch(code) and code == expected):
        raise AdapterError(f"{where}: code must be {expected} (a file in tools/{package}/), not {code!r}")


def _check_adapter(data, role: str, provider: str) -> dict:
    where = f"{adapter_skill(role, provider)}/adapter.yaml"
    if not isinstance(data, dict):
        raise AdapterError(f"{where}: must be a mapping")
    unknown = set(data) - TOP_KEYS
    if unknown:
        raise AdapterError(f"{where}: unknown field(s) {sorted(unknown)}")
    if data.get("role") != role or data.get("provider") != provider:
        raise AdapterError(f"{where}: role/provider inside the file must be {role}/{provider}")
    if not isinstance(data.get("name"), str):
        raise AdapterError(f"{where}: name is required")
    docs = data.get("docs", [])
    if not (isinstance(docs, list) and all(isinstance(d, str) and d.startswith("https://") for d in docs)):
        raise AdapterError(f"{where}: docs must be a list of https links")
    for key in ("discovery", "capabilities", "defaults"):
        if not isinstance(data.get(key, {}), dict):
            raise AdapterError(f"{where}: {key} must be a mapping")
    if not all(isinstance(v, bool) for v in data.get("capabilities", {}).values()):
        raise AdapterError(f"{where}: capabilities are true or false")
    if not _strings(data.get("scripts", [])) and data.get("scripts", []) != []:
        raise AdapterError(f"{where}: scripts must be a list of paths")
    _check_scripts(data.get("scripts", []), where)
    if "acme" in data:
        _check_acme(data["acme"], role, where)
    if "code" in data:
        _check_code(data["code"], role, provider, where)
    steps = data.get("manual_steps")
    if not isinstance(steps, dict):
        raise AdapterError(f"{where}: manual_steps is required")
    for step_id, step in steps.items():
        if not (isinstance(step_id, str) and STEP_ID.fullmatch(step_id)):
            raise AdapterError(f"{where}: step id {step_id!r} must be lowercase letters, digits, _")
        _check_step(f"{where} {step_id}", step)
    needed = [*ROLE_STEPS[role], *(TOOL_STEPS.get(role, ()) if "code" in data else ())]
    missing = [s for s in needed if s not in steps]
    if missing:
        raise AdapterError(f"{where}: missing the role's steps {missing}")
    return data


def _value_ok(key: str, value) -> bool:
    if not isinstance(value, str):
        return False
    if key.endswith(("_CIDR", "_IP")):
        # Networks and addresses: checked (and normalized) by render.py, which
        # refuses anything but real IPv4 networks / one address.
        from render import _address, _networks
        try:
            (_networks if key.endswith("_CIDR") else _address)(key, value)
        except RenderError:
            return False
        return True
    if key.endswith(("_DIR", "_REPO", "_FOLDER")):
        return bool(PATH_VALUE.fullmatch(value)) and ".." not in value.split("/") and value.strip("/") != ""
    if key.endswith("_OPTIONS"):
        return bool(OPTIONS_VALUE.fullmatch(value))
    if key.endswith("_ISO_VOLUME"):
        return bool(ISO_VOLUME_VALUE.fullmatch(value)) and ".." not in value
    if key.endswith("_ADDRESS"):
        return bool(ADDRESS_VALUE.fullmatch(value)) and ".." not in value
    return bool(SAFE_VALUE.fullmatch(value)) and ".." not in value.split("/")


def example_value(key: str) -> str:
    """A valid example for a placeholder, for tests and drafted adapters' checks."""
    if key.endswith(("_DIR", "_REPO", "_FOLDER")):
        return "/example/path"
    if key.endswith("_OPTIONS"):
        return "iothread=1"
    if key.endswith("_ISO_VOLUME"):
        return "local:iso/example-1.iso"
    if key.endswith("_CIDR"):
        return "192.0.2.0/24"
    if key.endswith("_IP"):
        return "192.0.2.10"
    return "example-1"


def _read_yaml(path: Path):
    yaml = _yaml()
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as error:
        raise AdapterError(f"{path.name}: not valid YAML ({type(error).__name__})") from None


def _generic_steps(role: str) -> dict:
    data = _read_yaml(ADAPTERS / "adapter-generic" / "adapter.yaml")
    try:
        steps = data["roles"][role]["manual_steps"]
    except (TypeError, KeyError):
        raise AdapterError(f"adapter-generic/adapter.yaml: no steps for role {role}") from None
    for step_id, step in steps.items():
        _check_step(f"adapter-generic/adapter.yaml {role}.{step_id}", step)
    return steps


def load_adapter(role: str, provider: str | None, root: Path | None = None) -> dict:
    """The adapter for role/provider, or the generic steps (generic: true)."""
    if role not in ROLE_STEPS:
        raise AdapterError(f"unknown role {role!r}; roles: {', '.join(ROLE_STEPS)}")
    if provider is not None and not (isinstance(provider, str) and PROVIDER.fullmatch(provider)):
        raise AdapterError("provider must be lowercase letters, digits and hyphens")
    root = ADAPTERS if root is None else Path(root)
    folder = root / adapter_skill(role, provider)
    path = folder / "adapter.yaml"
    if provider is not None and provider != "generic" and path.is_file():
        data = _check_adapter(_read_yaml(path), role, provider)
        return dict(data, generic=False, skill_dir=str(folder.resolve()))
    steps = _generic_steps(role)
    return {"role": role, "provider": provider or "generic", "name": provider or "generic", "generic": True,
            "docs": [], "discovery": {}, "capabilities": {}, "defaults": {}, "scripts": [], "manual_steps": steps}


def load_tool(adapter: dict):
    """The Python module of the adapter's tool, checked to have the role's verbs and a main(argv)."""
    where = adapter_skill(adapter["role"], adapter.get("provider"))
    code = adapter.get("code")
    if adapter.get("generic") or not code:
        raise AdapterError(f"{where} has no tool: every step it has is a manual step. A tool is a file in "
                           "tools/<role package>/ named by `code:` in adapter.yaml (docs/guide/12-add-a-module.md)")
    try:
        loaded = importlib.import_module(code)
    except Exception as error:  # ImportError, or whatever the tool's code raises while loading
        raise AdapterError(f"{where}: its tool {code!r} can't be loaded ({type(error).__name__}: {error})") from None
    if tuple(getattr(loaded, "VERBS", ())) != TOOL_VERBS[adapter["role"]]:
        raise AdapterError(f"{where}: its tool {code!r} must define VERBS = {TOOL_VERBS[adapter['role']]}")
    if not callable(getattr(loaded, "main", None)):
        raise AdapterError(f"{where}: its tool {code!r} must define main(argv)")
    return loaded


def acme_data(site: dict) -> dict:
    """The certificate-client data (provider code, token variable, secret name) of the DNS provider
    the site names under roles.dns_certificates.provider. Nothing is assumed: an unset provider, or
    an adapter without acme data, is an error that says what to do."""
    roles = site.get("roles") if isinstance(site, dict) else None
    entry = roles.get("dns_certificates") if isinstance(roles, dict) else None
    provider = entry.get("provider") if isinstance(entry, dict) else None
    if provider in (None, "ASK"):
        raise AdapterError("site.yaml: roles.dns_certificates.provider is not set; ask the user which DNS provider "
                           "holds the domain, then name its adapter (python3 tools/adapters.py show --role "
                           "dns_certificates --provider <name>)")
    adapter = load_adapter("dns_certificates", provider)
    acme = adapter.get("acme")
    if not acme:
        raise AdapterError(f"{adapter_skill('dns_certificates', provider)} has no acme data (the certificate client's provider code, the "
                           "token's environment variable and the name it is stored under); add an acme: block to its "
                           "adapter.yaml (see docs/guide/12-add-a-module.md and the chosen ingress's operations.md)")
    return acme


def _checksum_key(path: str) -> str:
    """lib.sh -> LIB_SHA256, discover-host.sh -> DISCOVER_SHA256: the first word of the file name."""
    stem = Path(path).name.split(".", 1)[0]
    return re.split(r"[-_]", stem, maxsplit=1)[0].upper() + "_SHA256"


PINNED_LINE = re.compile(r"([0-9a-f]{64})  (\S+)")


def _pinned() -> dict[str, str]:
    """The pinned list (sha256sum format): script path in the skills folder -> sha256."""
    try:
        # Bytes, decoded here: text mode would turn a lone CR or a CRLF into a newline, which
        # sha256sum -c does not do.
        text = CHECKSUMS.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        reason = "it is not UTF-8 text" if isinstance(error, UnicodeDecodeError) else error.strerror
        raise AdapterError(f"the checksum list {CHECKSUMS} can't be read ({reason}); the host "
                           "scripts can't be checked, so no step that runs one is shown") from None
    found = {}
    lines = text.split("\n")  # not splitlines(): sha256sum -c ends a line at a newline only
    if lines[-1] == "":
        lines.pop()  # the newline that ends the last line
    for number, line in enumerate(lines, start=1):
        match = PINNED_LINE.fullmatch(line)
        if match is None:
            raise AdapterError(f"{CHECKSUMS.name}:{number}: not a sha256sum line (lowercase hex, two spaces, "
                               "a path; the list takes no blank lines or comments)")
        if match[2] in found:  # `sha256sum -c` would complain too, and the last line would win silently
            raise AdapterError(f"{CHECKSUMS.name}:{number}: {match[2]} is listed twice")
        found[match[2]] = match[1]
    return found


def _pin_state(path: Path, digest: str) -> str:
    """Returns "pinned" when the script's sha256 is the one the list holds for it, "differs" when the
    list holds another, "unlisted" when the list does not hold it. The user runs these scripts as root,
    and a step shows the checksum of the file as it is, so a script the agent (or anything else)
    changed would pass the user's sha256sum check (review of ff605b1). The list is a file the
    agent's rules keep it from editing (a guard rail; README), outside every skill folder, and it
    needs no git."""
    try:
        key = path.resolve().relative_to(ADAPTERS.resolve()).as_posix()
    except ValueError:
        return "unlisted"
    pinned = _pinned().get(key)
    return "unlisted" if pinned is None else "pinned" if pinned == digest else "differs"


def derived_values(adapter: dict) -> dict:
    """Values the tool fills in itself, never the caller: AGENT_REPO (where this
    agent is installed, found from this file's location, so moving the agent
    keeps every step right) and <WORD>_SHA256 of each script the adapter ships."""
    import hashlib
    out = {"AGENT_REPO": str(REPO)}
    skill = Path(adapter["skill_dir"]) if adapter.get("skill_dir") else None
    if skill is not None:
        out["SKILL_DIR"] = str(skill)
    for path in adapter.get("scripts", []):
        target = (skill / path).resolve() if skill is not None else None
        if target is None or skill not in target.parents or not target.is_file():
            raise AdapterError(f"{adapter.get('provider')}: script {path} is not a file in its skill folder")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        state = _pin_state(target, digest)
        if state != "pinned":
            what = (f"differs from the pinned checksum in {CHECKSUMS.name}" if state == "differs"
                    else f"isn't listed in {CHECKSUMS.name}")
            raise AdapterError(f"{adapter.get('provider')}: script {path} {what}; the user runs it as root, "
                               "so this step isn't shown. Tell the user; don't change or restore it yourself")
        key = _checksum_key(path)
        if key in out:
            raise AdapterError(f"{adapter.get('provider')}: two scripts give the checksum {key}")
        out[key] = digest
    return out


def derived_keys(adapter: dict) -> set[str]:
    keys = {"AGENT_REPO", "SKILL_DIR"} | {_checksum_key(p) for p in adapter.get("scripts", [])}
    return keys


def _check_scripts(scripts: list, where: str) -> None:
    """Each shipped script gives one valid, distinct checksum key (checked on load)."""
    seen: dict[str, str] = {}
    for path in scripts:
        key = _checksum_key(path)
        if not KEY.fullmatch(key):
            raise AdapterError(f"{where}: script {path}: its name must start with a letter "
                               f"(its checksum key would be {key})")
        if key in seen:
            raise AdapterError(f"{where}: two scripts give the checksum {key}: {seen[key]} and {path}")
        seen[key] = path


def render_step(adapter: dict, step_id: str, values: dict) -> str:
    """The step as Markdown with every value filled in; refuses missing or unsafe values.
    The agent's folder and the scripts' checksums are filled in here, never passed in."""
    step = adapter.get("manual_steps", {}).get(step_id)
    if step is None:
        raise AdapterError(f"{adapter.get('provider')} has no step {step_id!r}")
    passed = sorted(derived_keys(adapter) & set(values))
    if passed:
        raise AdapterError(f"{', '.join(passed)} is filled in by the tool (from where the agent is "
                           "installed); leave it out of the values")
    uses = step.get("uses", [])
    unfillable = [k for k in uses if k.endswith("_SHA256") and k not in derived_keys(adapter)]
    if unfillable:
        raise AdapterError(f"step {step_id} uses checksum {', '.join(unfillable)}, but the adapter ships "
                           "no script it could be taken from; checksums are never typed in by hand")
    if any(k in derived_keys(adapter) for k in uses):
        derived = derived_values(adapter)
        if not all(_value_ok(k, derived[k]) for k in ("AGENT_REPO", "SKILL_DIR") if k in derived):
            raise AdapterError(f"the agent is installed at {derived['AGENT_REPO']!r}, a path the user's commands "
                               "can't carry safely; install it in a folder whose path has no spaces or "
                               "shell characters")
        values = dict(values, **derived)
    code = "\n".join(block.get("code", "") for block in step.get("blocks", []))
    for key in uses:
        if key.endswith("_CIDR") and "," in str(values.get(key, "")) and "{{" + key + "}}" in code:
            raise AdapterError(f"{key} holds several networks, but step {step_id} puts it in a command, "
                               "where it would split into separate arguments; give one network")
    clean = {}
    for key in uses:
        if key not in values:
            raise AdapterError(f"missing value for {{{{{key}}}}} in step {step_id}")
        value = values[key]
        if not _value_ok(key, value):
            raise AdapterError(f"value for {key} must be a plain name, path or address "
                               "(no spaces, quotes or shell characters; see SAFE_VALUE in tools/adapters.py)")
        clean[key] = value
    try:
        fill = lambda text: render(text, clean)  # noqa: E731
        out = [f"### {fill(step['title'])}", ""]
        out += [f"{n}. {fill(s)}" for n, s in enumerate(step["steps"], start=1)]
        for block in step.get("blocks", []):
            out += ["", f"```{'fish' if '(fish' in block['machine'] else 'bash'}", f"# {fill(block['machine'])}",
                    fill(block["code"]).rstrip("\n"), "```"]
        if step.get("report_back"):
            out += ["", "Report back:"] + [f"- {fill(r)}" for r in step["report_back"]]
    except RenderError as error:
        raise AdapterError(f"step {step_id}: {error}") from None
    return "\n".join(out) + "\n"


def draft_adapter(role: str, provider: str, recorded: list) -> str:
    """YAML for a new adapter from the steps the user actually did.

    Role steps nobody recorded come from the generic adapter, so the draft is
    complete; draft: true marks it for review before it joins the repo.
    """
    if role not in ROLE_STEPS:
        raise AdapterError(f"unknown role {role!r}")
    if not (isinstance(provider, str) and PROVIDER.fullmatch(provider)) or provider == "generic":
        raise AdapterError("provider must be lowercase letters, digits and hyphens")
    if not isinstance(recorded, list):
        raise AdapterError("recorded steps must be a list")
    steps = {}
    for item in recorded:
        if not isinstance(item, dict) or not (isinstance(item.get("id"), str) and STEP_ID.fullmatch(item["id"])):
            raise AdapterError("each recorded step needs an id: lowercase letters, digits, _")
        step = {k: v for k, v in item.items() if k != "id"}
        _check_step(f"recorded {item['id']}", step)
        steps[item["id"]] = step
    generic = _generic_steps(role)
    for step_id in ROLE_STEPS[role]:
        steps.setdefault(step_id, generic[step_id])
    data = {"role": role, "provider": provider, "name": provider, "draft": True,
            "notes": "Drafted while working; check every step against the provider's official docs.",
            "docs": [], "discovery": {}, "capabilities": {}, "scripts": [], "manual_steps": steps}
    _check_adapter(data, role, provider)
    return _yaml().safe_dump(data, sort_keys=False, allow_unicode=True)


def _check_host_key(values: dict) -> None:
    """HOST is the site file's hosts key for the server (it names the token file
    and hosts/<HOST>/), never its display or node name. Checked against the
    workspace's site.yaml when one is set."""
    if "HOST" not in values:
        return
    from workspace import WorkspaceError, WorkspaceNotSet, load_site, resolve_workspace
    try:
        # The step's own WORKSPACE value first, then the set or remembered one.
        ws = resolve_workspace(values.get("WORKSPACE") if isinstance(values.get("WORKSPACE"), str) else None)
    except WorkspaceNotSet:  # no workspace at all: the agent's own check stands
        return
    except WorkspaceError as error:
        raise AdapterError(f"workspace: {error}") from None
    if not (Path(ws) / "site.yaml").is_file():
        raise AdapterError(f"the site file {Path(ws) / 'site.yaml'} is missing; HOST can't be checked")
    try:
        site = load_site(ws)
    except (OSError, _yaml().YAMLError):
        raise AdapterError(f"the site file {Path(ws) / 'site.yaml'} can't be read as YAML") from None
    hosts = site.get("hosts") if isinstance(site, dict) else None
    if isinstance(hosts, dict) and hosts and values["HOST"] not in hosts:
        raise AdapterError(f"HOST {values['HOST']!r} is not a server key in the site file; use one of: "
                           f"{', '.join(sorted(map(str, hosts)))} (the key, not the server's display or node name)")


SKILL_TEMPLATE = """---
name: {skill}
description: "DRAFT manual steps for {provider} in the {role} role of the fcos-app-installer toolkit. Use when the user's {role} is {provider}. Review every step against {provider}'s official documentation before moving this skill into {skills_dir}/."
license: MIT
compatibility: Needs the fcos-app-installer toolkit; tools/adapters.py renders the steps.
---

# {provider} ({role}), draft

Drafted from the steps the user actually did. Before use: check each step and
menu name against {provider}'s official documentation, add the links to
`docs:` in adapter.yaml and below, then move this folder into `{skills_dir}/`.

Render a step with every value filled in, never by hand:

```fish
# desktop (fish)
python3 tools/adapters.py render --role {role} --provider {provider} --step <id> --values <values.json>
```
"""


TEST_TEMPLATE = '''"""Checks the drafted adapter loads and every role step renders.

Run it with FCOS_AGENT_ROOT set to the toolkit's folder, or after moving this folder into the
toolkit's {skills_dir}/ (the toolkit's one setting, tools/layout.py).
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS_DIR = Path({skills_dir!r})
if os.environ.get("FCOS_AGENT_ROOT"):
    ROOT = Path(os.environ["FCOS_AGENT_ROOT"])
elif HERE.parent.parts[-len(SKILLS_DIR.parts):] == SKILLS_DIR.parts:
    ROOT = HERE.parent.parents[len(SKILLS_DIR.parts) - 1]
else:
    sys.exit("set FCOS_AGENT_ROOT to the toolkit's folder, or move this folder into its " + str(SKILLS_DIR))
if not (ROOT / "tools" / "adapters.py").is_file():
    sys.exit(str(ROOT) + " is not the toolkit's folder (it has no tools/adapters.py)")
sys.path.insert(0, str(ROOT / "tools"))
from adapters import ROLE_STEPS, derived_keys, example_value, load_adapter, render_step  # noqa: E402

adapter = load_adapter({role!r}, {provider!r}, root=HERE.parent)
assert not adapter["generic"]
for step in ROLE_STEPS[{role!r}]:
    uses = adapter["manual_steps"][step].get("uses", [])
    render_step(adapter, step, {{k: example_value(k) for k in uses if k not in derived_keys(adapter)}})
print("ok")
'''


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="adapters.py")
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("draft")
    draft.add_argument("--role", required=True)
    draft.add_argument("--provider", required=True)
    draft.add_argument("--from", dest="source", required=True)
    draft.add_argument("--workspace")
    show = sub.add_parser("show")
    show.add_argument("--role", required=True)
    show.add_argument("--provider")
    rend = sub.add_parser("render")
    rend.add_argument("--role", required=True)
    rend.add_argument("--provider")
    rend.add_argument("--step", required=True)
    rend.add_argument("--values", required=True, help="JSON file: {KEY: value}")
    args = parser.parse_args(argv[1:])
    if args.command in ("show", "render"):
        try:
            adapter = load_adapter(args.role, args.provider)
            if args.command == "show":
                out = {"role": adapter["role"], "provider": adapter["provider"], "generic": adapter["generic"],
                       "capabilities": adapter.get("capabilities", {}), "defaults": adapter.get("defaults", {}),
                       "steps": {k: v.get("uses", []) for k, v in adapter["manual_steps"].items()}}
                sys.stdout.write(_yaml().safe_dump(out, sort_keys=False))
            else:
                values = json.loads(Path(args.values).read_text(encoding="utf-8"))
                if not isinstance(values, dict):
                    raise AdapterError("--values must hold a JSON object")
                _check_host_key(values)
                sys.stdout.write(render_step(adapter, args.step, values))
        except (AdapterError, OSError, ValueError) as error:
            print(f"adapters: {error}", file=sys.stderr)
            return 1
        return 0
    try:
        from workspace import WorkspaceError, resolve_workspace
        recorded = json.loads(Path(args.source).read_text(encoding="utf-8"))
        text = draft_adapter(args.role, args.provider, recorded)
        ws = resolve_workspace(args.workspace)
        # A draft must land in a real workspace, never in a folder OpenCode loads skills from:
        # there an unreviewed draft would become a live skill.
        if not (ws / "site.yaml").is_file():
            raise AdapterError(f"{ws} has no site.yaml: drafts go into an install's workspace")
        if "skills" in ws.parts or any(p in (".agents", ".opencode", ".claude") for p in ws.parts):
            raise AdapterError(f"{ws} is inside a skill or agent folder; drafts go into an install's workspace")
        folder = ws / "adapters-draft" / adapter_skill(args.role, args.provider)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "adapter.yaml").write_text(text, encoding="utf-8")
        (folder / "SKILL.md").write_text(
            SKILL_TEMPLATE.format(role=args.role, provider=args.provider, skills_dir=SKILLS_DIR,
                                  skill=adapter_skill(args.role, args.provider)), encoding="utf-8")
        (folder / f"test_{args.provider.replace('-', '_')}.py").write_text(
            TEST_TEMPLATE.format(skills_dir=SKILLS_DIR, role=args.role, provider=args.provider), encoding="utf-8")
        print(folder / "adapter.yaml")
    except (AdapterError, OSError, ValueError, WorkspaceError) as error:
        print(f"adapters: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
