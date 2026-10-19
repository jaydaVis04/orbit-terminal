# MRROBOT

An offline-ready x86 Linux CTF lab behind one command, with a red terminal,
Starship prompt, tmux, and Neovim. It uses QEMU system emulation so 32-bit and
64-bit Linux ELF binaries run under a real x86 kernel, including native ptrace
for GDB, strace, and ltrace on an ARM Mac.

## Use

```sh
mrrobot
mrrobot push mac:~/Downloads/challenge ctf:/work/challenge
mrrobot pull ctf:/work/exploit.py mac:~/Downloads/exploit.py
mrrobot pull -r ctf:/work/ mac:~/Downloads/ctf-results/
mrrobot status
mrrobot stop
```

Push from a second Mac terminal while the lab is open. You can also push first;
that starts and primes a temporary workspace, then `mrrobot` enters it. Use
writable guest paths such as `/work/` or `/home/ctf/`. Directories are supported
with `-r` for pull; push detects local directories automatically.

Your workspace is **temporary**. The last interactive shell exiting stops QEMU
and discards its disk overlay. Pull files to the Mac before leaving. A workspace
started by `push` stays available until you enter and exit, or run `mrrobot stop`.
Multiple terminals can enter the same running lab; it closes after the last one
leaves. `mrrobot stop` explicitly discards the active workspace.

The terminal turns red while inside and restores its configured colors when SSH
returns. The guest prompt labels the environment and network mode. Neovim uses
the same `Space f h` file finder, `Space f w` live grep, and `Space e` tree focus
bindings as ORBIT. The guest tmux prefix is Option-A; inside a host tmux with
the same prefix, press Option-A twice to pass it through.

## Offline and storage

New sessions are offline by default, with only a localhost SSH forwarding rule.
No host directories are mounted and no SSH agent is forwarded. Tools, libraries,
editor plugins, and prompts are already in the prepared image. To connect to a
remote challenge, stop the lab after exporting work, then start explicitly with:

```sh
mrrobot --online
```

Offline operation cannot take zero disk space. The emulator and prepared system
image must remain local. MRROBOT reuses installed QEMU and keeps its own image,
firmware, dedicated SSH identity, and settings in `~/.local/share/mrrobot/`.
Download archives, package-manager caches, and the build directory are removed
after preparation. Session logs and disk changes live in its `run/` directory
and are removed when the session stops. `mrrobot status` reports allocated space.

CPU/RAM settings are local in `~/.local/share/mrrobot/settings.json`; the defaults
are four emulated CPUs and 3072 MiB RAM. Cross-architecture system emulation is
slower than native execution. This environment targets x86 Linux ELF binaries;
it does not promise to run every Windows or macOS x86 executable.

## Tools

GDB with Pwndbg by default, plain GDB (`gdb-plain`), gdbserver, strace, ltrace,
file, checksec, tmux, Neovim, Python, pwntools, GCC/G++, multilib libraries,
libc debug symbols, binutils, ROPgadget, patchelf, ELF utilities, Valgrind,
socat, netcat, NASM, xxd, hexedit, ripgrep, fd, Git, curl, archive tools, and
local manual pages. The guest user is `ctf` with passwordless sudo inside the VM.

## Prepare on another Mac

Install QEMU, Python 3.12+, and the standard OpenSSH command-line tools. Run the
online preparation once from this repository:

```sh
python3 mrrobot/setup.py
```

Preparation downloads an Ubuntu 24.04 amd64 cloud image and verifies its SHA-256,
installs the toolchain, tests both ELF architectures, compresses the final image,
and installs `~/bin/mrrobot`. Subsequent launches need no network or downloads.
The VM image and SSH identity are never committed to Git.

For automation, `mrrobot run -- command args...` executes a command in a disposable
session and removes that session afterward, unless another interactive client
is still using it.

Sources: [QEMU system emulation](https://www.qemu.org/docs/master/system/index.html),
[QEMU user-emulation ptrace limitation](https://www.qemu.org/docs/master/user/main.html),
[Pwndbg setup](https://pwndbg.re/stable/setup/),
[Ubuntu minimal images](https://cloud-images.ubuntu.com/minimal/releases/noble/release/).
