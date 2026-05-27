#!/usr/bin/env python3
"""Extract (user_prompt, assistant_text) pairs from Claude Code's
.jsonl session logs and emit a clean markdown transcript suitable for
sharing with collaborators.

Drops:
  - tool_use / tool_result blocks
  - <system-reminder> + <command-name> + <local-command-stdout> tags
  - assistant thinking blocks
  - anything that looks like an absolute filesystem path /Users/<name>

Run:
  python3 meta/sanitize_log.py
    -> writes meta/session_<short>.md per .jsonl

  python3 meta/sanitize_log.py <path_to.jsonl>
    -> writes meta/session_<short>.md for that one log
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOGS = Path.home() / ".claude/projects/-Users-timm-gits-timm-icse27theories"
OUT  = REPO / "meta"

# Strip these tag blocks wholesale (open + content + close).
STRIP_TAGS = [
    "system-reminder", "command-name", "local-command-stdout",
    "command-message", "command-args", "user-prompt-submit-hook",
    "session-start-hook", "caveat",
]

# Replace abs paths with placeholders.
ANON_PAT = [
    (re.compile(r"/Users/[a-zA-Z0-9_]+"),       "/Users/<user>"),
    (re.compile(r"\b[a-zA-Z0-9._-]+@ieee\.org"), "<email>"),
]


def strip_tags(text: str) -> str:
    for tag in STRIP_TAGS:
        text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.S | re.I)
        text = re.sub(rf"<{tag} ?/?>", "", text, flags=re.I)
    return text


def anonymise(text: str) -> str:
    for pat, repl in ANON_PAT:
        text = pat.sub(repl, text)
    return text


def clean(text: str) -> str:
    return anonymise(strip_tags(text)).strip()


def extract_pairs(jsonl_path: Path):
    """Walk .jsonl, yield (role, content) tuples. role is 'user' or
    'assistant'. content is plain text (no tool calls)."""
    for line in jsonl_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") or {}
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        body = msg.get("content")
        if isinstance(body, str):
            txt = body
        elif isinstance(body, list):
            parts = []
            for blk in body:
                if not isinstance(blk, dict):
                    continue
                if blk.get("type") == "text":
                    parts.append(blk.get("text", ""))
                # Skip tool_use, tool_result, thinking
            txt = "\n".join(parts)
        else:
            continue
        txt = clean(txt)
        if txt:
            yield role, txt


def render(jsonl_path: Path, out_path: Path):
    lines = [f"# Session transcript: `{jsonl_path.name}`\n",
             "Pairs extracted by `meta/sanitize_log.py`. ",
             "Tool calls + thinking + system reminders stripped. ",
             "Filesystem paths anonymised.\n"]
    n_user = n_asst = 0
    for role, text in extract_pairs(jsonl_path):
        tag = "**You**" if role == "user" else "**Claude**"
        lines.append(f"\n---\n\n{tag}:\n\n{text}\n")
        n_user += (role == "user")
        n_asst += (role == "assistant")
    out_path.write_text("\n".join(lines))
    print(f"{jsonl_path.name}: {n_user} user turns, {n_asst} assistant turns "
          f"-> {out_path.relative_to(REPO)}")


def main():
    args = sys.argv[1:]
    paths = ([Path(a) for a in args]
             if args else sorted(LOGS.glob("*.jsonl")))
    OUT.mkdir(exist_ok=True)
    for p in paths:
        short = p.stem.split("-")[0]
        out = OUT / f"session_{short}.md"
        render(p, out)


if __name__ == "__main__":
    main()
