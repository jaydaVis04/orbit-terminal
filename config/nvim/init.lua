vim.g.mapleader = " "
vim.g.maplocalleader = ","
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

require("config.options")
require("config.keymaps")

-- Keep managed plugins separate from other editor distributions.
local root = vim.fn.stdpath("data") .. "/plugins"
local lazypath = root .. "/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  local output = vim.fn.system({
    "git", "clone", "--filter=blob:none", "--branch=stable",
    "https://github.com/folke/lazy.nvim.git", lazypath,
  })
  if vim.v.shell_error ~= 0 then error("Could not install lazy.nvim:\n" .. output) end
end
vim.opt.rtp:prepend(lazypath)
require("lazy").setup({ { import = "plugins" } }, {
  root = root,
  defaults = { lazy = false },
  install = { colorscheme = { "catppuccin-mocha" } },
  checker = { enabled = false },
  change_detection = { notify = false },
  ui = { border = "rounded" },
  performance = { rtp = { disabled_plugins = { "netrwPlugin", "tutor", "tohtml" } } },
})
