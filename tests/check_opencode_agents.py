"""Opt-in runtime check of the default group's OpenCode agents.

Generates groups/default.jsonc without MCP output (so no real MCP server
starts) into a fresh home under /tmp/opencode, adds harmless local stub MCP
servers named zap, codebase-memory-mcp and freecad, then runs the installed
OpenCode against a localhost model stub. For each primary-capable agent it
compares the skills, MCP servers and subagents shown to the model with
agents/generate.py, makes sample skill, MCP and
delegation calls, and checks explore's resolved read-only policy.
No real model, credentials, live settings or downloads are used.

    python3 tests/check_opencode_agents.py /path/to/rulesync/dist/cli/index.js
"""

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

REPO = Path(__file__).resolve().parents[1]
MCP_STUB = REPO / "tests/fixtures/mcp_stub.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "agents"))
import generate  # noqa: E402

PRIMARY = ["build", "plan", "design", "career", "ai-research", "security",
           "reverse-engineering", "3d-modeling", "second-opinion", "local-model"]
MODES = {"build": "primary", "plan": "primary", "general": "subagent", "explore": "subagent",
         "design": "all", "career": "all", "ai-research": "all", "security": "all",
         "reverse-engineering": "all", "3d-modeling": "all", "second-opinion": "primary",
         "local-model": "all"}
STUB_SERVERS = ["zap", "codebase-memory-mcp", "freecad"]
LISTED_SUBAGENTS = ["security-auditor", "reverse-engineer", "evaluator", "career"]
SKILL_CALLS = [("design", "resume-tailor", False), ("career", "resume-tailor", True),
               ("build", "typography", False), ("ai-research", "humanizer", True),
               ("security", "binary-triage", False), ("reverse-engineering", "binary-triage", True)]
MCP_CALLS = [("security", "zap", True), ("design", "zap", False),
             ("build", "codebase-memory-mcp", True), ("design", "codebase-memory-mcp", False),
             ("3d-modeling", "freecad", True), ("build", "freecad", False)]
SUBAGENT_CALLS = [("design", "security-auditor", False), ("security", "security-auditor", True),
                  ("build", "career", True), ("career", "evaluator", False),
                  ("second-opinion", "evaluator", True)]


class Stub(BaseHTTPRequestHandler):
    """Records requests; issues the pending tool call once, when that tool is offered."""

    requests = []
    pending = None  # (tool name, arguments)

    def log_message(self, *_args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 20_000_000:
            self.send_error(413)
            return
        raw = self.rfile.read(length).decode()
        Stub.requests.append(raw)
        offered = {t.get("function", {}).get("name") for t in json.loads(raw).get("tools", [])}
        call = Stub.pending if Stub.pending and Stub.pending[0] in offered else None
        if call:
            Stub.pending = None
        delta = {"role": "assistant"}
        if call:
            delta["tool_calls"] = [{"index": 0, "id": "c1", "type": "function",
                                    "function": {"name": call[0], "arguments": json.dumps(call[1])}}]
        else:
            delta["content"] = "ok"
        base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fixture"}
        chunks = [{**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                  {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if call else "stop"}]}]
        data = ("".join("data: " + json.dumps(c) + "\n\n" for c in chunks) + "data: [DONE]\n\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def model_visible_skills(skilldir):
    """Map skill ID to a description snippet, skipping user-invoked skills."""
    result = {}
    for path in skilldir.glob("*/SKILL.md"):
        head = path.read_text().split("---", 2)[1]
        if re.search(r"^\s*disable-model-invocation:\s*true", head, re.M):
            continue
        match = re.search(r"^description:[ \t]*(.*)$", head, re.M)
        value = match[1].strip()
        if value in (">", "|", ">-", "|-", ""):
            value = head[match.end():].strip().splitlines()[0].strip()
        result[path.parent.name] = value.strip("\"'")[:60]
    if len(set(result.values())) != len(result):
        raise AssertionError("Description snippets are not unique; lengthen them")
    return result


def spec_for(agent):
    return generate.agent_specs()[agent]


def expected_skills(agent, installed):
    return installed & generate.allowed_skills(spec_for(agent), installed)


def mcp_allowed(agent, server):
    return server in generate.allowed_mcp(spec_for(agent))


def subagent_allowed(agent, target):
    spec = spec_for(agent)
    return spec.get("mode") == "deny-specialists" or spec["subagents"] is None or target in spec["subagents"]


def mcp_path(server):
    return f"tools.{server}" if re.fullmatch(r"[A-Za-z_]\w*", server) else f'tools["{server}"]'


def run_agent(port, env, cwd, agent, message, json_output=False):
    args = ["opencode", "run", "--server", f"http://127.0.0.1:{port}", "--model", "fixture/fixture",
            "--agent", agent]
    if json_output:
        args += ["--format", "json"]
    return subprocess.run([*args, message], cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=120, check=True)


def first_state(run, tool):
    events = [json.loads(l) for l in run.stdout.splitlines() if l.startswith("{")]
    states = [e["part"]["state"] for e in events
              if e.get("type") == "tool_use" and e["part"].get("tool") == tool]
    if not states:
        raise AssertionError(f"No {tool} call observed: {run.stdout[-2000:]}")
    return states[0]


def call(port, env, root, agent, tool, arguments):
    Stub.pending = (tool, arguments)
    try:
        return first_state(run_agent(port, env, root, agent, "go", json_output=True), tool)
    finally:
        Stub.pending = None


def check_portable(cli):
    """Generate the specialists for other tools and parse each file."""
    import tomllib

    root = Path(tempfile.mkdtemp(prefix="other-tools-agents-", dir="/tmp/opencode"))
    print(f"Other-tools evidence directory: {root}", flush=True)
    env = {"PATH": os.environ["PATH"], "HOME": str(root), "XDG_CONFIG_HOME": str(root / ".config")}
    subprocess.run(["node", str(cli), "generate", "--config", "groups/default.jsonc", "--global",
                    "--features", "subagents", "--targets", ",".join(generate.PORTABLE_TARGETS)],
                   cwd=REPO, env=env, check=True, capture_output=True)
    for name, spec in generate.SPECIALISTS.items():
        claude = root / ".claude/agents" / f"{name}.md"
        head, body = claude.read_text().split("---\n", 2)[1:]
        assert f"name: {name}\n" in head and body.strip() == generate.agent_body(spec), claude
        denied = re.findall(r"^\s+- (mcp__\S+)$", head, re.M)
        assert denied == [f"mcp__{m}" for m in generate.MCP if m not in spec["mcp"]], (name, denied)
        codex = tomllib.loads((root / ".codex/agents" / f"{name}.toml").read_text())
        assert codex["name"] == name and codex["developer_instructions"].strip() == generate.agent_body(spec), codex
        copilot = (root / ".copilot/agents" / f"{name}.agent.md").read_text()
        assert f"name: {name}\n" in copilot and generate.agent_body(spec) in copilot, name
        cursor = list((root / ".cursor").rglob(f"{name}.md"))
        assert len(cursor) == 1 and generate.agent_body(spec) in cursor[0].read_text(), (name, cursor)
        assert f"name: {name}\n" in cursor[0].read_text(), cursor[0]
    for name in generate.OVERRIDES:  # OpenCode's own agents must not reach other tools
        assert not list(root.rglob(f"{name}.*")), name
    print(f"PASS other tools: {len(generate.SPECIALISTS)} agents each for Claude Code, Codex, Copilot "
          "(shared by Copilot CLI) and Cursor; Codex TOML parses", flush=True)


def check(cli):
    root = Path(tempfile.mkdtemp(prefix="opencode-agents-", dir="/tmp/opencode"))
    print(f"Evidence directory: {root}", flush=True)
    home = root / "home"
    home.mkdir()
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
           "XDG_DATA_HOME": str(home / ".local/share"), "XDG_STATE_HOME": str(home / ".local/state"),
           "XDG_CACHE_HOME": str(home / ".cache"), "OPENCODE_DISABLE_AUTOUPDATE": "1"}
    subprocess.run(["node", str(cli), "generate", "--config", "groups/default.jsonc", "--global",
                    "--features", "rules,subagents,skills,commands"],
                   cwd=REPO, env=env, check=True, capture_output=True)
    configdir = home / ".config/opencode"
    files = {p.stem for p in (configdir / "agents").glob("*.md")}
    expected = set(MODES) | {"evaluator", "metacognitive", "security-auditor", "threat-modeling-expert",
                             "reverse-engineer", "malware-analyst", "firmware-analyst"}
    assert files == expected, ("unexpected OpenCode agent files", files ^ expected)
    for path in (configdir / "agents").glob("*.md"):
        head = path.read_text().split("---", 2)[1]
        assert not re.search(r"^name:", head, re.M), path
        assert "disallowedTools" not in head, path  # Claude Code's section stays out of OpenCode
    for name, spec in generate.SPECIALISTS.items():
        body = (configdir / "agents" / f"{name}.md").read_text().split("---", 2)[2]
        assert body.strip() == generate.agent_body(spec), name
    skills = model_visible_skills(configdir / "skills")
    stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    server = None
    results = {}
    try:
        (configdir / "opencode.json").write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json", "model": "fixture/fixture",
            "providers": {"fixture": {
                "package": "@opencode/ai/providers/openai-compatible",
                "settings": {"baseURL": f"http://127.0.0.1:{stub.server_port}/v1"},
                "models": {"fixture": {"capabilities": {"tools": True},
                                       "limit": {"context": 200000, "output": 1000}}}}},
            "mcp": {"servers": {name: {"type": "local", "command": [sys.executable, str(MCP_STUB)]}
                                for name in STUB_SERVERS}}}))
        password = secrets.token_urlsafe(32)
        env["OPENCODE_PASSWORD"] = password
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = subprocess.Popen(["opencode", "serve", "--hostname", "127.0.0.1", "--port", str(port)],
                                  cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        headers = {"Authorization": "Basic " + base64.b64encode(("opencode:" + password).encode()).decode()}
        deadline = time.monotonic() + 40
        while True:
            if server.poll() is not None:
                raise RuntimeError("Private OpenCode server exited before discovery")
            try:
                request = urllib.request.Request(f"http://127.0.0.1:{port}/api/agent", headers=headers)
                with urllib.request.urlopen(request, timeout=5) as response:
                    agents = {a["id"]: a for a in json.load(response)["data"]}
                if set(MODES) <= agents.keys():
                    break
            except (urllib.error.URLError, TimeoutError):
                pass
            if time.monotonic() > deadline:
                raise TimeoutError("Agent discovery did not complete")
            time.sleep(0.2)
        # The Code Mode catalog can lag MCP connection by a few milliseconds, so wait
        # for every stub server to report connected, then let the catalog settle.
        deadline = time.monotonic() + 40
        while True:
            request = urllib.request.Request(f"http://127.0.0.1:{port}/api/mcp", headers=headers)
            with urllib.request.urlopen(request, timeout=5) as response:
                servers = {s["name"]: s["status"].get("status") for s in json.load(response)["data"]}
            if all(servers.get(name) == "connected" for name in STUB_SERVERS):
                break
            if time.monotonic() > deadline:
                raise TimeoutError(f"Stub MCP servers did not connect: {servers}")
            time.sleep(0.2)
        time.sleep(2)
        results["modes"] = {a: agents[a]["mode"] for a in MODES}
        assert results["modes"] == MODES, results["modes"]
        explore = agents["explore"]["permissions"]
        assert {"action": "*", "resource": "*", "effect": "deny"} in explore, explore
        assert not any(r["action"] in ("edit", "write", "skill") and r["effect"] == "allow"
                       for r in explore[explore.index({"action": "*", "resource": "*", "effect": "deny"}):]), explore
        print("PASS explore keeps its built-in read-only policy", flush=True)
        installed = set(skills)
        for agent in PRIMARY:
            before = len(Stub.requests)
            run_agent(port, env, root, agent, "hello")
            text = "\n".join(s for raw in Stub.requests[before:] for s in strings(json.loads(raw)))
            visible = {name for name, snippet in skills.items() if snippet in text}
            expected = expected_skills(agent, installed)
            mcp = {s: f"{mcp_path(s)}.ping(" in text for s in STUB_SERVERS}
            listed = {a: re.search(rf"^- {re.escape(a)}: ", text, re.M) is not None for a in LISTED_SUBAGENTS}
            results[agent] = {"skills": len(visible), "missing": sorted(expected - visible),
                              "unexpected": sorted(visible - expected), "mcp": mcp, "subagents": listed}
            assert visible == expected, (agent, results[agent])
            assert mcp == {s: mcp_allowed(agent, s) for s in STUB_SERVERS}, (agent, mcp)
            assert listed == {a: subagent_allowed(agent, a) and a != agent for a in LISTED_SUBAGENTS}, (agent, listed)
            print(f"PASS {agent}: {len(visible)} skills; MCP and subagent lists match", flush=True)
        for agent, skill, allowed in SKILL_CALLS:
            state = call(port, env, root, agent, "skill", {"id": skill})
            results[f"skill {agent}/{skill}"] = state["status"]
            assert state["status"] == ("completed" if allowed else "error"), (agent, skill, state)
            print(f"PASS {agent} loads {skill}: {state['status']}", flush=True)
        for agent, server_name, allowed in MCP_CALLS:
            state = call(port, env, root, agent, "execute",
                         {"code": f"return await {mcp_path(server_name)}.ping()"})
            reached = "MCP_STUB_PONG" in json.dumps(state)
            results[f"mcp {agent}/{server_name}"] = reached
            assert reached is allowed, (agent, server_name, state)
            print(f"PASS {agent} calls {server_name}: {'reached' if reached else 'blocked'}", flush=True)
        for agent, target, allowed in SUBAGENT_CALLS:
            state = call(port, env, root, agent, "subagent",
                         {"agent": target, "description": "permission test", "prompt": "Reply ok."})
            results[f"subagent {agent}/{target}"] = state["status"]
            assert state["status"] == ("completed" if allowed else "error"), (agent, target, state)
            print(f"PASS {agent} delegates to {target}: {state['status']}", flush=True)
    finally:
        try:
            (root / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        finally:
            try:
                if server is not None:
                    server.terminate()
                    try:
                        server.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()
            finally:
                try:
                    stub.shutdown()
                finally:
                    stub.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cli", type=Path, help="Existing rulesync 41 dist/cli/index.js; no package runner")
    args = parser.parse_args()
    if not args.cli.is_file():
        parser.error("The local rulesync CLI file does not exist")
    check_portable(args.cli.resolve())
    check(args.cli.resolve())
