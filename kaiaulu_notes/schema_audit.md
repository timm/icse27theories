# Kaiaulu parser schemas — verified from source

All column names below are from reading `R/<file>.R` in the kaiaulu
source uploaded as k.zip. Verified by following `setnames()` calls and
data.table construction. Do not deviate.

## parse_gitlog() — R/git.R:19

Returns a single `data.table` with columns:

```
author_name_email          chr   "Name <email@domain>"
author_datetimetz          chr   ISO-ish string; caller does as.POSIXct
commit_hash                chr   git SHA
committer_name_email       chr
committer_datetimetz       chr
commit_message             chr
file_pathname              chr   one row per file per commit
lines_added                int
lines_removed              int
file_pathname_renamed      chr   when applicable
```

Note: `author_datetimetz` is stored as a STRING. Caller must convert:
```r
project_git$author_datetimetz <- as.POSIXct(project_git$author_datetimetz,
                                            format="%Y-%m-%d %H:%M:%S")
```

## parse_commit_message_id() — R/git.R:143

**Does NOT return a separate table.** Mutates the input gitlog by
adding column `commit_message_id` and returns the modified gitlog:

```r
gitlog <- parse_gitlog(perceval_path, repo_path)
gitlog <- parse_commit_message_id(gitlog, issue_id_regex)
# now gitlog has a commit_message_id column
```

Implementation quirk (R/git.R:143-145): uses unusual nested
assignment `project_git$commit_message_id$commit_message_id <- ...`.
Don't worry about it; downstream code accesses it as
`gitlog$commit_message_id`.

## parse_git_blame() — R/git.R:160

**Inconsistent with parse_gitlog.** Splits the name+email+date+tz
into FOUR separate columns:

```
author_name        chr
author_email       chr
author_timestamp   chr
author_tz          chr
```

This is a known schema mismatch. Any join from blame to gitlog needs
to reconstruct `author_name_email = paste0(author_name, " <",
author_email, ">")` first.

## parse_jira() — R/jira.R:527

Returns a **LIST**, not a flat table:

```r
parsed <- parse_jira(json_folder_path)
jira_issues   <- parsed$issues     # data.table, 24 columns
jira_comments <- parsed$comments   # data.table, 11 columns
```

### parsed$issues columns

```
issue_key                       chr     "HELIX-1234"
issue_summary                   chr
issue_parent                    chr     parent issue key (epic, etc.)
issue_type                      chr     "Bug" / "Improvement" / "New Feature" / ...
issue_status                    chr     statusCategory.name — "To Do" / "Done" / "In Progress"
issue_resolution                chr     "Fixed" / "Won't Fix" / NA
issue_components                chr     SEMICOLON-joined string
issue_description               chr
issue_priority                  chr     "Critical" / "Major" / ...
issue_affects_versions          chr     semicolon-joined
issue_fix_versions              chr     semicolon-joined
issue_labels                    chr     semicolon-joined
issue_votes                     int
issue_watchers                  int
issue_created_datetimetz        chr
issue_updated_datetimetz        chr
issue_resolution_datetimetz     chr
issue_creator_id                chr
issue_creator_name              chr
issue_creator_timezone          chr
issue_assignee_id               chr
issue_assignee_name             chr
issue_assignee_timezone         chr
issue_reporter_id               chr
issue_reporter_name             chr
issue_reporter_timezone         chr
```

**Critical**: `issue_status` is the JIRA `status.statusCategory.name`,
not `status.name`. Apache projects with raw status values like
"Open" / "Resolved" / "Closed" map to "To Do" / "Done" / "Done"
respectively. The right filter for "closed/resolved" semantics is
`issue_status == "Done"`. See `known_bugs.md` for the kaiaulu
inconsistency this creates.

### parsed$comments columns

```
issue_key                       chr     join key to issues
comment_id                      chr
comment_created_datetimetz      chr
comment_updated_datetimetz      chr
comment_author_id               chr
comment_author_name             chr
comment_author_timezone         chr
comment_author_update_id        chr
comment_author_update_name      chr
comment_author_update_timezone  chr
comment_body                    chr
```

## parse_dv8_architectural_flaws() — R/dv8.R:577

Returns a `data.table`:

```
file_path                  chr   SINGULAR; differs from gitlog's file_pathname!
architecture_issue_type    chr   "anti-pattern name"
architecture_issue_id      chr   per-flaw id
```

**No `severity` column.** Each row is one (file, flaw_type, flaw_id)
participation. A file in N flaws appears N times. To count debt
weight, use `nrow(flaws)`, `uniqueN(flaws$architecture_issue_id)`,
or `uniqueN(flaws$file_path)` depending on semantics.

**Schema mismatch with gitlog**: dv8 uses `file_path`, gitlog uses
`file_pathname`. For any join, do:
```r
setnames(flaws, "file_path", "file_pathname")
```
or rename gitlog's column. Don't assume the natural join works.

## parse_dependencies() — R/src.R:184

Returns a **LIST**:

```r
deps <- parse_dependencies(depends_jar_path, git_repo_path, language)
deps$nodes      # data.table with column: filepath  (singular)
deps$edgelist   # data.table with src_filepath, dest_filepath,
                # plus typed-dependency count columns (Call, Use,
                # Import, ...) varying by language
```

## parse_java_code_refactoring_json() — R/src.R:261

Returns a **nested list** from `jsonlite::parse_json()` with no
flattening. NOT a data.table. Caller must flatten to a tabular form
before use. RefactoringMiner JSON structure:
```
$commits[[i]]$sha1
$commits[[i]]$refactorings[[j]]$type
$commits[[i]]$refactorings[[j]]$description
$commits[[i]]$refactorings[[j]]$leftSideLocations
$commits[[i]]$refactorings[[j]]$rightSideLocations
```

## identity_match() — R/identity.R:148

Operates on a LIST of project_log data.tables (e.g. gitlog + mbox).
Adds two columns to each table:

```
identity_id    int    canonical developer id across all log sources
raw_name       chr    the original name used in that source
```

Signature:
```r
project_log <- list(git_log = project_git, mail_log = project_mbox)
name_column <- c("author_name_email", "reply_from")  # one per table
project_log <- identity_match(project_log, name_column,
                              assign_identity_function = assign_exact_identity,
                              use_name_only = FALSE)
# now: project_log$git_log$identity_id and project_log$mail_log$identity_id
# refer to the same person across sources
```

For GitHub, identity_match requires an extra alias source (the GitHub
user -> email mapping is not in the standard extract). See Carlos's
sanity check #2.

## smell_radio_silence() — R/smells.R:207

Inputs:
- `mail.graph`: `list(nodes, edgelist)`, dev-dev reply network
- `clusters`: `list(assignment, info)` from community detection

Returns: vector of unique developer names (the "brokers").

Algorithm: for each cluster, collect outgoing edges by destination
cluster; if exactly one edge connects this cluster to a given
destination cluster, the source dev on that edge is a broker. Also:
any size-1 cluster's lone dev is automatically a broker.

See `smells/radio_silence.py` for a working Python port.

## metric_file_bug_frequency() — R/metric.R:16

Uses an `issue_status` filter that is **inconsistent** with what
`parse_jira()` produces. See `known_bugs.md`.
