local opt = vim.opt
opt.termguicolors = true
opt.background = "dark"
opt.number = true
opt.relativenumber = true
opt.signcolumn = "yes"
opt.cursorline = true
opt.cursorlineopt = "number,line"
opt.wrap = false
opt.linebreak = true
opt.scrolloff = 8
opt.sidescrolloff = 8
opt.splitright = true
opt.splitbelow = true
opt.splitkeep = "screen"
opt.mouse = "a"
opt.clipboard = "unnamedplus"
opt.ignorecase = true
opt.smartcase = true
opt.incsearch = true
opt.inccommand = "split"
opt.expandtab = true
opt.shiftwidth = 2
opt.tabstop = 2
opt.smartindent = true
opt.undofile = true
opt.updatetime = 200
opt.timeoutlen = 400
opt.ttimeoutlen = 20
opt.laststatus = 3
opt.showmode = false
opt.pumheight = 12
opt.winborder = "rounded"
opt.list = true
opt.listchars = { tab = "▏ ", trail = "·", nbsp = "␣" }
opt.fillchars = { eob = " ", fold = " ", foldopen = "", foldclose = "", foldsep = " ", diff = "╱" }
opt.foldcolumn = "1"
opt.foldlevel = 99
opt.foldlevelstart = 99
opt.foldenable = true
opt.guicursor = "n-v-c:block-Cursor,i-ci-ve:ver25-Cursor,r-cr-o:hor20-Cursor"
opt.shortmess:append("Isc")

vim.diagnostic.config({
  severity_sort = true,
  virtual_text = { spacing = 3, prefix = "●", severity = { min = vim.diagnostic.severity.WARN } },
  float = { border = "rounded", source = true },
  signs = { text = { [1] = " ", [2] = " ", [3] = " ", [4] = "󰌵 " } },
  underline = true,
  update_in_insert = false,
})

local group = vim.api.nvim_create_augroup("OrbitEditor", { clear = true })
vim.api.nvim_create_autocmd("TextYankPost", {
  group = group,
  callback = function() vim.hl.on_yank({ timeout = 140 }) end,
})
vim.api.nvim_create_autocmd("FileType", {
  group = group,
  pattern = { "python", "rust", "c", "cpp" },
  callback = function() vim.bo.shiftwidth = 4; vim.bo.tabstop = 4 end,
})
vim.api.nvim_create_autocmd("BufReadPost", {
  group = group,
  callback = function(event)
    local mark = vim.api.nvim_buf_get_mark(event.buf, '"')
    if mark[1] > 0 and mark[1] <= vim.api.nvim_buf_line_count(event.buf) then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})
