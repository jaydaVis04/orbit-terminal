#!/usr/bin/env python3
"""Install portable terminal profiles; keep preferences and backups local."""

import argparse
from datetime import datetime
import fcntl
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import tomllib

REPO = Path(__file__).resolve().parent
loader = importlib.machinery.SourceFileLoader("orbit_swap", str(REPO / "bin/swap"))
spec = importlib.util.spec_from_loader(loader.name, loader)
swap = importlib.util.module_from_spec(spec)
loader.exec_module(swap)


def load_preferences(path):
    defaults = tomllib.loads((REPO / ".config.example").read_text())
    overrides = tomllib.loads(path.read_text()) if path.exists() else {}
    for section, values in overrides.items():
        if section not in defaults or not isinstance(values, dict):
            raise ValueError(f"Unknown configuration section: {section}")
        for key, value in values.items():
            if key not in defaults[section]:
                raise ValueError(f"Unknown setting: {section}.{key}")
            expected = defaults[section][key]
            numeric = isinstance(expected, float) and type(value) in (float, int)
            if not numeric and type(value) is not type(expected):
                raise ValueError(f"Invalid type for {section}.{key}")
            defaults[section][key] = value
    c = defaults
    for value in (c["identity"]["display_name"], c["tmux"]["status_label"]):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,31}", value):
            raise ValueError("Display name and status label must be 1–32 plain characters")
    if not re.fullmatch(r"[MC]-[a-z0-9]", c["tmux"]["prefix"]):
        raise ValueError("tmux.prefix must look like M-a or C-a")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", c["cursor"]["color"]):
        raise ValueError("cursor.color must be a six-digit hex color")
    font = c["kitty"]["font_family"]
    if not font or any(ch in font for ch in "\n\r\x00#"):
        raise ValueError("Invalid font family")
    for key, low, high in (("font_size", 6, 40), ("padding", 0, 80), ("background_tint", 0, 1)):
        if not low <= c["kitty"][key] <= high:
            raise ValueError(f"kitty.{key} must be between {low} and {high}")
    cursor = c["cursor"]
    if not 0 < cursor["decay_min"] <= cursor["decay_max"] <= 2:
        raise ValueError("Cursor decay must satisfy 0 < min <= max <= 2 seconds")
    if not 0 <= cursor["trail"] <= 1000 or not 1 <= cursor["threshold"] <= 100:
        raise ValueError("Invalid cursor trigger or threshold")
    if len(c["editor"]["leader"]) != 1 or c["editor"]["leader"] in "\n\r\x00":
        raise ValueError("editor.leader must be one character")
    if c["editor"]["clipboard"] not in ("", "unnamed", "unnamedplus"):
        raise ValueError("Unsupported clipboard setting")
    if not re.fullmatch(r"[A-Za-z0-9_./~+-]+", c["editor"]["command"]):
        raise ValueError("editor.command must be a single executable path or name")
    if not all(isinstance(s, str) and re.fullmatch(r"[a-z0-9_]+", s) for s in c["editor"]["language_servers"]):
        raise ValueError("Invalid language-server name")
    if not all(isinstance(p, str) and p and not any(ch in p for ch in "\n\r\x00:") for p in c["paths"]["extra_path"]):
        raise ValueError("Extra PATH entries must be nonempty directories without colons")
    return c


def kitty_option(text, key, value):
    return re.sub(rf"(?m)^{re.escape(key)} .*$", f"{key} {value}", text)


def render_profile(theme, c, home):
    files = {}
    for directory in (REPO / "config/nvim", REPO / "config/neofetch"):
        for p in directory.rglob("*"):
            if p.is_file():
                files[p.relative_to(REPO / "config").as_posix()] = p.read_bytes()
    for p in (REPO / "themes" / theme).rglob("*"):
        if p.is_file():
            files[p.relative_to(REPO / "themes" / theme).as_posix()] = p.read_bytes()
    files["TERMINAL-KEYS.md"] = (REPO / "docs/KEYS.md").read_bytes()
    k = files["kitty/kitty.conf"].decode()
    for key, value in {
        "font_family": c["kitty"]["font_family"], "font_size": c["kitty"]["font_size"],
        "window_padding_width": c["kitty"]["padding"], "cursor": c["cursor"]["color"],
        "cursor_trail": c["cursor"]["trail"], "cursor_trail_color": c["cursor"]["color"],
        "cursor_trail_decay": f'{c["cursor"]["decay_min"]} {c["cursor"]["decay_max"]}',
        "cursor_trail_start_threshold": c["cursor"]["threshold"],
    }.items():
        k = kitty_option(k, key, value)
    if theme == "space":
        k = kitty_option(k, "background_tint", c["kitty"]["background_tint"])
        if not c["kitty"]["wallpaper"]:
            k = kitty_option(k, "background_image", "none")
    files["kitty/kitty.conf"] = k.encode()
    s = files["starship.toml"].decode()
    username_style = tomllib.loads(s)["username"]["style_user"]
    s = s.replace("$username", f'[{c["identity"]["display_name"]} ]({username_style})')
    s = re.sub(r"(?ms)^\[username\]\n.*?(?=^\[|\Z)", "", s)
    if not c["identity"]["show_hostname"]:
        s = re.sub(r"(?m)^\$hostname\\\n", "", s)
        s = re.sub(r"(?ms)^\[hostname\]\n.*?(?=^\[|\Z)", "", s)
    files["starship.toml"] = s.encode()
    t = files["tmux.conf"].decode()
    prefix = c["tmux"]["prefix"]
    t = t.replace("set -g prefix M-a", f"set -g prefix {prefix}").replace("bind M-a send-prefix", f"bind {prefix} send-prefix")
    t = t.replace(" ORBIT", " " + c["tmux"]["status_label"])
    if not c["identity"]["show_hostname"]:
        t = t.replace("#h", c["identity"]["display_name"])
    files["tmux.conf"] = t.encode()
    init = files["nvim/init.lua"].decode().replace('vim.g.mapleader = " "', "vim.g.mapleader = " + json.dumps(c["editor"]["leader"]))
    files["nvim/init.lua"] = init.encode()
    options = files["nvim/lua/config/options.lua"].decode().replace('opt.clipboard = "unnamedplus"', "opt.clipboard = " + json.dumps(c["editor"]["clipboard"]))
    files["nvim/lua/config/options.lua"] = options.encode()
    code = files["nvim/lua/plugins/code.lua"].decode()
    servers = ", ".join(json.dumps(s) for s in c["editor"]["language_servers"])
    code = re.sub(r"ensure_installed = \{[^}]*\}", "ensure_installed = { " + servers + " }", code)
    files["nvim/lua/plugins/code.lua"] = code.encode()
    appearance = files["nvim/lua/plugins/appearance.lua"].decode().replace('bg = "#ffffff"', 'bg = "' + c["cursor"]["color"] + '"')
    files["nvim/lua/plugins/appearance.lua"] = appearance.encode()
    nf = files["neofetch/config.conf"].decode().replace("    info title", '    prin "' + c["identity"]["display_name"] + '"')
    for field, enabled in (("Machine", c["welcome"]["show_machine"]), ("CPU", c["welcome"]["show_cpu"]), ("Memory", c["welcome"]["show_memory"])):
        if not enabled:
            nf = re.sub(rf'(?m)^    info "{field}" .*\n', "", nf)
    files["neofetch/config.conf"] = nf.encode()
    return files


def target(home, name):
    return home / ".tmux.conf" if name == "tmux.conf" else home / ".config" / name


def install(home, config, theme, no_reload=False, dry_run=False):
    home = home.expanduser().resolve()
    c = load_preferences(config)
    profiles = {name: render_profile(name, c, home) for name in ("space", "mocha")}
    entries = [{"profile_path": name, "target": str(target(home, name))} for name in sorted(profiles[theme])]
    if dry_run:
        print(f"Profile: {theme}. {len(entries)} managed files; no changes made.")
        for e in entries:
            print(e["target"])
        return
    root = home / ".config/terminal-themes"
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".swap.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = {}
        presence_file = root / "profiles/original/presence.json"
        if presence_file.exists():
            present = swap.load_json(presence_file)
            for e in entries:
                name = e["profile_path"]
                if name in present:
                    state = swap.read_state(root / "profiles/original" / name) if present[name] else None
                    if present[name] and state is None:
                        raise ValueError(f"Missing original profile file: {name}")
                    previous[name] = state
        for e in entries:
            name = e["profile_path"]
            if name not in previous:
                previous[name] = swap.read_state(Path(e["target"]))
        # A separate backup protects the active setup before each installation.
        backup = root / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup.mkdir(parents=True, mode=0o700)
        for e in entries:
            current = swap.read_state(Path(e["target"]))
            if current is not None:
                swap.write_state(backup / e["profile_path"], current)
        shellrc = home / ".zshrc"
        shell_state = swap.read_state(shellrc)
        if shell_state is not None:
            swap.write_state(backup / "zshrc", shell_state)
        steps = []
        for name, state in previous.items():
            if state is not None:
                steps.append((root / "profiles/original" / name, state))
        steps.append((presence_file, swap.encoded_json({n: s is not None for n, s in previous.items()})))
        for name, files in profiles.items():
            for relative, data in files.items():
                steps.append((root / "profiles" / name / relative, (data, 0o644)))
            steps.append((root / "profiles" / name / "presence.json", swap.encoded_json({n: True for n in files})))
        steps.append((root / "manifest.json", swap.encoded_json(entries)))
        steps.extend((Path(e["target"]), (profiles[theme][e["profile_path"]], 0o644)) for e in entries)
        steps.append((root / "assets/orbit.png", ((REPO / "assets/orbit.png").read_bytes(), 0o644)))
        steps.append((home / "bin/swap", ((REPO / "bin/swap").read_bytes(), 0o755)))
        steps.append((home / "bin/mrrobot", ((REPO / "bin/mrrobot").read_bytes(), 0o755)))
        steps.append((home / "bin/neofetch", ((REPO / "vendor/neofetch/neofetch").read_bytes(), 0o755)))
        integration = (REPO / "config/shell.zsh").read_text()
        prelude = f'export EDITOR={shlex.quote(c["editor"]["command"])}\nexport VISUAL="$EDITOR"\n'
        for entry in reversed(c["paths"]["extra_path"]):
            path = entry.replace("${HOME}", str(home)).replace("$HOME", str(home))
            if path.startswith("~/"):
                path = str(home / path[2:])
            prelude += f'export PATH={shlex.quote(path)}:"$PATH"\n'
        prelude += 'if (( $+commands[starship] )) && [[ ${STARSHIP_SHELL:-} != zsh ]]; then\n  eval "$(starship init zsh)"\nfi\n'
        prelude += "ORBIT_WELCOME=" + ("1" if c["welcome"]["enabled"] else "0") + "\n"
        steps.append((root / "support/shell.zsh", ((prelude + integration).encode(), 0o644)))
        rc = shell_state[0].decode() if shell_state else ""
        source = 'source "$HOME/.config/terminal-themes/support/shell.zsh"'
        if source not in rc:
            rc += '\n# ORBIT terminal integration\nif [[ -r "$HOME/.config/terminal-themes/support/shell.zsh" ]]; then\n  ' + source + '\nfi\n'
            steps.append((shellrc, (rc.encode(), shell_state[1] if shell_state else 0o644)))
        steps.append((root / "personal.toml", (config.read_bytes() if config.exists() else (REPO / ".config.example").read_bytes(), 0o600)))
        steps.append((root / "active", ((theme + "\n").encode(), 0o600)))
        swap.transaction(steps)
        if not config.exists() and config == REPO / ".config":
            swap.write_state(config, ((REPO / ".config.example").read_bytes(), 0o600))
        notes = [] if no_reload else swap.reload_running_apps([(e["profile_path"], Path(e["target"])) for e in entries])
        print(f"Installed {theme}; original files preserved in the local profile.")
        if notes:
            print("; ".join(notes) + ".")
        print("Restart Neovim; open a new Kitty shell for the welcome card.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=REPO / ".config")
    parser.add_argument("--home", type=Path, default=Path.home(), help="target home (also supports isolated tests)")
    parser.add_argument("--profile", choices=("space", "mocha"), default="space")
    parser.add_argument("--no-reload", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    install(args.home, args.config, args.profile, args.no_reload, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, swap.SwapError) as error:
        print(f"install: {error}", file=sys.stderr)
        sys.exit(1)
