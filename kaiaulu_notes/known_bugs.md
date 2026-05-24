# Known kaiaulu inconsistencies found during the May 2026 audit

Items worth raising with Carlos as kaiaulu issues. Each one is verified
by reading the source.

## 1. parse_jira() / metric_file_bug_frequency() filter mismatch

**File**: R/jira.R:583 vs R/metric.R:18

**parse_jira() does**:
```r
issue_status = issue_comment[["status"]][["statusCategory"]][["name"]][[1]]
```
This extracts `status.statusCategory.name` from the JIRA REST API.
Valid values: `"To Do"`, `"In Progress"`, `"Done"`, `"Undefined"`.

**metric_file_bug_frequency() does**:
```r
jira_issues_bug <- jira_issues[(issue_status == "Closed" |
                                issue_status == "Resolved") &
                                issue_type == "Bug"]
```
Filters on `"Closed"` and `"Resolved"`. Those values come from
`status.name`, NOT `status.statusCategory.name`.

**Result**: On Apache JIRA data passed through `parse_jira()`, the
metric function returns ZERO bug rows. Verified on Helix:

| status.name (raw) | status.statusCategory.name (kaiaulu output) |
|---|---|
| Open (34) | To Do |
| Resolved (12) | Done |
| Closed (3) | Done |
| In Progress (1) | In Progress |

**Recommended fix** (one of):
- Change `parse_jira()` to extract `status.name` (more specific,
  matches what metric.R expects).
- Or change all metric.R filters to use the broader category values
  (`"Done"` instead of `c("Closed","Resolved")`).
- Or document the dual-status semantics and ship both columns.

The second option is least disruptive. Same bug pattern affects:
- `metric_file_non_bug_frequency()`  R/metric.R:37
- `metric_file_bug_churn()`         R/metric.R:58
- `metric_file_non_bug_churn()`     R/metric.R:80

## 2. parse_git_blame() schema inconsistent with parse_gitlog()

**File**: R/git.R:160

`parse_gitlog()` returns the joined `author_name_email` and a single
`author_datetimetz` string. `parse_git_blame()` splits these into four
separate columns: `author_name`, `author_email`, `author_timestamp`,
`author_tz`.

**Result**: Cannot join blame data to gitlog without manual
reconstruction:
```r
blame[, author_name_email := paste0(author_name, " <",
                                    author_email, ">")]
```

**Recommended fix**: Have `parse_git_blame()` produce the same
`author_name_email` and `author_datetimetz` columns as
`parse_gitlog()`, or document the join recipe in the function's roxygen.

## 3. parse_dv8_architectural_flaws() column naming differs from gitlog

**File**: R/dv8.R:577

DV8 flaws use `file_path`. Gitlog uses `file_pathname`. Any user
joining flaws to gitlog will hit a silent column mismatch.

**Recommended fix**: rename to `file_pathname` inside the parser to
match the rest of the codebase. (Or rename gitlog to `file_path`.
Either way: pick one.)

## 4. parse_commit_message_id() has an unusual nested-column assignment

**File**: R/git.R:143-145

```r
project_git$commit_message_id$commit_message_id <- stringi::stri_match_first_regex(...)
```

This creates a nested column (data.table-as-list with named element).
It works downstream because metric.R accesses `project_git$commit_message_id`
as a vector, but the syntax is opaque and would benefit from a comment
or a flatter representation.

**Recommended fix**: flatten to a plain character vector column.

## 5. parse_java_code_refactoring_json() returns nested list, not data.table

**File**: R/src.R:261

Every other `parse_*` function returns a data.table (or a list of
data.tables). This one returns `jsonlite::parse_json()` output as-is —
a nested list. Inconsistent with the rest of the API and forces
every caller to flatten.

**Recommended fix**: ship a flat data.table:
```
commit_hash, refactoring_type, refactoring_description,
left_locations (semicolon-joined), right_locations (semicolon-joined)
```
