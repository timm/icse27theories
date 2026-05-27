# Per-function exploration vignettes

Each `explore_<theme>.Rmd` walks through one helper-module's public
functions on a single project (helix by default). Every intermediate
table is shown via `head()` so the knitted HTML stays under 1 MB.

Carlos's request:
> "notebooks to allow for exploration of the lift functions"

These are LIVE-RUNNABLE per kaiaulu vignette convention. To knit:

```bash
cd extract/lifts/explore
Rscript -e 'rmarkdown::render("explore_late_hire.Rmd")'
```

## Files

| file | helpers exercised | source R/ file |
|---|---|---|
| `explore_late_hire.Rmd` | `detect_late_hires`, `compute_velocity_changes` | `R/myths_late_hire.R` |
| `explore_szz.Rmd` | `parse_szz_bugfixes`, `compute_injection_changes`, `estimate_leak_rate`, `compute_failrate_per_window` | `R/myths_szz.R` |
| `explore_workforce.Rmd` | `compute_cohorts`, `estimate_transition_rates` | `R/myths_workforce.R` |
| `explore_refactor.Rmd` | `get_release_tags`, `compute_pay_rate`, `flatten_refactoring_json` | `R/myths_refactor.R` |
| `explore_mailing.Rmd` | `parse_mbox_dir`, `build_reply_edges`, `detect_radio_silence` | `R/myths_mailing.R` |

After Carlos's B7 review (fold `R/myths_*.R` into kaiaulu's existing
thematic R files), update the "source R/ file" column to point at
`R/git.R`, `R/mail.R`, etc.

## Conventions

- First chunk: `rm(list=ls())` + `set.seed(1)`
- Second chunk: `library(kaiaulu); library(data.table); library(stringi); library(magrittr)`
- Third chunk: load `conf/helix.yml` (or another project)
- Every helper call is preceded by a markdown paragraph stating
  expected output shape
- Every helper call is followed by `head(out, 10)` for inspection
- Last chunk: a one-paragraph "what we learned" summary
