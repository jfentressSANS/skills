# Voice Spec: SANS Account Plan Deliverables

**Source:** Originally distilled from the account-plan work built and approved for Deere & Company (July 2026). Revised 2026-07 against a hand-edited "North Star 2.0" reboot of that same document — tighter, and using an explicit Read:/Judgment:/Hypothesis:/Required response: taxonomy that the original calibration had banned. Where the two versions disagree, this file follows the reboot; it's the more recent, more deliberately-edited ground truth. This file is not generic executive-writing advice.

**Authority:** `references/voice-standards.md` (copied from exec-brief-editor) covers generic sentence-level mechanics — sentence length, contractions, active voice, concrete nouns. Use it as background. Wherever this file and that one disagree, this file wins, because this file is specific to what actually earned approval and that one is generic.

---

## Version History and Current Calibration

**North Star 1.0** (original calibration): banned the Read:/Judgment:/Hypothesis:/Required response: labels as leaked ledger scaffolding, ran full-form throughout.

**North Star 2.0** (2026-07 reboot, the hand-edited Deere reference document): introduced the four-part taxonomy as required, not banned. Measured at 100% full-form (zero contractions), near-zero em-dash usage (0.013/sentence). This is the version most of this file still describes below, and it remains the historically accurate description of that specific document. It is superseded as the active drafting target by North Star 3.0, below, but is not deleted from this file, because it's still the correct citation for anyone asking "what did the approved reference document actually look like."

**North Star 3.0** (2026-07-20, this revision): supersedes 2.0 as the live calibration every new account plan is drafted against. Two structural changes and one voice change, all permanent, all universal (not Deere-specific):

1. **Per-atom routing between the brief and the docx.** The two deliverables are no longer independently drafted. The brief is now built first, always. Every sentence in the brief gets tagged at drafting time with the ledger fact-ID(s) it draws from (see "Per-Atom Routing," below). When the docx is built, any atom the brief already covered inherits the brief's wording and grouping directly. Any atom the brief didn't cover (cut for space, or belonging to a section the brief has no equivalent of, like Key Risks or SWOT) gets atomized directly from the ledger using the method in `references/atomization-method.md`.
2. **The atomization method itself**, for all ledger-sourced (non-brief-covered) material: tag epistemic status, map every atom to a downstream destination elsewhere in the docx, group atoms by destination rather than by source topic, triage any atom with no destination, label only the payoff (Judgment) atom per group, and choose prose vs. prose-plus-bullets by atom count per group. Full procedure in `references/atomization-method.md`. This applies to Key Risks and SWOT too, not just Current Situation, since those sections have no brief equivalent to route from and always go through the full method.
3. **Contractions, flipped.** North Star 2.0 measured 100% full-form. North Star 3.0 expects contractions throughout narrative prose (Current Situation, Account Vision, Competitive Landscape footer, and anywhere else running prose appears), the same register the brief already uses. Plain data fields — Plan Header values, table cells, dates, citation IDs — are exempted from this, contractions don't meaningfully apply to a date or a dollar figure, so the check doesn't run there at all. See `lint-patterns.md` for the updated, flipped contraction check.

Everything else 2.0 established — the taxonomy, the em-dash threshold, the color system, the "full coverage, not full transcription" principle, the reader calibration — carries forward unchanged into 3.0.

**Validation status:** North Star 3.0, and everything under it (per-atom routing, the atomization method, the `_source`/`_brief_refs` schema, the verification worksheet), has been reasoned through and run exactly once, against Deere. None of it has been confirmed against a second, differently-shaped account ledger yet. Treat "universal" and "agnostic" language in this file and in `references/atomization-method.md` as design intent under active validation, not a demonstrated fact, until a second and third account have actually gone through the full pipeline.

---

## Per-Atom Routing

**The brief is built first, always**, even on a request for the docx alone. Both files are still delivered together regardless of what was asked for (unchanged rule, see SKILL.md), but the *generation order* is now fixed: brief, then docx, because the docx's Current Situation and Competitive Landscape sections are partially derived from the brief's own drafting, not written independently of it.

**Fact-ID tagging happens at brief-creation time, not after the fact**, in a concrete sidecar file, `{brief_filename_stem}.factmap.json` — see `references/brief-output-structure.md`, "Internal Fact-ID Tagging," for the exact schema. This is what makes routing mechanical rather than a reverse-engineered guess: by the time the docx gets drafted, there's already a record of exactly which ledger atoms the brief touched, and which it didn't.

**Routing is per-atom (or per-group), not per-section, and is recorded as real data, not guessed from section names.** A single docx section can, and for Deere did, blend brief-sourced groups with ledger-atomized groups. Current Situation's Voucher/Timing, Talent Pipeline, and ICS Gap groups mirrored the brief's own three H2 sections directly; its Buying Intent/Dormancy group had no brief equivalent and was atomized straight from the ledger via `references/atomization-method.md`. This is recorded per-group in `account_data.json` via `_source` ("brief" | "ledger") and `_brief_refs` (which brief element(s), by the same IDs the fact-map uses) — see `references/atomization-method.md`, "Recording Provenance," for the exact fields. **Do not approximate this by section name.** The first implementation of the downstream verification check (`cross_check.py`) tried exactly that — a hardcoded set of "brief-derived section names" — and it broke on the very first real run: Key Risks got listed as brief-derived even though it never is, which flagged every Key Risks figure as a permanent false mismatch, and Current Situation's own internal mixing produced partial false positives the section-name guess couldn't see either. Read real per-group tags; don't infer from where a paragraph happens to sit.

**Sections with no brief equivalent** (Key Risks, SWOT, and any future section the brief's own editorial-frame scoring cuts entirely) always run through the full atomization method, independent of the brief, because there's nothing to route from. These never carry `_source: "brief"` on any group, by construction — there's no need to special-case them by name anywhere downstream.

**Verification is two-part, not one check standing in for both jobs:**
1. **Brief-against-ledger** (semantic, judgment-based): `references/brief-verification-worksheet.md` — a dedicated re-read pass, separate from drafting, confirms every fact-ID-tagged element actually says what its cited fact(s) say, using five named mismatch categories (numeric drift, direction reversal, unsupported certainty, dropped caveat, fabricated elaboration). This is the check that matters most, it catches an error at the root before it can propagate into the docx. Two-strike rule applies, and Step 4 is gated on this step passing.
2. **Docx-against-brief** (mechanical, cheap): `scripts/cross_check.py brief.md docx.docx account_data.json` — reads `_source`/`_brief_refs` directly from the JSON to know exactly which docx content to check, then verifies bidirectionally: every number in the brief appears somewhere in the docx, and every number in a `_source: "brief"`-tagged group appears somewhere in the brief. This doesn't catch meaning-level drift, it only catches transcription slips during import, that's a deliberately cheap, narrow job, not a substitute for check #1. It also doesn't normalize numeral-vs-word forms or date formats — a known, accepted gap in a mechanical check, not a bug to chase.



## The Locked Reader

VP of Sales, Director of Sales, and CRO — read together as one audience, not three. This reader is not deciding what the AE should do next. They're deciding whether to trust that the work behind the account is sound: well-researched, well-structured, and something the AE, their manager, and leadership are all looking at the same way.

This is a different decision than the standard "VP/Director" calibration in exec-brief-editor's scoring rubric, which optimizes for execution decisions. Do not default back to that read. A section proving the plan's own quality control is not filler for this reader — it is the single highest-value thing in the document. See the "Confidence in Rigor" row added to `editorial-frame-scoring.md` for the formal scoring exception this implies.

Practical test before writing anything: if a sentence would only matter to someone about to make a next call to the customer, it's AE-level detail — it belongs in the full docx's working sections, not the compressed brief, and even in the docx it should read as evidence supporting the plan's credibility, not as a script.

---

## Required Structural Moves — Scope Differs by Deliverable

The original calibration had three required moves applying to both deliverables. As of the North Star 2.0 reboot, the scope split:

**Docx: two of three retired.** The Data Integrity callout and the Pipeline/Spend Alert callout no longer exist as dedicated boxes in the docx — the fact/contact/lint signal now lives in the Plan Refresh Log's prose, and the pipeline information folds into the Account Metrics Read: paragraph. This works specifically *because* the docx has the new Source Notes and Citation IDs appendix carrying the underlying trust signal in a different form (categorized citations, not a stated fact count).

**Brief: Data Integrity signal remains required, unchanged.** The brief has no citation appendix — bracket IDs and register tags stay out of it entirely (see the comparison table below) — so it has nothing to substitute the trust signal with. Keep building it as a prominent, explicit element the way the original calibration specified. The Pipeline/Spend Alert was never a separate box in the brief the way it was in the docx; it already lived in the BLUF/recommendation block, and continues to.

**Risks framed as called-out, not hidden** is required in both, unchanged:

State each risk plainly, then say what the plan does about it. Never soften a risk into a euphemism, and never list risks without a response. The rhetorical move that works here is structural honesty: a reader trusts a document more, not less, when it names its own weak points before being asked. In the docx's North Star 2.0 register, this is now expressed through the Read:/Required response: labels rather than an unlabeled bullet — the label changed, the requirement didn't. The brief can keep its existing unlabeled bullet form, or adopt the same labels if it reads naturally; nothing forces the brief to match the docx's exact labeling mechanically.

---

## The Opening (BLUF / Account Vision)

The Deere brief opened: *"Deere's SANS spend is down 97% from its 2023 peak. This plan says it's a budget freeze, not a lost account, and names what unsticks the $200K deal by October."*

That's an example of the register — a real number, a direct claim about what the situation actually is, and a concrete implication — not a fill-in-the-blank template. Don't force a future account into the specific "X is down Y%, this plan says it's a Z not a W" shape if that's not the account's actual story. Some accounts will be expanding, not declining; some will have no single dramatic number. Write the opening sentence that's true for this account, in this register: specific, direct, no hedging, states the plan's actual thesis rather than describing the document.

What must carry over regardless of the account's specific shape: a real number in the first sentence wherever one exists, and a clear statement of what the plan concludes — not what it examines.

---

## Sentence-Level Deltas From Generic Voice Standards

Everything in `voice-standards.md` applies. These are additions specific to account-plan work:

- **No forecast-speak.** This reader isn't reading a pipeline forecast. Avoid language that reads as a number the rep is committing to hit (avoid "we will close," prefer "the plan targets" or the objective table's own Target Value column doing that work).
- **Trust-building specifics over persuasive specifics.** Numbers like $62,951, 5.3%, 191 facts work because they're falsifiable and precise, not because they're impressive. Prefer the number that proves rigor over the number that sounds good.
- **Label the epistemic status of every claim using the four-part taxonomy below — this replaced hedge-word-only phrasing as of the North Star 2.0 reboot.**

---

## The Read:/Judgment:/Hypothesis:/Required response: Taxonomy

**This reverses the previous version of this file, which banned these exact labels as leaked ledger scaffolding.** That ban was calibrated against one bad example: a docx that carried the ledger's single, undifferentiated `Read:` label forward nine times as leftover residue, with no real distinction being made. The North Star 2.0 reboot uses four *different* labels, each doing a specific, consistent job — and reverse-engineering every instance across the reboot document showed the same four-way split every time, not random labeling. That's a taxonomy, not scaffolding, and it's now required, not banned.

- **Read:** — a synthesized statement of what the source facts show, woven into one statement rather than listed separately. Grounded, not evaluative.
- **Judgment:** — an explicit evaluative call the plan is making, distinguished from the Read: facts above it. This is the label for what the old rule called "hedging the claim" — use the label now, not just a hedge word.
- **Hypothesis:** — a theory explicitly flagged as *not yet confirmed*. Distinguished from Judgment: by confidence level — a Judgment is a call the plan is standing behind; a Hypothesis is flagged precisely because it isn't confirmed yet.
- **Required response:** — the mandated action tied to a named risk. This is what "state the risk, then what the plan does about it" (see the one remaining required structural move above) looks like labeled explicitly.

**How to tell this apart from the banned failure mode:** the test isn't "does the word Read appear" — it's whether the label is doing real classification work or just marking where the ledger happened to break paragraphs. A single generic Read: label with no Judgment/Hypothesis/Required-response counterpart anywhere nearby, applied mechanically to every paragraph, is the old failure mode. Four labels used consistently, each reserved for a distinct epistemic status, is the current requirement. When drafting, ask which of the four statuses a given sentence actually has — don't default to Read: as a catch-all the way the flawed docx defaulted to it.

**What's still banned, unchanged:** `Data — [Topic]:` headers opening a paragraph (that's ledger bookkeeping structure, not one of the four labels), and bracket fact-IDs (`[spend-2024]`) or register tags (`OBSERVED-INTERNAL`, `INTERPRETATION`) anywhere in the main body — those still only belong in the Source Notes and Citation IDs appendix (see `sfdc-template-map.md`).

---

## What Changes Between the Brief and the Full Docx

Same voice, same one required structural move, different depth and different mechanics. As of North Star 3.0, they are also no longer independently drafted — see "Per-Atom Routing," above — but the two deliverables still differ in depth, structure, and purpose:

| | Brief | Full Docx |
|---|---|---|
| Word count | ≤60% of source .md, refire/halt rules apply | No cap — full section coverage |
| Structure | BLUF, recommendation block, 4–5 H2 max, Next Steps footer | Fixed 12-section SFDC template plus the Source Notes and Citation IDs appendix, every section present |
| Missing data | Cut ruthlessly per editorial-frame scoring | Flag with a placeholder — never cut a required section |
| Citations | Never in the reader-facing text — but every sentence is tagged internally with its source fact-ID(s) at drafting time, for routing and verification | Banned from the main body; required in the appendix |
| Content source | Drafted first, directly from the ledger | Drafted second — inherits the brief's wording/grouping for any atom the brief covers; atomizes directly from the ledger (see `references/atomization-method.md`) for everything else |
| Purpose | 30-second confidence read | The actual working document, ready to sync to Salesforce |

They are not independent views of the source anymore, and the cross-check step's job has changed accordingly (see "Per-Atom Routing," above): it no longer verifies two parallel drafts agree by coincidence, it verifies the docx faithfully carried forward what the brief already established, and that the brief itself was correct against the ledger in the first place.

---

## "Full Coverage" Means Every Section, Not Every Sub-Fact Gets Equal Space

The docx has no word cap, and that's correct — it's the working document, not a 30-second read. But "no cap" has been misread once already as license to give every sub-topic in the source ledger its own full paragraph, transcribed at roughly the ledger's own length. That's not full coverage. That's full *transcription*, and it's a different thing with a different (worse) result.

**What actually happened:** the source ledger's Current Situation material has eight Data/Read sub-topics (financials, strategic direction, cyber org, talent model, product/OT, regulatory, buying signals, relationship history). One version gave five of them their own paragraph — roughly 440 words total — and folded the other three into single clauses inside related paragraphs. A different run gave all eight their own full paragraph — roughly 1,070 words — and came out substantially longer and, because the ledger's own per-topic structure was preserved that literally, also triggered the scaffolding-leakage problem the taxonomy above now governs.

**The current calibration anchor is the North Star 2.0 reboot: roughly 1,610 words and 5 pages total for the Deere account**, down from an earlier full version's 3,059 words and 8 pages covering the same account. That's the compression level to match — not a hard per-account word count (a more complex account will run longer, a simpler one shorter), but the *ratio* of compression relative to source material.

**The actual rule:** apply the same "does this reader need this, and at what depth" judgment *inside* each section of the docx that the brief applies *across* the whole document. Full coverage means the reader can find something about every topic if they look — not that every topic gets identical, undifferentiated weight regardless of how decision-relevant it is. A sub-topic that doesn't earn its own paragraph can usually still earn a clause inside a related one, or a line in a table elsewhere in the document. It rarely needs to disappear entirely, and it rarely needs a full paragraph either.

**A rough calibration, not a hard cap:** if a single docx section is running toward double what a comparably-complex account should need, that's a signal to go back and ask which sub-topics actually earned full paragraph treatment versus which ones are along for the ride because the source happened to include them.

---

## The Color System

Table headers are navy (`1F3864`) by default; Customer Landscape and Competitive Landscape tables use green (`D9EAD3`) instead — this is the one deliberate header-color exception, not a per-account choice. SWOT quadrants are each a single uniform color, header and content matching: Strengths green (`E2EFDA`), Weaknesses yellow (`FFF2CC`), Opportunities blue (`DEEAF1`), Threats peach (`FCE4D6`) — see `build_docx.js` for the exact hex values, which are already wired in and don't need to be re-specified per account. Every long multi-row table (Objectives, Tracker, Relationship Map, Curriculum, Refresh Log) zebra-stripes automatically. None of this is something to decide when drafting a new account's JSON — it's fixed in the script, the same way the template structure is.
