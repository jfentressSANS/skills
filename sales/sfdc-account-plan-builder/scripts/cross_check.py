#!/usr/bin/env python3
"""
cross_check.py — Docx-vs-Brief Import Fidelity Check (North Star 3.0)

As of North Star 3.0, the brief and the full account-plan docx are no
longer independently drafted from the same source ledger — the docx now
inherits wording and grouping from the brief for any atom the brief covers
(see voice-spec.md, "Per-Atom Routing"). Agreement between the two is no
longer a coincidence worth checking for its own sake; of course they agree
on brief-covered material, one was built from the other on purpose.

This script's job narrowed accordingly. It does NOT verify the brief was
correct against the ledger — that's Step 3b in SKILL.md, a semantic
re-read (see references/brief-verification-worksheet.md), not something a
regex script can do. This script verifies a cheaper, narrower thing: that
the docx faithfully carried forward whatever numbers the brief established,
catching transcription drift during import, not factual drift at the source.

REVISION HISTORY: the first version of this script (2026-07-20, earlier the
same day) approximated "which docx content is brief-derived" with a
hardcoded set of section names (Current Situation, Key Risks, Competitive
Landscape). That was wrong in two ways, found on the very next real run:
(1) Key Risks is NEVER brief-derived — it has no brief equivalent, ever,
for any account — so that hardcoded entry made every run flag 100% of Key
Risks as a false mismatch, permanently. (2) Current Situation itself is a
MIXED case (some groups brief-sourced, some ledger-only), which a
section-level guess can't see, producing partial false positives inside
the section too (a ledger-only group's own figures, correctly absent from
the brief, got flagged as if that were an error).

The fix: stop guessing from section names. Read real per-group provenance
directly from account_data.json's "_source" / "_brief_refs" metadata (see
sfdc-template-map.md) — the same JSON that drives the docx build. A group
only gets checked against the brief if it's actually tagged "_source":
"brief". Nothing else is guessed.

Usage:
    python cross_check.py <brief.md> <full_plan.docx> <account_data.json>

    account_data.json is required for Direction 2 (docx -> brief). If
    omitted, Direction 2 is skipped entirely with a warning — this script
    no longer falls back to section-name guessing, since that's exactly
    the bug this revision fixes.

Exit codes:
    0 — No mismatches found. Safe to ship both files.
    1 — Mismatches found. Do not ship either file until resolved.
    2 — File not found, or docx/JSON read failed.
"""

import re
import sys
import json
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table


DOLLAR_RE = re.compile(r"\$[\d,]+(?:\.\d+)?\s*[KkMmBb]?\b")
PERCENT_RE = re.compile(r"\d+(?:\.\d+)?%")
DATE_RE = re.compile(
    r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2}/\d{4}\b|"
    r"\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
)
_NUMBER_WORDS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)
# Known limitation, unchanged from the prior revision, not addressed here:
# this does not normalize "11 years" vs "eleven years", "10-year" (hyphenated)
# vs "10 years" (spaced), or "10/30/2026" vs "October 30, 2026". Those are
# accepted false-positive risks of a mechanical, non-semantic check — see
# SKILL.md Step 6. Out of scope for this revision, which fixes the routing
# bug, not the normalization gap.
DURATION_RE = re.compile(
    rf"\b(?:\d+|{_NUMBER_WORDS})\s+(?:day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)

PATTERNS = [
    ("Dollar figures", DOLLAR_RE, lambda m: re.sub(r"\s+", "", m).upper()),
    ("Percentages", PERCENT_RE, lambda m: m.strip()),
    ("Dates", DATE_RE, lambda m: m),
    ("Durations", DURATION_RE, lambda m: re.sub(r"\s+", " ", m.strip().lower())),
]


def iter_block_items(doc):
    parent_elm = doc.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, doc)
        elif child.tag == qn('w:tbl'):
            yield Table(child, doc)


def extract_docx_full_text(docx_path: Path) -> str:
    """Whole-document text, read via python-docx directly (never pandoc —
    see SKILL.md Step 5 / lint-patterns.md Pattern 12 for why)."""
    try:
        doc = Document(str(docx_path))
    except Exception as e:
        print(f"Error reading {docx_path}: {e}")
        sys.exit(2)
    lines = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            if block.text.strip():
                lines.append(block.text.strip())
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        lines.append(cell.text.strip())
    return "\n".join(lines)


def collect_brief_sourced_text(account_data: dict) -> tuple[str, list[str]]:
    """Walk account_data.json for any group explicitly tagged
    '_source': 'brief', across any section that supports the metadata.
    Currently that's current_situation_paragraphs only — the one section
    with genuinely mixed brief/ledger provenance (see
    references/atomization-method.md). Sections with no per-group tagging
    at all (key_risks, swot, etc.) are always ledger-only by design and are
    never included here, no section-name special-casing required.

    Returns (concatenated text of brief-sourced groups, list of group
    descriptions for the report)."""
    texts = []
    descriptions = []

    csp = account_data.get("current_situation_paragraphs")
    if isinstance(csp, list):
        for i, entry in enumerate(csp):
            if not isinstance(entry, dict):
                continue  # plain strings carry no provenance tag -> ledger-only by default
            if entry.get("_source") != "brief":
                continue
            if "text" in entry:
                texts.append(entry["text"])
            if "lead" in entry:
                texts.append(entry["lead"])
            if isinstance(entry.get("bullets"), list):
                texts.extend(entry["bullets"])
            refs = entry.get("_brief_refs", [])
            descriptions.append(f"current_situation_paragraphs[{i}] <- {refs}")

    # Strip the **bold** markdown convention before figure-matching so a
    # bolded number isn't accidentally missed by a pattern expecting plain text.
    combined = re.sub(r"\*\*(.+?)\*\*", r"\1", "\n".join(texts))
    return combined, descriptions


def report_section(title: str, missing: set, direction: str) -> bool:
    if not missing:
        print(f"  \u2713 {title} ({direction}): all figures corroborated")
        return False
    print(f"  \u2717 {title} ({direction}): figures NOT corroborated:")
    for item in sorted(missing):
        print(f"      - {item}")
    return True


def main():
    if len(sys.argv) not in (3, 4):
        print("Usage: python cross_check.py <brief.md> <full_plan.docx> [account_data.json]")
        sys.exit(2)

    brief_path = Path(sys.argv[1])
    docx_path = Path(sys.argv[2])
    json_path = Path(sys.argv[3]) if len(sys.argv) == 4 else None

    if not brief_path.exists():
        print(f"Error: brief file not found: {brief_path}")
        sys.exit(2)
    if not docx_path.exists():
        print(f"Error: docx file not found: {docx_path}")
        sys.exit(2)
    if json_path is not None and not json_path.exists():
        print(f"Error: account_data.json not found: {json_path}")
        sys.exit(2)

    brief_text = brief_path.read_text(encoding="utf-8")
    docx_full_text = extract_docx_full_text(docx_path)

    print("\n" + "=" * 60)
    print("CROSS-CHECK: docx import fidelity vs. brief (North Star 3.0)")
    print("=" * 60)
    print(f"  Brief: {brief_path}")
    print(f"  Docx:  {docx_path}")

    any_mismatch = False

    print("\nDirection 1 \u2014 brief -> docx (every brief figure should be corroborated somewhere in the full docx):")
    for title, pattern, normalizer in PATTERNS:
        brief_set = {normalizer(m) for m in pattern.findall(brief_text)}
        docx_set = {normalizer(m) for m in pattern.findall(docx_full_text)}
        only_brief = brief_set - docx_set
        any_mismatch |= report_section(title, only_brief, "brief\u2192docx")

    print("\nDirection 2 \u2014 docx -> brief (every figure in docx groups explicitly tagged _source:\"brief\" should be corroborated in the brief):")
    if json_path is None:
        print("  (skipped \u2014 no account_data.json provided; this direction requires it, no section-name fallback is used)")
    else:
        account_data = json.loads(json_path.read_text(encoding="utf-8"))
        brief_sourced_text, descriptions = collect_brief_sourced_text(account_data)
        if not descriptions:
            print("  (no groups tagged _source:\"brief\" found in account_data.json \u2014 nothing to check in this direction)")
        else:
            print(f"  Checking {len(descriptions)} brief-sourced group(s): {descriptions}")
            for title, pattern, normalizer in PATTERNS:
                docx_group_set = {normalizer(m) for m in pattern.findall(brief_sourced_text)}
                brief_set = {normalizer(m) for m in pattern.findall(brief_text)}
                only_docx = docx_group_set - brief_set
                any_mismatch |= report_section(title, only_docx, "docx\u2192brief")

    print()
    if any_mismatch:
        print("VERDICT: MISMATCH FOUND")
        print("-" * 60)
        print("Do not ship either file yet. For each flagged figure above:")
        print("  1. Check it against the source ledger .md directly \u2014")
        print("     that's the system of record, not either downstream file.")
        print("  2. Fix whichever file (brief or docx) doesn't match the source.")
        print("  3. Re-run this check before delivering.")
        print("Never silently ship a known mismatch. Note: this script catches")
        print("import/transcription drift only. A number wrong in BOTH files")
        print("because the brief itself misread the ledger is Step 3b's job \u2014")
        print("see references/brief-verification-worksheet.md.")
        sys.exit(1)
    else:
        print("VERDICT: CLEAN")
        print("-" * 60)
        print("Every brief figure is corroborated somewhere in the docx, and")
        print("every figure in the docx's brief-sourced groups is corroborated")
        print("in the brief. Safe to deliver both files together.")
        sys.exit(0)


if __name__ == "__main__":
    main()
