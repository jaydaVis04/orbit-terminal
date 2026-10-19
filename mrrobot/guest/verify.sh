#!/usr/bin/env bash
set -euo pipefail
export DEBUGINFOD_URLS=""
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME=/tmp/cache
export TERM=xterm-256color
test "$(uname -m)" = x86_64
infocmp xterm-kitty >/dev/null
infocmp tmux-256color >/dev/null
test "$(cat /proc/sys/kernel/yama/ptrace_scope)" = 0
test "$(cat /proc/sys/kernel/core_pattern)" = '/work/core.%e.%p'
tools=(
  bash cat less ls cp mv rm mkdir rmdir touch ln chmod chown stat du df date tee
  head tail wc sort uniq cut tr paste split join comm diff cmp patch find xargs
  grep sed awk rg fd ps top htop kill pkill pgrep watch time timeout lsof ss ip
  ping dig host traceroute nc socat curl wget ssh scp rsync tar gzip bzip2 xz zstd lz4 zip
  unzip 7z unrar cpio man info which whereis fzf tree bat jq sqlite3 openssl base64
  sha256sum md5sum hexdump od xxd strings file clear vi bc dc dos2unix
  gdb gdb-plain pwndbg gdbserver strace ltrace checksec tmux nvim nano python
  python3 pip ipython gcc g++ make cmake readelf objdump nm addr2line objcopy
  strip size c++filt patchelf lddtree nasm ndisasm yasm hexedit ROPgadget ropper
  r2 rabin2 radiff2 decompile ghidra-headless java javac javap jar jdeps
  binwalk foremost exiftool yara upx z3 unsquashfs mmls fls icat tshark tcpdump
  valgrind one_gadget seccomp-tools ruby starship ctf-tools
)
for tool in "${tools[@]}"; do
  executable="$(command -v "$tool")" || { echo "Missing required tool: $tool"; exit 1; }
  if [[ "$executable" == /* && ! -s "$executable" ]]; then
    echo "Empty executable: $tool"
    exit 1
  fi
done
echo "PASS: ${#tools[@]} Linux essentials and CTF commands are available"
man -w ls less strings >/dev/null
echo 'PASS: local manual pages for core commands, the pager, and binary inspection'
test_directory="$(mktemp -d /work/.mrrobot-test.XXXXXX)"
finish() {
  result=$?
  if (( result != 0 )); then
    for log in "$test_directory"/*.log; do
      if [[ -f "$log" ]]; then
        printf '\nVerification context: %s\n' "$(basename "$log")"
        tail -n 25 "$log"
      fi
    done
  fi
  rm -rf -- "$test_directory"
  exit "$result"
}
trap finish EXIT
cd "$test_directory"
cat > probe.c <<'C'
#include <stdio.h>
int main(void) { puts("mrrobot-test"); return 0; }
C
gcc -g -O0 -fno-pie -no-pie probe.c -o probe64
gcc -m32 -g -O0 -fno-pie -no-pie probe.c -o probe32
printf 'int main(void) { *(volatile int *)0 = 0; return 0; }\n' > coreprobe.c
gcc -g -O0 coreprobe.c -o coreprobe
file probe64 probe32
strings -a probe64 | grep -q mrrobot-test
hexdump -C probe64 > hexdump.log
less -F -X probe.c > /dev/null
printf 'SELECT 6 * 7;\n' | sqlite3 | grep -qx 42
printf 'archive-probe\n' > archive.txt
7z a -bd -y archive.7z archive.txt >/dev/null
7z t -bd archive.7z >/dev/null
zstd -q archive.txt -o archive.txt.zst
test "$(zstd -q -dc archive.txt.zst)" = archive-probe
echo 'PASS: paging, binary strings/hexdump, SQLite, and archive utilities'
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
python3 - <<'PY' > python.log 2>&1
from pwn import ELF, Corefile, process
from pathlib import Path
import resource
import subprocess
import angr
import claripy
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64
from unicorn.x86_const import UC_X86_REG_EAX
from keystone import Ks, KS_ARCH_X86, KS_MODE_64
import lief
import pefile
import elftools
import r2pipe
import yara
from Crypto.Cipher import AES
import requests
import z3
for bits in (32, 64):
    name = f'./probe{bits}'
    assert ELF(name, checksec=False).bits == bits
    child = process(name)
    assert child.recvline(timeout=5) == b'mrrobot-test\n'
    child.close()
print('PASS: pwntools loads and launches 32-bit and 64-bit ELF binaries')
resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
crash = subprocess.Popen(['./coreprobe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
assert crash.wait() == -11
core = Path(f'/work/core.coreprobe.{crash.pid}')
try:
    assert core.is_file(), 'Kernel did not write the core file'
    parsed = Corefile(str(core))
    assert parsed.bits == 64 and parsed.pc != 0
    parsed.close()
finally:
    core.unlink(missing_ok=True)
print('PASS: local core dumps and pwntools Corefile analysis')
assert [i.mnemonic for i in Cs(CS_ARCH_X86, CS_MODE_64).disasm(b'\x90\xc3', 0)] == ['nop', 'ret']
code, _ = Ks(KS_ARCH_X86, KS_MODE_64).asm('mov eax, 42')
cpu = Uc(UC_ARCH_X86, UC_MODE_64)
cpu.mem_map(0x1000, 0x1000)
cpu.mem_write(0x1000, bytes(code))
cpu.emu_start(0x1000, 0x1000 + len(code))
assert cpu.reg_read(UC_X86_REG_EAX) == 42
symbol = claripy.BVS('byte', 8)
solver = claripy.Solver()
solver.add(symbol ^ 0x55 == 0x37)
assert solver.eval(symbol, 1)[0] == 0x62
number = z3.Int('number')
solver_z3 = z3.Solver()
solver_z3.add(number * 2 == 14)
assert solver_z3.check() == z3.sat
assert solver_z3.model()[number].as_long() == 7
assert lief.parse('probe64') is not None
assert yara.compile(source='rule probe { strings: $a = "mrrobot-test" condition: $a }').match('probe64')
project = angr.Project('./probe64', auto_load_libs=False)
simulation = project.factory.simulation_manager(project.factory.entry_state())
simulation.run(n=100)
assert any(b'mrrobot-test' in state.posix.dumps(1) for state in simulation.deadended)
print('PASS: angr execution, Claripy/Z3 solving, Capstone, Unicorn, Keystone, LIEF, YARA, and Python analysis imports')
PY
grep -q 'PASS: angr execution' python.log
cat python.log
r2 -2 -q -c 'e scr.color=0;is~main' probe64 > radare.log
grep -q main radare.log
ROPgadget --binary probe64 > gadgets.log
grep -q 'Unique gadgets found' gadgets.log
ropper --file probe64 --search ret > ropper.log 2>&1
grep -q ret ropper.log
binwalk probe64 > binwalk.log
grep -q ELF binwalk.log
printf 'rule probe { strings: $a = "mrrobot-test" condition: $a }\n' > probe.yar
yara probe.yar probe64 | grep -q probe
tshark --version > /dev/null
tcpdump --version > /dev/null
one_gadget --version > /dev/null
seccomp-tools --version > /dev/null
echo 'PASS: radare2, ROP tools, Binwalk, YARA, and packet-analysis commands'
decompile probe64 -o decompiled.c > decompile.log 2>&1
grep -q mrrobot-test decompiled.c
grep -q main decompiled.c
echo 'PASS: offline Ghidra headless analysis exports working C pseudocode'
nvim --headless '+lua assert(require("telescope")); assert(require("nvim-tree")); assert(vim.fn.maparg(" fw", "n") ~= ""); print("PASS: offline Neovim configuration and navigation")' +qa
tmux -L mrrobot-verify -f "$HOME/.tmux.conf" new-session -d -s test /bin/sleep 10
tmux -L mrrobot-verify kill-server
starship prompt --status 0 >/dev/null
echo 'PASS: red tmux and Starship configurations'
cd /work
echo 'MRROBOT toolchain verification passed'
