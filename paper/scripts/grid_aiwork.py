#!/usr/bin/env python3
"""Sweep aiwork over (gen_boost, churn_mult); emit CSV + SVG heatmap.

Reproduces the May 11 / 2026-05-29 6x6 grid showing how the
METR / GitClear / GitHub regime sits in aiwork's parameter space.

Outputs:
  paper/outputs/grid_aiwork.csv   long-form (gen_boost, churn_mult, gap)
  paper/outputs/figs/grid_aiwork.svg   heatmap, deps-free
"""
import csv, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from sd import aiwork, run

GENS   = [0.0, 0.2, 0.5, 1.0, 1.5, 2.0]
CHURNS = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]


def gap_at(gb, cm):
    m  = aiwork()
    bi = {k: list(v) for k, v in m.init.items()}
    bi['gen_boost']  = [gb, 0, 2, 'frac/ai']
    bi['churn_mult'] = [cm, 0, 5, 'frac/ai']
    def y(ai_val):
        bi2 = {**bi, 'ai': [ai_val, 0, 1, 'frac']}
        return m.y(run(bi2, m.step))
    return y(1) - y(0)


def build_grid():
    g = {}
    for gb in GENS:
        for cm in CHURNS:
            g[(gb, cm)] = gap_at(gb, cm)
    return g


def write_csv(grid, path):
    with path.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['gen_boost', 'churn_mult', 'gap'])
        for (gb, cm), v in sorted(grid.items()):
            w.writerow([gb, cm, f"{v:.2f}"])


def lerp_color(v, vmin, vmax):
    """Diverging colormap: red(neg) -> white(0) -> blue(pos).
    Returns hex string."""
    if v >= 0:
        t = v / vmax if vmax > 0 else 0
        r = int(255 - 200 * t)
        g = int(255 - 130 * t)
        b = int(255 -  50 * t)
    else:
        t = v / vmin if vmin < 0 else 0
        r = int(255 -  50 * t)
        g = int(255 - 130 * t)
        b = int(255 - 200 * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def write_svg(grid, path):
    cell_w, cell_h = 78, 44
    n_col, n_row = len(GENS), len(CHURNS)
    left, top = 110, 70
    grid_w, grid_h = n_col * cell_w, n_row * cell_h
    W = left + grid_w + 230   # extra room for right-side legend
    H = top + grid_h + 80

    vals = list(grid.values())
    vmin, vmax = min(vals), max(vals)

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="-apple-system, Segoe UI, sans-serif">',
        '<style>',
        '  .lbl  { font-size: 11px; fill: #444; }',
        '  .axl  { font-size: 12px; fill: #222; font-weight: 600; }',
        '  .ttl  { font-size: 14px; fill: #111; font-weight: 700; }',
        '  .cell { font-size: 12px; fill: #111; font-weight: 600; text-anchor: middle; }',
        '  .cellneg { fill: #fff; }',
        '</style>',
        f'<text class="ttl" x="{W//2}" y="22" text-anchor="middle">'
        f'aiwork: gap = y(ai=1) − y(ai=0) over (gen_boost, churn_mult)</text>',
        f'<text class="lbl" x="{W//2}" y="40" text-anchor="middle" '
        f'fill="#666">red = AI hurts &middot; blue = AI helps &middot; '
        f'diagonal contour = regime boundary</text>',
    ]

    # Column labels (gen_boost, top axis)
    for i, gb in enumerate(GENS):
        x = left + i * cell_w + cell_w // 2
        s.append(f'<text class="lbl" x="{x}" y="{top - 8}" text-anchor="middle">'
                 f'+{int(gb*100)}%</text>')
    s.append(f'<text class="axl" x="{left + grid_w//2}" y="{top - 28}" '
             f'text-anchor="middle">gen_boost (AI speedup)</text>')

    # Row labels (churn_mult, left axis)
    for j, cm in enumerate(CHURNS):
        y = top + j * cell_h + cell_h // 2 + 4
        s.append(f'<text class="lbl" x="{left - 10}" y="{y}" text-anchor="end">'
                 f'churn {int(cm)}×</text>')
    s.append(f'<text class="axl" x="20" y="{top + grid_h//2}" '
             f'text-anchor="middle" transform="rotate(-90 20 {top + grid_h//2})">'
             f'churn_mult (AI rework inflation)</text>')

    # Cells
    for i, gb in enumerate(GENS):
        for j, cm in enumerate(CHURNS):
            v = grid[(gb, cm)]
            x = left + i * cell_w
            y = top + j * cell_h
            fill = lerp_color(v, vmin, vmax)
            txt_cls = "cell"
            # darker cells -> white text for contrast
            if abs(v) / max(abs(vmin), abs(vmax)) > 0.55:
                txt_cls = "cell cellneg"
            s.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                     f'fill="{fill}" stroke="#fff" stroke-width="1"/>')
            sign = '+' if v >= 0 else ''
            s.append(f'<text class="{txt_cls}" x="{x + cell_w//2}" '
                     f'y="{y + cell_h//2 + 4}">{sign}{int(round(v))}</text>')

    # Study annotations (positioned manually based on the mapping in the prose)
    annotations = [
        ("GitHub RCT 2024 (+2–4%)",   3, 0, "#1f6db8"),  # gen+100%, churn 0×
        ("GitClear 2024 (~2× churn)", 1, 2, "#a83232"),  # gen+20%,  churn 2×
        ("METR 2025 (−19%)",          0, 1, "#a83232"),  # gen+0%,   churn 1×
    ]
    legend_x = left + grid_w + 14
    legend_y = top + 6
    for k, (label, ci, ri, col) in enumerate(annotations):
        cx = left + ci * cell_w + cell_w // 2
        cy = top + ri * cell_h + cell_h // 2
        s.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="none" '
                 f'stroke="{col}" stroke-width="2.2"/>')
        # legend dot + label outside grid
        ly = legend_y + k * 18
        s.append(f'<circle cx="{legend_x + 6}" cy="{ly}" r="5" fill="none" '
                 f'stroke="{col}" stroke-width="2"/>')
        s.append(f'<text class="lbl" x="{legend_x + 16}" y="{ly + 4}">{label}</text>')

    # Footnote
    s.append(f'<text class="lbl" x="{left}" y="{top + grid_h + 28}">'
             f'○ marks the approximate parameter region each study samples '
             f'(heuristic placement, not derived from study artifacts).</text>')
    s.append(f'<text class="lbl" x="{left}" y="{top + grid_h + 46}">'
             f'Source: paper/scripts/grid_aiwork.py — deps-free, reproducible.</text>')

    s.append('</svg>')
    path.write_text('\n'.join(s))


def main():
    out = HERE / "outputs"
    figs = out / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    grid = build_grid()
    csv_path = out / "grid_aiwork.csv"
    svg_path = figs / "grid_aiwork.svg"
    write_csv(grid, csv_path)
    write_svg(grid, svg_path)
    vmin, vmax = min(grid.values()), max(grid.values())
    print(f"Wrote {csv_path.relative_to(HERE)}  ({len(grid)} cells, "
          f"range [{vmin:+.1f}, {vmax:+.1f}])")
    print(f"Wrote {svg_path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
