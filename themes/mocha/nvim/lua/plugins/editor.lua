return {
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    keys = {
      { "<leader>e", "<cmd>NvimTreeToggle<cr>", desc = "Toggle explorer" },
      { "<leader>E", "<cmd>NvimTreeFindFile<cr>", desc = "Reveal current file" },
    },
    opts = {
      view = { width = 34, preserve_window_proportions = true },
      renderer = { group_empty = true, root_folder_label = ":~:s?$?/..?", indent_markers = { enable = true }, highlight_git = "name" },
      filters = { dotfiles = false, custom = { "^\\.git$", "^node_modules$", "^\\.DS_Store$" } },
      update_focused_file = { enable = true },
      actions = { open_file = { quit_on_open = false, window_picker = { enable = false } } },
      diagnostics = { enable = true, show_on_dirs = true },
      git = { enable = true, ignore = false },
    },
  },
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim", "nvim-tree/nvim-web-devicons" },
    cmd = "Telescope",
    keys = {
      { "<leader><leader>", "<cmd>Telescope find_files<cr>", desc = "Find files" },
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find files" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Search project" },
      { "<leader>fw", "<cmd>Telescope grep_string<cr>", desc = "Find word" },
      { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Find buffer" },
      { "<leader>fr", "<cmd>Telescope oldfiles<cr>", desc = "Recent files" },
      { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "Search help" },
      { "<leader>fk", "<cmd>Telescope keymaps<cr>", desc = "Search keymaps" },
      { "<leader>/", "<cmd>Telescope current_buffer_fuzzy_find<cr>", desc = "Search buffer" },
    },
    opts = {
      defaults = {
        prompt_prefix = "   ", selection_caret = "❯ ", sorting_strategy = "ascending",
        layout_config = { prompt_position = "top", width = 0.90, height = 0.82 },
        file_ignore_patterns = { "node_modules/", "%.git/", "target/", "%.lock$" },
        mappings = { i = { ["<Esc>"] = "close", ["<C-j>"] = "move_selection_next", ["<C-k>"] = "move_selection_previous" } },
      },
      pickers = { find_files = { hidden = true }, buffers = { sort_mru = true, ignore_current_buffer = true } },
    },
  },
  {
    "jake-stewart/multicursor.nvim", branch = "1.0",
    config = function() require("config.multicursor") end,
  },
  {
    "nvim-treesitter/nvim-treesitter", branch = "main", lazy = false,
    build = ":TSUpdate",
    config = function() require("config.treesitter") end,
  },
  {
    "kevinhwang91/nvim-ufo", dependencies = { "kevinhwang91/promise-async" },
    config = function()
      local ufo = require("ufo")
      ufo.setup({
        provider_selector = function(_, ft, bt)
          if bt ~= "" or ft == "NvimTree" then return "" end
          return { "treesitter", "indent" }
        end,
        open_fold_hl_timeout = 150,
        preview = { win_config = { border = "rounded", winblend = 0, maxheight = 16 } },
      })
      vim.keymap.set("n", "zR", ufo.openAllFolds, { desc = "Open all folds" })
      vim.keymap.set("n", "zM", ufo.closeAllFolds, { desc = "Close all folds" })
      vim.keymap.set("n", "zr", ufo.openFoldsExceptKinds, { desc = "Open folds except comments/imports" })
      vim.keymap.set("n", "zm", ufo.closeFoldsWith, { desc = "Close folds by level" })
      vim.keymap.set("n", "zK", ufo.peekFoldedLinesUnderCursor, { desc = "Peek fold" })
    end,
  },
  {
    "folke/twilight.nvim",
    config = function()
      require("twilight").setup({
        dimming = { alpha = 0.40, color = { "Normal", "#cdd6f4" }, term_bg = "#1e1e2e", inactive = true },
        context = 12, treesitter = true,
        expand = { "function", "function_definition", "function_declaration", "method", "table", "if_statement" },
        exclude = { "NvimTree", "alpha", "lazy", "mason", "TelescopePrompt", "help", "qf" },
      })
      -- Neovim 0.12 returns nil for a missing parser; Twilight expects an error.
      -- Keep syntax-aware context where available and use lines elsewhere.
      local view = require("twilight.view")
      local get_context = view.get_context
      view.get_context = function(buf, line)
        local ok, parser = pcall(vim.treesitter.get_parser, buf)
        if ok and parser then return get_context(buf, line) end
        local radius = math.floor(require("twilight.config").options.context / 2)
        return math.max(1, line - radius + 1), math.min(vim.api.nvim_buf_line_count(buf) + 1, line + radius + 2)
      end
      require("twilight").enable()
      vim.api.nvim_create_autocmd({ "BufEnter", "FileType" }, {
        group = vim.api.nvim_create_augroup("OrbitTwilight", { clear = true }),
        callback = function()
          vim.schedule(function()
            if view.enabled then view.on_win_enter() end
          end)
        end,
      })
      vim.keymap.set("n", "<leader>ut", "<cmd>Twilight<cr>", { desc = "Toggle Twilight dimming" })
    end,
  },
  { "echasnovski/mini.bufremove", version = "*", opts = {} },
  { "kylechui/nvim-surround", version = "*", event = "VeryLazy", opts = {} },
  { "windwp/nvim-autopairs", event = "InsertEnter", opts = {
    enabled = function()
      local mc = package.loaded["multicursor-nvim"]
      return not (mc and mc.hasCursors())
    end,
  } },
  {
    "lewis6991/gitsigns.nvim", event = { "BufReadPre", "BufNewFile" },
    opts = { on_attach = function(buf)
      local gs = require("gitsigns")
      local map = function(key, fn, desc) vim.keymap.set("n", key, fn, { buffer = buf, desc = desc }) end
      map("]h", function() gs.nav_hunk("next") end, "Next Git hunk")
      map("[h", function() gs.nav_hunk("prev") end, "Previous Git hunk")
      map("<leader>gp", gs.preview_hunk, "Preview hunk")
      map("<leader>gs", gs.stage_hunk, "Stage hunk")
      map("<leader>gr", gs.reset_hunk, "Reset hunk")
      map("<leader>gb", gs.blame_line, "Blame line")
    end },
  },
  { "tpope/vim-fugitive", cmd = { "Git", "G", "Gdiffsplit", "Gvdiffsplit" },
    keys = { { "<leader>gg", "<cmd>Git<cr>", desc = "Git status" } } },
}
