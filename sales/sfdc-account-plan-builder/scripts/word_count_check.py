#!/usr/bin/env python3
"""
word_count_check.py — Executive Brief Word Count Enforcer

Checks whether the rewritten output stays within the 60% word count cap
relative to the original input. Fires refire instructions if over cap.
Halts if over 65% after second pass.

Usage:
    python word_count_check.py <original_file.md> <rewritten_file.md>
    python word_count_check.py <original_file.md> <rewritten_file.md> --pass <1|2>

Exit codes:
    0 — Within cap. Output passes word count check.
    1 — Over cap (61-65%). Refire with 'cut harder' instruction.
    2 — Hard over (>65%). Halt. Surface to user.
    3 — File not found or argument error.

Cap thresholds:
    ≤ 60%  — PASS
    61-65% — REFIRE: cut harder, target 50%
    > 65%  — HALT: surface to user, do not publish
"""

import re
import sys
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Word counting
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """
    Count words in markdown text.
    Strips markdown syntax before counting to get prose word count.
    """
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove markdown headers (keep the text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove markdown links, keep link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)

    # Remove HTML tags if present
    text = re.sub(r'<[^>]+>', '', text)

    # Remove table separators
    text = re.sub(r'^\|[-:| ]+\|$', '', text, flags=re.MULTILINE)

    # Split and count
    words = text.split()
    return len(words)


# ---------------------------------------------------------------------------
# Ratio calculation and verdict
# ---------------------------------------------------------------------------

def calculate_ratio(original_count: int, rewritten_count: int) -> float:
    """Return rewritten count as a percentage of original count."""
    if original_count == 0:
        return 0.0
    return (rewritten_count / original_count) * 100


def get_verdict(ratio: float) -> tuple[str, int]:
    """
    Returns (verdict_label, exit_code).

    Verdicts:
        PASS    (≤60%)  → exit 0
        REFIRE  (61-65%) → exit 1
        HALT    (>65%)  → exit 2
    """
    if ratio <= 60.0:
        return "PASS", 0
    elif ratio <= 65.0:
        return "REFIRE", 1
    else:
        return "HALT", 2


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

REFIRE_INSTRUCTION = """
REFIRE INSTRUCTION
------------------
The rewritten output is over the 60% word count cap.
Refire the rewriter with this instruction appended:

  "The current output is [RATIO]% of the original word count.
   The cap is 60%. Cut harder. Target 50%.
   Priority cut order:
   1. Methodology sections — cut entirely
   2. Background the reader already has — cut entirely
   3. Restatements of the recommendation — cut to one instance
   4. Weaker evidence that supports a point already made by stronger evidence
   5. Qualifications and caveats that do not change the recommendation"

After rewriting, run word_count_check.py again with --pass 2.
"""

HALT_INSTRUCTION = """
HALT — DO NOT PUBLISH
---------------------
The rewritten output is [RATIO]% of the original word count.
The hard cap is 65% on a second pass (60% target).

Two-strike rule: this check has either failed twice, or the output
is so far over cap that a second pass is required.

Surface the current draft to the user with:
  - Current word count: [REWRITTEN] words
  - Original word count: [ORIGINAL] words
  - Current ratio: [RATIO]%
  - Target: 60% ([TARGET] words)
  - Gap: [GAP] words to cut

The user must either:
  1. Edit the draft manually to hit the cap, or
  2. Override with a written reason why the cap does not apply
     to this specific brief.

Never silently bypass the word count cap.
"""


def format_instruction(template: str, ratio: float, rewritten: int,
                        original: int) -> str:
    target = int(original * 0.60)
    gap = rewritten - target
    return (template
            .replace("[RATIO]", f"{ratio:.1f}")
            .replace("[REWRITTEN]", f"{rewritten:,}")
            .replace("[ORIGINAL]", f"{original:,}")
            .replace("[TARGET]", f"{target:,}")
            .replace("[GAP]", f"{gap:,}"))


def print_report(original_path: str, rewritten_path: str,
                 original_count: int, rewritten_count: int,
                 ratio: float, verdict: str, pass_number: int) -> None:

    print(f"\n{'='*60}")
    print(f"WORD COUNT CHECK (Pass {pass_number})")
    print(f"{'='*60}")
    print(f"  Original:  {original_path}")
    print(f"  Rewritten: {rewritten_path}")
    print(f"\n  Original word count:  {original_count:,}")
    print(f"  Rewritten word count: {rewritten_count:,}")
    print(f"  Ratio:                {ratio:.1f}% of original")
    print(f"  Cap:                  60% ({int(original_count * 0.60):,} words)")
    print(f"\n  Verdict: {verdict}")

    if verdict == "PASS":
        print(f"\n  ✓ Output is within the 60% word count cap.\n")

    elif verdict == "REFIRE":
        print(f"\n  ✗ Output exceeds 60% cap. Refire required.")
        print(format_instruction(REFIRE_INSTRUCTION, ratio,
                                 rewritten_count, original_count))

    elif verdict == "HALT":
        if pass_number >= 2:
            print(f"\n  ✗ Output still exceeds cap after second pass. HALT.")
        else:
            print(f"\n  ✗ Output is far over cap (>65%). HALT.")
        print(format_instruction(HALT_INSTRUCTION, ratio,
                                 rewritten_count, original_count))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Executive Brief Word Count Enforcer — checks 60% cap."
    )
    parser.add_argument("original_file", help="Path to the original input file")
    parser.add_argument("rewritten_file", help="Path to the rewritten output file")
    parser.add_argument(
        "--pass", "-p",
        dest="pass_number",
        type=int,
        choices=[1, 2],
        default=1,
        help="Which pass this is (1 = first run, 2 = after refire). Default: 1"
    )
    args = parser.parse_args()

    original_path = Path(args.original_file)
    rewritten_path = Path(args.rewritten_file)

    # File existence checks
    errors = []
    if not original_path.exists():
        errors.append(f"Original file not found: {original_path}")
    if not rewritten_path.exists():
        errors.append(f"Rewritten file not found: {rewritten_path}")
    if errors:
        for e in errors:
            print(f"Error: {e}")
        sys.exit(3)

    # Count words
    original_text = original_path.read_text(encoding="utf-8")
    rewritten_text = rewritten_path.read_text(encoding="utf-8")

    original_count = count_words(original_text)
    rewritten_count = count_words(rewritten_text)
    ratio = calculate_ratio(original_count, rewritten_count)

    # On pass 2, REFIRE becomes HALT (two-strike rule)
    verdict, exit_code = get_verdict(ratio)
    if args.pass_number >= 2 and verdict == "REFIRE":
        verdict = "HALT"
        exit_code = 2

    # Report
    print_report(
        str(original_path), str(rewritten_path),
        original_count, rewritten_count,
        ratio, verdict, args.pass_number
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
