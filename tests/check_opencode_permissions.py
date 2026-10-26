"""Opt-in runtime check using a local rulesync CLI and the installed OpenCode.

No downloads, real model calls, live settings, or MCP backends are needed.
Run with --legacy to confirm rulesync 38 reproduces the permission loss.
"""

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request


class ModelStub(BaseHTTPRequestHandler):
    """Supply tool calls; OpenCode itself must execute or deny them."""

    def log_message(self, *_args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 2_000_000:
            self.send_error(413)
            return
        request = json.loads(self.rfile.read(length))
        messages = request.get("messages", [])
        tool_results = [m for m in messages if m.get("role") == "tool"]
        text = json.dumps(messages)
        skill = "humanizer" if "TEST_LOAD_humanizer" in text else "eli5"
        invoke = "TEST_LOAD_" in text and not tool_results
        delta = {"role": "assistant"}
        if invoke:
            delta["tool_calls"] = [
                {
                    "index": 0,
                    "id": "call_fixture",
                    "type": "function",
                    "function": {"name": "skill", "arguments": json.dumps({"id": skill})},
                }
            ]
        else:
            delta["content"] = "Fixture complete."
        chunk = {
            "id": "chatcmpl-fixture",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "fixture",
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }
        final = {
            **chunk,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if invoke else "stop"}],
        }
        data = "".join("data: " + json.dumps(c) + "\n\n" for c in (chunk, final))
        data = (data + "data: [DONE]\n\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def isolated_environment(home):
    return {
        "PATH": os.environ["PATH"],
        "LANG": "C.UTF-8",
        "TERM": "dumb",
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "XDG_STATE_HOME": str(home / ".local/state"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
    }


def write_fixture(root):
    source = root / "src/subagents"
    source.mkdir(parents=True)
    (source / "design.md").write_text(
        '---\nname: design\ntargets: ["opencode"]\ndescription: Permission fixture.\n'
        'opencode:\n  mode: all\n  permissions:\n'
        '    - {action: skill, resource: "*", effect: deny}\n'
        '    - {action: skill, resource: humanizer, effect: allow}\n'
        '    - {action: "zap_*", resource: "*", effect: deny}\n---\n'
    )
    (source / "build.md").write_text(
        '---\nname: build\ntargets: ["opencode"]\ndescription: Permission fixture.\n'
        'opencode:\n  mode: primary\n  permissions:\n'
        '    - {action: skill, resource: eli5, effect: deny}\n---\n'
    )
    (root / "rulesync.jsonc").write_text(json.dumps({
        "targets": ["opencode"], "features": ["subagents"], "delete": False, "inputRoots": ["src"],
    }))


def wait_for_agents(port, password, server):
    headers = {"Authorization": "Basic " + base64.b64encode(("opencode:" + password).encode()).decode()}
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Private OpenCode server exited before discovery")
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{port}/api/agent", headers=headers)
            with urllib.request.urlopen(request, timeout=5) as response:
                agents = {a["id"]: a for a in json.load(response)["data"]}
            if "design" in agents:
                return agents
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.2)
    raise TimeoutError("Agent discovery did not complete")


def check(cli, legacy):
    root = Path(tempfile.mkdtemp(prefix="rulesync-permissions-", dir="/tmp/opencode"))
    print(f"Evidence directory: {root}", flush=True)
    home = root / "home"
    home.mkdir()
    env = isolated_environment(home)
    write_fixture(root)
    subprocess.run(["node", str(cli), "generate", "--global"], cwd=root, env=env, check=True)
    configdir = home / ".config/opencode"
    for skill in ("eli5", "humanizer"):
        dest = configdir / "skills" / skill
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: Harmless permission fixture.\n---\nFIXTURE_LOADED_{skill}\n"
        )
    stub = ThreadingHTTPServer(("127.0.0.1", 0), ModelStub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    server = None
    results = {}
    try:
        config = {
            "$schema": "https://opencode.ai/config.json",
            "model": "fixture/fixture",
            "providers": {"fixture": {
                "package": "@opencode/ai/providers/openai-compatible",
                "settings": {"baseURL": f"http://127.0.0.1:{stub.server_port}/v1"},
                "models": {"fixture": {"capabilities": {"tools": True},
                                       "limit": {"context": 32000, "output": 1000}}},
            }},
        }
        (configdir / "opencode.json").write_text(json.dumps(config))
        password = secrets.token_urlsafe(32)
        env["OPENCODE_PASSWORD"] = password
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = subprocess.Popen(
            ["opencode", "serve", "--hostname", "127.0.0.1", "--port", str(port)],
            cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        agents = wait_for_agents(port, password, server)
        results["resolved"] = {name: agents[name]["permissions"] for name in ("build", "design")}
        expected = {"action": "skill", "resource": "eli5", "effect": "deny"}
        assert (expected in results["resolved"]["build"]) is not legacy
        for agent, skill, allowed in (("design", "eli5", False), ("design", "humanizer", True), ("build", "eli5", False)):
            run = subprocess.run(
                ["opencode", "run", "--server", f"http://127.0.0.1:{port}", "--model", "fixture/fixture",
                 "--agent", agent, "--format", "json", f"TEST_LOAD_{skill}"],
                cwd=root, env=env, text=True, capture_output=True, timeout=45,
            )
            key = f"{agent}/{skill}"
            results[key] = {"exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
            assert run.returncode == 0, results[key]
            events = [json.loads(line) for line in run.stdout.splitlines() if line.startswith("{")]
            states = [e["part"]["state"] for e in events if e.get("type") == "tool_use" and e["part"].get("tool") == "skill"]
            assert len(states) == 1, results[key]
            state = states[0]
            assert state["input"] == {"id": skill}, state
            if allowed or legacy:
                assert state["status"] == "completed", state
                assert f"FIXTURE_LOADED_{skill}" in state["output"], state
            else:
                assert state["status"] == "error", state
                assert state["error"] == "Permission denied: skill", state
                assert f"FIXTURE_LOADED_{skill}" not in json.dumps(events), state
            print(f"PASS {key}: {state['status']}", flush=True)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cli", type=Path, help="Existing rulesync dist/cli/index.js; no package runner")
    parser.add_argument("--legacy", action="store_true", help="Expect the rulesync 38 permission-loss bug")
    args = parser.parse_args()
    if not args.cli.is_file():
        parser.error("The local rulesync CLI file does not exist")
    check(args.cli.resolve(), args.legacy)
