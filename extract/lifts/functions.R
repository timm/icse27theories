# functions.R
#
# Companion library for the lift_*.Rmd notebooks. Written in
# kaiaulu's library style: snake_case verb_noun, data.table-first,
# roxygen comments on every exported helper.
#
# These functions are CANDIDATES for upstream contribution into
# kaiaulu's R/ directory. Each is self-contained.

require(data.table)
require(stringi)
require(magrittr)

# ---- Brooks model helpers ------------------------------------------------

#' Detect Late-Hire Events from Git Log
#'
#' A late hire is a developer whose first commit is at least
#' \code{min_project_age_days} after the project's first commit.
#' Returns a data.table with one row per late hire.
#'
#' @param project_git A gitlog data.table (output of parse_gitlog +
#'   optional identity_match). Must contain identity_id (preferred)
#'   or author_name_email and author_datetimetz columns.
#' @param min_project_age_days Numeric. Minimum days after project
#'   start for a hire to count as "late." Default 365.
#' @return data.table with columns: identity_id (or
#'   author_name_email), first_commit_at, days_after_project_start.
#' @export
detect_late_hires <- function(project_git, min_project_age_days = 365) {
  id_col <- if ("identity_id" %in% names(project_git)) "identity_id"
            else "author_name_email"

  first_commits <- project_git[, .(
    first_commit_at = min(author_datetimetz)
  ), by = id_col]

  project_start <- min(project_git$author_datetimetz)
  first_commits[, days_after_project_start :=
    as.numeric(difftime(first_commit_at, project_start, units = "days"))]

  first_commits[days_after_project_start >= min_project_age_days]
}

#' Compute Veteran Velocity Before and After Each Late-Hire Event
#'
#' For each late hire, compute the commit rate of veterans (devs who
#' joined before the hire) in the windows before and after. Returns
#' one row per late hire.
#'
#' @param project_git A gitlog data.table.
#' @param late_hires Output of \code{detect_late_hires()}.
#' @param window_days Numeric. Size of the pre/post window in days.
#' @return data.table with columns: identity_id (or
#'   author_name_email), pre_velocity, post_velocity, brooks_tax.
#' @export
compute_velocity_changes <- function(project_git, late_hires,
                                     window_days = 90) {
  id_col <- if ("identity_id" %in% names(project_git)) "identity_id"
            else "author_name_email"

  results <- lapply(seq_len(nrow(late_hires)), function(i) {
    hire_id   <- late_hires[i, get(id_col)]
    hire_at   <- late_hires[i, first_commit_at]
    win_start <- hire_at - as.difftime(window_days, units = "days")
    win_end   <- hire_at + as.difftime(window_days, units = "days")

    # Veterans = devs who joined strictly before hire_at
    veterans <- project_git[author_datetimetz < hire_at,
                            unique(get(id_col))]

    pre_commits <- project_git[
      get(id_col) %in% veterans &
      author_datetimetz >= win_start &
      author_datetimetz <  hire_at,
      uniqueN(commit_hash)
    ]
    post_commits <- project_git[
      get(id_col) %in% veterans &
      author_datetimetz >  hire_at &
      author_datetimetz <= win_end,
      uniqueN(commit_hash)
    ]

    data.table(
      id            = hire_id,
      hire_at       = hire_at,
      pre_velocity  = pre_commits  / window_days,
      post_velocity = post_commits / window_days
    )
  })
  rbindlist(results)
}

# ---- Brooksq model helpers (SZZ-driven) ----------------------------------

#' Parse PyDriller B-SZZ Output
#'
#' Reads a CSV produced by an external PyDriller SZZ pass and returns
#' a data.table joinable to a gitlog on commit_hash. Each row is one
#' (fixing_commit -> introducing_commit, file) triple.
#'
#' @param szz_csv_path Path to the SZZ CSV. Expected columns:
#'   fixing_commit_hash, introducing_commit_hash, file_path, jira_keys,
#'   fixing_date, introducing_date.
#' @return data.table with the same columns, dates parsed to POSIXct.
#' @export
parse_szz_bugfixes <- function(szz_csv_path) {
  dt <- data.table::fread(szz_csv_path)
  dt[, fixing_date       := as.POSIXct(fixing_date,       tz = "UTC")]
  dt[, introducing_date  := as.POSIXct(introducing_date,  tz = "UTC")]
  dt
}

#' Count Bug Introductions per Late-Hire Window
#'
#' For each late-hire event, counts bug-introducing commits in the
#' pre-window and post-window. Uses the SZZ pairs table: a commit is
#' "bug-introducing" if it appears as introducing_commit_hash for any
#' downstream fix. Returns one row per late hire.
#'
#' @param szz Output of \code{parse_szz_bugfixes()}.
#' @param late_hires Output of \code{detect_late_hires()}.
#' @param window_days Numeric. Pre/post window size in days.
#' @return data.table with: id, hire_at, pre_intros, post_intros,
#'   inj_rate_pre, inj_rate_post.
#' @export
compute_injection_changes <- function(szz, late_hires,
                                      window_days = 90) {
  id_col <- if ("identity_id" %in% names(late_hires)) "identity_id"
            else "author_name_email"
  intros <- unique(szz[, .(introducing_commit_hash, introducing_date)])
  results <- lapply(seq_len(nrow(late_hires)), function(i) {
    hire_at   <- late_hires[i, first_commit_at]
    win_start <- hire_at - as.difftime(window_days, units = "days")
    win_end   <- hire_at + as.difftime(window_days, units = "days")
    pre_n  <- intros[introducing_date >= win_start &
                     introducing_date <  hire_at, .N]
    post_n <- intros[introducing_date >  hire_at &
                     introducing_date <= win_end, .N]
    data.table(
      id            = late_hires[i, get(id_col)],
      hire_at       = hire_at,
      pre_intros    = pre_n,
      post_intros   = post_n,
      inj_rate_pre  = pre_n  / window_days,
      inj_rate_post = post_n / window_days
    )
  })
  rbindlist(results)
}

#' Estimate Leak Rate from SZZ Pairs
#'
#' Leak rate = fraction of introductions that are still un-fixed
#' beyond a given latency threshold. Higher = more bugs leak past the
#' immediate review window into the field.
#'
#' @param szz Output of \code{parse_szz_bugfixes()}.
#' @param latency_days Numeric. Bugs taking longer than this to fix
#'   count as "leaked." Default 30.
#' @return Numeric in [0,1].
#' @export
estimate_leak_rate <- function(szz, latency_days = 30) {
  latencies <- as.numeric(difftime(szz$fixing_date,
                                   szz$introducing_date,
                                   units = "days"))
  latencies <- latencies[is.finite(latencies) & latencies >= 0]
  if (length(latencies) == 0) return(NA_real_)
  mean(latencies > latency_days)
}

# ---- Congruence model helpers (radio-silence smell) ----------------------

#' Parse All Mbox Files in a Directory via kaiaulu::parse_mbox
#'
#' Wraps Perceval-via-kaiaulu over every \code{*.mbox} file in
#' \code{mbox_dir}. Returns a single data.table with the union of
#' message records.
#'
#' @param perceval_path Path to perceval executable.
#' @param mbox_dir Directory containing one or more .mbox files.
#' @return data.table with kaiaulu's parse_mbox columns
#'   (message_id, reply_to, sender, ...).
#' @export
parse_mbox_dir <- function(perceval_path, mbox_dir) {
  files <- list.files(mbox_dir, pattern = "\\.mbox$",
                      full.names = TRUE)
  if (length(files) == 0) {
    stop("no .mbox files in ", mbox_dir)
  }
  rbindlist(lapply(files, function(f) {
    tryCatch(parse_mbox(perceval_path, f),
             error = function(e) {
               warning(sprintf("parse_mbox failed on %s: %s",
                               basename(f), conditionMessage(e)))
               NULL
             })
  }), fill = TRUE)
}

#' Build Reply Edge List from Mbox Messages
#'
#' Resolves each (child, parent_message_id) reply link to a (child,
#' parent_identity) edge by looking up the parent message's sender.
#'
#' kaiaulu::parse_mbox returns columns:
#'   reply_id, in_reply_to_id, reply_from, ...
#' After identity_match on \code{reply_from}, each row gets
#' identity_id. We pivot on (reply_id → identity_id) to build edges.
#'
#' @param msgs data.table with cols reply_id, in_reply_to_id,
#'   identity_id (post-identity_match).
#' @return data.table with cols src_id, dst_id, weight.
#' @export
build_reply_edges <- function(msgs) {
  mid_to_id <- setNames(msgs$identity_id, msgs$reply_id)
  replies <- msgs[!is.na(in_reply_to_id) & in_reply_to_id != "",
                  .(child_id = identity_id, parent_mid = in_reply_to_id)]
  replies[, parent_id := mid_to_id[parent_mid]]
  replies <- replies[!is.na(parent_id) & parent_id != child_id]
  replies[, `:=`(
    src_id = pmin(child_id, parent_id),
    dst_id = pmax(child_id, parent_id)
  )]
  replies[, .(weight = .N), by = .(src_id, dst_id)]
}

#' Detect Radio-Silence Brokers
#'
#' Ports kaiaulu R/smells.R:207. A broker bridges otherwise-
#' disconnected community pairs: in any cluster, if a vertex is the
#' SOLE outgoing edge to some other cluster, it is a "radio silence"
#' broker — its absence severs the inter-cluster channel.
#'
#' Implementation: build a Louvain partition of the largest connected
#' component, then for each (cluster, vert) compute the count of
#' edges to each external cluster; flag vert as broker if any
#' external-cluster edge count == 1.
#'
#' @param edges data.table of (src_id, dst_id, weight) on identity_ids.
#' @return list with: graph, partition (named vec id→cluster),
#'   brokers (unique ids), incidents (data.table of one row per
#'   (cluster, dev, sole-cluster-bridged-to) tuple), cluster_sizes.
#' @export
detect_radio_silence <- function(edges) {
  g <- igraph::graph_from_data_frame(
    d = edges[, .(src_id, dst_id, weight)],
    directed = FALSE)
  ccs <- igraph::components(g)
  main_ids <- which(ccs$membership == which.max(ccs$csize))
  g_main <- igraph::induced_subgraph(g, main_ids)
  louv <- igraph::cluster_louvain(g_main,
                                  weights = igraph::E(g_main)$weight)
  membership <- igraph::membership(louv)
  ids <- igraph::V(g_main)$name

  brokers   <- character(0)
  incidents <- data.table(dev = character(),
                          cluster = integer(),
                          bridge_to = integer())

  for (cid in unique(membership)) {
    devs <- ids[membership == cid]
    if (length(devs) == 1) {
      brokers <- c(brokers, devs)
      incidents <- rbind(incidents,
                         data.table(dev = devs, cluster = cid,
                                    bridge_to = NA_integer_))
      next
    }
    # outgoing edges per (vert, target-cluster)
    out_counts <- list()
    for (v in devs) {
      nbrs <- igraph::neighbors(g_main, v)
      nbr_ids <- ids[as.integer(nbrs)]
      nbr_cls <- membership[nbr_ids]
      ext <- nbr_cls[nbr_cls != cid]
      if (length(ext) == 0) next
      for (oc in unique(ext)) {
        key <- paste(oc, v, sep = "|")
        out_counts[[key]] <- (out_counts[[key]] %||% 0L) +
                             sum(ext == oc)
      }
    }
    # for each external cluster, find which devs have exactly 1 edge
    by_target <- split(names(out_counts), sapply(strsplit(names(out_counts), "\\|"), `[`, 1))
    for (target_str in names(by_target)) {
      total_links <- sum(unlist(out_counts[by_target[[target_str]]]))
      if (total_links == 1) {
        key <- by_target[[target_str]][1]
        v <- strsplit(key, "\\|")[[1]][2]
        brokers <- c(brokers, v)
        incidents <- rbind(incidents,
                           data.table(dev = v, cluster = cid,
                                      bridge_to = as.integer(target_str)))
      }
    }
  }
  list(
    graph         = g_main,
    partition     = membership,
    brokers       = unique(brokers),
    incidents     = incidents,
    cluster_sizes = sort(as.integer(table(membership)), decreasing = TRUE)
  )
}

# ---- Learn model helpers -------------------------------------------------

#' Compute Workforce Cohort Distribution
#'
#' For each developer, compute tenure (last_commit - first_commit) and
#' assign to Jr / Tr / Sr buckets.
#'
#' @param project_git A gitlog data.table with identity_id.
#' @param jr_max_days Tenure < this = Jr. Default 365.
#' @param sr_min_days Tenure >= this = Sr. Default 1095 (3 years).
#' @return data.table with identity_id, tenure_days, cohort.
#' @export
compute_cohorts <- function(project_git, jr_max_days = 365,
                            sr_min_days = 1095) {
  per_dev <- project_git[, .(
    first_commit = min(author_datetimetz),
    last_commit  = max(author_datetimetz),
    n_commits    = uniqueN(commit_hash)
  ), by = identity_id]
  per_dev[, tenure_days := as.numeric(difftime(last_commit, first_commit,
                                               units = "days"))]
  per_dev[, cohort := fcase(
    tenure_days <  jr_max_days,  "Jr",
    tenure_days >= sr_min_days,  "Sr",
    default                   = "Tr"
  )]
  per_dev
}

#' Estimate Transition Rates from Cohort Trajectories
#'
#' Buckets the project history into time slices and counts devs who
#' moved Jr→Tr (train) and Tr→Sr (promote) between slices. Rates =
#' transitions / starting-bucket-size, normalised to per-year.
#'
#' Slice size defaults to 90 days (not 365) to avoid the artifact where
#' jr_max_days=365 + slice=365 forces every surviving Jr to graduate,
#' saturating train_rate at 1.0.
#'
#' @param project_git A gitlog data.table with identity_id.
#' @param jr_max_days Tenure < this = Jr at slice midpoint.
#' @param sr_min_days Tenure >= this = Sr at slice midpoint.
#' @param slice_days Time-slice width. Default 90.
#' @return list with train_rate, promote_rate (medians over slices,
#'   annualised by multiplying per-slice fractions by 365/slice_days).
#' @export
estimate_transition_rates <- function(project_git, jr_max_days = 365,
                                      sr_min_days = 1095,
                                      slice_days = 90) {
  start <- min(project_git$author_datetimetz)
  end   <- max(project_git$author_datetimetz)
  step  <- as.difftime(slice_days, units = "days")
  cuts  <- seq(start, end, by = step)
  if (length(cuts) < 2) return(list(train_rate = NA_real_,
                                    promote_rate = NA_real_))

  # First-commit-date per dev (anchor for tenure)
  per_dev <- project_git[, .(first_commit = min(author_datetimetz)),
                          by = identity_id]

  cohorts_at <- function(when) {
    active <- per_dev[first_commit <= when]
    active[, td := as.numeric(difftime(when, first_commit, units = "days"))]
    active[, cohort := fcase(
      td <  jr_max_days, "Jr",
      td >= sr_min_days, "Sr",
      default          = "Tr"
    )]
    active[, .(identity_id, cohort)]
  }

  train_n   <- promote_n   <- integer(0)
  jr_at_t   <- tr_at_t     <- integer(0)
  for (i in seq_len(length(cuts) - 1)) {
    c0 <- cohorts_at(cuts[i])
    c1 <- cohorts_at(cuts[i + 1])
    m  <- merge(c0, c1, by = "identity_id",
                suffixes = c("_0", "_1"))
    jr_at_t   <- c(jr_at_t,   sum(m$cohort_0 == "Jr"))
    tr_at_t   <- c(tr_at_t,   sum(m$cohort_0 == "Tr"))
    train_n   <- c(train_n,   sum(m$cohort_0 == "Jr" & m$cohort_1 == "Tr"))
    promote_n <- c(promote_n, sum(m$cohort_0 == "Tr" & m$cohort_1 == "Sr"))
  }

  annualise <- 365 / slice_days
  list(
    train_rate   = annualise * median(train_n   / pmax(jr_at_t, 1),
                                      na.rm = TRUE),
    promote_rate = annualise * median(promote_n / pmax(tr_at_t, 1),
                                      na.rm = TRUE),
    n_slices     = length(cuts) - 1,
    slice_days   = slice_days
  )
}

# ---- Rework model helpers ------------------------------------------------

#' Compute Failure Rate per Rolling Window
#'
#' Calibrates the rework model's \code{failrate} parameter as the
#' fraction of commits in each window that introduce a bug (per SZZ).
#'
#' @param szz Output of \code{parse_szz_bugfixes()}.
#' @param project_git A gitlog data.table.
#' @param window_days Numeric. Window size in days.
#' @return data.table with window_start, n_commits, n_intro_commits, failrate.
#' @export
compute_failrate_per_window <- function(szz, project_git, window_days = 90) {
  commits <- unique(project_git[, .(commit_hash, author_datetimetz)])
  intro_hashes <- unique(szz$introducing_commit_hash)
  commits[, has_intro := commit_hash %in% intro_hashes]
  commits <- commits[order(author_datetimetz)]

  start <- min(commits$author_datetimetz)
  end   <- max(commits$author_datetimetz)
  step  <- as.difftime(window_days, units = "days")
  windows <- seq(start, end, by = step)
  out <- lapply(windows, function(ws) {
    we <- ws + step
    chunk <- commits[author_datetimetz >= ws & author_datetimetz < we]
    if (nrow(chunk) == 0) return(NULL)
    data.table(
      window_start    = ws,
      n_commits       = nrow(chunk),
      n_intro_commits = sum(chunk$has_intro),
      failrate        = sum(chunk$has_intro) / nrow(chunk)
    )
  })
  rbindlist(out[!sapply(out, is.null)])
}

# ---- Defmap model helpers ------------------------------------------------

#' Compute Per-Release-Phase Defect Flow
#'
#' For each release-tag phase, count:
#' - injected: bug-introducing commits whose date falls in this phase
#' - caught:   bug-fixing commits in same phase as their introducer
#' - leaked:   introducers in this phase whose fix is in a later phase
#'             or absent
#'
#' \code{tst_proxy} = caught / max(injected, 1) — calibrates the defmap
#' model's \code{tst} testing-intensity parameter.
#'
#' @param szz Output of \code{parse_szz_bugfixes()}.
#' @param project_git A gitlog data.table.
#' @param tag_dates data.table with columns: tag, date (POSIXct).
#' @return data.table per phase with injected, caught, leaked, tst_proxy.
#' @export
compute_per_phase_defects <- function(szz, project_git, tag_dates) {
  tag_dates <- tag_dates[order(date)]
  phase_for <- function(ts) {
    idx <- findInterval(ts, tag_dates$date)
    idx[idx == 0] <- 1L
    tag_dates$tag[idx]
  }
  szz[, phase_intro := phase_for(introducing_date)]
  szz[, phase_fix   := phase_for(fixing_date)]

  intro_per_phase <- unique(szz[, .(introducing_commit_hash, phase_intro,
                                    phase_fix)])
  out <- intro_per_phase[, .(
    injected = .N,
    caught   = sum(phase_intro == phase_fix, na.rm = TRUE),
    leaked   = sum(phase_intro != phase_fix, na.rm = TRUE)
  ), by = phase_intro]
  setnames(out, "phase_intro", "phase")
  out[, tst_proxy := caught / pmax(injected, 1)]
  out
}

# ---- Dora model helpers --------------------------------------------------

#' Compute DORA-style Metrics from Tags + SZZ
#'
#' batch_size  : mean commits between consecutive tags
#' cfr         : (bug-fix commits) / (total commits) over the full history
#' arrival_rate: commits per day (mean)
#' rec_rate    : 1 / median(fix_date - intro_date) in days
#'
#' @param szz Output of \code{parse_szz_bugfixes()}.
#' @param project_git A gitlog data.table.
#' @param tag_dates data.table with columns: tag, date (POSIXct).
#' @return list with named numeric values.
#' @export
compute_dora_metrics <- function(szz, project_git, tag_dates) {
  commits <- unique(project_git[, .(commit_hash, author_datetimetz)])
  setorder(commits, author_datetimetz)
  total_commits <- nrow(commits)
  span_days <- as.numeric(difftime(max(commits$author_datetimetz),
                                   min(commits$author_datetimetz),
                                   units = "days"))

  arrival_rate <- total_commits / max(span_days, 1)

  # batch_size = total commits / (tags - 1)
  n_tags <- nrow(tag_dates)
  batch_size <- if (n_tags >= 2) total_commits / (n_tags - 1) else NA_real_

  n_fixes <- uniqueN(szz$fixing_commit_hash)
  cfr <- n_fixes / total_commits

  latencies <- as.numeric(difftime(szz$fixing_date, szz$introducing_date,
                                   units = "days"))
  latencies <- latencies[is.finite(latencies) & latencies >= 0]
  median_mttr <- if (length(latencies)) median(latencies) else NA_real_
  rec_rate <- if (is.finite(median_mttr) && median_mttr > 0) 1 / median_mttr
              else NA_real_

  list(
    batch_size   = batch_size,
    cfr          = cfr,
    arrival_rate = arrival_rate,
    rec_rate     = rec_rate,
    n_tags       = n_tags,
    span_days    = span_days
  )
}

#' Build a Tag-Date Table for a Git Repo
#'
#' Wraps git system calls to enumerate tags in v:refname order and
#' fetch each tag's commit date.
#'
#' @param git_repo_path Path to .git or worktree.
#' @return data.table with tag, date (POSIXct).
#' @export
get_tag_dates <- function(git_repo_path) {
  repo <- gsub("/\\.git/?$", "", git_repo_path)
  tags <- system2("git", c("-C", repo, "tag", "--sort=v:refname"),
                  stdout = TRUE)
  if (length(tags) == 0) return(data.table(tag = character(),
                                           date = as.POSIXct(character())))
  unix_ts <- vapply(tags, function(tg) {
    out <- system2("git",
                   c("-C", repo, "log", "-1", "--format=%ct", tg),
                   stdout = TRUE)
    if (length(out) == 0) NA_character_ else out[1]
  }, character(1))
  data.table(tag  = tags,
             date = as.POSIXct(as.numeric(unix_ts),
                               origin = "1970-01-01", tz = "UTC"))[
                                 order(date)]
}

# ---- Debt model helpers --------------------------------------------------

#' Compute Pay Rate from Refactoring Activity
#'
#' Pay rate = fraction of commits in each rolling window that contain
#' at least one RefactoringMiner-detected refactoring. Calibrates the
#' \code{pay_rate} parameter of the debt SD model.
#'
#' @param project_git A gitlog data.table.
#' @param refactorings Output of \code{flatten_refactoring_json()}.
#' @param window_days Numeric. Rolling window size in days. Default 90.
#' @return data.table with: window_start, window_end, n_commits,
#'   n_refactor_commits, pay_rate.
#' @export
compute_pay_rate <- function(project_git, refactorings,
                             window_days = 90) {
  commits <- unique(project_git[, .(commit_hash, author_datetimetz)])
  refactor_hashes <- unique(refactorings$commit_hash)
  commits[, has_refactor := commit_hash %in% refactor_hashes]
  commits <- commits[order(author_datetimetz)]

  start <- min(commits$author_datetimetz)
  end   <- max(commits$author_datetimetz)
  step  <- as.difftime(window_days, units = "days")

  windows <- seq(start, end, by = step)
  out <- lapply(windows, function(ws) {
    we <- ws + step
    chunk <- commits[author_datetimetz >= ws & author_datetimetz < we]
    if (nrow(chunk) == 0) return(NULL)
    data.table(
      window_start       = ws,
      window_end         = we,
      n_commits          = nrow(chunk),
      n_refactor_commits = sum(chunk$has_refactor),
      pay_rate           = sum(chunk$has_refactor) / nrow(chunk)
    )
  })
  rbindlist(out[!sapply(out, is.null)])
}

#' Crude Born-Rate Proxy from Gitlog Churn
#'
#' Approximates the debt model's \code{born_rate} as the share of
#' commits in each window that touch many files (a proxy for "ship
#' fast → introduce debt"). Threshold defaults to 5 files.
#'
#' @param project_git A gitlog data.table.
#' @param window_days Numeric. Window size in days.
#' @param big_commit_files Numeric. Min files for "big commit." Default 5.
#' @return data.table with: window_start, n_commits, n_big_commits,
#'   born_rate.
#' @export
compute_born_rate_proxy <- function(project_git, window_days = 90,
                                    big_commit_files = 5) {
  cs <- project_git[, .(
    files_touched = uniqueN(file_pathname),
    when          = min(author_datetimetz)
  ), by = commit_hash]
  cs[, big := files_touched >= big_commit_files]

  start <- min(cs$when); end <- max(cs$when)
  step  <- as.difftime(window_days, units = "days")
  windows <- seq(start, end, by = step)
  out <- lapply(windows, function(ws) {
    we <- ws + step
    chunk <- cs[when >= ws & when < we]
    if (nrow(chunk) == 0) return(NULL)
    data.table(
      window_start  = ws,
      n_commits     = nrow(chunk),
      n_big_commits = sum(chunk$big),
      born_rate     = sum(chunk$big) / nrow(chunk)
    )
  })
  rbindlist(out[!sapply(out, is.null)])
}

# ---- Archpat model helpers -----------------------------------------------

#' Get Release Tags from a Git Repository
#'
#' Wraps system call to \code{git tag}. Returns tags in lexicographic
#' order (which usually approximates release order for SemVer projects).
#'
#' @param git_repo_path Path to the .git directory or working tree.
#' @return Character vector of tag names.
#' @export
get_release_tags <- function(git_repo_path) {
  repo <- gsub("/\\.git/?$", "", git_repo_path)
  out  <- system2("git",
                  args = c("-C", repo, "tag", "--sort=v:refname"),
                  stdout = TRUE)
  out
}

#' Check Out a Git Snapshot to a Temporary Directory
#'
#' Creates a worktree at the given tag/commit. Returns the worktree
#' path. Caller is responsible for cleanup via
#' \code{system2("git", c("-C", repo, "worktree", "remove", path))}.
#'
#' @param git_repo_path Path to the .git directory or working tree.
#' @param ref Tag name, branch name, or commit hash.
#' @return Character path to the snapshot directory.
#' @export
checkout_snapshot <- function(git_repo_path, ref) {
  repo <- gsub("/\\.git/?$", "", git_repo_path)
  snap <- tempfile(pattern = paste0("snap_", gsub("/", "_", ref), "_"))
  system2("git",
          args = c("-C", repo, "worktree", "add", "--detach", snap, ref),
          stdout = FALSE, stderr = FALSE)
  snap
}

#' Run RefactoringMiner on a Git Repository
#'
#' System call to the RefactoringMiner CLI. Returns the path to the
#' resulting JSON file. The JSON is the standard RefactoringMiner
#' \code{-all} output (every refactoring across the project history).
#'
#' @param refminer_jar Path to RefactoringMiner-*.jar.
#' @param git_repo_path Path to the .git directory or working tree.
#' @param out_path Optional output file path. Default: tempfile.
#' @return Character path to the resulting JSON file.
#' @export
run_refactoring_miner <- function(refminer_jar, git_repo_path,
                                  out_path = NULL) {
  repo <- gsub("/\\.git/?$", "", git_repo_path)
  if (is.null(out_path)) {
    out_path <- tempfile(fileext = ".json")
  }
  system2("java",
          args = c("-jar", refminer_jar,
                   "-a", repo,        # -a = all commits
                   "-json", out_path),
          stdout = FALSE, stderr = FALSE)
  out_path
}

#' Flatten RefactoringMiner JSON to a data.table
#'
#' kaiaulu's parse_java_code_refactoring_json returns a nested list.
#' This helper flattens to one row per refactoring event.
#'
#' @param refminer_json_path Path to a RefactoringMiner JSON output
#'   file (from \code{run_refactoring_miner}).
#' @return data.table with: commit_hash, refactoring_type,
#'   refactoring_description, left_locations, right_locations.
#' @export
flatten_refactoring_json <- function(refminer_json_path) {
  raw <- jsonlite::fromJSON(refminer_json_path, simplifyVector = FALSE)
  rows <- lapply(raw$commits, function(c) {
    if (length(c$refactorings) == 0) return(NULL)
    rbindlist(lapply(c$refactorings, function(r) {
      data.table(
        commit_hash             = c$sha1,
        refactoring_type        = r$type,
        refactoring_description = r$description %||% NA_character_,
        left_locations  = paste(sapply(r$leftSideLocations,  `[[`,
                                       "filePath"), collapse = ";"),
        right_locations = paste(sapply(r$rightSideLocations, `[[`,
                                       "filePath"), collapse = ";")
      )
    }))
  })
  rbindlist(rows[!sapply(rows, is.null)])
}

#' Compute Per-File Bug Frequency
#'
#' Joins gitlog (with commit_message_id) to JIRA bugs and counts
#' bug-touching commits per file.
#'
#' @param project_git A gitlog data.table that has been processed
#'   through parse_commit_message_id.
#' @param jira_bugs A data.table of bug issues from
#'   parse_jira()$issues filtered to issue_type == "Bug".
#' @param issue_id_regex Used to extract the issue key from the
#'   commit_message_id column.
#' @return data.table with file_pathname, bug_count.
#' @export
compute_file_bug_frequency <- function(project_git, jira_bugs,
                                       issue_id_regex) {
  bug_keys <- jira_bugs$issue_key
  bug_commits <- project_git[commit_message_id %in% bug_keys]
  bug_commits[, .(bug_count = uniqueN(commit_hash)), by = file_pathname]
}

#' Compute Per-File Churn over a Recent Window
#'
#' @param project_git A gitlog data.table.
#' @param window_days Numeric. Window size for "recent."
#' @return data.table with file_pathname, churn_score in [0,1].
#' @export
compute_file_churn <- function(project_git, window_days = 180) {
  cutoff <- max(project_git$author_datetimetz) -
           as.difftime(window_days, units = "days")
  recent <- project_git[author_datetimetz >= cutoff]
  recent_commits <- recent[, .(recent_n = uniqueN(commit_hash)),
                           by = file_pathname]
  total_commits  <- project_git[, .(total_n = uniqueN(commit_hash)),
                                by = file_pathname]
  m <- merge(recent_commits, total_commits, by = "file_pathname",
             all.y = TRUE)
  m[is.na(recent_n), recent_n := 0]
  m[, churn_score := recent_n / total_n]
  m[, .(file_pathname, churn_score)]
}

#' Assign Each File to a Stock (Patterned, Legacy, or Drift)
#'
#' Implements the archpat model's partition. A file is Patterned if
#' it participates in any GoF pattern instance; Legacy if it has
#' high accumulated bug count and is not Patterned; Drift if it has
#' recent high churn and is not Patterned or Legacy.
#'
#' @param patterned_files Character vector of file paths in GoF
#'   patterns.
#' @param file_bug_freq Output of compute_file_bug_frequency.
#' @param file_churn Output of compute_file_churn.
#' @param legacy_bug_threshold Numeric. Min bug count for Legacy.
#' @param drift_churn_threshold Numeric in [0,1]. Min churn for Drift.
#' @return data.table with file_pathname, stock in
#'   {"Patterned","Legacy","Drift","Other"}.
#' @export
assign_file_partition <- function(patterned_files,
                                  file_bug_freq,
                                  file_churn,
                                  legacy_bug_threshold  = 5,
                                  drift_churn_threshold = 0.7) {
  all_files <- union(file_bug_freq$file_pathname,
                     file_churn$file_pathname)
  out <- data.table(file_pathname = all_files)
  out <- merge(out, file_bug_freq, by = "file_pathname", all.x = TRUE)
  out <- merge(out, file_churn,    by = "file_pathname", all.x = TRUE)
  out[is.na(bug_count), bug_count := 0]
  out[is.na(churn_score), churn_score := 0]
  out[, stock := fcase(
    file_pathname %in% patterned_files,                       "Patterned",
    bug_count    >= legacy_bug_threshold,                     "Legacy",
    churn_score  >= drift_churn_threshold,                    "Drift",
    default = "Other"
  )]
  out
}

# ---- Stubs for remaining archpat lifts -----------------------------------
# These need implementations once we have pattern4 + RefactoringMiner
# actually running on Helix. Names are placeholders matching the model's
# init keys.

#' @export
compute_feature_velocity      <- function(project_git, jira_issues) NA_real_
#' @export
compute_migration_rate        <- function(gof_per_tag) NA_real_
#' @export
compute_smell_appearance_rate <- function(gof_per_tag) NA_real_
#' @export
compute_legacy_growth_rate    <- function(project_git, patterned_files) NA_real_
#' @export
compute_born_pat_rate         <- function(refactorings, gof_per_tag) NA_real_
#' @export
compute_born_leg_rate         <- function(project_git, patterned_files) NA_real_

# ---- Utility -------------------------------------------------------------

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

#' Merge Commit Dates Back into a Refactoring Table
#'
#' RefactoringMiner output has commit_hash but no date. Join from
#' gitlog to recover the commit_datetimetz.
#'
#' @export
merge_commit_dates <- function(refactorings, project_git) {
  hashes <- unique(project_git[, .(commit_hash, author_datetimetz)])
  m <- merge(refactorings, hashes, by = "commit_hash", all.x = TRUE)
  m$author_datetimetz
}
