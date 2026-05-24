# Open-source tool landscape for the 3 historically-blocking signals

Verified via web search May 2026. All findings recoverable from
public sources.

## Refactor detection — solved

**RefactoringMiner** (Tsantalis et al.)
- License: MIT (confirmed from Maven POM)
- Current version: 3.1.3
- Language: Java (some recent multi-language support)
- Benchmark: precision/recall on 547 commits across 188 projects,
  re-validated Dec 2025
- Already wired in kaiaulu via parse_java_code_refactoring_json
- Repo: https://github.com/tsantalis/RefactoringMiner

Zero additional integration work. Just install + run.

## SZZ-style bug location — solved, multiple options

| implementation | language | license | strengths |
|---|---|---|---|
| PyDriller (B-SZZ) | Python | MIT | easiest entry; ~10 lines to first bug-introducing commit |
| SZZ Unleashed | Java | open | MA-SZZ with Williams-Spacco line mapping; well-cited |
| OpenSZZ | (web) | open | git + JIRA combo; designed for our data shape |
| RA-SZZ / RA-SZZ* | Java | open | uses RefactoringMiner to filter refactor false positives; best accuracy on developer-informed oracle |

Repos:
- PyDriller: https://github.com/ishepard/pydriller
- SZZ Unleashed: https://github.com/wogscpar/SZZUnleashed
- OpenSZZ: https://github.com/clowee/OpenSZZ

**Validation benchmark**: Linux kernel since Oct 2013 labels every bug
fix with the bug-introducing commit. As of v6.1-rc5, 76,046
ground-truth pairs available. Larger than any researcher-curated
oracle.

Recommendation: PyDriller for quick wins, OpenSZZ for the paper.

## DV8-style architectural analysis — partial substitute exists

**Arcan** (ESSeRE Lab, Università Milano-Bicocca)
- License: open source
- Language: Java only
- Detects: Unstable Dependency, Hub-Like Dependency, Cyclic
  Dependency, God Component (4 smells)
- Output: file-level (file, smell_type, smell_id) triples —
  structurally identical to DV8's flaws output
- Companion tool ASTracker evolves smells across versions
- Repo: https://essere.disco.unimib.it/wiki/arcan/

**Key difference from DV8**: Arcan uses ONLY structural dependencies
and software metrics. DV8 ALSO uses historical change metrics. So
Arcan misses the co-change dimension entirely. (Sas et al. 2022, EMSE.)

**For archpat**: the model consumes file-level architectural-issue
counts to partition into Patterned/Legacy/Drift. Arcan's smells fit
this slot structurally. The substitution is methodologically defensible.

Other options:
- **DesigniteJava** — open source, Java, 17 design + 10 implementation
  smells (different granularity)
- **Designite** — C# only, free academic license; not relevant for Helix
- **CodeScene** — commercial, free tier, behavioral analysis like
  DV8's historical angle (but not open)

## Architectural patterns (GoF) — also available

**pattern4.jar** (Tsantalis / Concordia)
- URL: https://users.encs.concordia.ca/~nikolaos/files/pattern_detection/pattern4.jar
- Detects GoF design patterns in Java source
- Already has a kaiaulu wrapper (`parse_gof_patterns`); only blocker
  has been setup
- Carlos confirms Claude Code can handle the setup → GoF is back on

**For archpat**: pattern4.jar is the closest match to Ric's original
"patterns" semantics. Preferred over Arcan for that model. Arcan
becomes a sensitivity check rather than the primary signal.

## Architectural anti-patterns by other means

Other public ASTracker/Arcan-style work includes:
- **AsTdEA** — modified Arcan for C/C++ projects
- Various academic tools (DeepLearningSmells, code2vec-based detectors)
  but none with the maturity of Arcan or pattern4.jar

## Summary table

| signal | best open option | install effort | gap vs proprietary |
|---|---|---|---|
| refactor detection | RefactoringMiner | low; jar download | none |
| SZZ bug location | PyDriller (Python) or OpenSZZ (more sophisticated) | low–moderate | none |
| architectural anti-patterns (GoF) | pattern4.jar | low; jar download | none — IS the canonical academic tool |
| architectural smells (DV8-style) | Arcan + ASTracker | moderate; Java setup | structural-only; no historical co-change |

## Net for the paper

All three signals once labeled "blockers" have working open-source
alternatives. The remaining gaps (no AI attribution, no CI flake
logs, no org/HR data) are gaps in field-wide data collection, not in
tooling. That's the headline contribution.
