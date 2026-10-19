import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

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

    def wallpaper(self):
        wallpaper = lab.KittyWallpaper()
        wallpaper.enabled = True
        wallpaper.window = "11"
        wallpaper.control = Mock(return_value=json.dumps([{"id": 7, "tabs": []}]))
        wallpaper.change = Mock()
        return wallpaper

    def test_wallpaper_restores_after_an_error(self):
        wallpaper = self.wallpaper()
        with self.assertRaises(RuntimeError), patch.object(lab, "alive", return_value=True):
            with wallpaper:
                raise RuntimeError("SSH failed")
        self.assertEqual(wallpaper.change.call_args_list[-1].args, ("0",))
        self.assertFalse((lab.ROOT / "appearance.json").exists())

    def test_wallpaper_restores_after_the_last_client_in_its_os_window(self):
        first, second = self.wallpaper(), self.wallpaper()
        with patch.object(lab, "alive", return_value=True):
            with patch.object(lab.os, "getpid", return_value=111):
                first.__enter__()
            with patch.object(lab.os, "getpid", return_value=222):
                second.__enter__()
            second.change.assert_not_called()
            with patch.object(lab.os, "getpid", return_value=111):
                first.__exit__(None, None, None)
            self.assertEqual(first.change.call_count, 1)
            with patch.object(lab.os, "getpid", return_value=222):
                second.__exit__(None, None, None)
        second.change.assert_called_once_with("0", entering=False)
        self.assertFalse((lab.ROOT / "appearance.json").exists())

    def test_failed_wallpaper_change_removes_its_graphics_cover(self):
        wallpaper = lab.KittyWallpaper()
        with patch.object(wallpaper, "fade"), \
             patch.object(wallpaper, "control", side_effect=OSError("Kitty unavailable")), \
             patch.object(wallpaper, "clear_cover") as clear:
            with self.assertRaises(OSError):
                wallpaper.change("wallpaper.png", entering=True)
            clear.assert_called_once()

    def test_boot_display_uses_guest_logs_without_claiming_ssh_is_ready(self):
        lab.RUN.mkdir()
        console = lab.RUN / "console.log"
        screen = lab.BootScreen()
        screen.enabled = True
        console.write_text("Linux version 6.8.0\n")
        screen.console()
        self.assertEqual(screen.stage, 4)
        console.write_text("Started ssh.service - OpenBSD Secure Shell server.\n")
        screen.console()
        self.assertEqual(screen.stage, 5)


if __name__ == "__main__":
    unittest.main()
