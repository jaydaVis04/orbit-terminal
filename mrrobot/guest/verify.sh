#!/usr/bin/env bash
set -euo pipefail
export DEBUGINFOD_URLS=""
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME=/tmp/cache
export TERM=xterm-256color
test "$(uname -m)" = x86_64
infocmp xterm-kitty >/dev/null
infocmp tmux-256color >/dev/null
for tool in gdb gdb-plain pwndbg strace ltrace file checksec tmux nvim python3 gcc g++ \
            readelf objdump strings patchelf socat nc nasm hexedit ROPgadget starship; do
  command -v "$tool" >/dev/null || { echo "Missing required tool: $tool"; exit 1; }
done
mkdir -p /work/.mrrobot-test
cd /work/.mrrobot-test
cat > probe.c <<'C'
#include <stdio.h>
int main(void) { puts("mrrobot-test"); return 0; }
C
gcc -g -O0 -fno-pie -no-pie probe.c -o probe64
gcc -m32 -g -O0 -fno-pie -no-pie probe.c -o probe32
file probe64 probe32
for bits in 64 32; do
  gdb -q -batch -ex 'python import pwndbg; print("PWNDBG_ACTIVE")' -ex 'break main' -ex run -ex 'p sizeof(void*)' -ex continue "./probe$bits" > "gdb$bits.log" 2>&1
  grep -q 'Breakpoint 1,' "gdb$bits.log"
  grep -q 'exited normally' "gdb$bits.log"
  grep -q 'PWNDBG_ACTIVE' "gdb$bits.log"
  strace -o "strace$bits.log" "./probe$bits" >/dev/null
  grep -q 'write(' "strace$bits.log"
  ltrace -o "ltrace$bits.log" "./probe$bits" >/dev/null
  grep -q 'puts(' "ltrace$bits.log"
  checksec --file="./probe$bits" > "checksec$bits.log"
  echo "PASS: ${bits}-bit execution, Pwndbg/GDB breakpoints, strace, ltrace, checksec"
done
python3 - <<'PY'
from pwn import ELF, process
for bits in (32, 64):
    name = f'./probe{bits}'
    assert ELF(name, checksec=False).bits == bits
    child = process(name)
    assert child.recvline(timeout=5) == b'mrrobot-test\n'
    child.close()
print('PASS: pwntools loads and launches 32-bit and 64-bit ELF binaries')
PY
nvim --headless '+lua assert(require("telescope")); assert(require("nvim-tree")); assert(vim.fn.maparg(" fw", "n") ~= ""); print("PASS: offline Neovim configuration and navigation")' +qa
tmux -L mrrobot-verify -f "$HOME/.tmux.conf" new-session -d -s test /bin/sleep 10
tmux -L mrrobot-verify kill-server
starship prompt --status 0 >/dev/null
echo 'PASS: red tmux and Starship configurations'
cd /work
rm -rf /work/.mrrobot-test
echo 'MRROBOT toolchain verification passed'
