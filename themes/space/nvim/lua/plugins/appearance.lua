-- ORBIT: cool starlight, dark navy panels, and a little nebula violet.
local orbit = {
  base = "#090d18", mantle = "#060914", panel = "#10182a", raised = "#19233a",
  border = "#26324d", text = "#d8e2ff", muted = "#7f8daf",
  cyan = "#7bdff6", violet = "#b39dff", pink = "#f6a6d5", amber = "#ffd18c",
}

return {
  {
    "catppuccin/nvim", name = "catppuccin", priority = 1000,
    config = function()
      require("catppuccin").setup({
        flavour = "mocha",
        dim_inactive = { enabled = false }, -- Twilight owns dimming.
        styles = { comments = { "italic" }, keywords = {}, functions = {}, variables = {} },
        color_overrides = {
          mocha = {
            base = orbit.base, mantle = orbit.mantle, crust = "#040710",
            surface0 = orbit.panel, surface1 = orbit.raised, surface2 = orbit.border,
            overlay0 = "#53627e", overlay1 = orbit.muted, overlay2 = "#9ca9ca",
            subtext0 = "#9ca9ca", subtext1 = "#b8c5e4", text = orbit.text,
            lavender = "#b7c9ff", blue = "#89b4ff", sapphire = "#8ccbf2",
            sky = orbit.cyan, teal = "#82d5cc", green = "#a0dcc1",
            mauve = orbit.violet, pink = orbit.pink, flamingo = "#f4b8ca",
            rosewater = "#f2d5e4", peach = orbit.amber, yellow = "#f4dfaa", red = "#f18da9",
          },
        },
        integrations = {
          nvimtree = true, gitsigns = true, treesitter = true, which_key = true,
          telescope = { enabled = true }, blink_cmp = true,
          native_lsp = { enabled = true }, ufo = true, indent_blankline = { enabled = true },
        },
        custom_highlights = function(c)
          return {
            Cursor = { fg = c.base, bg = "#ffffff" },
            lCursor = { fg = c.base, bg = "#ffffff" },
            CursorLine = { bg = "#101727" },
            CursorLineNr = { fg = c.sky, bold = true },
            LineNr = { fg = "#45536e" },
            WinSeparator = { fg = c.surface2, bg = c.base },
            FloatBorder = { fg = c.surface2, bg = c.mantle },
            NormalFloat = { bg = c.mantle },
            FloatTitle = { fg = c.mauve, bg = c.mantle, bold = true },
            Visual = { bg = "#27314d" },
            Search = { fg = c.peach, bg = "#342d29" },
            IncSearch = { fg = c.base, bg = c.peach, bold = true },
            Pmenu = { bg = c.surface0 },
            PmenuSel = { bg = c.surface1, fg = c.sky, bold = true },
            IblIndent = { fg = "#1b263d" },
            NvimTreeNormal = { bg = c.mantle },
            NvimTreeNormalNC = { bg = c.mantle },
            NvimTreeWinSeparator = { fg = c.surface2, bg = c.mantle },
            NvimTreeRootFolder = { fg = c.mauve, bold = true },
            NvimTreeFolderName = { fg = c.text },
            NvimTreeFolderIcon = { fg = c.sky },
            NvimTreeOpenedFolderName = { fg = c.sky, bold = true },
            NvimTreeIndentMarker = { fg = c.surface2 },
            NvimTreeCursorLine = { bg = c.surface0 },
            TelescopeNormal = { bg = c.mantle },
            TelescopeBorder = { fg = c.surface2, bg = c.mantle },
            TelescopePromptNormal = { bg = c.surface0 },
            TelescopePromptBorder = { fg = c.surface2, bg = c.surface0 },
            TelescopePromptPrefix = { fg = c.sky },
            TelescopePromptTitle = { fg = c.base, bg = c.sky, bold = true },
            TelescopeResultsTitle = { fg = c.mauve, bg = c.mantle },
            TelescopePreviewTitle = { fg = c.base, bg = c.mauve, bold = true },
            TelescopeSelection = { bg = c.surface1, fg = c.text },
            TelescopeSelectionCaret = { fg = c.sky },
            TelescopeMatching = { fg = c.sky, bold = true },
            AlphaHeader = { fg = c.mauve },
            AlphaTitle = { fg = c.sky, bold = true },
            AlphaButtons = { fg = c.text },
            AlphaShortcut = { fg = c.sky, bold = true },
            AlphaFooter = { fg = c.overlay1 },
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
    opts = function()
      local function mode_theme(accent)
        return {
          a = { fg = orbit.base, bg = accent, gui = "bold" },
          b = { fg = orbit.text, bg = orbit.panel },
          c = { fg = orbit.muted, bg = orbit.mantle },
        }
      end
      local wide = function() return vim.o.columns >= 100 end
      return {
      options = {
        theme = {
          normal = mode_theme(orbit.cyan), insert = mode_theme(orbit.violet),
          visual = mode_theme(orbit.pink), replace = mode_theme(orbit.amber),
          command = mode_theme(orbit.amber), inactive = mode_theme(orbit.border),
        },
        globalstatus = true,
        component_separators = { left = "", right = "" },
        section_separators = { left = "", right = "" },
        disabled_filetypes = { statusline = { "alpha" } },
      },
      sections = {
        lualine_a = { { "mode", icon = "󰑓", fmt = function(mode)
          return mode:gsub("V%-LINE", "V-L"):gsub("V%-BLOCK", "V-B")
        end } },
        lualine_b = { { "branch", icon = "", fmt = function(branch)
          return #branch > 20 and branch:sub(1, 18) .. "…" or branch
        end }, { "diff", cond = wide } },
        lualine_c = { { "filename", path = 1, symbols = { modified = " ●", readonly = " " } }, "diagnostics" },
        lualine_x = {
          { function()
              local mc = package.loaded["multicursor-nvim"]
              return mc and mc.hasCursors() and ("󰗧 " .. mc.numCursors()) or ""
            end, color = { fg = orbit.amber } },
          { "filetype", cond = wide },
        },
        lualine_y = { "progress" }, lualine_z = { "location" },
      },
      extensions = { "nvim-tree", "lazy", "mason", "quickfix", "fugitive" },
    } end,
  },
  {
    "akinsho/bufferline.nvim", version = "*",
    dependencies = { "nvim-tree/nvim-web-devicons", "catppuccin" },
    opts = function()
      local theme = require("catppuccin.special.bufferline").get_theme()
      local highlights = type(theme) == "function" and theme() or theme
      highlights.fill = { bg = orbit.mantle }
      highlights.background = { fg = orbit.muted, bg = orbit.mantle }
      highlights.buffer_selected = { fg = orbit.text, bg = orbit.panel, bold = true, italic = false }
      highlights.indicator_selected = { fg = orbit.cyan, bg = orbit.panel }
      highlights.modified_selected = { fg = orbit.amber, bg = orbit.panel }
      return {
      highlights = highlights,
      options = {
        diagnostics = "nvim_lsp", separator_style = "thin", always_show_bufferline = false,
        show_close_icon = false, show_buffer_close_icons = false,
        indicator = { icon = "▎", style = "icon" },
        offsets = { { filetype = "NvimTree", text = "  󰑓  ORBIT / FILES", text_align = "left", separator = true } },
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
      d.section.header.val = {
        [[       .                .       ]],
        [[              .-"""-.           ]],
        [[   .      .-'  .     '-.        ]],
        [[       .-'---._____.---'-.   *   ]],
        [[      (_____.-'   '-._____)      ]],
        [[           '-._____.-'    .      ]],
      }
      d.section.header.opts.hl = "AlphaHeader"
      local title = {
        type = "text", val = "O  R  B  I  T   /   N E O V I M",
        opts = { position = "center", hl = "AlphaTitle" },
      }
      d.section.buttons.val = {
        d.button("f", "  Find a file", ":Telescope find_files<CR>"),
        d.button("r", "  Recent files", ":Telescope oldfiles<CR>"),
        d.button("e", "󰙅  Explorer", ":NvimTreeFocus<CR>"),
        d.button("n", "  New file", ":enew<CR>"),
        d.button("h", "󰋖  Key guide", ":edit ~/.config/TERMINAL-KEYS.md<CR>"),
        d.button("l", "󰒲  Plugins", ":Lazy<CR>"),
        d.button("q", "󰅚  Quit", ":qa<CR>"),
      }
      for _, button in ipairs(d.section.buttons.val) do
        button.opts.width = 38
        button.opts.hl = "AlphaButtons"
        button.opts.hl_shortcut = "AlphaShortcut"
      end
      d.section.buttons.opts.spacing = 0
      d.section.footer.val = "SPACE · leader     SPACE u t · Twilight"
      d.section.footer.opts.hl = "AlphaFooter"
      d.config.layout = {
        { type = "padding", val = 1 }, d.section.header,
        { type = "padding", val = 1 }, title,
        { type = "padding", val = 1 }, d.section.buttons,
        { type = "padding", val = 1 }, d.section.footer,
      }
      require("alpha").setup(d.config)
    end,
  },
}
