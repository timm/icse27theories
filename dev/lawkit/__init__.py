"""lawkit: test any SE law expressed as a paper/sd.py model.
core (claim + verdict) -> battery (is the machine sound?) -> regimes
(where does it hold?) -> evidence (does this project sit there?)."""
import sys
from pathlib import Path
_dev = Path(__file__).resolve().parent.parent          # dev/
sys.path[:0] = [str(_dev / "paper_patches"), str(_dev.parent / "paper")]
