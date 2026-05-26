# Kaiaulu PR handoff

Branch `myths-lifts` staged at `/tmp/kaiaulu-pr` against `sailuh/kaiaulu`
master. 16 new files, 2570 insertions, no edits to existing kaiaulu code.

## What's in the PR

```
R/myths_late_hire.R       95 lines   detect_late_hires, compute_velocity_changes
R/myths_szz.R            230 lines   SZZ-pair, injection/leak, DORA, per-phase, file freq
R/myths_workforce.R      109 lines   Sterman cohort + transition rates
R/myths_refactor.R       302 lines   refactor pay/born rate + release snapshots + archpat
R/myths_mailing.R        150 lines   mbox parse + reply edges + radio silence

vignettes/brooks_late_hire_velocity.Rmd          F3 lift
vignettes/brooksq_szz_injection_leak.Rmd         F1 + F4 lift
vignettes/debt_refactor_pay_rate.Rmd             F2 lift
vignettes/archpat_gof_pattern_partition.Rmd      Pattern density
vignettes/dora_szz_metrics.Rmd                   DORA-4
vignettes/rework_szz_cycle.Rmd                   Rework cycle
vignettes/defmap_active_latent.Rmd               Active/Latent/Fixed
vignettes/bugs_gokumoto_growth.Rmd               Goel-Okumoto
vignettes/learn_workforce_cohorts.Rmd            Sterman learning
vignettes/congruence_radio_silence.Rmd           Broker loss

conf/airflow.yml          New project (kaiaulu's conf/ already has the
                          other 7 family members)
```

## Tim's commands to ship this PR

```bash
# 1. Fork sailuh/kaiaulu on github.com (web UI, one click).
#    Resulting fork URL: https://github.com/timm/kaiaulu

# 2. Add Tim's fork as a remote on the local staging clone.
cd /tmp/kaiaulu-pr
git remote add timm https://github.com/timm/kaiaulu.git
git push timm myths-lifts

# 3. Open the PR via the GitHub web UI:
#    https://github.com/sailuh/kaiaulu/compare/master...timm:kaiaulu:myths-lifts
#    Title:  Add 10 system-dynamics-lift vignettes + 5 R/ helper modules
#    Body:   paste the commit body from `git log -1 --format=%B` here
```

## Knit + zip step (HTML deliverable for Carlos + Rick)

The PR is .R/.Rmd/.yml only. Carlos asked for a separate zip of knitted
HTML notebooks. To produce it:

```bash
# 1. Install kaiaulu locally with this branch's changes.
cd /tmp/kaiaulu-pr
R -e 'devtools::install(".", build_vignettes = FALSE)'

# 2. Knit each vignette. Each uses head() for table inspection so HTML
#    sizes stay reasonable (existing knitted brooks/archpat/bugs/learn/
#    congruence are ~640 KB each).
mkdir -p ~/myths-knit-out
for f in vignettes/*.Rmd; do
  R -e "rmarkdown::render('$f', output_dir = '~/myths-knit-out')"
done

# 3. Zip and ship.
cd ~ && zip -r myths-lifts-knit.zip myths-knit-out
# Attach myths-lifts-knit.zip to email to Carlos + Rick, or upload to
# Drive. Do NOT commit it to the PR.
```

## What Tim still has to do manually (the "could not be filled" list)

Per Carlos's instruction: any config parameter the vignette needs but
the kaiaulu conf/ does not provide, document at the top of the Rmd
around the `parse_config` chunk. Current gaps in the airflow vignette:

- `issue_tracker.jira.*`: airflow's JIRA was archived after 2021;
  vignette currently runs against the GitHub project only. To
  reproduce pre-2021 analysis, uncomment the jira block in
  `conf/airflow.yml` and supply local JIRA dumps under
  `../../rawdata/airflow/jira/`.

- The PyDriller B-SZZ pass is external to kaiaulu. Vignettes that
  depend on it (brooksq, defmap, rework, dora, bugs) document the
  expected input CSV schema near their first `parse_szz_bugfixes()`
  call.

## What's not in the PR (intentional)

- `NEWS.md` bump: Carlos said only `.R`, `.Rmd`, `.yml`. Roll into the
  next kaiaulu release on the maintainer side.
- `NAMESPACE` + `man/*.Rd`: regenerate locally on the kaiaulu side via
  `roxygen2::roxygenise()`. All new functions carry roxygen blocks.
- Existing `conf/<project>.yml` files: kaiaulu master already has 7 of
  our 8 family projects. Their existing conf is correct; ours had
  Tim-machine absolute paths and would have clashed.

## Where each Rmd plugs into the MYTHS framework

- `models/sd.py:<name>()` in icse27theories defines the SD model.
- `vignettes/<name>_*.Rmd` lifts a scalar from real OSS data.
- The scalar feeds back into the SD verdict pipeline via
  `scripts/calibrate.py` (icse27theories).

Reverse map:

| MYTHS finding | kaiaulu vignette                              |
|---------------|-----------------------------------------------|
| F1 leak_rate  | brooksq_szz_injection_leak.Rmd                |
| F2 pay_rate   | debt_refactor_pay_rate.Rmd                    |
| F3 brooks 11x | brooks_late_hire_velocity.Rmd                 |
| F4 split      | brooksq_szz_injection_leak.Rmd (F4 sub-finding) |
| F0 boundary   | implied by all lifts that breach sd.py bounds |
