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

push: ## prompt msg, commit -am, push
	@read -p "Reason? " msg; git commit -am "$$msg"; git push; git status

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
	   "ps2pdf|pdf target (postscript -> pdf, ghostscript)"; do \
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
