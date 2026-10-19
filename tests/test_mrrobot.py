import contextlib
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("mrrobot_cli", str(REPO / "bin/mrrobot"))
spec = importlib.util.spec_from_loader(loader.name, loader)
lab = importlib.util.module_from_spec(spec)
loader.exec_module(lab)


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.patcher = patch.multiple(lab, ROOT=root, RUN=root / "run", STATE=root / "state.json")
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_transfer_endpoint_validation(self):
        self.assertEqual(lab.endpoint("ctf:/work/a file", "ctf"), "/work/a file")
        self.assertEqual(lab.endpoint("mac:/tmp/a file", "mac"), str(Path("/tmp/a file").resolve()))
        for value in ("mac:/work/a", "ctf:relative", "ctf:/work/../etc", "ctf:/work/a\nfile"):
            with self.assertRaises(lab.LabError):
                lab.endpoint(value, "ctf")

    def test_cleanup_refuses_unrecognized_directories(self):
        lab.RUN.mkdir()
        preserved = lab.RUN / "important"
        preserved.write_text("preserve")
        with self.assertRaises(lab.LabError):
            lab.cleanup()
        self.assertEqual(preserved.read_text(), "preserve")

    def test_cleanup_removes_only_owned_runtime(self):
        lab.RUN.mkdir()
        (lab.RUN / ".mrrobot-session").write_text("owned")
        (lab.RUN / "overlay").write_text("disposable")
        preserved = lab.ROOT / "system.qcow2"
        preserved.write_text("prepared base")
        lab.cleanup()
        self.assertFalse(lab.RUN.exists())
        self.assertEqual(preserved.read_text(), "prepared base")

    def test_failed_initial_push_does_not_leave_a_running_lab(self):
        state = {"clients": [], "pending_entry": False}
        with patch.object(lab, "current", return_value=state), \
             patch.object(lab, "start_unlocked", return_value=state), \
             patch.object(lab, "stop_unlocked") as stop:
            with self.assertRaises(lab.LabError):
                with lab.activity():
                    raise lab.LabError("transfer failed")
            stop.assert_called_once()

    def test_last_client_controls_disposal(self):
        state = {"clients": [999999], "pending_entry": False}
        with patch.object(lab, "current", return_value=state), \
             patch.object(lab, "start_unlocked", return_value=state), \
             patch.object(lab, "alive", return_value=True), \
             patch.object(lab, "stop_unlocked") as stop:
            with lab.activity(entry=True):
                self.assertIn(os.getpid(), state["clients"])
            stop.assert_not_called()
            self.assertEqual(state["clients"], [999999])

    def test_terminal_colors_restore_after_an_error(self):
        class Terminal(io.StringIO):
            def isatty(self):
                return True
        output = Terminal()
        with contextlib.redirect_stdout(output), patch.dict(os.environ, {"TERM": "xterm-256color", "TMUX": ""}):
            with self.assertRaises(RuntimeError):
                with lab.red_terminal():
                    raise RuntimeError("closed connection")
        self.assertIn("MRROBOT", output.getvalue())
        self.assertIn("\x1b]111", output.getvalue())
        self.assertIn("\x1b]104", output.getvalue())


if __name__ == "__main__":
    unittest.main()
