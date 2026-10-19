import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("orbit_install", ROOT / "install.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.config = self.home / "preferences.toml"
        self.config.write_text((ROOT / ".config.example").read_text())

    def install(self, profile="space"):
        with contextlib.redirect_stdout(io.StringIO()):
            module.install(self.home, self.config, profile, no_reload=True)

    def swap(self, profile):
        env = dict(os.environ, TERMINAL_THEMES_HOME=str(self.home))
        result = subprocess.run([str(self.home / "bin/swap"), "terminal", profile, "--no-reload"],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_install_and_exact_original_restore(self):
        original = b"# an existing configuration\nset -g mouse off\n"
        (self.home / ".tmux.conf").write_bytes(original)
        self.install()
        self.assertTrue((self.home / ".config/nvim/init.lua").is_file())
        self.swap("original")
        self.assertEqual((self.home / ".tmux.conf").read_bytes(), original)
        self.assertFalse((self.home / ".config/nvim/init.lua").exists())
        self.swap("space")
        self.assertIn("#090d18", (self.home / ".config/kitty/kitty.conf").read_text())

    def test_reinstall_preserves_original_and_avoids_duplicate_shell_sources(self):
        (self.home / ".tmux.conf").write_text("# before installation\n")
        self.install()
        self.install("mocha")
        rc = (self.home / ".zshrc").read_text()
        self.assertEqual(rc.count('source "$HOME/.config/terminal-themes/support/shell.zsh"'), 1)
        self.swap("original")
        self.assertEqual((self.home / ".tmux.conf").read_text(), "# before installation\n")

    def test_profile_edits_survive_switching(self):
        self.install()
        kitty = self.home / ".config/kitty/kitty.conf"
        changed = kitty.read_text() + "\n# local adjustment\n"
        kitty.write_text(changed)
        self.swap("mocha")
        self.swap("space")
        self.assertEqual(kitty.read_text(), changed)

    def test_personal_preferences_are_rendered_without_os_identity(self):
        settings = self.config.read_text().replace('display_name = "pilot"', 'display_name = "navigator"')
        settings = settings.replace('prefix = "M-a"', 'prefix = "C-a"').replace('color = "#ffffff"', 'color = "#abcdef"')
        self.config.write_text(settings)
        self.install()
        starship = tomllib.loads((self.home / ".config/starship.toml").read_text())
        self.assertIn("navigator", starship["format"])
        self.assertNotIn("$username", starship["format"])
        self.assertNotIn("$hostname", starship["format"])
        tmux = (self.home / ".tmux.conf").read_text()
        self.assertIn("set -g prefix C-a", tmux)
        self.assertIn("bind C-a send-prefix", tmux)
        self.assertNotIn("#h", tmux)
        self.assertIn("cursor #abcdef", (self.home / ".config/kitty/kitty.conf").read_text())
        self.assertNotIn("info title", (self.home / ".config/neofetch/config.conf").read_text())
        self.assertEqual((self.home / ".config/terminal-themes/personal.toml").stat().st_mode & 0o777, 0o600)

    def test_invalid_preferences_do_not_write_active_files(self):
        for field, value in [('display_name = "pilot"', 'display_name = "bad#[]"'),
                             ('decay_min = 0.25', 'decay_min = 1.0')]:
            self.config.write_text((ROOT / ".config.example").read_text().replace(field, value))
            with self.assertRaises(ValueError):
                self.install()
            self.assertFalse((self.home / ".tmux.conf").exists())

    def test_dry_run_makes_no_changes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            module.install(self.home, self.config, "space", no_reload=True, dry_run=True)
        self.assertFalse((self.home / ".config").exists())

    def test_corrupt_incoming_profile_is_rejected(self):
        self.install()
        kitty = self.home / ".config/kitty/kitty.conf"
        before = kitty.read_bytes()
        incoming = self.home / ".config/terminal-themes/profiles/mocha/kitty/kitty.conf"
        incoming.unlink()
        env = dict(os.environ, TERMINAL_THEMES_HOME=str(self.home))
        result = subprocess.run([str(self.home / "bin/swap"), "terminal", "mocha", "--no-reload"],
                                env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(kitty.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
