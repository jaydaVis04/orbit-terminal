return {
  {
    "catppuccin/nvim", name = "catppuccin", priority = 1000,
    config = function()
      require("catppuccin").setup({
        flavour = "mocha",
        dim_inactive = { enabled = false }, -- Twilight owns dimming.
        integrations = {
          nvimtree = true, gitsigns = true, treesitter = true, which_key = true,
          telescope = { enabled = true }, blink_cmp = true,
          native_lsp = { enabled = true }, ufo = true, indent_blankline = { enabled = true },
        },
        custom_highlights = function(c)
          return {
            Cursor = { fg = c.base, bg = "#ffffff" },
            FloatBorder = { fg = c.surface2, bg = c.mantle },
            NormalFloat = { bg = c.mantle },
            MultiCursorCursor = { fg = c.base, bg = c.peach },
            MultiCursorVisual = { bg = c.surface1 },
            MultiCursorDisabledCursor = { fg = c.base, bg = c.overlay0 },
            MultiCursorDisabledVisual = { bg = c.surface0 },
            UfoFoldedBg = { bg = c.surface0 },
            UfoFoldedFg = { fg = c.subtext1 },
            UfoFoldedEllipsis = { fg = c.mauve, italic = true },
          }
        end,
      })
      vim.cmd.colorscheme("catppuccin-mocha")
    end,
  },
  { "nvim-tree/nvim-web-devicons", opts = {} },
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons", "catppuccin" },
    opts = {
      options = {
        theme = "catppuccin-mocha", globalstatus = true,
        component_separators = { left = "│", right = "│" },
        section_separators = { left = "", right = "" },
        disabled_filetypes = { statusline = { "alpha" } },
      },
      sections = {
        lualine_a = { { "mode", icon = "" } },
        lualine_b = { "branch", "diff" },
        lualine_c = { { "filename", path = 1, symbols = { modified = " ●", readonly = " " } }, "diagnostics" },
        lualine_x = {
          { function()
              local mc = package.loaded["multicursor-nvim"]
              return mc and mc.hasCursors() and ("󰗧 " .. mc.numCursors()) or ""
            end, color = { fg = "#fab387" } },
          "filetype",
        },
        lualine_y = { "progress" }, lualine_z = { "location" },
      },
      extensions = { "nvim-tree", "lazy", "mason", "quickfix", "fugitive" },
    },
  },
  {
    "akinsho/bufferline.nvim", version = "*",
    dependencies = { "nvim-tree/nvim-web-devicons", "catppuccin" },
    opts = function() return {
      highlights = require("catppuccin.special.bufferline").get_theme(),
      options = {
        diagnostics = "nvim_lsp", separator_style = "thin", always_show_bufferline = false,
        show_close_icon = false, show_buffer_close_icons = false,
        offsets = { { filetype = "NvimTree", text = "  󰙅  Explorer", text_align = "left", separator = true } },
      },
    } end,
  },
  {
    "folke/which-key.nvim", event = "VeryLazy",
    opts = {
      preset = "helix", delay = 350,
      spec = {
        { "<leader>b", group = "buffers" }, { "<leader>c", group = "code / config" },
        { "<leader>f", group = "find" }, { "<leader>g", group = "git" },
        { "<leader>m", group = "multicursor" }, { "<leader>u", group = "view" },
        { "<leader>x", group = "diagnostics" },
      },
    },
  },
  { "lukas-reineke/indent-blankline.nvim", main = "ibl", event = { "BufReadPost", "BufNewFile" },
    opts = { indent = { char = "│" }, scope = { enabled = false } } },
  {
    "goolord/alpha-nvim", event = "VimEnter",
    config = function()
      local d = require("alpha.themes.dashboard")
      d.section.header.val = { "", "", "N E O V I M", "", "quiet focus · sharp tools", "" }
      d.section.header.opts.hl = "Function"
      d.section.buttons.val = {
        d.button("f", "  Find a file", ":Telescope find_files<CR>"),
        d.button("r", "  Recent files", ":Telescope oldfiles<CR>"),
        d.button("e", "󰙅  Explorer", ":NvimTreeToggle<CR>"),
        d.button("n", "  New file", ":enew<CR>"),
        d.button("h", "󰋖  Key guide", ":edit ~/.config/TERMINAL-KEYS.md<CR>"),
        d.button("l", "󰒲  Plugins", ":Lazy<CR>"),
        d.button("q", "󰅚  Quit", ":qa<CR>"),
      }
      d.section.footer.val = "SPACE is your leader  ·  SPACE u t toggles Twilight"
      d.section.footer.opts.hl = "Comment"
      require("alpha").setup(d.config)
    end,
  },
}
