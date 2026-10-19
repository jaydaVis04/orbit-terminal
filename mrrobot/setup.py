#!/usr/bin/env python3
"""Prepare the offline x86 lab once. Downloads/build caches are removed on success."""

import argparse
import fcntl
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tarfile
import threading
import time

REPO = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("MRROBOT_HOME", Path.home() / ".local/share/mrrobot")).expanduser().resolve()
BUILD = ROOT / "build"
UBUNTU = "https://cloud-images.ubuntu.com/minimal/releases/noble/release/"
PWNDBG = "2026.09.15"
STARSHIP = "1.27.0"
NVIM = "0.12.0"
KITTY = "0.49.2"
TOOLKIT_REVISION = 2
RADARE2 = "6.2.4"
GHIDRA = "12.1.4"


def install_appearance():
    shutil.copy2(REPO / "assets/mrrobot.png", ROOT / "wallpaper.png")
    directory = Path.home() / ".config/kitty"
    directory.mkdir(parents=True, exist_ok=True)
    addon = directory / "mrrobot.conf"
    contents = (REPO / "config/kitty/mrrobot.conf").read_bytes()
    if addon.exists() and addon.read_bytes() != contents:
        backup = addon.with_suffix(".conf.mrrobot.bak")
        if not backup.exists():
            shutil.copy2(addon, backup)
    addon.write_bytes(contents)
    config = directory / "kitty.conf"
    current = config.read_text() if config.exists() else ""
    if "include mrrobot.conf" not in [line.strip() for line in current.splitlines()]:
        backup = config.with_suffix(".conf.mrrobot.bak")
        if config.exists() and not backup.exists():
            shutil.copy2(config, backup)
        config.write_text(current.rstrip() + "\n\ninclude mrrobot.conf\n")
    settings_path = ROOT / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    settings.setdefault("fade_seconds", 2.4)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    try:
        listing = subprocess.run(["ps", "-axo", "pid=,comm="], capture_output=True, text=True, timeout=5)
        for line in listing.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and Path(parts[1]).name == "kitty":
                try:
                    os.kill(int(parts[0]), signal.SIGUSR1)
                except OSError:
                    pass
    except (OSError, subprocess.SubprocessError):
        print("Reload Kitty with Cmd+Shift+R to enable wallpaper changes.")


def download(url, path):
    if not path.exists():
        subprocess.run(["curl", "--fail", "--location", "--retry", "3", "--silent", "--show-error",
                        "--output", str(path) + ".partial", url], check=True)
        os.replace(str(path) + ".partial", path)


def port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def firmware():
    binary = Path(shutil.which("qemu-system-x86_64")).resolve()
    for directory in (binary.parent.parent / "share/qemu", Path("/opt/homebrew/share/qemu"),
                      Path("/usr/local/share/qemu"), Path("/usr/share/qemu")):
        if (directory / "edk2-x86_64-code.fd").is_file():
            shutil.copy2(directory / "edk2-x86_64-code.fd", ROOT / "firmware.fd")
            shutil.copy2(directory / "edk2-i386-vars.fd", ROOT / "vars.fd")
            return
    raise RuntimeError("QEMU's x86 EDK2 firmware was not found")


def pack_editor():
    lock = json.loads((REPO / "config/nvim/lazy-lock.json").read_text())
    repositories = {"telescope.nvim": "nvim-telescope/telescope.nvim", "plenary.nvim": "nvim-lua/plenary.nvim",
                    "nvim-tree.lua": "nvim-tree/nvim-tree.lua", "nvim-web-devicons": "nvim-tree/nvim-web-devicons"}
    plugins = BUILD / "plugins"
    plugins.mkdir(exist_ok=True)
    for name, upstream in repositories.items():
        if (plugins / name).is_dir():
            continue
        archive = BUILD / (name + ".tar.gz")
        download(f"https://codeload.github.com/{upstream}/tar.gz/{lock[name]['commit']}", archive)
        with tarfile.open(archive) as tar:
            tar.extractall(plugins, filter="data")
            extracted = plugins / tar.getmembers()[0].name.split("/")[0]
        if extracted.name != name:
            extracted.rename(plugins / name)
    with tarfile.open(BUILD / "nvim-plugins.tar", "w") as tar:
        for name in repositories:
            tar.add(plugins / name, arcname=name)


def prepare_downloads():
    image_name = "ubuntu-24.04-minimal-cloudimg-amd64.img"
    download(UBUNTU + image_name, BUILD / "ubuntu.qcow2")
    download(UBUNTU + "SHA256SUMS", BUILD / "SHA256SUMS")
    if not (BUILD / "verified-image").exists():
        expected = next(line.split()[0] for line in (BUILD / "SHA256SUMS").read_text().splitlines()
                        if line.split()[-1].lstrip("*") == image_name)
        actual = hashlib.sha256((BUILD / "ubuntu.qcow2").read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("Ubuntu image checksum mismatch")
        subprocess.run(["qemu-img", "resize", str(BUILD / "ubuntu.qcow2"), "16G"], check=True)
        (BUILD / "verified-image").write_text(actual + "\n")
    download(f"https://github.com/pwndbg/pwndbg/releases/download/{PWNDBG}/pwndbg_{PWNDBG}_amd64.deb", BUILD / "pwndbg.deb")
    download(f"https://github.com/starship/starship/releases/download/v{STARSHIP}/starship-x86_64-unknown-linux-musl.tar.gz", BUILD / "starship.tar.gz")
    download(f"https://github.com/neovim/neovim/releases/download/v{NVIM}/nvim-linux-x86_64.tar.gz", BUILD / "nvim.tar.gz")
    download(f"https://raw.githubusercontent.com/kovidgoyal/kitty/v{KITTY}/terminfo/kitty.terminfo", BUILD / "kitty.terminfo")
    pack_editor()
    prepare_tool_downloads()


def prepare_tool_downloads():
    assets = (
        (f"https://github.com/radareorg/radare2/releases/download/{RADARE2}/radare2_{RADARE2}_amd64.deb",
         "radare2.deb", "7019eedc0e0e87d1f53d6b8f5fc62b898567679c5efdce7fbfc557c9e7655e90"),
        (f"https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_{GHIDRA}_build/ghidra_{GHIDRA}_PUBLIC_20260921.zip",
         "ghidra.zip", "ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db"),
    )
    for url, name, expected in assets:
        print(f"Downloading and verifying {name}…", flush=True)
        path = BUILD / name
        download(url, path)
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise RuntimeError(f"Checksum mismatch for {name}; the image has not been replaced")


def start_builder(upgrade=False):
    server = None
    if not upgrade:
        server = cloud_seed()
        threading.Thread(target=server.serve_forever, daemon=True).start()
    ssh_port = port()
    args = ["qemu-system-x86_64", "-nodefaults", "-name", "mrrobot-build", "-machine", "q35", "-accel", "tcg,thread=multi,tb-size=128",
            "-cpu", "max", "-smp", "4", "-m", "3072",
            "-drive", f"if=pflash,format=raw,readonly=on,file={ROOT}/firmware.fd",
            "-drive", f"if=pflash,format=raw,file={BUILD}/vars.fd",
            "-drive", f"file={BUILD}/ubuntu.qcow2,format=qcow2,if=virtio,discard=unmap",
            "-netdev", f"user,id=net0,hostfwd=tcp:127.0.0.1:{ssh_port}-:22", "-device", "virtio-net-pci,netdev=net0",
            "-display", "none", "-serial", f"file:{BUILD}/console.log",
            "-monitor", f"unix:{BUILD}/monitor.sock,server=on,wait=off", "-pidfile", str(BUILD / "qemu.pid"), "-daemonize"]
    if server:
        args += ["-smbios", f"type=1,serial=ds=nocloud;s=http://10.0.2.2:{server.server_port}/"]
    try:
        subprocess.run(args, check=True)
        options = ["-F", "/dev/null", "-i", str(ROOT / "identity"), "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none",
                   "-o", "BatchMode=yes", "-o", "ConnectTimeout=3", "-o", "StrictHostKeyChecking=accept-new",
                   "-o", "HostKeyAlias=mrrobot", "-o", f"UserKnownHostsFile={ROOT}/known_hosts"]
        ssh = ["ssh", *options, "-p", str(ssh_port), "ctf@127.0.0.1"]
        for _ in range(180):
            if subprocess.run(ssh + ["true"], capture_output=True).returncode == 0:
                return ssh, options, ssh_port
            time.sleep(2)
        raise RuntimeError("The builder did not become reachable; inspect build/console.log")
    finally:
        if server:
            server.shutdown()
            server.server_close()


def cloud_seed():
    seed = BUILD / "seed"
    seed.mkdir(exist_ok=True)
    public_key = (ROOT / "identity.pub").read_text().strip()
    (seed / "meta-data").write_text("instance-id: mrrobot-build\nlocal-hostname: mrrobot\n")
    (seed / "vendor-data").write_text("#cloud-config\n{}\n")
    (seed / "user-data").write_text("""#cloud-config
hostname: mrrobot
manage_etc_hosts: true
users:
  - name: ctf
    groups: [sudo]
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - """ + public_key + """
ssh_pwauth: false
disable_root: true
package_update: false
runcmd:
  - [systemctl, disable, --now, apt-daily.timer, apt-daily-upgrade.timer]
""")
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(seed)))
    return server


def provision(ssh, options, ssh_port, upgrade=False):
    subprocess.run(ssh + ["mkdir -p /tmp/mrrobot"], check=True)
    names = ["radare2.deb", "ghidra.zip"]
    if not upgrade:
        names += ["pwndbg.deb", "starship.tar.gz", "nvim.tar.gz", "nvim-plugins.tar", "kitty.terminfo"]
    files = [BUILD / name for name in names]
    files += sorted(path for path in (REPO / "mrrobot/guest").iterdir() if path.is_file())
    subprocess.run(["scp", *options, "-P", str(ssh_port), *map(str, files), "ctf@127.0.0.1:/tmp/mrrobot/"], check=True)
    with (BUILD / "provision.log").open("w") as log:
        script = "tools.sh" if upgrade else "provision.sh"
        result = subprocess.run(ssh + [f"sudo bash /tmp/mrrobot/{script}"], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError("Provisioning failed; inspect build/provision.log")
    with (BUILD / "verify.log").open("w") as log:
        result = subprocess.run(ssh + ["bash /tmp/mrrobot/verify.sh"], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError("Toolchain checks failed; inspect build/verify.log")
    print("All guest toolchain checks passed.", flush=True)


def freeze(ssh):
    subprocess.run(ssh + ["sudo rm -rf /tmp/mrrobot /tmp/cache /home/ctf/.cache /root/.cache /var/log/cloud-init*; sudo fstrim -av; sudo shutdown -h now"], check=False)
    for _ in range(120):
        if not (BUILD / "monitor.sock").exists():
            break
        time.sleep(1)
    if (BUILD / "monitor.sock").exists():
        raise RuntimeError("Builder did not stop; the prepared image has not been replaced")
    subprocess.run(["qemu-img", "convert", "-O", "qcow2", "-c", "-o", "compression_type=zstd",
                    str(BUILD / "ubuntu.qcow2"), str(ROOT / "system.qcow2.partial")], check=True)
    (ROOT / "system.qcow2.partial").chmod(0o444)
    # Existing QEMU sessions retain their open base image; future sessions get
    # the verified replacement. Serialize publication with the normal launcher.
    with (ROOT / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        os.replace(ROOT / "system.qcow2.partial", ROOT / "system.qcow2")
        (ROOT / "ready.json").write_text(json.dumps({"architecture": "x86_64", "system": "Ubuntu 24.04",
            "pwndbg": PWNDBG, "starship": STARSHIP, "nvim": NVIM, "ephemeral": True,
            "toolkit_revision": TOOLKIT_REVISION, "radare2": RADARE2, "ghidra": GHIDRA}, indent=2) + "\n")
    settings_path = ROOT / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    settings.setdefault("memory_mb", 3072)
    settings.setdefault("cpus", 4)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    shutil.rmtree(BUILD)
    destination = Path.home() / "bin/mrrobot"
    destination.parent.mkdir(exist_ok=True)
    shutil.copy2(REPO / "bin/mrrobot", destination)
    destination.chmod(0o755)
    print("MRROBOT is ready. Run `mrrobot`. Build downloads and package caches were removed.")


def stop_builder(ssh=None):
    if not (BUILD / "monitor.sock").exists():
        return
    if ssh:
        try:
            subprocess.run(ssh + ["sudo sync; sudo shutdown -h now"],
                           capture_output=True, timeout=30)
        except subprocess.SubprocessError:
            pass
        deadline = time.monotonic() + 90
        while (BUILD / "monitor.sock").exists() and time.monotonic() < deadline:
            time.sleep(1)
    if (BUILD / "monitor.sock").exists():
        with socket.socket(socket.AF_UNIX) as monitor:
            monitor.connect(str(BUILD / "monitor.sock"))
            monitor.sendall(b"quit\n")


def main():
    global BUILD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upgrade-tools", action="store_true", help="upgrade an existing offline image without changing active sessions")
    args = parser.parse_args()
    for executable in ("qemu-system-x86_64", "qemu-img", "curl", "ssh", "scp", "ssh-keygen"):
        if not shutil.which(executable):
            raise RuntimeError(f"Required host program is missing: {executable}")
    if (ROOT / "ready.json").exists() and not args.upgrade_tools:
        install_appearance()
        shutil.copy2(REPO / "bin/mrrobot", Path.home() / "bin/mrrobot")
        print("The offline image is already prepared. Run `mrrobot`.")
        return
    if args.upgrade_tools and not ((ROOT / "ready.json").is_file() and (ROOT / "system.qcow2").is_file()):
        raise RuntimeError("Prepare the base image first with setup.py")
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    ROOT.chmod(0o700)
    if not args.upgrade_tools:
        install_appearance()
    build_lock = (ROOT / ".build.lock").open("a")
    fcntl.flock(build_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.upgrade_tools:
        BUILD = ROOT / "build-tools"
    if BUILD.is_symlink():
        raise RuntimeError("Refusing to use a symlink build directory")
    BUILD.mkdir(exist_ok=True)
    if not (ROOT / "identity").exists():
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "mrrobot-local", "-f", str(ROOT / "identity")], check=True)
    if args.upgrade_tools:
        print("Preparing expanded offline tools; current sessions stay open…", flush=True)
        prepare_tool_downloads()
        if not (BUILD / "ubuntu.qcow2").exists():
            subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", "-F", "qcow2", "-b",
                            str(ROOT / "system.qcow2"), str(BUILD / "ubuntu.qcow2")], check=True)
    else:
        print("Downloading and verifying the x86 system and offline tools…", flush=True)
        prepare_downloads()
        firmware()
    shutil.copy2(ROOT / "vars.fd", BUILD / "vars.fd")
    print("Booting the x86 builder…", flush=True)
    ssh = None
    try:
        ssh, options, ssh_port = start_builder(upgrade=args.upgrade_tools)
        print(f"Provisioning the guest. Progress is in {BUILD.name}/provision.log…", flush=True)
        provision(ssh, options, ssh_port, upgrade=args.upgrade_tools)
        freeze(ssh)
    finally:
        stop_builder(ssh)


if __name__ == "__main__":
    main()
