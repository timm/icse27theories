# META: power prompts for SE-theory-as-code

A field guide to the prompt patterns that produced this repo. Each
pattern is a way of steering an LLM to do science-by-engineering: pose
a thesis, encode it as falsifiable structure, hammer it with stats,
report what survives.

## Pattern bank

### Direction-setting

1. **"Report, don't do."**
   - Asks for analysis and a recommendation, not action.
   - Why: opens space for redirection before the LLM commits work to disk.
   - Example: "what does that test ACTUALLY check on brooks?"

2. **"Give me N options ranked by leverage."**
   - Asks for a ranked menu, not a single plan.
   - Why: surfaces alternatives I'd not have thought of; lets me pick.
   - Example: "give me 3 ways to slice this. Pick one and execute."

3. **"What would refute this?"**
   - Inverts the usual confirmation framing.
   - Why: the answer encodes the model's hypothesis as a testable
     experiment. Forces sharper claims.

4. **"Act as Carlos / Rick / a paper reviewer."**
   - Roleplay critique from a named expert.
   - Why: surfaces the kind of feedback a domain expert would write.

### Code-as-science

5. **"Bake the thesis into a verdict()."**
   - Don't describe an SE theory; encode it as a function that
     returns CONFIRM / REFUTE / neutral.
   - Why: enforces falsifiability at the syntax level.

6. **"Use a [default, lo, hi, 'unit'] tuple."**
   - Every parameter declares its plausible range AND its unit.
   - Why: enables both stress-testing (perturb within [lo, hi]) and
     dimensional analysis (catch unit mismatches at flow joins).

7. **"Stress with both inputs AND params."**
   - Don't just perturb one axis.
   - Why: the 2x2 stress matrix classifies a thesis into universal /
     world-conditional / process-conditional / fragile. A single-axis
     sweep can't see the typology.

8. **"Use stats.same, not threshold."**
   - Verdict by Cliff's-δ + KS + median-ε, not single-shot heuristic.
   - Why: rejects single-comparison artefacts. Many published SE
     theses don't survive proper non-parametric two-sample stats.

### Engineering-discipline

9. **"Don't add features. Just fix the bug."**
   - Resist scope creep.
   - Why: refactor temptations during a bug-fix double the PR size
     and dilute the diff.

10. **"What's the simplest thing that could fail this?"**
    - Adversarial small-input test.
    - Why: catches edge-case bugs (e.g. clamp under-flow, zero-length
      lists) before stress sweeps surface them as anomalies.

11. **"Write the assertion before the code."**
    - Test-first when the test is cheap.
    - Why: clarifies what "done" means.

12. **"Vendor, don't import."**
    - For tiny utility functions, paste into the repo with attribution.
    - Why: keeps the paper artifact dependency-free; reviewer types
      `make` and it works.

### Doc-as-data

13. **"Make scope-creep the diff."**
    - Big PR → smaller commits. Each commit is one named decision.
    - Why: a reviewer's diff is easier to read than a single 3000-line
      patch.

14. **"Quote the metric in the headline."**
    - Findings should say "0.36-0.59 across 5 projects" not "convergent
      across many projects."
    - Why: pre-empts skeptical questioning.

15. **"Use 4 categories at most."**
    - When classifying anything (cells, finding types, project
      attributes), keep the partition shallow.
    - Why: 4-class partitions fit in a 2x2 mental model.

### Verification

16. **"Replay this on a fresh project."**
    - For any claim about model behaviour, run the same code on a
      project you haven't yet seen.
    - Why: prevents over-fit storytelling.

17. **"Save N=100 for now; the cost is amortised."**
    - Use 100-repeat sampling as the default; only drop to N=20 when
      runtime matters.
    - Why: SD models are so cheap (50µs/run) that N=100 costs <1s for
      33 models.

18. **"Bless the floor, don't track each diff."**
    - For HTML / generated artifacts, store the size and check
      "did anything shrink >20%?" not "are all bytes identical?"
    - Why: avoids re-blessing on every regeneration; catches genuine
      regressions.

### Communication

19. **"Caveman mode."**
    - Drop articles, filler, hedging. Fragments OK.
    - Why: cuts response time AND review time. Same info in fewer
      bytes.

20. **"Report in under 200 words."**
    - Cap verbose responses.
    - Why: forces ranking. A 200-word response prioritises.

21. **"Name what is NOT in the result."**
    - "I tried X and Y; X worked, Y returned NaN."
    - Why: surfaces the dead ends so I can avoid retrying them.

### LLM-as-collaborator

22. **"Trust but verify the summary."**
    - Always grep the actual file after an agent reports it changed.
    - Why: agents over-report success; the diff is the source of truth.

23. **"Pin the cache TTL on your tool calls."**
    - Wait long enough to amortise cache reads, short enough to stay
      responsive.
    - Why: 5-minute cache window is the boundary. 1200-1800s waits
      mean the next firing reads everything uncached.

24. **"Strip the LLM's reasoning before showing teammates."**
    - Internal monologue is for the LLM; the deliverable is the
      output.
    - Why: keeps the public surface professional + anonymous for
      submission.

### Workflow

25. **"3 directories, no more."**
    - Repo split: `paper/` (artifact), `extract/` (supply chain),
      `docs/` (site). Hard wall between layers.
    - Why: reviewers only need one directory; everything else is
      provenance.

26. **"One scalar per (model, project, metric) row."**
    - Long-form CSV. New metric = new row, never new column.
    - Why: schema-stable across extractions.

27. **"Make every claim a CSV column."**
    - If a finding doesn't have a column in `outputs/*.csv`, it
      doesn't have evidence.
    - Why: forces empirical anchoring.

28. **"Render the diagram from the same source as the model."**
    - SD diagrams should be generated from the init dict + step body,
      not hand-drawn.
    - Why: a hand-drawn diagram drifts from code; an auto-generated
      one can't.

### Meta

29. **"Show me a worked example, then the abstraction."**
    - Walk through one model end-to-end before designing the
      framework.
    - Why: prevents over-abstraction. The general engine emerges from
      the worked case, not from a blueprint.

30. **"Make the next session resumable."**
    - End each session with TODO.md / PR_HANDOFF.md / state files
      that let me restart cold.
    - Why: cognitive surface matches one work-session; cross-session
      continuity comes from disk artifacts.

## Reading order

A new collaborator reading this for the first time should:

1. Run `python3 paper/sd.py` — 33 model verdicts in 0.02 s.
2. Run `python3 paper/full_audit.py` — 33 × 11 tests in 1.3 s.
3. Read `paper/MODELS_README.md` — model catalogue + cells.
4. Read `docs/index.html` — narrative + findings.
5. Read this file — the prompts that produced the apparatus.

## Anonymity note

If you fork this repo for double-blind submission, strip:
- `docs/index.html`'s `gh-ribbon` block (already commented for easy removal)
- `docs/scripts/link_sd_refs.py:GH_BASE` (swap for anonymous mirror)
- `paper/MODELS_README.md` author-specific references
- this file's section headers if they leak the author's voice
