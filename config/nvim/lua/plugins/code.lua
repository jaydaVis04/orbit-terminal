return {
  {
    "saghen/blink.cmp", version = "1.*",
    dependencies = { "rafamadriz/friendly-snippets" },
    opts = {
      keymap = { preset = "default", ["<CR>"] = { "accept", "fallback" } },
      appearance = { nerd_font_variant = "mono" },
      completion = {
        list = { selection = { preselect = false, auto_insert = false } },
        menu = { border = "rounded" },
        documentation = { auto_show = true, window = { border = "rounded" } },
        accept = { auto_brackets = { enabled = false } },
      },
      sources = { default = { "lsp", "path", "snippets", "buffer" } },
      fuzzy = { implementation = "lua" },
      signature = { enabled = true, window = { border = "rounded" } },
    },
  },
  {
    "neovim/nvim-lspconfig",
    dependencies = { "mason-org/mason.nvim", "mason-org/mason-lspconfig.nvim", "saghen/blink.cmp" },
    config = function()
      require("mason").setup({ ui = { border = "rounded" } })
      local capabilities = require("blink.cmp").get_lsp_capabilities()
      capabilities.textDocument.foldingRange = { dynamicRegistration = false, lineFoldingOnly = true }
      vim.lsp.config("*", { capabilities = capabilities })
      vim.lsp.config("lua_ls", {
        settings = { Lua = {
          runtime = { version = "LuaJIT" }, diagnostics = { globals = { "vim" } },
          workspace = { checkThirdParty = false, library = { vim.env.VIMRUNTIME } },
          telemetry = { enable = false },
        } },
      })
      vim.lsp.config("clangd", { cmd = { "clangd", "--background-index", "--clang-tidy", "--fallback-style=LLVM" } })
      require("mason-lspconfig").setup({
        ensure_installed = { "lua_ls", "clangd", "pyright", "rust_analyzer", "ts_ls", "bashls" },
        automatic_enable = true,
      })
      vim.api.nvim_create_autocmd("LspAttach", {
        group = vim.api.nvim_create_augroup("OrbitLsp", { clear = true }),
        callback = function(event)
          local function map(key, fn, desc) vim.keymap.set("n", key, fn, { buffer = event.buf, desc = desc }) end
          map("gd", vim.lsp.buf.definition, "Go to definition")
          map("gD", vim.lsp.buf.declaration, "Go to declaration")
          map("gr", "<cmd>Telescope lsp_references<cr>", "References")
          map("gi", vim.lsp.buf.implementation, "Go to implementation")
          map("K", vim.lsp.buf.hover, "Documentation")
          map("<leader>cr", vim.lsp.buf.rename, "Rename symbol")
          map("<leader>ca", vim.lsp.buf.code_action, "Code action")
        end,
      })
    end,
  },
  {
    "stevearc/conform.nvim", cmd = { "ConformInfo" },
    keys = { { "<leader>cf", function() require("conform").format({ async = true, lsp_format = "fallback" }) end,
      mode = { "n", "v" }, desc = "Format file / selection" } },
    opts = {
      formatters_by_ft = { lua = { "stylua" }, python = { "ruff_format", "black", stop_after_first = true },
        javascript = { "prettierd", "prettier", stop_after_first = true },
        typescript = { "prettierd", "prettier", stop_after_first = true },
        c = { "clang_format" }, cpp = { "clang_format" }, rust = { "rustfmt" } },
      default_format_opts = { lsp_format = "fallback" },
      notify_on_error = true,
    },
  },
}
