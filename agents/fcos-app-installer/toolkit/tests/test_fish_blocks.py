"""A command block that asks for a secret, run in a real fish and pasted the way a terminal pastes: the block
first, then the secret. A line copied from a terminal usually ends in a newline, and fish keeps a pasted newline
as part of the secret instead of submitting it, so the block has to strip it. Needs fish; skipped without it."""
import os
import pty
import re
import select
import shutil
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from adapters import derived_keys, example_value, load_adapter, render_step  # noqa: E402
from layout import SKILLS  # noqa: E402

FISH = shutil.which("fish")
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None


class FishSession:
    """fish in a pseudo-terminal that answers the terminal queries newer fish versions send at start."""

    def __init__(self, home: str):
        self.screen = b""
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.environ.update(TERM="xterm-256color", HOME=home, XDG_DATA_HOME=f"{home}/data",
                              XDG_CONFIG_HOME=f"{home}/config")
            os.execvp("fish", ["fish", "-i", "--no-config"])
        self.wait_for(b"> ", 15)

    def _read(self, seconds: float) -> None:
        ready, _, _ = select.select([self.fd], [], [], seconds)
        if not ready:
            return
        try:
            data = os.read(self.fd, 4096)
        except OSError:
            return
        self.screen += data
        if b"\x1b[c" in data or b"\x1b[0c" in data:
            os.write(self.fd, b"\x1b[?62;c")
        if b"\x1b[6n" in data:
            os.write(self.fd, b"\x1b[1;1R")

    def wait_for(self, marker: bytes, timeout: float) -> None:
        start = len(self.screen)
        end = time.monotonic() + timeout
        while marker not in self.screen[start:]:
            if time.monotonic() > end:
                shown = re.sub(rb"\x1b[\[\]][0-9;?<>=]*[ -/]*[@-~]?", b"", self.screen[start:])
                raise AssertionError(f"waited {timeout}s for {marker!r}; the terminal showed {shown[-400:]!r}")
            self._read(0.2)

    def paste(self, text: str) -> None:
        os.write(self.fd, b"\x1b[200~" + text.encode() + b"\x1b[201~")
        for _ in range(5):  # let fish take it in
            self._read(0.1)

    def enter(self) -> None:
        os.write(self.fd, b"\r")

    def close(self) -> None:
        try:
            os.kill(self.pid, signal.SIGKILL)  # an interactive fish takes seconds to answer "exit" in a bare pty
            os.waitpid(self.pid, 0)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass


@unittest.skipUnless(FISH, "needs fish")
class StoreTokenBlockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fcos-fish-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "ws" / "secrets").mkdir(parents=True)
        adapter = load_adapter("virtualization", "proxmox")
        skip = derived_keys(adapter)
        self.values = {key: example_value(key) for key in adapter["manual_steps"]["store_api_token"]["uses"]
                       if key not in skip}
        self.values["WORKSPACE"] = str(self.tmp / "ws")
        step = render_step(adapter, "store_api_token", self.values)
        self.block = step.split("```fish\n", 1)[1].split("```", 1)[0]
        self.stored = self.tmp / "ws" / "secrets" / f"proxmox-{self.values['HOST']}.token"
        lib = SKILLS / "hypervisor-proxmox" / "scripts" / "lib.sh"
        self.key_id = re.search(r"^KEY_ID='([^']+)'", lib.read_text(), re.M).group(1)

    def run_block(self, pasted_secret: str, expect: bytes) -> FishSession:
        session = FishSession(str(self.tmp))
        self.addCleanup(session.close)
        session.paste(self.block)
        session.enter()
        session.wait_for(b"secret", 10)
        session.paste(pasted_secret)
        session.enter()
        session.wait_for(expect, 10)
        return session

    def test_a_clean_paste_is_stored_with_the_server_address_and_says_so(self):
        self.run_block("S3CRET-value", b"Stored")
        self.assertEqual(self.stored.read_text(), f"{self.key_id}=S3CRET-value\naddress={self.values['HOST_ADDRESS']}\n")
        self.assertEqual(oct(self.stored.stat().st_mode & 0o777), "0o600")

    def test_a_pasted_trailing_newline_or_spaces_never_reach_the_file(self):
        for pasted in ("S3CRET-value\n", "  S3CRET-value  \n", "S3CRET-value \n\n"):
            with self.subTest(pasted=pasted):
                self.stored.unlink(missing_ok=True)
                self.run_block(pasted, b"Stored")
                self.assertEqual(self.stored.read_text(),
                                 f"{self.key_id}=S3CRET-value\naddress={self.values['HOST_ADDRESS']}\n")

    def test_an_empty_secret_stores_nothing_and_says_so(self):
        self.run_block("\n", b"nothing was stored")
        self.assertFalse(self.stored.exists() and self.stored.read_text().strip())

    def test_the_prompt_says_to_press_enter(self):
        self.assertRegex(self.block, r'read -s -P "[^"]*press Enter')


if __name__ == "__main__":
    unittest.main()
