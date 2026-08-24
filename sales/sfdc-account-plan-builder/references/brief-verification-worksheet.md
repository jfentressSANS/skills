# Brief Verification Worksheet (Step 3b)

**Purpose:** Give the brief-against-ledger check (SKILL.md Step 3b) the same level of concreteness the mechanical checks already have. `lint_gate.py` has twelve named patterns with regexes and fix instructions. `cross_check.py` has explicit figure categories. Step 3b, until this file existed, had one paragraph saying "confirm the brief says what the ledger says" — the least specified step in the pipeline, despite being the one that catches errors at the root before they propagate into the docx. This file is what actually gets checked, and how.

**Validation status:** written and reasoned through once, against Deere's ledger and brief. Not yet exercised against a second account's fact-map. Treat the five mismatch categories below as a reasonable starting taxonomy, not a closed, proven-complete list — a differently-shaped ledger may surface a mismatch type not named here.

---

## Precondition

This step requires `{brief_filename_stem}.factmap.json` to already exist (produced during Step 3 drafting — see `brief-output-structure.md`, "Internal Fact-ID Tagging"). If it doesn't exist, or is missing tags for elements that clearly make specific claims, that's itself a finding — go back to Step 3, not forward to Step 4.

## Procedure

1. Load the fact-map. For each tagged element (`h1_thesis`, `recommendation_block`, each `h2:...`, `next_steps`):
2. Retrieve the raw fact text for every `fact_id` it cites, from the ledger's own citation/fact section.
3. Re-read the brief's actual text for that element against the raw fact(s). Do this fresh — don't reuse the judgment made while drafting; that's exactly the self-checking-while-writing failure mode this step exists to avoid (see SKILL.md Step 3b's framing, same reasoning as why the lint gate runs after voice rewrite, not during it).
4. Classify what you find using the five categories below. An element can be clean, or can produce one or more hits.
5. Compile a hit list in the same format `lint_gate.py` uses (pattern name, location, matched text, description, fix) — see "Report Format," below.
6. Two-strike rule, same discipline as lint: hits found → one correction pass against the ledger, targeting exactly those hits → re-verify → if hits remain, halt and surface to the user with the full hit list. Never silently ship a known mismatch.

**Gate:** Step 4 (building the docx) does not begin until this step passes clean, or the user has explicitly overridden a surfaced halt with a written reason. Nothing currently enforces this mechanically — there's no script that blocks Step 4 from running — so this is a discipline to hold deliberately, the same way "never ski silently bypass a lint failure" is a discipline `lint_gate.py`'s hit list depends on a human actually respecting.

---

## The Five Mismatch Categories

### 1. Numeric Drift
**What it is:** A number in the brief doesn't match the number in the cited fact. "Nine months" in the ledger becomes "eight months" in the brief.

**Why it matters more here than elsewhere:** under per-atom routing, this number doesn't just live in the brief — it propagates into the docx wherever that element's group is tagged `_source: "brief"`. An error caught here is caught once. An error missed here is now wrong in two documents that agree with each other, which is precisely the failure mode independent-drafting-plus-cross-check used to catch and per-atom routing no longer does on its own.

**Fix:** Correct the brief against the ledger's actual figure. If the ledger itself is ambiguous or the ledger's own citation is wrong, that's a ledger problem — flag it, don't quietly pick a number.

### 2. Direction Reversal
**What it is:** The brief states a trend in the opposite direction from the source. Source says a metric declined; brief says it grew. Less common than numeric drift, but more damaging when it happens, since it inverts the claim rather than just mis-stating its magnitude.

**Fix:** Correct the direction. Re-check every other claim in the same element — a direction reversal often means the drafting pass misread the underlying fact more broadly, not just on this one sentence.

### 3. Unsupported Certainty
**What it is:** The source ledger flags something as a Hypothesis (explicitly unconfirmed), but the brief states it as settled fact, dropping the hedge.

**Example:** Ledger: "Hypothesis — a 2024 budget freeze doesn't explain accounts that lapsed years earlier." Brief, if it dropped the hedge: "The 2024 budget freeze isn't the real cause of the dormancy." The second version claims something the source doesn't actually establish.

**Fix:** Restore the epistemic status. This doesn't mean the brief has to use the literal word "Hypothesis" (see `voice-spec.md` — the brief's register doesn't require the four-part label taxonomy the docx uses), but the sentence has to read as unconfirmed if the source says it's unconfirmed. "Read it as suggesting..." or "It looks like..." can carry this without the formal label.

### 4. Dropped Caveat That Changes Meaning
**What it is:** The source has a boundary condition or qualifier that isn't just supporting detail, it changes what the claim actually licenses. Compression that drops it isn't tightening, it's a different, less defensible claim.

**Example, drawn from this account's own ledger:** the source says the FTC settlement is "a timely and legitimate reason to raise product security now, though the approach should ask, not assert, since no source frames the settlement itself as a security problem." A version that keeps "timely reason to raise product security" but drops "ask, not assert" has quietly upgraded a suggested opening into an assertion the source explicitly warned against making.

**How to tell this apart from ordinary, healthy compression:** ask whether the dropped material changes what the reader is licensed to do or claim, versus whether it just changes how much support the reader sees for a claim that's otherwise unchanged. Losing supporting evidence for a stable claim is normal brief-writing. Losing the condition that makes a claim safe to act on is this category.

**Fix:** Either restore the caveat in compressed form (usually a clause, not a full sentence) or, if the brief's word budget genuinely can't carry it, flag the omission explicitly rather than silently dropping something load-bearing.

### 5. Fabricated Elaboration
**What it is:** The brief states a specific detail (a name, a number, a causal link) that doesn't trace to any cited fact-ID at all. Distinct from numeric drift (which requires an actual cited number to drift from) — this is content invented where none of the underlying facts contain it.

**Fix:** Cut the detail, or trace it to a real fact-ID if one exists that wasn't tagged. Never leave a specific, falsifiable-sounding claim in the brief with nothing behind it.

---

## Two Categories That Look Like Mismatches But Aren't

**Legitimate synthesis.** An element citing multiple fact-IDs and combining them into one sentence is the brief doing exactly what a brief is supposed to do. Don't flag a well-constructed synthesis as a mismatch just because it doesn't read like any single cited fact verbatim — check whether the synthesis is *true to* the combined facts, not whether it *echoes* any one of them.

**Dangling reference.** A `fact_id` in the fact-map that doesn't exist anywhere in the ledger's citation section — this is a tagging error, not a content mismatch. Report it as its own line item ("Dangling Reference: `fact-id-that-does-not-exist` cited by `h2:...`, not found in ledger"), separate from the five content categories above, since the fix is different (correct the tag) from a content fix (correct the claim).

---

## Report Format

Mirror `lint_gate.py`'s hit format so a reviewer sees a consistent shape across every gate in this pipeline:

```
[Category] Element: h2:<title>
  Cited fact-ID(s): <fact-id-1>, <fact-id-2>
  Brief text: "<the sentence or clause in question>"
  Source text: "<what the cited fact(s) actually say>"
  Why it fails: <one sentence>
  Fix: <specific correction>
```

Compile every hit before starting corrections — fix all of them in one pass, not one at a time, then re-verify the whole element list once, not after each individual fix.
