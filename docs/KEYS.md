# Keyboard guide

## Neovim

Leader is **Space**. Pause after pressing it to see available shortcuts.

| Keys | Action |
| --- | --- |
| Space e / Space E | Explorer / reveal current file |
| Space Space / Space f f | Find files |
| Space f g / Space f w | Search project / word under cursor |
| Space f b / Space f r | Buffers / recent files |
| Space / | Search this buffer |
| Shift-H / Shift-L | Previous / next buffer |
| Space b d | Close buffer, preserving splits |
| Ctrl-S / Space w | Save |
| Ctrl-H/J/K/L | Move between editor splits |
| Space \| / Space - | Split vertically / horizontally |
| gd / gr / gi / K | Definition / references / implementation / documentation |
| Space c r / Space c a / Space c f | Rename / code action / format |
| Space g g / Space g p / Space g b | Git status / hunk preview / blame |
| Space u t | Toggle Twilight (starts enabled) |
| Space u w / Space u n / Space u d | Toggle wrap / relative numbers / diagnostics |
| za / zR / zM / zK | Toggle fold / open all / close all / peek fold |
| Space c h | Open this guide |

### Multicursor

Place the cursor on a word. Press **Ctrl-N** to add its next occurrence, then
edit normally: `ciw`, type replacement, Escape. Press Escape again to clear the
extra cursors. Use `u` to undo.

| Keys | Action |
| --- | --- |
| Ctrl-N / Space m n | Add next matching word or selection |
| Space m N / Space m s | Add previous match / skip next match |
| Space m a | Add every matching word or selection |
| Option-Shift-Up/Down | Add cursor above / below |
| Space m k / Space m j | Add above / below in any terminal |
| ga + motion, or visual ga | Add cursors to a text object or selected lines |
| Left / Right with extra cursors | Select previous / next cursor |
| Space m t / Space m x | Toggle cursors / delete main cursor |
| Space m c / Space m r | Clear / restore extra cursors |
| Space m = | Align cursor columns |

Ctrl-N adds cursors in normal/visual mode and navigates completion in insert mode.
Ctrl-Space opens completion; Ctrl-N/P select; Ctrl-Y or Enter accepts a selection;
Tab/Shift-Tab jump snippet placeholders. Enter remains a newline until an item is
selected. Auto-pairs pause while multiple cursors are active.

`:Lazy` manages plugins. `:Mason` manages language servers and tools. Lua, C/C++,
Python, Rust, JavaScript/TypeScript, and Bash servers are configured. Formatting
is explicit with Space c f. `:TSInstallDefaults` installs the default parser set;
`:TSUpdate` refreshes parsers. Treesitter uses no additional Vim regex highlighting;
languages without a parser keep their syntax fallback. Neovim 0.12+ is required.

## tmux

The prefix is **Option-A**: press it, release, then press the next key.
Option-A twice sends a literal Option-A to the application.

| After Option-A | Action |
| --- | --- |
| c | New window in current directory |
| \| / - | Split left-right / top-bottom |
| h j k l | Select pane |
| H J K L | Resize pane (repeatable) |
| z | Zoom pane |
| 1–9 / n / p / Tab | Select / next / previous / last window |
| , / $ | Rename window / session |
| [ | Copy mode; v selects, y copies to macOS clipboard, Escape exits |
| d | Detach |
| r | Reload configuration |
| I | Install tmux plugins |

**Option-S** saves sessions; **Option-R** restores. Continuum saves every 15
minutes and restores at server startup. New windows and panes start at index 1.

## Kitty and shell

Both Option keys act as Alt so Option-A reaches tmux. Command-C/V keep their
macOS clipboard behavior. Command-T opens a tab; Command-Enter opens a window;
Command-Shift-Enter splits; Command-Shift-R reloads appearance. The shell cursor
is a white block with a slow, stretchy white trail; Neovim uses a block in normal mode
and a beam while inserting.

Open a new Kitty window after setup to load Option-key handling and Starship.
Existing shells can run `exec zsh` to load the prompt.
