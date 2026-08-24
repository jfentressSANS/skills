---
name: sfdc-account-plan-builder
description: |
  Turns a SANS fact-ledger account-plan .md (numbered sections, [citations]) into a leadership brief + SFDC Word doc for VP/Director/CRO confidence review. Use on "build/generate the account plan."
---

# SFDC Account Plan Builder

Turns a verified, fact-cited account-plan markdown file into two leadership-ready deliverables: a compressed one-page brief and a complete SFDC-formatted Word document, both written independently from the same source and cross-checked against each other before delivery.

This skill exists because those two documents earned real approval once already — for Deere & Company, built in stages across one long working session. This SKILL.md and its bundled references are that session's judgment calls made permanent, so every future account gets the same quality bar without re-deriving it from scratch.

## Setup (fill once per install)

No API keys or org-specific values — the only install-time requirement is local tooling. Before first use, confirm each of these is on `PATH`:

| Tool | Used for | Check | Install |
|---|---|---|---|
| Node.js + `docx` npm package | Step 4, `build_docx.js` | `node -e "require('docx')"` | `npm install docx` (run once inside this skill's folder) |
| Python 3 + `python-docx` | Steps 5–6, `extract_docx_text.py` / `cross_check.py` | `python3 -c "import docx"` | `pip install python-docx` |
| LibreOffice (`soffice`) | Step 4, docx → PDF render for visual QA | `command -v soffice` | https://www.libreoffice.org/download/ (or your package manager: `brew install --cask libreoffice`) |
| Poppler (`pdftoppm`) | Step 4, PDF → JPEG page render | `command -v pdftoppm` | `brew install poppler` (or your package manager) |

Run this preflight before Step 4:
```bash
for bin in node python3 soffice pdftoppm; do
  command -v "$bin" >/dev/null 2>&1 || echo "MISSING: $bin — see Setup table above"
done
node -e "require('docx')" 2>/dev/null || echo "MISSING: npm package 'docx' — run: npm install docx"
python3 -c "import docx" 2>/dev/null || echo "MISSING: python package 'python-docx' — run: pip install python-docx"
```

If running inside Anthropic's code-execution sandbox (the `/mnt/skills/public/docx/...` environment is present), that environment's own `soffice.py` wrapper works in place of a bare `soffice` install — skip the LibreOffice/Poppler install steps above and use `python /mnt/skills/public/docx/scripts/office/soffice.py` instead, per Step 4.

## When to Use This Skill

- The user uploads or pastes a ledger-style account-plan markdown file — numbered sections, `[fact-id]` citations, register labels like `OBSERVED-INTERNAL` or `INTERPRETATION`, a methodology note with fact/contact counts — and wants it turned into something a sales leader can read.
- Phrases like "build the account plan for the sales team," "build the account plan for [Account]," "generate the SFDC account plan," "run the account plan pipeline on this."
- The user references a repeatable account-research pipeline that produces this markdown format and wants the next stage of the workflow run.

## What This Skill Assumes

**The input is already verified.** The source ledger `.md` comes from the user's own account-research pipeline, which has already done the fact-checking, citation, and quality-control work. This skill does not re-derive facts, does not go looking for new information about the account, and does not second-guess the source's claims. Its job is to transform and write, not to research.

**The reader is fixed.** VP of Sales, Director of Sales, and CRO, read as one audience. This reader isn't deciding what the AE does next — they're deciding whether to trust that the account is backed by real, structured work. Don't re-run a reader interview for this skill the way exec-brief-editor normally would; the calibration is locked. See `references/voice-spec.md` for what this means in practice, and the "VP / Director / CRO — Confidence in Rigor" row in exec-brief-editor's `references/editorial-frame-scoring.md` for the formal scoring exception it implies.

**No comparison to a prior plan.** Every source `.md` this skill receives comes from the same consistent pipeline going forward. There's no "we caught errors in the old version" story to tell — that framing was specific to migrating one account (Deere) off a legacy process. Describe only what this run found.

## Output

Every run produces exactly two files, generated independently from the same source and then checked against each other:

1. **`{Account_Name}_Account_Plan_Brief_{Date}.md`** — one-page executive brief
2. **`{Account_Name}_Account_Plan_{Date}.docx`** — full SFDC-formatted account plan

`{Date}` is ISO format (`2026-07-17`). Deliver both together, never one now and one later — the whole point is that they're two views of one verified source.

## Instructions

### Step 1: Ingest the source

Accept the ledger `.md` as an uploaded file or pasted directly in chat — either way, read the whole thing before doing anything else. You need the full picture to draft an accurate brief and a complete docx from the same material.

Locate the methodology / Plan Refresh Log section. That's where the fact count, contact count, lint/quality-check status, and any cross-validation percentage live — you'll need these verbatim for the brief's Data Integrity signal (still a dedicated element there) and for the docx's Plan Refresh Log entry (folded into prose, not a separate callout — see `references/voice-spec.md`).

### Step 2: Check for missing sections

Load `references/sfdc-template-map.md`. It lists every section the docx expects, where each one's content lives in the ledger `.md`, and the JSON schema `build_docx.js` consumes.

For any expected section or field with no corresponding content in the input: do not invent it, do not skip it, do not leave it blank. Use the literal value `"__MISSING__"` in the JSON — the build script renders it as a visible flagged placeholder automatically. A flagged gap reads as an honest limitation of the source data. A silently blank or fabricated section reads as either negligence or dishonesty, and this is a rigor-confidence document — either one defeats its purpose.

### Step 3: Draft the one-page brief

Load `references/voice-spec.md` in full before writing a single sentence. It is the calibration this skill runs on — the specific reader, the required structural moves (which differ slightly between brief and docx now — see voice-spec.md), the register — not generic advice. `references/voice-standards.md` fills in sentence-level mechanics where voice-spec.md is silent; where they conflict, voice-spec.md wins.

Apply exec-brief-editor's structural mechanics: BLUF thesis, three-line recommendation block, H2 sections with **So what:** blocks (see `references/brief-output-structure.md`), Next Steps footer, 60% word-count cap measured against the source `.md`.

Every brief must contain all three required structural moves from `voice-spec.md` — a Data Integrity signal, a pipeline/spend-alert callout, and risks framed as called out rather than hidden. These aren't per-account judgment calls; build them every time.

**As of North Star 3.0, this step always runs first, even on a request for the docx alone** (see `voice-spec.md`, "Per-Atom Routing"). While drafting, tag each sentence internally with the ledger fact-ID(s) it draws from — see `references/brief-output-structure.md`, "Internal Fact-ID Tagging." This tagging is never reader-facing; it exists solely so Step 4 can route atoms correctly and Step 3b (below) can verify them.

Run the checks in order:
```
python scripts/word_count_check.py source.md brief.md
python scripts/lint_gate.py brief.md --verbose
```
Two-strike rule on lint: one hit list, one rewrite pass targeting exactly those hits, then halt and surface to the user if violations remain. Never ship a brief that failed lint silently — see `references/lint-patterns.md` for what to look for and why each pattern matters.

### Step 3b: Verify the brief against the ledger

**New step, North Star 3.0.** Separate from drafting, the same way the lint gate is separate from voice rewrite — self-checking while writing tends to miss what a fresh, dedicated re-read catches. Load `references/brief-verification-worksheet.md` for the concrete procedure, mismatch categories, and report format — this is not a one-paragraph judgment call, it has the same level of structure as `lint_gate.py`'s patterns and `cross_check.py`'s figure categories.

Requires `{brief_filename_stem}.factmap.json` to exist first (produced during Step 3 — see `references/brief-output-structure.md`, "Internal Fact-ID Tagging"). Walk every tagged element and confirm it actually says what its cited fact-ID(s) say, using the five mismatch categories in the worksheet (numeric drift, direction reversal, unsupported certainty, dropped caveat that changes meaning, fabricated elaboration).

Two-strike rule, same discipline as lint: flag any mismatch found, one correction pass against the ledger, then halt and surface to the user if a mismatch remains. **Step 4 does not begin until this step passes clean** (or the user has explicitly overridden a halt with a written reason) — this check matters more than the mechanical cross-check in Step 6, it catches an error at the root, before it can propagate into the docx and have both documents confidently agree on something wrong.

### Step 4: Build the full account plan docx

With `references/sfdc-template-map.md` and `references/voice-spec.md` in mind, extract the account's content into a single JSON file matching the schema documented in `sfdc-template-map.md`.

**As of North Star 3.0, this is not an independent full write of the source.** Route atom-by-atom (see `voice-spec.md`, "Per-Atom Routing"):
- For any atom the brief already covers (check the fact-ID tags from Step 3): inherit the brief's own wording and grouping directly. Convert nothing for voice — North Star 3.0 uses contractions in both documents' prose now, so brief sentences drop in without a full-form conversion pass.
- For any atom the brief doesn't cover (cut for space, or belonging to a section the brief has no equivalent of — Key Risks and SWOT always fall here, since the brief dissolves risk atoms into its other sections and typically cuts SWOT entirely): atomize directly from the ledger using `references/atomization-method.md` — tag epistemic status, map each atom to a downstream destination, group by destination not topic, triage orphaned atoms explicitly, label only the payoff atom per group, choose prose vs. prose-plus-bullets by atom count.

The script handles any number of objectives, tracker actions, relationship-map contacts, and curriculum rows — never hardcode a row count or assume this account looks like any prior one.

Then run:
```
node scripts/build_docx.js account_data.json output.docx
```

Render and look at the result before moving on. Use whichever conversion path Setup identified as available:
```
# Local install (LibreOffice + Poppler on PATH):
soffice --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 90 output.pdf page

# Anthropic code-execution sandbox (has /mnt/skills/public/docx/... mounted):
python /mnt/skills/public/docx/scripts/office/soffice.py --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 90 output.pdf page
```
Check that flagged placeholders from Step 2 actually appear where expected, that no table has broken across a page badly, that all four SWOT quadrants are colored (not just two), and that the Plan Refresh Log's fact/contact/lint numbers match what Step 3's brief used for its Data Integrity signal. Also check the new Source Notes and Citation IDs appendix rendered — it's easy to build the JSON for it and forget to verify it actually appears at the end of the docx.

### Step 5: Lint the docx prose

The brief goes through `lint_gate.py` in Step 3. The docx never did until a 2026-07 diagnostic found why that's a problem: a docx built in a separate chat, from the same source, carried the ledger's own "Read:" labels forward nine times and used zero contractions in over a thousand words — and none of it was caught, because nothing was checking. Voice drift doesn't announce itself; it needs a gate, the same way the brief has one.

Extract the docx's actual text first — **never use `pandoc` for this.** `pandoc -t plain` renders tables as ASCII grids (`+-----+`), and the long hyphen runs in those borders get miscounted as em-dashes (confirmed during the same diagnostic: pandoc reported 1,219 "em-dashes" in a docx with zero real ones). Use the bundled extractor instead, which reads the docx's own paragraph/table structure directly, and tags table-cell lines distinctly from prose paragraphs (`[TABLE] ` prefix) so the contraction check below can tell them apart:
```
python scripts/extract_docx_text.py output.docx output.txt
python scripts/lint_gate.py output.txt --doc-type docx --verbose
```
`--doc-type docx` matters — it applies the em-dash threshold calibrated for docx-register prose (currently 0.15, same number as the brief, and skips the check under 50 sentences). **As of North Star 3.0, the contraction check runs in both modes**, not brief-only — it only evaluates narrative prose, table cells and data fields are excluded from the count in both modes (see `references/lint-patterns.md`, Pattern 16). Note that `Read:`/`Judgment:`/`Hypothesis:`/`Required response:` labels are required now, not banned — see the taxonomy in `voice-spec.md` before assuming any of those four are a problem, and see `references/atomization-method.md` for why most sentences in Current Situation should carry no label at all, only the one payoff sentence per group does.

Same two-strike rule as Step 3: one hit list, one rewrite pass targeting exactly those hits, then halt and surface to the user if violations remain. Pay particular attention to any "Ledger Data-Block Header" or "Ledger Citation Residue" hit outside the Source Notes appendix — these mean source structure leaked through instead of getting dissolved into prose, or a citation escaped the appendix it belongs in (see `references/voice-spec.md`, "Never Carry the Ledger's Own Scaffolding Forward").

### Step 6: Cross-check the docx against the brief

**As of North Star 3.0, this step's job has changed.** The brief and docx are no longer independently drafted (see Step 4 and `voice-spec.md`, "Per-Atom Routing"), so agreement between them is no longer a coincidence worth checking for its own sake — of course they agree on brief-covered atoms, one was built from the other on purpose. The check that actually matters now, verifying the brief was correct against the ledger in the first place, already happened in Step 3b. This step is the narrower, cheaper second half: confirming the docx faithfully carried forward whatever the brief established, catching transcription drift during import, not factual drift at the source.

Run:
```
python scripts/cross_check.py brief.md output.docx account_data.json
```
**The third argument is required for the full check.** The script reads real per-group provenance directly from `account_data.json`'s `_source`/`_brief_refs` fields (see `references/atomization-method.md`, "Recording Provenance") — it does not guess which sections are brief-derived from section names. An earlier version of this script tried the section-name-guess approach and got it wrong on the very first real run: Key Risks was hardcoded as "brief-derived" even though it has no brief equivalent, ever, which flagged every Key Risks figure as a permanent false mismatch. Don't reintroduce that pattern.

This checks bidirectionally: every dollar figure, percentage, date, and duration in the brief should appear somewhere in the docx (Direction 1, checked against the whole docx), and every such figure in docx groups explicitly tagged `_source: "brief"` should appear somewhere in the brief (Direction 2, checked only against those tagged groups — never a whole section, since a section like Current Situation can mix brief-sourced and ledger-sourced groups). It will not catch meaning-level drift — that is Step 3b's job, applied earlier in the pipeline, not this step's. It also will not normalize numeral-vs-word forms ("11 years" vs. "eleven years") or date formats ("10/30/2026" vs. "October 30, 2026") — known, accepted gaps in a deliberately mechanical check, not something to chase down here.

Any mismatch: halt, do not ship either file, and fix whichever one is wrong **against the source ledger `.md`** — the source is the system of record, not either downstream document. Re-run the check after fixing.

### Step 7: Deliver both files together

**Unchanged, and explicitly reaffirmed as of North Star 3.0**: every run always produces and delivers both files together, regardless of what the person asked for, even a request for the docx alone. The brief is now load-bearing for how the docx gets built (see Step 4), not just a nice-to-have companion, so it is never optional output. Save both to the outputs directory and present them in the same message. Briefly note what, if anything, got flagged as missing in Step 2 — the reader should know about a data gap, not discover it by noticing an odd callout box on their own.

## Working with Bundled Resources

| File | Load At |
|---|---|
| `references/voice-spec.md` | Step 3 (before drafting the brief) and Step 4 (before writing docx prose) — this is the skill's core asset, not optional background |
| `references/atomization-method.md` | Step 4, for any atom the brief doesn't cover (Key Risks and SWOT always; Current Situation and Competitive Landscape wherever the brief has gaps) |
| `references/sfdc-template-map.md` | Step 2 (missing-section check) and Step 4 (JSON schema + section mapping) |
| `references/voice-standards.md` | Background sentence-level mechanics; voice-spec.md overrides where they conflict |
| `references/lint-patterns.md` | Step 3 (after drafting the brief) and Step 5 (before linting the docx) |
| `references/brief-output-structure.md` | Step 3, for the brief's required shape (BLUF, recommendation block, So-what blocks, Next Steps), and for the fact-ID tagging convention used in Step 3b and Step 4 |
| `references/brief-verification-worksheet.md` | Step 3b, the concrete procedure, mismatch categories, and report format |
| `scripts/build_docx.js` | Step 4 |
| `scripts/word_count_check.py` | Step 3 |
| `scripts/lint_gate.py` | Step 3 (`--doc-type brief`, the default) and Step 5 (`--doc-type docx`) |
| `scripts/extract_docx_text.py` | Step 5, always — never substitute `pandoc` here (see Step 5 and Pattern 12 in `lint-patterns.md`) |
| `scripts/cross_check.py` | Step 6 |

Step 3b (verify the brief against the ledger) has a bundled worksheet now (`references/brief-verification-worksheet.md`) — it's a semantic re-read, not a mechanical check, but it has the same level of structure as the mechanical ones: named mismatch categories, a procedure, and a report format.

**Working files that never get delivered.** `{brief_filename_stem}.factmap.json` (Step 3, tagging) and any notes produced during Step 3b's re-read stay in the working directory. Neither is copied to the outputs directory or presented to the user — they're scaffolding for routing and verification, not deliverables, the same way `brief-output-structure.md`'s "never reader-facing" rule already treats the tags themselves.

## Why This Isn't Just exec-brief-editor Twice

exec-brief-editor's default posture is CUT — most sections don't earn their place, and methodology is the first thing to go. That's right for a reader who needs to know what to do next. It's wrong for a reader whose actual question is "can I trust this account plan," where the methodology section is often the single most important thing in the document. This skill bundles its own copies of the generic mechanics precisely so a future change to exec-brief-editor's general cutting logic can't quietly change what this skill produces — the two are siblings, not one calling the other.

Since North Star 3.0, this distinction sharpens rather than disappears: the docx *inherits* the brief's wording and grouping for whatever the brief happens to cover, but for everything the brief's own default-to-CUT posture removed, the docx still owes this reader full coverage, and gets there through the atomization method rather than exec-brief-editor's cutting logic. The two skills still make opposite calls about the same material; North Star 3.0 just makes the docx explicitly reuse the brief's good writing where it exists, instead of re-deriving it independently and hoping the two happen to agree.
