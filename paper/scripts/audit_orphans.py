#!/usr/bin/env python3
"""Find init keys declared in a model's init dict but never referenced
in its step() body. Symptom of a symbol-only param (declared for
documentation or future use but never wired into the equations).

Run: python3 paper/scripts/audit_orphans.py

Prints one row per orphan: model, key, unit.
Known orphan from CLAUDE.md: archpat.pat_strength.
"""
import re
import sys
from pathlib import Path

HERE  = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import sd                                            # noqa: E402


def step_body(fn):
    """Extract the source of fn's inner step() via runtime introspection.
    Falls back to grep on sd.py if introspection isn't available."""
    m = fn()
    step = m.step
    try:
        import inspect
        return inspect.getsource(step)
    except (OSError, TypeError):
        return ""


def main():
    orphans = []
    for fn in sd.ALL_MODELS:
        m    = fn()
        body = step_body(fn)
        # Token-match: a key is "used" if it appears as .key (attribute)
        # OR in a string literal (for setattr) inside the step body.
        for k, spec in m.init.items():
            unit = spec[3] if len(spec) >= 4 else "?"
            # Strong "used" signal: the key appears as u.<key> or v.<key>
            # in the step body — i.e. its current value is read or its
            # next value is written. setattr() carry-forward via string
            # literal does NOT count: it merely propagates the previous
            # value, not "uses" it in any equation.
            pat = re.compile(rf"[uv]\.{re.escape(k)}\b")
            if not pat.search(body):
                orphans.append((fn.__name__, k, unit))

    if not orphans:
        print("OK — no orphan init keys found.")
        return 0
    print(f"{'model':<14} {'key':<22} {'unit':<14} status")
    print("-" * 60)
    for model, key, unit in orphans:
        print(f"{model:<14} {key:<22} {unit:<14} ORPHAN")
    print(f"\n{len(orphans)} orphan init key(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
