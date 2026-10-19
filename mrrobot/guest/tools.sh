#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
work=/tmp/mrrobot

# Explicit essentials: minimal cloud images omit even tools such as less.
# Restore local documentation when the minimal image excludes man/info files.
/usr/bin/python3 - <<'PY'
from pathlib import Path
for path in Path('/etc/dpkg/dpkg.cfg.d').glob('*'):
    if not path.is_file():
        continue
    lines = path.read_text().splitlines(keepends=True)
    kept = [line for line in lines if not (
        line.lstrip().startswith('path-exclude') and
        any(directory in line for directory in ('/usr/share/man', '/usr/share/info'))
    )]
    if kept != lines:
        path.write_text(''.join(kept))
PY
printf 'wireshark-common wireshark-common/install-setuid boolean false\n' | debconf-set-selections
apt-get update
apt-get install -y --no-install-recommends \
  bash bash-completion coreutils findutils diffutils grep sed gawk less file \
  bsdextrautils util-linux procps psmisc lsof time tree htop debianutils patch man-db \
  manpages manpages-dev info nano vim-tiny fzf bat ripgrep fd-find bc dc dos2unix \
  tar gzip bzip2 xz-utils zstd lz4 zip unzip p7zip-full unrar-free cpio rpm2cpio \
  curl wget git rsync openssh-client openssl ca-certificates jq sqlite3 \
  iproute2 iputils-ping dnsutils net-tools traceroute socat netcat-openbsd tcpdump tshark \
  binutils binutils-multiarch elfutils patchelf pax-utils nasm yasm \
  build-essential gcc-multilib g++-multilib cmake pkg-config python3-dev \
  python3-venv libffi-dev libssl-dev gdb gdbserver strace ltrace valgrind \
  libc6-dbg libc6-i386 lib32stdc++6 hexedit binwalk foremost \
  libimage-exiftool-perl yara upx-ucl z3 openjdk-21-jdk-headless \
  squashfs-tools sleuthkit ruby ruby-dev
if ! man -w ls strings >/dev/null 2>&1; then
  apt-get install -y --no-install-recommends --reinstall \
    coreutils bash findutils diffutils grep sed binutils file util-linux procps
fi
apt-get install -y --no-install-recommends "$work/radare2.deb"

if [[ ! -d /opt/ghidra_12.1.4_PUBLIC ]]; then
  unzip -q "$work/ghidra.zip" -d /opt
fi
ln -sfn /opt/ghidra_12.1.4_PUBLIC /opt/ghidra
ln -sf /usr/bin/fdfind /usr/local/bin/fd
ln -sf /usr/bin/batcat /usr/local/bin/bat

/usr/bin/python3 -m venv /opt/ctf
/opt/ctf/bin/python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools
/opt/ctf/bin/python3 -m pip install --no-cache-dir -r "$work/requirements.txt"
/opt/ctf/bin/python3 -m pip check
gem install --no-document one_gadget seccomp-tools

bash "$work/optimize.sh"
bash "$work/commands.sh"

apt-get clean
rm -rf /var/lib/apt/lists/* /root/.cache /home/ctf/.cache
find /var/lib/gems -type f -name '*.gem' -delete
sync
