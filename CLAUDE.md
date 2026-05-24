# Conventions for Claude

## Code style
- 2-space indent, 85-char lines, minimum LOC, maximum readability
- Python: `i` for self, `the` for config (Menzies house style)
- R: kaiaulu function-naming style (verb_noun, snake_case)
- Use `data.table` in R (not tibble/dplyr)
- Use `%>%` from magrittr (kaiaulu does), not the base `|>`

## Deliverable format (Carlos's request, May 6 2026)
- Each analysis ships as **`.Rmd` + companion `.R`** pair
- Format must match kaiaulu's existing vignettes/ style
- YAML header: html_document, toc, number_sections, vignette block
- First chunk: `rm(list=ls()); seed <- 1; set.seed(seed)`
- Second chunk: `require()` calls for all libs (warning=FALSE,message=FALSE)
- Use `parse_config("../tools.yml")` and `parse_config("../conf/<project>.yml")`
- Use kaiaulu helpers: `get_tool_project`, `get_git_repo_path`, etc.
- Prose between chunks explaining the analysis

The `.Rmd` is for the analysis flow. The companion `.R` holds reusable
functions in kaiaulu's library style (with roxygen comments).

Carlos will branch each delivered notebook into kaiaulu as a PR. Treat
each `.Rmd` as something a student would submit for code review.

## Tool installs (Carlos's URLs)
Each of these is a system call from kaiaulu. To enable a kaiaulu wrapper
function, install the binary and provide the path via `tools.yml`.

| tool | repo | enables kaiaulu function |
|------|------|---|
| Perceval | https://github.com/chaoss/grimoirelab-perceval | parse_gitlog, parse_mbox |
| Depends | https://github.com/multilang-depends/depends | parse_dependencies |
| scc | https://github.com/boyter/scc | parse_line_metrics |
| RefactoringMiner | https://github.com/tsantalis/RefactoringMiner | parse_java_code_refactoring_json |
| pattern4.jar | https://users.encs.concordia.ca/~nikolaos/files/pattern_detection/pattern4.jar | parse_gof_patterns (GoF detection) |

Sanity check after install: call a kaiaulu wrapper without ever
mentioning the underlying tool. If it works, the wiring is correct.

## Forbidden moves
- **Do not invent kaiaulu column names.** Verify every column against
  `/path/to/kaiaulu/R/<file>.R` before writing a join or filter.
- **Do not assume `parse_jira()` returns a flat table** — it returns
  `list(issues, comments)`.
- **Do not filter `issue_status` on `c("Closed","Resolved")`** — that's
  what kaiaulu's own metric.R does and it's broken (see
  `kaiaulu_notes/known_bugs.md`). Use `issue_status == "Done"`.
- **Do not assume `dv8_flaws` has a `severity` column** — it doesn't.
- **Do not join `gitlog$file_pathname` to `dv8_flaws$file_path`
  directly** — schema mismatch; rename explicitly.
- **Do not flag a model as "informable" without naming the specific
  kaiaulu function and column** that produces the lift value.
- **Do not produce prose reports as primary output** — output `.Rmd`
  notebooks per Carlos's request. Prose only in `.md` reference docs.

## When acting
- Verify the kaiaulu source before writing schema-dependent code.
- If a parser's output schema is unclear, view its source (search
  `R/<area>.R` for `setnames(` to see what columns it produces).
- Flag uncertainties explicitly. Do not paper over a missing signal
  with "we could lift this somehow."
- After running a tool, summarize the result in one paragraph + the
  raw numbers. No verbose narrative.

## Project status flag
This project is in a handoff state from Claude (web) to Claude Code.
Tim drives. Carlos reviews each delivered `.Rmd` as a PR into kaiaulu.
Rick and Umar are downstream collaborators.
