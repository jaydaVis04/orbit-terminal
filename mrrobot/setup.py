#!/usr/bin/env python3
"""Prepare the offline x86 lab once. Downloads/build caches are removed on success."""

import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
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


def start_builder():
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
    threading.Thread(target=server.serve_forever, daemon=True).start()
    ssh_port = port()
    args = ["qemu-system-x86_64", "-name", "mrrobot-build", "-machine", "q35", "-accel", "tcg,thread=multi,tb-size=128",
            "-cpu", "max", "-smp", "4", "-m", "3072",
            "-smbios", f"type=1,serial=ds=nocloud;s=http://10.0.2.2:{server.server_port}/",
            "-drive", f"if=pflash,format=raw,readonly=on,file={ROOT}/firmware.fd",
            "-drive", f"if=pflash,format=raw,file={ROOT}/vars.fd",
            "-drive", f"file={BUILD}/ubuntu.qcow2,format=qcow2,if=virtio,discard=unmap",
            "-netdev", f"user,id=net0,hostfwd=tcp:127.0.0.1:{ssh_port}-:22", "-device", "virtio-net-pci,netdev=net0",
            "-display", "none", "-serial", f"file:{BUILD}/console.log",
            "-monitor", f"unix:{BUILD}/monitor.sock,server=on,wait=off", "-pidfile", str(BUILD / "qemu.pid"), "-daemonize"]
    subprocess.run(args, check=True)
    options = ["-F", "/dev/null", "-i", str(ROOT / "identity"), "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none",
               "-o", "BatchMode=yes", "-o", "ConnectTimeout=3", "-o", "StrictHostKeyChecking=accept-new",
               "-o", "HostKeyAlias=mrrobot", "-o", f"UserKnownHostsFile={ROOT}/known_hosts"]
    ssh = ["ssh", *options, "-p", str(ssh_port), "ctf@127.0.0.1"]
    for _ in range(180):
        if subprocess.run(ssh + ["true"], capture_output=True).returncode == 0:
            server.shutdown()
            return ssh, options, ssh_port
        time.sleep(2)
    raise RuntimeError("The builder did not become reachable; inspect build/console.log")


def provision(ssh, options, ssh_port):
    subprocess.run(ssh + ["mkdir -p /tmp/mrrobot"], check=True)
    files = [BUILD / name for name in ("pwndbg.deb", "starship.tar.gz", "nvim.tar.gz", "nvim-plugins.tar", "kitty.terminfo")]
    files += list((REPO / "mrrobot/guest").iterdir())
    subprocess.run(["scp", *options, "-P", str(ssh_port), *map(str, files), "ctf@127.0.0.1:/tmp/mrrobot/"], check=True)
    with (BUILD / "provision.log").open("w") as log:
        result = subprocess.run(ssh + ["sudo bash /tmp/mrrobot/provision.sh"], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError("Provisioning failed; inspect build/provision.log")
    subprocess.run(ssh + ["bash /tmp/mrrobot/verify.sh"], check=True)


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
    os.replace(ROOT / "system.qcow2.partial", ROOT / "system.qcow2")
    (ROOT / "ready.json").write_text(json.dumps({"architecture": "x86_64", "system": "Ubuntu 24.04",
        "pwndbg": PWNDBG, "starship": STARSHIP, "nvim": NVIM, "ephemeral": True}, indent=2) + "\n")
    (ROOT / "settings.json").write_text('{"memory_mb": 3072, "cpus": 4}\n')
    shutil.rmtree(BUILD)
    destination = Path.home() / "bin/mrrobot"
    destination.parent.mkdir(exist_ok=True)
    shutil.copy2(REPO / "bin/mrrobot", destination)
    destination.chmod(0o755)
    print("MRROBOT is ready. Run `mrrobot`. Build downloads and package caches were removed.")


def main():
    for executable in ("qemu-system-x86_64", "qemu-img", "curl", "ssh", "scp", "ssh-keygen"):
        if not shutil.which(executable):
            raise RuntimeError(f"Required host program is missing: {executable}")
    if (ROOT / "ready.json").exists():
        print("The offline image is already prepared. Run `mrrobot`.")
        return
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    ROOT.chmod(0o700)
    BUILD.mkdir(exist_ok=True)
    if not (ROOT / "identity").exists():
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "mrrobot-local", "-f", str(ROOT / "identity")], check=True)
    print("Downloading and verifying the x86 system and offline tools…", flush=True)
    prepare_downloads()
    firmware()
    print("Booting the x86 builder…", flush=True)
    try:
        ssh, options, ssh_port = start_builder()
        print("Provisioning the guest. Progress is in build/provision.log…", flush=True)
        provision(ssh, options, ssh_port)
        freeze(ssh)
    finally:
        if (BUILD / "monitor.sock").exists():
            with socket.socket(socket.AF_UNIX) as monitor:
                monitor.connect(str(BUILD / "monitor.sock"))
                monitor.sendall(b"quit\n")


if __name__ == "__main__":
    main()
