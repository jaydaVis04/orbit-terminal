#!/usr/bin/env python3
"""Scan tracked/unignored package files, never the private local .config."""

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "absolute user home": re.compile(rb"/(?:Users|home)/[A-Za-z0-9][A-Za-z0-9_.-]+/"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "OpenAI credential": re.compile(rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}"),
    "AWS access key": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "credential assignment": re.compile(rb"(?im)^\s*(?:export\s+)?(?:api_key|access_token|auth_token|password|secret)\s*=\s*['\"]?[^\s'\"$#]{8,}"),
}
FORBIDDEN_NAMES = {".config", ".env", "manifest.json", "original-backup", "original-checksums.json", "presence.json"}


def main():
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    files = sorted(set(p for p in raw.decode().split("\0") if p))
    problems = []
    for name in files:
        path = ROOT / name
        if Path(name).name in FORBIDDEN_NAMES or any(p in ("backups", "__pycache__", "state") for p in Path(name).parts):
            problems.append((name, "private/generated file"))
        data = path.read_bytes()
        if path.suffix == ".png":
            # Refuse textual PNG metadata; the wallpaper requires only image chunks.
            offset = 8
            while offset + 12 <= len(data):
                length = int.from_bytes(data[offset:offset + 4], "big")
                kind = data[offset + 4:offset + 8]
                if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
                    problems.append((name, "image metadata"))
                offset += length + 12
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(data):
                problems.append((name, label))
        for marker in sys.argv[1:]:
            if marker.encode().lower() in data.lower():
                problems.append((name, "identifying text"))
    if problems:
        for name, label in problems:
            print(f"{name}: {label}", file=sys.stderr)
        return 1
    print(f"Privacy scan passed for {len(files)} package files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
