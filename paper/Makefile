# vim: ts=2 sw=2 sts=2 et :
SHELL := /bin/bash
OPEN  := $(shell command -v open 2>/dev/null || command -v xdg-open 2>/dev/null || echo true)
need   = @command -v $(1) >/dev/null || { printf "missing: %s (needed for %s)\n" $(1) $(2); exit 1; }

help: ## show help
	@gawk 'BEGIN {FS = ":.*?##"; \
	         printf "\nUsage:\n  make \033[36m<target>\033[0m [VAR=val ...]\n\ntargets:\n"} \
	       /^[~a-zA-Z0-9_%\.\/ -]+:.*?##/ { \
	         printf("  \033[36m%-20s\033[0m %s\n", $$1, $$2) | "sort" }' $(MAKEFILE_LIST)
	@printf "\ndefaults:\n"
	@gawk 'match($$0, /^([A-Za-z][A-Za-z0-9]*)[ \t]*\?=[ \t]*([^#]*[^# \t])[ \t]*#[ \t]*(.+)/, a) { \
	         printf("  \033[36m%-8s\033[0m = %-30s %s\n", a[1], a[2], a[3]) | "sort" }' $(MAKEFILE_LIST)

push: ## audit staleness + bless pages + prompt msg, commit -am, push
	@cd .. && python3 paper/scripts/audit_staleness.py || { \
	  echo "FAIL: docs out of sync with paper/outputs/full_audit.csv"; \
	  echo "Run: cd paper && make audit-staleness  for details. "; \
	  exit 1; }
	@cd .. && python3 docs/scripts/check_pages.py || { \
	  echo "FAIL: docs/models/*.html violates page contract"; \
	  exit 1; }
	@read -p "Reason? " msg; cd .. && git commit -am "$$msg" && git push && git status

refresh: ## ingest data/dropzone/* + run full pipeline + gates (raw data + lift CSVs)
	@cd .. && python3 scripts/refresh.py

refresh-lifts: ## ingest only lift CSVs from data/dropzone/ (skip raw-data path)
	@cd .. && python3 scripts/refresh.py --lifts-only

refresh-dry: ## show what refresh would do without moving files or running steps
	@cd .. && python3 scripts/refresh.py --dry-run

doctor: ## check required tools (✓ found, ✗ missing)
	@for e in \
	   "R|run R scripts" \
	   "Rscript|render .Rmd, run companion .R" \
	   "pandoc|Rmd -> html via rmarkdown" \
	   "java|RefactoringMiner, Depends, pattern4.jar" \
	   "git|push target, kaiaulu git parsing" \
	   "gawk|help target (self-doc)" \
	   "scc|kaiaulu parse_line_metrics" \
	   "perceval|kaiaulu parse_gitlog, parse_mbox" \
	   "a2ps|pdf target (text -> postscript)" \
	   "ps2pdf|pdf target (postscript -> pdf, ghostscript)" \
	   "nvim|vi target (boots nvim with vim.pack)" \
	   "tmux|tmux target (private socket conf)"; do \
	   c=$${e%%|*}; use=$${e##*|}; \
	   if command -v $$c >/dev/null; then \
	     printf "  \033[32m✓\033[0m %-10s used by: %s\n" "$$c" "$$use"; \
	   else \
	     printf "  \033[31m✗\033[0m %-10s missing — can't: %s\n" "$$c" "$$use"; fi; done
	@printf "\nkaiaulu binaries (set paths in tools.yml):\n"
	@printf "  Perceval        https://github.com/chaoss/grimoirelab-perceval\n"
	@printf "  Depends         https://github.com/multilang-depends/depends\n"
	@printf "  scc             https://github.com/boyter/scc\n"
	@printf "  RefactoringMiner https://github.com/tsantalis/RefactoringMiner\n"
	@printf "  pattern4.jar    https://users.encs.concordia.ca/~nikolaos/files/pattern_detection/pattern4.jar\n"
	@printf "\nmacOS: brew install r pandoc gawk a2ps ghostscript scc openjdk\n"
	@printf   "linux: apt install r-base pandoc gawk a2ps ghostscript default-jdk\n"

## inference layer (this dir) ----------------------------------

inference: outputs/full_audit.csv outputs/lifts.csv outputs/cross_project.csv outputs/boundary_check.csv outputs/calibrated_verdicts.csv ## structural V&V + all data-anchored reports

outputs/full_audit.csv: sd.py tests.py full_audit.py
	python3 full_audit.py

outputs/lifts.csv: scripts/melt_lifts.py ## one row per (model, project, metric); rebuilt from upstream extract/ run
	python3 scripts/melt_lifts.py

outputs/cross_project.csv: outputs/lifts.csv cross_project.py
	python3 cross_project.py

outputs/boundary_check.csv: outputs/lifts.csv boundary_check.py
	python3 boundary_check.py

outputs/calibrated_verdicts.csv: outputs/lifts.csv calibrate.py
	python3 calibrate.py

audit-orphans: ## flag init keys never read/written in step()
	python3 scripts/audit_orphans.py

audit-staleness: ## flag docs/ numbers drifting from outputs/full_audit.csv
	python3 scripts/audit_staleness.py

findings: inference ## print headline findings F0..F4
	@echo "==== F0 boundary-adequacy violations ===="
	@grep -E "out_of_range|at_boundary" outputs/boundary_check.csv | head -20 || true
	@echo "==== F1 brooksq.leak_rate per project ===="
	@awk -F, '$$1=="brooksq" && $$3=="leak_rate"' outputs/lifts.csv
	@echo "==== F2 debt.pay_rate per project ===="
	@awk -F, '$$1=="debt" && $$3=="pay_rate_median"' outputs/lifts.csv
	@echo "==== F3 brooks_tax per project ===="
	@awk -F, '$$1=="brooks" && $$3=="brooks_tax_median"' outputs/lifts.csv
	@echo "==== F4 brooksq.inj_rate_increase per project ===="
	@awk -F, '$$1=="brooksq" && $$3=="inj_rate_increase"' outputs/lifts.csv

clean-inference: ## remove generated inference CSVs (keep lifts.csv)
	rm -f outputs/full_audit.csv outputs/cross_project.csv outputs/boundary_check.csv outputs/calibrated_verdicts.csv

## render (extract-side Rmd notebooks) ----------------------------

RmdFiles := $(wildcard ../extract/lifts/*.Rmd) $(wildcard ../extract/feasibility/*.Rmd) $(wildcard ../extract/smells/*.Rmd)
HtmlFiles := $(RmdFiles:.Rmd=.html)

render: $(HtmlFiles) ## render all .Rmd -> .html

%.html: %.Rmd ## one .Rmd -> .html
	$(call need,Rscript,render)
	@echo "rendering: $<"
	@Rscript -e 'rmarkdown::render("$<", output_format="html_document", quiet=TRUE)'

clean-html: ## remove rendered .html
	@find lifts feasibility smells models -name '*.html' -delete 2>/dev/null; true

## vi -----------------------------------------------------------

F ?= $(firstword $(wildcard *.R) $(wildcard *.py) $(wildcard *.Rmd)) # for vi

vi: ## tuned nvim + catppuccin via vim.pack (wiped on exit)
	$(call need,nvim,vi)
	$(call need,git,vi)
	@D=$$(mktemp -d); trap "rm -rf $$D" EXIT; \
	 printf '%s\n' "$$INITLUA" > $$D/init.lua; \
	 NVIM_APPNAME=icse27 nvim --clean -u $$D/init.lua $F

define INITLUA
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

vim.o.number = true
vim.o.relativenumber = true
vim.o.cursorline = true
vim.o.mouse = "a"
vim.o.termguicolors = true
vim.o.expandtab = true
vim.o.tabstop = 2
vim.o.shiftwidth = 2
vim.o.softtabstop = 2
vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.scrolloff = 8
vim.o.signcolumn = "yes"
vim.o.splitbelow = true
vim.o.splitright = true
vim.o.wrap = true
vim.o.linebreak = true
vim.o.clipboard = "unnamedplus"
vim.o.fillchars = "vert:│,eob:·"
vim.o.winborder = "rounded"
vim.o.splitkeep = "screen"
vim.o.smoothscroll = true

vim.opt.packpath:prepend(vim.fn.stdpath("data") .. "/site")
vim.pack.add({
  "https://github.com/catppuccin/nvim",
  "https://github.com/nvim-lualine/lualine.nvim",
  "https://github.com/zaldih/themery.nvim",
  "https://github.com/folke/tokyonight.nvim",
  "https://github.com/rebelot/kanagawa.nvim",
  "https://github.com/rose-pine/neovim",
  "https://github.com/EdenEast/nightfox.nvim",
})
vim.cmd.colorscheme("catppuccin-mocha")
vim.cmd("hi! WinSeparator guifg=#7aa2f7 guibg=NONE")
vim.cmd("hi! VertSplit    guifg=#7aa2f7 guibg=NONE")
require("lualine").setup({ options = { theme = "auto" } })
require("themery").setup({
  themes = {
    "catppuccin-mocha","catppuccin-latte",
    "tokyonight-storm","tokyonight-day",
    "kanagawa-wave","kanagawa-dragon",
    "rose-pine","rose-pine-dawn",
    "nightfox","duskfox","carbonfox",
  },
  livePreview = true,
})

vim.api.nvim_create_autocmd("TextYankPost", {
  callback = function() vim.hl.on_yank() end,
})

vim.diagnostic.config({
  virtual_text     = false,
  signs            = true,
  underline        = true,
  update_in_insert = false,
  severity_sort    = true,
  float            = { border = "rounded" },
})

vim.filetype.add({ extension = { Rmd = "rmd", rmd = "rmd" } })

local function on_attach(a)
  local c = vim.lsp.get_client_by_id(a.data.client_id)
  if c then c.server_capabilities.semanticTokensProvider = nil end
  local b = { buffer = a.buf, silent = true }
  vim.keymap.set("n", "K",         vim.lsp.buf.hover,         b)
  vim.keymap.set("n", "gd",        vim.lsp.buf.definition,    b)
  vim.keymap.set("n", "gr",        vim.lsp.buf.references,    b)
  vim.keymap.set("n", "<leader>e", vim.diagnostic.open_float, b)
end
vim.api.nvim_create_autocmd("LspAttach", { callback = on_attach })

if vim.fn.executable("R") == 1 then
  vim.lsp.config("r_language_server", {
    cmd          = {"R", "--slave", "-e", "languageserver::run()"},
    filetypes    = {"r", "rmd"},
    root_markers = {"DESCRIPTION", ".Rprofile", ".git"},
  })
  vim.lsp.enable("r_language_server")
end

if vim.fn.executable("pylsp") == 1 then
  vim.lsp.config("pylsp", {
    cmd          = {"pylsp"},
    filetypes    = {"python"},
    root_markers = {"pyproject.toml", "setup.py", "setup.cfg", ".git"},
  })
  vim.lsp.enable("pylsp")
end
endef
export INITLUA

## tmux ---------------------------------------------------------

tmux: ## tuned tmux on private socket (wiped on exit)
	$(call need,tmux,tmux)
	@D=$$(mktemp -d); trap "rm -rf $$D" EXIT; \
	 printf '%s\n' "$$TMUXCONF" > $$D/tmux.conf; \
	 tmux -L icse27 -f $$D/tmux.conf new-session -A -s main

define TMUXCONF
# --- core ---
set -g  default-terminal "tmux-256color"
set -ag terminal-overrides ",xterm-256color:RGB,*:RGB"
set -g  mouse on
set -g  base-index 1
setw -g pane-base-index 1
set -g  renumber-windows on
set -g  escape-time 0
set -g  history-limit 50000
set -g  focus-events on
setw -g aggressive-resize on
setw -g mode-keys vi

# --- prefix: C-Space ---
unbind C-b
set -g prefix C-Space
bind C-Space send-prefix

# --- splits keep cwd; | vertical, - horizontal ---
unbind '"'
unbind %
bind '|' split-window -h -c "#{pane_current_path}"
bind '-' split-window -v -c "#{pane_current_path}"
bind  c  new-window      -c "#{pane_current_path}"

# --- sessions: fast make/jump ---
bind  C command-prompt -p "session:" "new-session -s '%%'"
bind  S choose-tree -Zs
bind -n M-h switch-client -p
bind -n M-l switch-client -n

# --- copy-mode vi ---
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi y send -X copy-selection-and-cancel

# --- catppuccin-mocha status bar ---
set -g  status-position top
set -g  status-justify  centre
set -g  status-style          "bg=#1e1e2e,fg=#cdd6f4"
set -g  window-status-style   "bg=#1e1e2e,fg=#a6adc8"
set -g  window-status-current-style "bg=#cba6f7,fg=#1e1e2e,bold"
set -g  window-status-format         " #I:#W "
set -g  window-status-current-format " #I:#W "
set -g  pane-border-style        "fg=#45475a"
set -g  pane-active-border-style "fg=#89b4fa"
set -g  message-style "bg=#cba6f7,fg=#1e1e2e,bold"
set -g  status-left-length  40
set -g  status-right-length 60
set -g  status-left  "#[bg=#89b4fa,fg=#1e1e2e,bold] #S #[bg=#1e1e2e,fg=#89b4fa]"
set -g  status-right "#[fg=#a6e3a1]#[bg=#a6e3a1,fg=#1e1e2e,bold] %H:%M #[bg=#a6e3a1,fg=#fab387]#[bg=#fab387,fg=#1e1e2e,bold] %d-%b "
endef
export TMUXCONF

## pdf ----------------------------------------------------------

Font   ?= 5         # for ~/tmp/%.pdf
Cols   ?= 2         # for ~/tmp/%.pdf
Orient ?= landscape # for ~/tmp/%.pdf

define RSSH
style R is
alphabets are "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_.0"
case sensitive
keywords in Keyword are
  if,else,for,while,repeat,function,return,break,next,in,TRUE,FALSE,
  NULL,NA,NA_integer_,NA_real_,NA_character_,Inf,NaN,T,F
end keywords
keywords in Keyword_strong are
  library,require,source,setwd,c,list,data.frame,data.table,vector,
  matrix,array,length,names,nrow,ncol,dim,sapply,lapply,mapply,apply,
  print,cat,paste,paste0,sprintf,assign,get,exists,is.null,is.na,
  stop,warning,message,tryCatch,Reduce,Filter,Map,which
end keywords
keywords in Comment are self end keywords
sequences are "#" Comment,C-string end sequences
end style
endef
export RSSH

~/tmp/%.pdf : %.R Makefile ## R -> pdf via a2ps
	$(call need,a2ps,pdf)
	$(call need,ps2pdf,pdf)
	@mkdir -p ~/tmp
	@echo "pdfing : $@ ..."
	@D=$$(mktemp -d); trap "rm -rf $$D" EXIT; \
	 mkdir -p $$D/.a2ps; echo "$$RSSH" > $$D/.a2ps/r.ssh; \
	 HOME=$$D a2ps -Bj --$(Orient) --line-numbers=1 --highlight-level=normal \
	      --borders=no --pro=color --right-footer="" --left-footer="" \
	      --pretty-print=r --footer="page %p." -M letter \
	      --font-size=$(Font) --columns $(Cols) \
	      -o - $< | ps2pdf - $@
	@$(OPEN) $@
