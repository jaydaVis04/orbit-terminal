import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("mrrobot_setup", Path(__file__).resolve().parents[1] / "mrrobot/setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ImageUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.build = self.root / "build-tools"
        self.build.mkdir()
        for name, value in (("ROOT", self.root), ("BUILD", self.build)):
            replacement = patch.object(setup, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def test_upgrade_builder_keeps_runtime_disk_and_firmware_separate(self):
        with patch.object(setup, "cloud_seed") as seed, patch.object(setup, "port", return_value=2222), \
                patch.object(setup.subprocess, "run", return_value=Mock(returncode=0)) as run:
            setup.start_builder(upgrade=True)
        seed.assert_not_called()
        arguments = run.call_args_list[0].args[0]
        self.assertIn(f"file={self.build}/ubuntu.qcow2,format=qcow2,if=virtio,discard=unmap", arguments)
        self.assertIn(f"if=pflash,format=raw,file={self.build}/vars.fd", arguments)
        self.assertFalse(any(str(self.root / "run") in argument for argument in arguments))

    def test_failed_conversion_preserves_the_installed_offline_image(self):
        image = self.root / "system.qcow2"
        image.write_bytes(b"working offline image")
        metadata = self.root / "ready.json"
        metadata.write_text('{"toolkit_revision": 1}\n')

        def command(arguments, **kwargs):
            if arguments[0] == "qemu-img":
                raise subprocess.CalledProcessError(1, arguments)
            return Mock(returncode=0)

        with patch.object(setup.subprocess, "run", side_effect=command):
            with self.assertRaises(subprocess.CalledProcessError):
                setup.freeze(["ssh", "builder"])
        self.assertEqual(image.read_bytes(), b"working offline image")
        self.assertEqual(metadata.read_text(), '{"toolkit_revision": 1}\n')
        self.assertTrue(self.build.is_dir())

    def test_bad_tool_checksum_is_rejected_before_booting(self):
        def corrupt_download(url, path):
            path.write_bytes(b"not the official release")

        with patch.object(setup, "download", side_effect=corrupt_download), \
                patch.object(setup.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "Checksum mismatch for radare2.deb"):
                setup.prepare_tool_downloads()
        run.assert_not_called()

    def test_failed_build_flushes_and_shuts_down_before_removing_qemu(self):
        monitor = self.build / "monitor.sock"
        monitor.touch()

        def shutdown(arguments, **kwargs):
            self.assertIn("sudo sync; sudo shutdown -h now", arguments)
            monitor.unlink()
            return Mock(returncode=0)

        with patch.object(setup.subprocess, "run", side_effect=shutdown), \
                patch.object(setup.socket, "socket") as connection:
            setup.stop_builder(["ssh", "builder"])
        connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
