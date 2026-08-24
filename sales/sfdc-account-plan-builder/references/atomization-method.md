# Atomization Method

**Status:** Permanent, intended to be universal. Introduced 2026-07-20 during the Deere North Star 3.0 revision.

**Validation status — read before assuming this is proven generic:** this method has been validated exactly once, against Deere's ledger. It has not yet been run against a second, differently-shaped account ledger. Every instruction below is written as if it generalizes, but that's a design intent, not a demonstrated fact — the same honesty standard `voice-spec.md` applies to North Star 2.0 ("measured against this one document") applies here: treat this as *validated against one account*, not confirmed universal, until it's actually run against a second and third ledger with a genuinely different shape (different number of Current Situation sub-topics, a Key Risks section with different density, a source ledger that doesn't cleanly split into 4-ish destination groups). Update this status line once that happens.

**Why this exists:** A diagnostic run against Deere's Level 2 build found that Key Risks read cleanly while Current Situation read as dense and hard to action, even though Current Situation carried *more* raw intelligence (31 distinct atoms vs. 19). The cause wasn't verbosity. It was that Current Situation's four topic-based paragraphs each packaged 6-10 facts that fanned out to 3-5 *different* downstream destinations (a Tracker action, a Curriculum row, a SWOT bullet, all mixed into one block with no signal for which sentence fed what), while each Key Risks bullet packaged 2-4 facts feeding only 1-2 destinations. This method generalizes the fix.

---

## The procedure

Run this against every source ledger before drafting any narrative section of the docx.

### Step 1: Atomize

Break the section's source material into individual atomic facts and calls, one clean sentence each. An atom is the smallest unit that means something on its own. "Deere's FY2025 revenue fell to $45.684B, down 11.7%" is one atom, not two, even though it carries two numbers, because neither number means anything without the other. "The security org grew from 32 to 230" and "the CISO calls talent the hardest problem his team solves" are two atoms, not one, because either can be dropped or kept independently of the other.

### Step 2: Tag epistemic status

Every atom gets exactly one of four tags, using the same taxonomy already required in the docx's main body (see `voice-spec.md`):

- **Read** — a synthesized statement of what the source shows
- **Judgment** — an explicit evaluative call the plan is making
- **Hypothesis** — a theory flagged as not yet confirmed
- **Required response** — a mandated action tied to a named risk or guardrail

### Step 3: Map every atom to a downstream destination

For each atom, identify what elsewhere in the docx actually depends on it: a specific Objective, a specific Tracker action, a Relationship Map row, a Curriculum row, a SWOT bullet, a Competitive Landscape point, another section's Judgment. Write this down explicitly, don't hold it as an impression. An atom can feed more than one destination.

### Step 4: Group atoms by destination, not by source topic

This is the actual fix, and it's the step Current Situation skipped. Don't organize atoms into paragraphs by what they're *about* (financials, org structure, product security, buying intent). Organize them by what they *feed*. Atoms that all support the same Objective, or the same cluster of Tracker actions, belong in the same group, even if they came from different parts of the source ledger and cover different topics on their face. The resulting groups are usually recognizable as the plan's real storylines, not the ledger's original section headers.

### Step 5: Triage orphaned atoms

Any atom with no downstream destination found in Step 3 needs an explicit decision, not silence:

- **Cut it.** True but genuinely inert, nothing elsewhere in the plan turns on it. (Example: a macro financial data point that doesn't inform any timing decision.)
- **Cut it as a duplicate.** It already lives somewhere else in the docx in its own right (a table cell, another section); repeating it in narrative prose adds nothing.
- **Give it a real destination.** If the atom reads like something a seller genuinely needs before acting, most often a caution or guardrail, and nothing currently captures it, create one. A Key-Risks-style item (Read + Required response) is usually the right shape for this, since "here's a fact plus what to do about it" is exactly the form Key Risks already handles well.

Never leave an atom drifting with no destination and no decision recorded about why.

### Step 6: Label only the payoff atom per group

Don't label every atom's epistemic status inline (that recreates the density problem). Each group gets exactly one labeled sentence, its Judgment, the atom that states what the group actually means, not just what it contains. Every other atom in the group runs as unlabeled connected prose supporting that Judgment.

### Step 7: Choose prose, or prose-plus-bullets, by atom count

- **Groups with roughly 6 atoms or fewer:** one flowing paragraph, labeled Judgment sentence included inline.
- **Groups with roughly 7+ atoms:** a short prose lead-in (usually the Judgment atom, 1-2 sentences) followed by 3-5 bullets carrying the supporting facts. Uniform prose at this density recreates the original problem; uniform bullets at low density makes the section feel over-fragmented and loses the connective narrative the brief already does well. Match the format to the actual atom count, per group, not per section.

---

## Where this sits relative to brief-derived content

This method is what governs any atom **not** covered by the executive brief (see `voice-spec.md`, "Per-Atom Routing"). For atoms the brief already covers, the brief's own wording and grouping is inherited directly rather than re-atomized from scratch, since the brief already did steps 4-7 for that material as part of its own drafting. This method exists specifically for the material the brief didn't have room for, plus for sections the brief has no equivalent of at all (Key Risks, SWOT), which always run through the full method independent of the brief.

---

## Recording Provenance: `_source` and `_brief_refs`

Every group produced by this method, or inherited from the brief, gets tagged with two metadata fields in `account_data.json`. These are not rendering content — `build_docx.js` reads and discards them — they exist so `scripts/cross_check.py` knows exactly which docx content to check against the brief, instead of guessing from section names (see the revision history in `cross_check.py` for what went wrong the one time section-name guessing was tried: it flagged Key Risks, which has no brief equivalent, ever, as a permanent false mismatch).

```json
{ "text": "...",  "_source": "brief" | "ledger", "_brief_refs": ["h1_thesis", "h2:Exact Brief Section Title", ...] }
```

or, for the lead-plus-bullets shape:

```json
{ "lead": "...", "bullets": ["...", "..."], "_source": "brief" | "ledger", "_brief_refs": [...] }
```

- **`_source: "brief"`** — this group's wording and grouping was inherited from the brief. `_brief_refs` names which brief element(s) it came from, using the same IDs the brief's own fact-map sidecar uses (see `brief-output-structure.md`, "Internal Fact-ID Tagging"): `h1_thesis`, `recommendation_block`, `h2:<exact title>`, or `next_steps`.
- **`_source: "ledger"`** — this group was atomized fresh from the ledger via this method, with no brief equivalent. `_brief_refs` is an empty array. `cross_check.py` never checks this group's figures against the brief — a ledger-only group's own facts (like Deere's buying-intent/dormancy material) having no counterpart in the brief is expected, not an error.
- **A plain string with no wrapper object** (no `_source` tag at all) is treated as ledger-only by default — the safe assumption, since an untagged group is never checked against the brief either way.

This is currently only implemented for `current_situation_paragraphs`, the one section with genuinely mixed brief/ledger provenance. Sections that are always one or the other (Key Risks, SWOT: always ledger; nothing currently: always brief) don't need per-group tagging, since there's no mixing to disambiguate — but if a future account's ledger produces a section with the same kind of mixing, the same two fields are the pattern to extend to it.
