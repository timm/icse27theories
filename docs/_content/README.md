# MYTHS content store

Per-model content as YAML. The page generator (`scripts/gen_rich.py`) is a
dumb template engine: it reads these YAMLs and renders HTML. Edit content
HERE, never edit `docs/models/*.html` directly.

## Why this exists

LLM-driven regeneration was losing prose on every pass (see `brooks`,
`diapers` regressions). Holding content as data in versioned YAMLs:

1. Diffs are reviewable — text changes show as text changes
2. Generator is small and bounded
3. `scripts/check_pages.py` enforces minimum richness per page
4. A page floor (`scripts/_page_floor.json`) detects shrinkage

## Schema

```yaml
name: <model-key>           # filename stem
year: <int>                 # for sort order
cell: universal|process-cond|fragile|world-cond|dark|toy
cite_short: "Author (year). Title."
manual: false               # true = generator skips this entry

# === Panel 1: Summary ===
intro1: <html paragraph>
intro2: <html paragraph>
intuition: <html paragraph>
y_text: "<one sentence>"    # success-measure headline
y_para: <html paragraph>
rq_text: "<one sentence>"   # conjecture headline
rq_para: <html paragraph>
cell_para: <html paragraph> # justifies stress-matrix cell

# === Panel 2: Model ===
mermaid: |                  # optional. omit to skip diagram
  flowchart LR
    ...
code_commented: |
  def <name>():
    ...

# === Panel 3: Data lift ===
lift_intro: <html block>
lift_rmd: lifts/lift_<name>.Rmd   # optional. omit if not lifted

# === Panel 4: Attrs/Tools/Sanity ===
attrs_table:
  - [attr, source, kaiaulu_func, project, value]
tools_table:
  - [tool, role, install]
sanity: <html paragraph>

# === Panel 5: Scorecard ===
scorecard_extras: <html block>  # optional

# === Panel 6: Results ===
results_intro: <html paragraph>
results_table_cols: [col1, col2, ...]
results_table_rows:
  - [val, val, ...]
results_discussion: <html block>
implications: ["...", "..."]

# === References ===
refs:
  - cite: "Author (Year). Title. Venue."
    url:  https://doi.org/...
    kind: peer-reviewed|book|preprint|industry|magazine
```

## Workflow

1. Edit YAML in this directory
2. Run `python3 scripts/gen_rich.py`
3. Run `python3 scripts/check_pages.py` (must pass)
4. After visual review, `python3 scripts/check_pages.py --bless`
5. Commit YAML + generated HTML + new floor in one commit
