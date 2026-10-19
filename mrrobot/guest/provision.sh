#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export PIP_NO_CACHE_DIR=1
work=/tmp/mrrobot
apt-get update
apt-get install -y --no-install-recommends \
  sudo bash-completion openssh-server ca-certificates curl git gdb gdbserver ncurses-term \
  strace ltrace file checksec tmux python3 python3-pip python3-venv python3-pwntools \
  binutils binutils-multiarch build-essential gcc-multilib g++-multilib libc6-dbg \
  libc6-i386 lib32stdc++6 patchelf elfutils socat netcat-openbsd nasm xxd hexedit \
  ripgrep fd-find unzip zip xz-utils jq procps psmisc man-db manpages-dev valgrind
apt-get install -y --no-install-recommends "$work/pwndbg.deb"
for candidate in ropper python3-ropper; do
  if apt-cache show "$candidate" >/dev/null 2>&1; then
    apt-get install -y --no-install-recommends "$candidate"
    break
  fi
done
tar -xzf "$work/starship.tar.gz" -C /usr/local/bin starship
tar -xzf "$work/nvim.tar.gz" -C /opt
ln -sf /opt/nvim-linux-x86_64/bin/nvim /usr/local/bin/nvim
ln -sf /usr/bin/fdfind /usr/local/bin/fd
tic -x -o /usr/share/terminfo "$work/kitty.terminfo"
pwndbg_binary="$(command -v pwndbg)"
printf '#!/bin/sh\nexec %s "$@"\n' "$pwndbg_binary" > /usr/local/bin/gdb
chmod 755 /usr/local/bin/gdb
printf '#!/bin/sh\nexec /usr/bin/gdb "$@"\n' > /usr/local/bin/gdb-plain
chmod 755 /usr/local/bin/gdb-plain
install -d -o ctf -g ctf /work /home/ctf/.config/nvim /home/ctf/.config
cp "$work/starship.toml" /home/ctf/.config/starship.toml
cp "$work/init.lua" /home/ctf/.config/nvim/init.lua
cp "$work/tmux.conf" /home/ctf/.tmux.conf
cp "$work/gdbinit" /home/ctf/.gdbinit
mkdir -p /home/ctf/.local/share/nvim/site/pack/offline/start
tar -xf "$work/nvim-plugins.tar" -C /home/ctf/.local/share/nvim/site/pack/offline/start
if ! grep -q '# MRROBOT:' /home/ctf/.bashrc; then
  cat "$work/bashrc" >> /home/ctf/.bashrc
fi
chown -R ctf:ctf /home/ctf /work
cat > /etc/sysctl.d/99-mrrobot.conf <<'SYSCTL'
kernel.yama.ptrace_scope = 0
kernel.core_pattern = /work/core.%e.%p
SYSCTL
sysctl --system >/dev/null
cat > /etc/profile.d/mrrobot.sh <<'PROFILE'
export XDG_CACHE_HOME=/tmp/cache
export PIP_NO_CACHE_DIR=1
export UV_NO_CACHE=1
export PYTHONDONTWRITEBYTECODE=1
export LESSHISTFILE=-
export HISTFILE=/dev/null
export GDBHISTFILE=/dev/null
export DEBUGINFOD_URLS=""
export EDITOR=nvim
export VISUAL=nvim
PROFILE
systemctl disable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades.service pollinate.service || true
systemctl mask apt-daily.service apt-daily-upgrade.service || true
# The prepared image is self-contained; future boots need no cloud metadata.
touch /etc/cloud/cloud-init.disabled
cat > /etc/motd <<'MOTD'
MRROBOT / x86_64 CTF LAB
Session changes are temporary. Use `mrrobot pull` on the Mac to save your work.
MOTD
printf 'ctf ALL=(ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/ctf
chmod 440 /etc/sudoers.d/ctf
apt-get clean
rm -rf /var/lib/apt/lists/* /root/.cache /home/ctf/.cache
journalctl --rotate || true
journalctl --vacuum-size=1M || true
printf 'READY\n' > /etc/mrrobot-ready
