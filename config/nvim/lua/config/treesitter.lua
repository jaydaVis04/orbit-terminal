local ts = require("nvim-treesitter")
ts.setup({ install_dir = vim.fn.stdpath("data") .. "/treesitter" })

local M = {}
M.parsers = {
  "bash", "c", "cpp", "css", "html", "javascript", "jsdoc", "json",
  "lua", "luadoc", "markdown", "markdown_inline", "python", "regex", "rust",
  "toml", "tsx", "typescript", "vim", "vimdoc", "yaml",
}
vim.treesitter.language.register("json", "jsonc")

local function attach(buf)
  if not vim.api.nvim_buf_is_valid(buf) or vim.bo[buf].buftype ~= "" then return end
  local lang = vim.treesitter.language.get_lang(vim.bo[buf].filetype)
  if not lang then return end
  -- On Neovim 0.12, this replaces highlight.additional_vim_regex_highlighting = false.
  -- Preserve regex highlighting only for languages without an installed parser.
  if pcall(vim.treesitter.start, buf, lang) then
    vim.bo[buf].syntax = ""
  end
end
vim.api.nvim_create_autocmd("FileType", {
  group = vim.api.nvim_create_augroup("OrbitTreesitter", { clear = true }),
  callback = function(event) attach(event.buf) end,
})
vim.api.nvim_create_user_command("TSInstallDefaults", function()
  ts.install(M.parsers)
end, { desc = "Install this configuration's language parsers" })
return M
