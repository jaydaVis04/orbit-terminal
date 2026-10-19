vim.g.mapleader = " "
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1
vim.opt.termguicolors = true
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.mouse = "a"
vim.opt.signcolumn = "yes"
vim.opt.cursorline = true
vim.opt.expandtab = true
vim.opt.shiftwidth = 4
vim.opt.tabstop = 4
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.splitright = true
vim.opt.splitbelow = true
vim.opt.scrolloff = 8
vim.opt.wrap = false
vim.opt.undofile = false
vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.shadafile = "NONE"
vim.opt.showmode = false
vim.opt.laststatus = 3
vim.opt.guicursor = "n-v-c:block,i-ci:ver25,r:hor20"
vim.opt.winborder = "rounded"
local hl = vim.api.nvim_set_hl
hl(0,"Normal",{fg="#f4cbd3",bg="#10070b"})
hl(0,"NormalFloat",{fg="#f4cbd3",bg="#1d0c12"})
hl(0,"FloatBorder",{fg="#7a2331",bg="#1d0c12"})
hl(0,"Comment",{fg="#985867",italic=true})
hl(0,"Function",{fg="#ff6b7f",bold=true})
hl(0,"Keyword",{fg="#ff334f",bold=true})
hl(0,"String",{fg="#e9a097"})
hl(0,"Number",{fg="#ff9da7"})
hl(0,"Type",{fg="#ff8c9d"})
hl(0,"CursorLine",{bg="#251018"})
hl(0,"LineNr",{fg="#75404d"})
hl(0,"CursorLineNr",{fg="#ff334f",bold=true})
hl(0,"Visual",{bg="#672438"})
hl(0,"StatusLine",{fg="#10070b",bg="#ff334f",bold=true})
hl(0,"WinSeparator",{fg="#7a2331"})
vim.opt.statusline = " MRROBOT / x86  %f %m%=%l:%c  %p%% "
vim.cmd("packloadall")
require("nvim-tree").setup({view={width=30},renderer={indent_markers={enable=true}},update_focused_file={enable=true}})
require("telescope").setup({defaults={sorting_strategy="ascending",layout_config={prompt_position="top"}}})
local map=vim.keymap.set
map("n","<leader>e","<cmd>NvimTreeFocus<cr>",{desc="Focus explorer"})
map("n","<leader>fe","<cmd>NvimTreeToggle<cr>",{desc="Toggle explorer"})
map("n","<leader>fh","<cmd>Telescope find_files<cr>",{desc="Find files"})
map("n","<leader>ff","<cmd>Telescope find_files<cr>",{desc="Find files"})
map("n","<leader>fw","<cmd>Telescope live_grep<cr>",{desc="Live grep"})
map("n","<leader>fb","<cmd>Telescope buffers<cr>",{desc="Buffers"})
map("n","<leader>w","<cmd>write<cr>",{desc="Save"})
map("n","<Esc>","<cmd>nohlsearch<cr>")
for key,dir in pairs({h="h",j="j",k="k",l="l"}) do map("n","<C-"..key..">","<C-w>"..dir) end
