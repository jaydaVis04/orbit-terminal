#!/usr/bin/python3
"""Decompile a binary to C using the bundled offline Ghidra headless analyzer."""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="output C file (default: BINARY.decompiled.c)")
    args = parser.parse_args()
    binary = args.binary.expanduser().resolve()
    if not binary.is_file():
        parser.error("binary must be an existing file")
    output = (args.output or Path(str(binary) + ".decompiled.c")).expanduser().resolve()
    if output == binary:
        parser.error("output cannot overwrite the input binary")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mrrobot-ghidra-") as directory:
        generated = Path(directory) / "decompiled.c"
        result = subprocess.run([
            "/usr/local/bin/ghidra-headless", directory, "analysis",
            "-import", str(binary), "-scriptPath", "/usr/local/share/mrrobot/ghidra-scripts",
            "-postScript", "ExportDecompiled.java", str(generated),
            "-deleteProject", "-analysisTimeoutPerFile", "180", "-max-cpu", "2",
        ])
        if result.returncode:
            return result.returncode
        if not generated.is_file():
            parser.exit(1, "Ghidra did not produce a C file; check the analysis output above.\n")
        shutil.copyfile(generated, output)
    print(f"Decompiled C: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
