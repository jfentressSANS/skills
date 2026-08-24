#!/usr/bin/env python3
"""
lint_gate.py — Executive Brief AI-Tell Detector

Scans a markdown file for LLM output signatures that would undermine
credibility with executive readers. Hard hits block publish.

Includes two checks added 2026-07 after a Deere account-plan diagnostic:
ledger-register leakage (Data — blocks, Read: labels, [bracket-id]
citations surviving into the deliverable) and contraction-avoidance rate
(a document that consistently uses "do not" instead of "don't" reads
stiffer than the calibrated voice, even with no single bad sentence).

Usage:
    python lint_gate.py <input_file.md>
    python lint_gate.py <input_file.md> --verbose

Exit codes:
    0 — No violations found. Output is clean.
    1 — Violations found. Output is blocked. Review hit list.

Two-strike rule:
    Run once. If violations found, fix and rerun.
    If violations remain on second run, halt and surface to user.
    Never silently bypass.
"""

import re
import sys
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

PATTERNS = [
    {
        "name": "Reversal Cliffhanger",
        "regex": r"\b(wasn't|isn't|is not|was not)\s+(the|a|an|about)\s+\w+\.\s+(it|that|the)\s+\w+\s+(was|is)",
        "flags": re.IGNORECASE,
        "description": "Sets up a negative claim then reverses it for drama. Real executives don't write this way.",
        "fix": "State the actual claim directly. Remove the reversal structure.",
    },
    {
        "name": "Antithesis Tic",
        "regex": r"it'?s not (just )?\w+[,.\s\-\u2014]+\s*(it'?s|it is)\s+\w+",
        "flags": re.IGNORECASE,
        "description": "The 'it's not just X, it's Y' construction. Creates the appearance of nuance without delivering it.",
        "fix": "State both things directly without the reversal scaffold.",
    },
    {
        "name": "Throat-Clearing Opener",
        "regex": r"^\s*(In today's|As we all know|It's no secret|In this (article|report|document|brief)|Let me start by|Before we begin|It goes without saying|At its core)",
        "flags": re.IGNORECASE | re.MULTILINE,
        "description": "Orienting sentences that delay information. Reader already knows they are reading the document.",
        "fix": "Delete the opener. Start with the first piece of actual information.",
    },
    {
        "name": "Recap Signature",
        "regex": r"\b(In summary|To recap|Let's review|Key takeaways|In conclusion|To sum up|As a summary|Summing up)\b",
        "flags": re.IGNORECASE,
        "description": "Summary language that signals the document is ending. Structure communicates this without labeling.",
        "fix": "Remove the recap header. Use 'Next Steps' for the action summary.",
    },
    {
        "name": "Filler Transition",
        "regex": r"\b(Having said that|With that being said|That being said|Moving on to|Speaking of which|On that note|With that in mind)\b",
        "flags": re.IGNORECASE,
        "description": "Transition phrases that paper over logical gaps without creating logical connection.",
        "fix": "Delete the transition. If paragraphs can't connect without it, reorder or cut.",
    },
    {
        "name": "Rigid Optimism Close",
        "regex": r"\bDespite (its|these|the) (challenges|drawbacks|limitations|headwinds).{0,60}(exciting|bright|promising|opportunity|potential|future)",
        "flags": re.IGNORECASE | re.DOTALL,
        "description": "Acknowledges challenges then pivots to generic optimism. Signals analysis stopped before getting difficult.",
        "fix": "End on the action. 'The next 90 days determine whether X holds. Three decisions needed by end of month.'",
    },
    {
        "name": "Imagine-a-World Opener",
        "regex": r"^\s*Imagine (a world|a future|if|what it would|yourself)",
        "flags": re.IGNORECASE | re.MULTILINE,
        "description": "Hypothetical scene-setting. TED Talk convention, not executive brief convention.",
        "fix": "Delete. Start with the actual situation.",
    },
    {
        "name": "Magic-Adverb Verb",
        "regex": r"\b(quietly|fundamentally|deeply|remarkably|profoundly|genuinely|truly|meaningfully)\s+(transforms|changes|redefines|reveals|signals|matters|shifts|alters|reshapes)\b",
        "flags": re.IGNORECASE,
        "description": "Vague intensifying adverb + grandiose verb. Asserts significance without providing evidence.",
        "fix": "State the specific change with a number. 'Response time dropped from 4.2 days to 18 hours.'",
    },
    {
        "name": "Vague Attribution",
        "regex": r"\b(industry reports|observers have|experts argue|studies suggest|some critics argue|research shows|analysts say|it is widely believed)\b",
        "flags": re.IGNORECASE,
        "description": "Claims attributed to anonymous sources. Unfalsifiable. Reader cannot check or follow up.",
        "fix": "Name the specific source or cut the claim.",
    },
    {
        "name": "Inline Code Chip",
        "regex": r"(?<!`)`[^`\n]+`(?!`)",
        "flags": 0,
        "description": "Single-backtick fragment in prose. Signals developer documentation, not executive communication.",
        "fix": "Remove the backticks. Bold the term if emphasis is needed (**term**), or cut if it doesn't belong in executive prose.",
    },
    {
        "name": "Ledger Data-Block Header",
        "regex": r"\bData\s*[\u2014-]\s*[A-Z][A-Za-z /]{2,40}:",
        "flags": 0,
        "description": "A ledger section header ('Data — Cybersecurity organization:') left in place as a paragraph lead-in. This is internal bookkeeping structure, not one of the four allowed taxonomy labels (Read:/Judgment:/Hypothesis:/Required response:) and not a sentence a person would write to a VP.",
        "fix": "Cut the header. Open the paragraph with the actual first fact instead.",
    },
    {
        "name": "Ledger Citation Residue",
        "regex": r"\[[a-z][a-z0-9]*(?:-[a-z0-9]+)+\]|\b(?:OBSERVED-INTERNAL|OBSERVED-EXTERNAL|INTERPRETATION)\b",
        "flags": 0,
        "description": "A raw ledger fact-ID citation (e.g. '[spend-2024]') or internal claim-type register label leaked into the main body. These belong only in the Source Notes and Citation IDs appendix (exempted below), not elsewhere in the deliverable.",
        "fix": "Remove the bracket citation or register label from the main body. If it needs to be preserved, it belongs in the Source Notes and Citation IDs appendix instead.",
    },
]

# Note: as of the North Star 2.0 reboot, "Ledger Interpretation Label" is no
# longer a mechanical pattern here. Read:/Judgment:/Hypothesis:/Required
# response: are required taxonomy labels (see voice-spec.md), not a banned
# scaffolding leak — whether a given "Read:" is doing real classification
# work or just mechanically marking paragraph breaks isn't something a
# regex can tell apart from the correct, required usage. That distinction
# is now drafting-time judgment, governed by voice-spec.md, not a gate.

# "Ledger Citation Residue" is exempted inside the Source Notes and
# Citation IDs appendix, where bracket citations are required, not banned.
# See scan_patterns() below for the boundary detection.
APPENDIX_HEADING_PATTERN = re.compile(r"^\s*Source Notes and Citation IDs\s*$", re.IGNORECASE)
EXEMPT_IN_APPENDIX = {"Ledger Citation Residue"}

# Note: Schema Leaks (Pattern 11) cannot be detected by regex — context-dependent.
# The model performs manual review per references/lint-patterns.md Step 1b.

# AI vocabulary blocklist — any single hit is a hard block
# This is a self-contained copy (see SKILL.md: "self-contained, not a
# dependency on exec-brief-editor"), so it's free to diverge from that
# skill's generic list where this domain requires it. Two words removed
# from the original list, found during the Deere diagnostic (2026-07):
#   - "landscape": this skill's own fixed template has required section
#     headers "Customer Landscape" and "Competitive Landscape" (see
#     sfdc-template-map.md). Banning it would block every single account
#     plan regardless of prose quality.
#   - "champion": standard, correct sales-methodology vocabulary for a
#     Relationship Map's role column ("technical champion"), not filler
#     AI-speak in this context.
AI_VOCAB = [
    "delve", "leverage", "robust", "seamless", "holistic", "synergy",
    "paradigm", "empower", "harness", "streamline", "cutting-edge",
    "best-in-class", "ecosystem", "game-changer", "unlock", "elevate",
    "disrupt", "tapestry", "notably", "moreover", "furthermore",
    "utilize", "underscore", "pivotal", "transcend", "elucidate", "illuminate",
    "navigate", "testament", "realm", "foster", "cultivate", "spearhead",
    "actionable", "scalable", "innovative", "transformative",
    "visionary", "groundbreaking", "drive", "stakeholder", "deliverable",
]

AI_VOCAB_REGEX = r"\b(" + "|".join(AI_VOCAB) + r")\b"

# Em-dash overuse thresholds
EM_DASH_THRESHOLD = 0.15       # em-dashes per sentence — briefs (compressed, one-page)
DOCX_EM_DASH_THRESHOLD = 0.15  # em-dashes per sentence — full account-plan docx
# Recalibrated 2026-07 against the North Star 2.0 reboot: measured 0.013
# em-dashes/sentence (1 real em-dash across 75 sentences) — the tighter
# register apparently uses the Read:/Judgment: labels to demarcate shifts
# in claim-type instead of em-dashes, reducing the need for them as a
# connective device. The old 0.35 threshold (calibrated to the prior
# North Star's 0.28) is now far too loose. Rather than pick a new number
# with a tight multiplier against 0.013 — which would be fragile on the
# same kind of small-sample noise the sentence-count floor already exists
# to guard against — this reuses the brief's already-validated 0.15: over
# 11x the new North Star's measured rate (comfortable headroom against
# false positives on a genuinely tighter document) while still a real
# tightening from 0.35. Same EM_DASH_MIN_SENTENCES floor still applies.
EM_DASH_MIN_SENTENCES = 50     # below this, the rate is too noisy on a small sample to mean anything
# Raised from 30 to 50 alongside the docx threshold tightening (0.35->0.15):
# a tighter threshold is more sensitive to small-sample noise, so it needs
# a larger minimum sample to stay reliable. Confirmed empirically: Meridian
# (30 sentences, exactly the old floor) still tripped the new threshold at
# 0.33, driven by structural em-dashes in short label-style table cells
# ("Alex Rutherford — Engineering Manager") and the flagText() placeholder
# wording (now fixed separately to not use an em-dash at all) — not by
# actual prose overuse.
# Docx threshold calibrated 2026-07 against the North Star account-plan docx
# itself: 0.28 em-dashes/sentence, real usage confirmed via clean extraction
# (not a table-border artifact). The brief's 0.15 threshold was calibrated
# for compressed one-page writing and was never tested against fuller,
# more discursive docx-style prose — applied unchanged, it would have
# blocked the one document this skill exists to reproduce.
# The minimum-sentence floor was added after the same diagnostic's synthetic
# Meridian test fixture (28 sentences) tripped the rate on real but sparse
# em-dash usage — 3 from the flagText() placeholder function firing on
# missing sections, 2 inside short table-cell labels, the rest genuine
# short-document prose. A handful of structural em-dashes swings the ratio
# hard when the denominator is this small; the contraction check already
# had an equivalent floor (CONTRACTION_MIN_INSTANCES) and the em-dash check
# needed the same treatment.

# Contraction-avoidance threshold
# Calibrated against the Deere diagnostic (2026-07): the North Star and its
# companion brief ran 0% full-form (8 contractions, 0 full forms). The
# flawed docx from the same source ran 100% full-form (0 contractions,
# 13+ full forms). 0.5 sits well clear of both real examples.
FULL_FORMS = [
    "do not", "does not", "did not", "is not", "are not", "was not", "were not",
    "cannot", "can not", "have not", "has not", "had not", "will not", "would not",
    "should not", "could not", "it is", "that is", "there is",
]
CONTRACTIONS = [
    "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
    "can't", "haven't", "hasn't", "hadn't", "won't", "wouldn't",
    "shouldn't", "couldn't", "it's", "that's", "there's",
]
CONTRACTION_RATE_THRESHOLD = 0.5  # full-forms as a share of (full-forms + contractions)
CONTRACTION_MIN_INSTANCES = 4     # below this total, there's not enough signal either way
# North Star 3.0 (2026-07-20): this check now runs in BOTH modes. North Star
# 2.0 measured 100% full-form in the docx and this check was disabled there
# as a result. North Star 3.0 deliberately supersedes that — contractions
# are now expected in docx narrative prose the same as the brief (see
# voice-spec.md, "Version History and Current Calibration"). The one
# permanent change from the brief's original version of this check: it now
# only evaluates prose paragraphs, never table cells or data fields (see
# TABLE_TAG below) — a date or dollar figure was never meaningfully
# "full-form" or "contracted," so those lines are excluded from the count
# in both modes, not just docx.

TABLE_TAG = "[TABLE] "  # prefix extract_docx_text.py applies to table-cell lines


def prose_only(text: str) -> str:
    """Return only narrative-paragraph lines, dropping table-cell/data-field
    lines tagged by extract_docx_text.py. Used for the contraction check,
    which only ever applies to running prose. Plain .md briefs have no
    tagged lines, so this is a no-op for brief-mode input."""
    kept = [ln for ln in text.split("\n") if not ln.startswith(TABLE_TAG)]
    return "\n".join(kept)


# ---------------------------------------------------------------------------
# Scanning functions
# ---------------------------------------------------------------------------

def count_sentences(text: str) -> int:
    """Approximate sentence count by counting terminal punctuation."""
    sentences = re.findall(r'[.!?]+(?:\s|$)', text)
    return max(len(sentences), 1)  # avoid division by zero


def count_em_dashes(text: str) -> int:
    """Count em-dashes (— and --) in text."""
    return len(re.findall(r'\u2014|--', text))


def count_full_forms(text: str) -> int:
    """Count full-form negations/contractable phrases (do not, is not, ...)."""
    pattern = r"\b(" + "|".join(FULL_FORMS) + r")\b"
    return len(re.findall(pattern, text, re.IGNORECASE))


def count_contractions(text: str) -> int:
    """Count contracted forms (don't, isn't, it's, ...)."""
    pattern = r"\b(" + "|".join(CONTRACTIONS) + r")\b"
    return len(re.findall(pattern, text, re.IGNORECASE))


def scan_patterns(text: str, lines: list[str]) -> list[dict]:
    """Run all structural regex patterns against the full text.

    Patterns named in EXEMPT_IN_APPENDIX stop applying once a line matching
    APPENDIX_HEADING_PATTERN is reached — citations are required in the

    Source Notes and Citation IDs appendix, not banned there.
    """
    hits = []
    appendix_start = None
    for i, line in enumerate(lines, start=1):
        if APPENDIX_HEADING_PATTERN.match(line):
            appendix_start = i
            break

    for pattern in PATTERNS:
        compiled = re.compile(pattern["regex"], pattern["flags"])
        exempt_name = pattern["name"] in EXEMPT_IN_APPENDIX
        for i, line in enumerate(lines, start=1):
            if exempt_name and appendix_start is not None and i >= appendix_start:
                continue
            match = compiled.search(line)
            if match:
                hits.append({
                    "pattern": pattern["name"],
                    "line": i,
                    "text": line[len(TABLE_TAG):].strip()[:120] if line.startswith(TABLE_TAG) else line.strip()[:120],
                    "match": match.group(0),
                    "description": pattern["description"],
                    "fix": pattern["fix"],
                })
    return hits


def scan_vocab(text: str, lines: list[str]) -> list[dict]:
    """Scan for AI vocabulary blocklist hits."""
    hits = []
    compiled = re.compile(AI_VOCAB_REGEX, re.IGNORECASE)
    for i, line in enumerate(lines, start=1):
        display = line[len(TABLE_TAG):].strip()[:120] if line.startswith(TABLE_TAG) else line.strip()[:120]
        for match in compiled.finditer(line):
            hits.append({
                "pattern": "AI Vocabulary",
                "line": i,
                "text": display,
                "match": match.group(0).lower(),
                "description": f"Blocked word: '{match.group(0)}' — appears at disproportionately high rates in LLM output.",
                "fix": f"Replace '{match.group(0)}' with a specific, concrete alternative. See lint-patterns.md fix map.",
            })
    return hits


def scan_em_dashes(text: str, threshold: float = EM_DASH_THRESHOLD) -> list[dict]:
    """Check em-dash rate against threshold. Skipped below EM_DASH_MIN_SENTENCES."""
    hits = []
    dash_count = count_em_dashes(text)
    sentence_count = count_sentences(text)

    if sentence_count < EM_DASH_MIN_SENTENCES:
        return hits  # sample too small for the rate to mean anything

    rate = dash_count / sentence_count

    if rate > threshold:
        hits.append({
            "pattern": "Em-Dash Overuse",
            "line": "document-wide",
            "text": f"{dash_count} em-dashes across ~{sentence_count} sentences ({rate:.2f} per sentence)",
            "match": f"Rate: {rate:.2f} (threshold: {threshold})",
            "description": f"GPT-4.1 uses em-dashes at 3.3x human rate. Current rate ({rate:.2f}) exceeds threshold ({threshold}).",
            "fix": "Replace most em-dashes with periods. Separate the clauses. The sentence almost always becomes clearer.",
        })
    return hits


def scan_contraction_rate(text: str) -> list[dict]:
    """Check full-form-vs-contraction rate against threshold, narrative
    prose only (table cells / data fields excluded via prose_only())."""
    hits = []
    prose = prose_only(text)
    full = count_full_forms(prose)
    contracted = count_contractions(prose)
    total = full + contracted

    if total < CONTRACTION_MIN_INSTANCES:
        return hits  # not enough instances either way to mean anything

    rate = full / total
    if rate > CONTRACTION_RATE_THRESHOLD:
        hits.append({
            "pattern": "Contraction Avoidance",
            "line": "document-wide (prose only)",
            "text": f"{full} full forms vs. {contracted} contractions ({rate:.0%} full-form) in narrative prose",
            "match": f"Rate: {rate:.0%} (threshold: {CONTRACTION_RATE_THRESHOLD:.0%})",
            "description": "North Star 3.0 expects contractions throughout narrative prose in both the brief and the docx (don't, it's, doesn't) — table cells and data fields are excluded from this count. A document that consistently avoids contractions in its prose sections reads stiffer and more formal than the calibrated register, even when every individual sentence looks fine on its own.",
            "fix": "Rewrite full forms as contractions where natural in prose paragraphs: 'do not' \u2192 \"don't\", 'is not' \u2192 \"isn't\", 'does not' \u2192 \"doesn't\". Leave table cells and data fields untouched.",
        })
    return hits


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_hit(hit: dict, verbose: bool = False) -> str:
    lines = [
        f"  [{hit['pattern']}] Line {hit['line']}",
        f"  Matched: \"{hit['match']}\"",
    ]
    if verbose:
        lines.append(f"  Context: {hit['text']}")
        lines.append(f"  Why: {hit['description']}")
        lines.append(f"  Fix: {hit['fix']}")
    return "\n".join(lines)


def print_report(hits: list[dict], filepath: str, verbose: bool = False, doc_type: str = "brief") -> None:
    print(f"\n{'='*60}")
    print(f"LINT GATE REPORT: {filepath}")
    print(f"{'='*60}")
    print(f"Doc type: {doc_type} (em-dash threshold: {DOCX_EM_DASH_THRESHOLD if doc_type == 'docx' else EM_DASH_THRESHOLD})")

    if not hits:
        print("\n✓ PASS — No violations found. Output is clean.\n")
        return

    print(f"\n✗ BLOCKED — {len(hits)} violation(s) found.\n")
    print("Hit list:")
    print("-" * 40)

    for i, hit in enumerate(hits, start=1):
        print(f"\n{i}. {format_hit(hit, verbose)}")

    print("\n" + "-" * 40)
    print("Two-strike rule:")
    print("  1. Fix all violations above.")
    print("  2. Rerun lint_gate.py on the revised output.")
    print("  3. If violations remain, HALT and surface to user.")
    print("  Never silently bypass a lint failure.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Executive Brief Lint Gate — detects AI-tell patterns before publish."
    )
    parser.add_argument("input_file", help="Path to the markdown file to scan")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full context, description, and fix for each violation"
    )
    parser.add_argument(
        "--doc-type",
        choices=["brief", "docx"],
        default="brief",
        help="Which register this text is: 'brief' (default, 0.15 em-dash threshold) or 'docx' (0.35 threshold, calibrated to the North Star account-plan docx)."
    )
    args = parser.parse_args()

    filepath = Path(args.input_file)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(2)

    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    em_dash_threshold = DOCX_EM_DASH_THRESHOLD if args.doc_type == "docx" else EM_DASH_THRESHOLD

    # Run all scans
    hits = []
    hits.extend(scan_patterns(text, lines))
    hits.extend(scan_vocab(text, lines))
    hits.extend(scan_em_dashes(text, threshold=em_dash_threshold))
    # North Star 3.0: contraction check now runs in both modes (prose only,
    # via prose_only() — table cells and data fields are excluded).
    hits.extend(scan_contraction_rate(text))

    # Sort by line number (document-wide hits go last)
    def sort_key(h):
        ln = h["line"]
        return (1, 0) if isinstance(ln, str) else (0, int(ln))

    hits.sort(key=sort_key)

    # Report
    print_report(hits, str(filepath), verbose=args.verbose, doc_type=args.doc_type)

    # Exit code
    sys.exit(0 if not hits else 1)


if __name__ == "__main__":
    main()
