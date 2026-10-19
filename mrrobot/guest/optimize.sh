#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# This offline lab uses apt/pip and plain core files, so these background
# services add startup work without serving the analysis workflow.
apt-get purge -y snapd apport
systemctl set-default multi-user.target
install -d /etc/systemd/journald.conf.d /etc/security/limits.d
cat > /etc/systemd/journald.conf.d/mrrobot.conf <<'JOURNAL'
[Journal]
Storage=volatile
RuntimeMaxUse=16M
JOURNAL
cat > /etc/security/limits.d/99-mrrobot.conf <<'LIMITS'
ctf soft core unlimited
ctf hard core unlimited
LIMITS
sysctl -w kernel.yama.ptrace_scope=0
sysctl -w kernel.core_pattern=/work/core.%e.%p
systemctl restart systemd-journald
rm -rf /var/log/journal /var/crash
install -d -m 1777 /var/crash

# Ghidra's Linux x86 decompiler handles all supported file/processor formats.
# Native launch helpers for other operating systems are unnecessary here.
/usr/bin/python3 - <<'PY'
from pathlib import Path
import shutil
unneeded = {'linux_arm_64', 'linux_aarch64', 'mac_arm_64', 'mac_x86_64',
            'win_arm_64', 'win_x86_64', 'win_x86_32'}
removed = 0
for directory in (Path('/opt/ghidra').resolve()).rglob('os'):
    if not directory.is_dir():
        continue
    for native in directory.iterdir():
        if native.name in unneeded and native.is_dir():
            removed += sum(path.stat().st_size for path in native.rglob('*') if path.is_file())
            shutil.rmtree(native)
print(f'Removed {removed / 1024**2:.1f} MiB of unused native helpers')
PY
apt-get clean
rm -rf /var/lib/apt/lists/* /root/.cache /home/ctf/.cache
find /var/lib/gems -type f -name '*.gem' -delete
sync
