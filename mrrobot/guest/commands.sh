#!/usr/bin/env bash
set -euo pipefail
work=/tmp/mrrobot
install -d /usr/local/share/mrrobot/ghidra-scripts
install -m 644 "$work/ExportDecompiled.java" /usr/local/share/mrrobot/ghidra-scripts/
install -m 644 "$work/TOOLS.txt" /usr/local/share/mrrobot/TOOLS.txt
install -m 755 "$work/decompile.py" /usr/local/bin/decompile
install -m 755 "$work/verify.sh" /usr/local/bin/ctf-verify

# The tiered C1 compiler crashed in this x86 TCG guest. Keep the optimizing
# compiler and conservative vector instructions for Ghidra's JVM.
temporary="$(mktemp /usr/local/bin/.mrrobot-command.XXXXXX)"
cat > "$temporary" <<'GHI'
#!/bin/sh
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:+$JAVA_TOOL_OPTIONS }-XX:-TieredCompilation -XX:UseAVX=0"
exec /opt/ghidra/support/analyzeHeadless "$@"
GHI
chmod 755 "$temporary"
mv -f "$temporary" /usr/local/bin/ghidra-headless

# Select the CTF venv for interactive shells and `mrrobot run`, while retaining
# Ubuntu's own /usr/bin/python3 for apt and system utilities.
for tool in python python3 pip pip3 ipython ropper ROPgadget pwn; do
  target="$tool"
  [[ "$tool" == python ]] && target=python3
  temporary="$(mktemp /usr/local/bin/.mrrobot-command.XXXXXX)"
  printf '#!/bin/sh\nexport PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1\nexec /opt/ctf/bin/%s "$@"\n' "$target" > "$temporary"
  chmod 755 "$temporary"
  mv -f "$temporary" "/usr/local/bin/$tool"
done
printf '#!/bin/sh\nexec cat /usr/local/share/mrrobot/TOOLS.txt\n' > /usr/local/bin/ctf-tools
chmod 755 /usr/local/bin/ctf-tools
/opt/ctf/bin/python3 -m pip freeze > /usr/local/share/mrrobot/python.lock
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /usr/local/share/mrrobot/packages.lock
gem list --local > /usr/local/share/mrrobot/ruby.lock
printf '2\n' > /etc/mrrobot-toolkit-version
sync
