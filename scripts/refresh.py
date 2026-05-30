#!/usr/bin/env python3
"""Refresh the site from artifacts dropped in data/dropzone/.

Usage:
  python3 scripts/refresh.py                # lift CSVs + raw data
  python3 scripts/refresh.py --lifts-only   # skip raw-data render path
  python3 scripts/refresh.py --dry-run      # show what would happen

Drop-zone contract documented in data/dropzone/README.md.

Pipeline:
  1. Move lift_<model>_<project>.csv files from dropzone → paper/outputs/
  2. Move <project>/ subdirs from dropzone → data/<project>/ (unless --lifts-only)
  3. (Skipped if --lifts-only) For each moved project subdir, knit any
     extract/lifts/*.Rmd notebooks against it. NOT IMPLEMENTED yet —
     requires Rscript + kaiaulu + perceval; calls into paper/Makefile
     `render` target with a warning if the toolchain is missing.
  4. melt_lifts.py → lifts.csv (only if any lift CSVs landed)
  5. boundary_check.py → boundary_check.csv
  6. calibrate.py → calibrated_verdicts.csv
  7. cross_project.py → cross_project.csv
  8. full_audit.py → full_audit.csv
  9. docs/scripts/gen_rich.py → 33 auto pages
  10. paper/scripts/audit_staleness.py + docs/scripts/check_pages.py
  11. Print before/after diff of full_audit.csv key columns + list
      of model pages whose scorecard rows changed.
"""
import argparse, csv, re, shutil, subprocess, sys
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[1]
DROPZONE = ROOT / "data" / "dropzone"
DATA     = ROOT / "data"
OUTPUTS  = ROOT / "paper" / "outputs"

LIFT_RE = re.compile(r"^lift_([a-z_]+)_([a-z0-9]+)\.csv$")

# Steps to run after artifacts land. Each is (label, command, cwd, needs_lifts).
# needs_lifts=True means skip the step when no source lift CSVs exist
# (melt_lifts would otherwise WIPE the frozen lifts.csv to 0 rows;
#  downstream steps then cascade-fail on empty input).
PIPELINE = [
    ("melt_lifts",      ["python3", "paper/scripts/melt_lifts.py"], ROOT, True),
    ("boundary_check",  ["python3", "boundary_check.py"],           ROOT / "paper", False),
    ("calibrate",       ["python3", "calibrate.py"],                ROOT / "paper", False),
    ("cross_project",   ["python3", "cross_project.py"],            ROOT / "paper", False),
    ("full_audit",      ["python3", "full_audit.py"],               ROOT / "paper", False),
    ("gen_rich",        ["python3", "docs/scripts/gen_rich.py"],    ROOT, False),
    ("audit_staleness", ["python3", "paper/scripts/audit_staleness.py"], ROOT, False),
    ("check_pages",     ["python3", "docs/scripts/check_pages.py"], ROOT, False),
]


def lift_source_csvs_exist():
    """Return True if any per-project lift_<m>_<p>.csv files are in OUTPUTS."""
    return any(p.name != "lifts.csv"
               and LIFT_RE.match(p.name)
               for p in OUTPUTS.glob("lift_*.csv"))


def snapshot_audit():
    """Capture per-model (cell, verdict, verdict_n) from full_audit.csv."""
    p = OUTPUTS / "full_audit.csv"
    if not p.exists():
        return {}
    return {r["model"]: (r["cell"], r["verdict"], r["verdict_n"], r["gap"])
            for r in csv.DictReader(p.open())}


def scan_dropzone():
    """Return (lift_csvs, project_subdirs) found under data/dropzone/."""
    lift_csvs = []
    project_dirs = []
    for entry in sorted(DROPZONE.iterdir()):
        if entry.name in ("README.md", ".DS_Store"):
            continue
        if entry.is_file() and entry.suffix == ".csv":
            if LIFT_RE.match(entry.name):
                lift_csvs.append(entry)
            else:
                print(f"  [skip] {entry.name} — doesn't match lift_<model>_<project>.csv")
        elif entry.is_dir():
            project_dirs.append(entry)
        else:
            print(f"  [skip] {entry.name} — not a CSV or subdir")
    return lift_csvs, project_dirs


def move_lift(p: Path, dry_run: bool):
    target = OUTPUTS / p.name
    print(f"  lift: {p.name} → paper/outputs/")
    if not dry_run:
        shutil.move(str(p), str(target))


def move_project(p: Path, dry_run: bool):
    target = DATA / p.name
    print(f"  raw:  data/dropzone/{p.name}/ → data/{p.name}/")
    if not dry_run:
        if target.exists():
            print(f"        WARNING: data/{p.name}/ already exists; merging not handled. Skipping.")
            return False
        shutil.move(str(p), str(target))
    return True


def run_step(label, cmd, cwd, dry_run: bool):
    print(f"\n→ {label}: {' '.join(cmd)} (cwd={cwd.relative_to(ROOT)})")
    if dry_run:
        return True
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()
    for line in tail[-3:]:
        print(f"  {line}")
    if r.returncode != 0:
        print(f"  FAIL ({label}) returncode={r.returncode}")
        return False
    return True


def diff_audit(before, after):
    changed = []
    for m, post in sorted(after.items()):
        pre = before.get(m)
        if pre is None:
            changed.append((m, "NEW", "—", str(post)))
            continue
        if pre != post:
            changed.append((m, "CHANGED", str(pre), str(post)))
    removed = [m for m in before if m not in after]
    return changed, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lifts-only", action="store_true",
                    help="skip raw-data render path; only ingest lift CSVs")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would happen but don't move or run anything")
    args = ap.parse_args()

    print("=" * 60)
    print("MYTHS refresh — drop-zone ingest")
    print("=" * 60)

    if not DROPZONE.exists():
        print(f"\nNo dropzone at {DROPZONE.relative_to(ROOT)} — nothing to do.")
        return 0

    lifts, projects = scan_dropzone()
    print(f"\nFound {len(lifts)} lift CSV(s) and {len(projects)} raw project subdir(s).")

    if not lifts and not projects:
        print("Drop-zone empty. Running pipeline anyway to re-validate.")

    # Snapshot audit before
    before = snapshot_audit()

    # 1+2. Move artifacts
    if lifts or projects:
        print("\nMoving artifacts:")
        for p in lifts:
            move_lift(p, args.dry_run)
        if not args.lifts_only:
            for p in projects:
                ok = move_project(p, args.dry_run)
                if ok:
                    print(f"        TODO: knit extract/lifts/*.Rmd against data/{p.name}/ "
                          f"(R toolchain — not yet wired; run `make render` manually for now).")
        elif projects:
            print(f"\n  --lifts-only: leaving {len(projects)} project subdir(s) untouched.")

    # 4-10. Pipeline
    have_sources = lift_source_csvs_exist()
    if not have_sources:
        print("\nNote: no per-project lift_<m>_<p>.csv files on disk. "
              "Skipping melt_lifts to preserve frozen paper/outputs/lifts.csv.")
    for label, cmd, cwd, needs_lifts in PIPELINE:
        if needs_lifts and not have_sources:
            print(f"\n→ {label}: SKIPPED (no source lift CSVs to melt)")
            continue
        if not run_step(label, cmd, cwd, args.dry_run):
            print(f"\nPipeline FAILED at step `{label}`. Stop.")
            return 1

    if args.dry_run:
        print("\n[dry-run complete]")
        return 0

    # 11. Diff
    after = snapshot_audit()
    changed, removed = diff_audit(before, after)
    print("\n" + "=" * 60)
    print("Audit diff")
    print("=" * 60)
    if not changed and not removed:
        print("No (cell, verdict, verdict_n, gap) changes across models.")
    else:
        for m, kind, pre, post in changed:
            print(f"  {kind:8s} {m:20s} {pre} → {post}")
        for m in removed:
            print(f"  REMOVED  {m}")
    print(f"\nTotal models now: {len(after)}")
    print("Refresh complete.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
