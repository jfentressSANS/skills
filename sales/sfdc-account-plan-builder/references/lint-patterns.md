# Lint Patterns: AI-Tell Detection and Blocking Rules

**Purpose:** Catch patterns that mark output as AI-generated before it reaches the reader. Every pattern below has been documented as a high-frequency LLM output signature. Hard hits block publish. Two-strike rule applies. Halt on second failure.

---

## The Two-Strike Rule

1. Run lint on the rewritten output.
2. If any hard hit fires: collect the full hit list, pipe it back into the rewriter with the instruction "fix these specific violations," and rerun once.
3. If the second pass also fails: **HALT**. Surface the failing draft to the user with the complete hit list. Never silently bypass a lint failure. The user must edit or explicitly override with a written reason.

**Why no silent bypass:** A silently bypassed lint failure means the AI-tell reaches the reader. The point of the lint gate is reader protection, not process compliance. Silent bypass defeats the entire purpose.

---

## Hard-Hit Patterns (Block on Any Single Hit)

### Pattern 1: Reversal Cliffhanger
**What it is:** A sentence that sets up a negative claim, then immediately reverses it for effect. LLMs use this structure constantly because it creates artificial drama.

**Example:** *"The problem wasn't the technology. The problem was the people."*

**Regex:**
```
\b(wasn't|isn't|is not|was not)\s+(the|a|an|about)\s+\w+\.\s+(it|that|the)\s+\w+\s+(was|is)
```

**Why it fails:** Real executives do not write this way. The structure signals LLM output immediately to any reader who writes professionally.

**Fix:** State the actual claim directly. *"The core problem was organizational, not technical."*

---

### Pattern 2: Antithesis Tic
**What it is:** The "it's not just X, it's Y" construction. LLMs reach for this to create the appearance of nuance where none exists.

**Example:** *"This isn't just a sales problem. It's a culture problem."*

**Regex:**
```
it'?s not (just )?\w+[,.\s\-—]+\s*(it'?s|it is)\s+\w+
```

**Why it fails:** The construction implies a non-obvious distinction that the sentence rarely delivers. Readers recognize the rhetorical scaffolding and discount the content.

**Fix:** State both things directly. *"This is a culture problem that's showing up in sales numbers."*

---

### Pattern 3: Throat-Clearing Opener
**What it is:** Opening sentences that orient the reader to the document rather than delivering information. LLMs insert these because they mimic essay structure.

**Examples:**
- *"In today's competitive landscape..."*
- *"As we all know..."*
- *"It's no secret that..."*
- *"In this report, I will..."*
- *"Before we begin..."*

**Regex:**
```
^\s*(In today's|As we all know|It's no secret|In this (article|report|document|brief)|Let me start by|Before we begin|It goes without saying|At its core)
```

**Why it fails:** The reader already knows they are reading the document. Orienting sentences delay the information and signal that the writer is filling space.

**Fix:** Delete the opener. Start with the first piece of actual information.

---

### Pattern 4: Recap Signature
**What it is:** Summary language that signals the document is ending before it needs to. LLMs add this because training data includes academic and journalistic conventions that require conclusions.

**Examples:**
- *"In summary..."*
- *"To recap..."*
- *"Key takeaways..."*
- *"In conclusion..."*

**Regex:**
```
\b(In summary|To recap|Let's review|Key takeaways|In conclusion|To sum up|As a summary|Summing up)\b
```

**Why it fails:** Executive readers do not need to be told the document is summarizing. The structure of the document communicates this. Recap language adds an extra layer of scaffolding that consumes attention without delivering information.

**Fix:** Remove the recap header. If a summary section is needed, title it "Next Steps" and make it action-oriented, not retrospective.

---

### Pattern 5: Filler Transitions
**What it is:** Transition phrases that consume space without creating logical connection.

**Examples:**
- *"Having said that..."*
- *"With that being said..."*
- *"That being said..."*
- *"Moving on to..."*
- *"Speaking of which..."*

**Regex:**
```
\b(Having said that|With that being said|That being said|Moving on to|Speaking of which|On that note|With that in mind)\b
```

**Why it fails:** These phrases exist to paper over logical gaps between sections. If the logical connection between two paragraphs requires a filler transition, the paragraphs are probably in the wrong order or one of them should be cut.

**Fix:** Delete the transition. If the paragraphs cannot connect without it, reorder or cut.

---

### Pattern 6: Rigid Optimism Close
**What it is:** Closing sentences that acknowledge challenges, then pivot to generic optimism. LLMs produce this because training data includes corporate boilerplate that always ends positively.

**Example:** *"Despite its challenges, the organization faces an exciting future full of opportunity."*

**Regex:**
```
\bDespite (its|these|the) (challenges|drawbacks|limitations|headwinds).{0,60}(exciting|bright|promising|opportunity|potential|future)
```

**Why it fails:** The construction signals that the writer has not engaged with the challenges. Real executives read this as a sign that the analysis stopped before it got difficult.

**Fix:** End on the action, not on the sentiment. *"The next 90 days determine whether the cost reduction holds. Three decisions need to happen by end of month."*

---

### Pattern 7: Imagine-a-World Opener
**What it is:** Hypothetical scene-setting openers that invite the reader to imagine a future state.

**Example:** *"Imagine a world where every sales rep closes at 40%..."*

**Regex:**
```
^\s*Imagine (a world|a future|if|what it would|yourself)
```

**Why it fails:** This is a TED Talk convention, not an executive brief convention. An executive opening a brief needs information, not an invitation to daydream.

**Fix:** Delete. Start with the actual situation.

---

### Pattern 8: Magic-Adverb Verbs
**What it is:** Combinations of a vague intensifying adverb with a grandiose verb. LLMs use these to make claims sound significant without delivering specifics.

**Examples:**
- *"quietly transforms"*
- *"fundamentally changes"*
- *"deeply matters"*
- *"profoundly redefines"*

**Regex:**
```
\b(quietly|fundamentally|deeply|remarkably|profoundly|genuinely|truly|meaningfully)\s+(transforms|changes|redefines|reveals|signals|matters|shifts|alters|reshapes)
```

**Why it fails:** The adverb does no work — it asserts significance without providing evidence of it. Every instance of a magic-adverb verb is a missed opportunity to state what actually changed and by how much.

**Fix:** State the specific change. *"Response time dropped from 4.2 days to 18 hours."* Not *"fundamentally transforms response efficiency."*

---

### Pattern 9: Vague Attribution
**What it is:** Claims attributed to anonymous sources — industry, experts, studies, observers — without naming a specific source.

**Examples:**
- *"Studies suggest..."*
- *"Experts argue..."*
- *"Industry reports indicate..."*
- *"Observers have noted..."*

**Regex:**
```
\b(industry reports|observers have|experts argue|studies suggest|some critics argue|research shows|analysts say|it is widely believed)\b
```

**Why it fails:** Vague attribution is unfalsifiable. The reader cannot check the claim, cannot assess its credibility, and cannot follow up. In an executive brief, vague attribution signals that the specific claim was too weak to survive scrutiny with a real source attached.

**Fix:** Name the specific source, or cut the claim if no specific source exists.

---

### Pattern 10: Inline Code Chips
**What it is:** Single-line backtick-wrapped fragments scattered through prose paragraphs outside of code blocks. LLMs insert these when discussing technical terms, tool names, or configuration values in a narrative context.

**Example:** *"The team uses `Salesforce` to manage pipeline, and the `CRM` data feeds into `Tableau`."*

**Regex:**
```
(?<!`)`[^`\n]+`(?!`)
```
Applied outside fenced code blocks (` ``` ` regions). Match any single-backtick chip that is not part of a code fence.

**Why it fails:** Code formatting in prose signals developer documentation, not executive communication. An exec brief is not a README. The backtick chip breaks the reading rhythm and signals AI or technical origin to any professional reader.

**Fix:** Remove the backticks. If the term is important, bold it (`**Salesforce**`) or use it as a plain noun. If it was a file path or command, it does not belong in the prose of an executive brief — cut it or move it to an appendix.

---

### Pattern 11: Schema Leaks *(Manual Review — No Regex)*
**What it is:** Internal vocabulary appearing in customer-facing or executive-facing prose. Examples: referring to "our Tier 2 playbook," "per the Q3 OKR framework," "the Stage 3 opportunity," or "the enterprise ICP" in a brief that will be read by someone outside the internal system.

**Why no regex:** Schema leaks are context-dependent. The same word may be internal jargon in one brief and the customer's own vocabulary in another. Regex cannot distinguish.

**Detection rule:** Before passing to output, read every H2 section header and every **So what:** block. Flag any term that assumes the reader has access to internal systems, internal stage names, internal playbook names, or internal classification vocabulary. If the reader would need to ask "what does that mean?" — it's a schema leak.

**Why it fails:** The reader receives vocabulary that implies a system they cannot see. The brief signals that it was written from the inside out — optimized for the writer's mental model, not the reader's decision-making context.

**Fix:** Replace with the term the reader uses, or remove the reference to the internal system entirely. *"Stage 3 opportunity"* becomes *"the $240K Acme deal expected to close this quarter."*

---

### Pattern 12: Em-Dash Overuse
**What it is:** Excessive use of em-dashes as a sentence-level connective device. GPT-4.1 uses em-dashes at 3.3× the rate of human writers.

**Formula (brief):**
```
Count of em-dashes (—) ÷ Total sentence count > 0.15
```

**Formula (docx):**
```
Count of em-dashes (—) ÷ Total sentence count > 0.15
```

**Same threshold in both modes now — history of why:** Originally the docx threshold was 0.35, set against the first approved North Star docx (measured 0.28 em-dashes/sentence). The North Star 2.0 reboot measures 0.013/sentence — near zero — because its tighter register uses the Read:/Judgment:/Hypothesis:/Required response: labels to mark shifts in claim-type instead of em-dashes as connective tissue. Rather than compute a fresh, untested threshold with a tight multiplier against 0.013 (fragile on small-sample noise, the same problem the sentence floor below exists to guard against), the docx threshold now reuses the brief's already-validated 0.15 — over 11× the reboot's measured rate, comfortable margin against false positives, while still real tightening from 0.35.

**Minimum-sample floor:** the rate isn't evaluated at all below 50 total sentences, in either mode. Raised from 30 alongside the threshold tightening — a tighter threshold is more sensitive to small-sample noise, so it needs a larger minimum sample to stay reliable. Confirmed empirically: a synthetic test account with exactly 30 sentences still tripped the new threshold at 0.33, driven by structural em-dashes in short label-style table cells ("Alex Rutherford — Engineering Manager") and the skill's own `flagText()` placeholder wording. The latter is now fixed at the source (the placeholder text no longer uses an em-dash at all, since it's generated boilerplate, not organic prose, and shouldn't count toward a prose-style check either way) — but the floor still needed raising for genuinely small accounts with a few unavoidable label-style em-dashes.

**Critical dependency — extraction method matters:** Never run this check against text extracted via `pandoc -t plain` (or any tool that renders tables as ASCII grids, e.g. `+-----------------------------------------------------------------------+`). Long hyphen runs in table borders get counted as em-dashes by the `--` half of the detection regex — confirmed during the 2026-07 diagnostic, where pandoc extraction reported 1,219 "em-dashes" in a docx containing zero real em-dash characters. Always extract with `scripts/extract_docx_text.py`, which reads the docx's paragraph/table model directly and never emits border characters.

**Why it fails:** Em-dash overuse is the single most reliable AI-tell in prose. Human writers use em-dashes occasionally, for specific rhetorical purposes. LLM prose uses them as a default connective — linking clauses that should be separate sentences, or inserting parenthetical material that should be cut.

**Fix:** Replace most em-dashes with periods. Separate the clauses. The sentence almost always becomes clearer.

---

### Pattern 13: Retired
**What it was:** A hard block on the literal label `Read:` introducing an interpretation, on the theory that it was always leaked ledger scaffolding.

**Why it's retired, not just relaxed:** The North Star 2.0 reboot uses `Read:`/`Judgment:`/`Hypothesis:`/`Required response:` as a required four-part taxonomy (see `voice-spec.md`), not a banned leak. A regex can't tell a real, consistently-applied taxonomy apart from the original failure mode (one generic label, applied mechanically, with no real classification behind it) — that distinction is drafting-time judgment now, not a mechanical gate. Don't try to rebuild this as a script check; read `voice-spec.md`'s taxonomy section instead when drafting or reviewing.

---

### Pattern 14: Ledger Data-Block Header
**What it is:** A ledger section header (`Data — Cybersecurity organization:`) left in place as a paragraph lead-in.

**Formula:**
```
"Data" + (em-dash or hyphen) + Capitalized label + colon
```

**Why it fails:** This is internal bookkeeping structure, not one of the four allowed taxonomy labels and not a sentence a person would write to a VP. It signals the paragraph was assembled by walking the ledger's own section order rather than by deciding what the reader needs first.

**Fix:** Cut the header. Open the paragraph with the actual first fact instead.

---

### Pattern 15: Ledger Citation Residue
**What it is:** A raw ledger fact-ID citation (`[spend-2024]`) or internal claim-type register label (`OBSERVED-INTERNAL`, `INTERPRETATION`) leaked into the **main body** of the deliverable.

**Formula:**
```
[lowercase-word(s)-joined-by-hyphens]  OR  OBSERVED-INTERNAL | OBSERVED-EXTERNAL | INTERPRETATION
```

**Exempted in the Source Notes and Citation IDs appendix.** As of the North Star 2.0 reboot, this new appendix section requires exactly this content — categorized citation IDs preserving the research trail. The check stops applying once a line matching the appendix's heading is reached (see `scan_patterns()` in `lint_gate.py`); everywhere before that heading, the ban still applies in full.

**Why it fails (in the main body):** These exist for the ledger's own audit trail. A reader outside that system has no way to resolve a bracket ID, and a register label describes the ledger's confidence bookkeeping, not something the reader needs to see mid-narrative.

**Fix:** Remove from the main body. If it needs to be preserved, it belongs in the Source Notes and Citation IDs appendix, not inline.

---

### Pattern 16: Contraction Avoidance
**What it is:** A document that consistently uses full forms ("do not," "is not," "does not") instead of contractions ("don't," "isn't," "doesn't"), even when no individual sentence looks wrong.

**Formula (both modes, as of North Star 3.0):**
```
Full-form count ÷ (full-form count + contraction count) > 0.5
(only evaluated when full-form count + contraction count ≥ 4 — below that, there's no signal either way)
Evaluated only against narrative prose paragraphs — table cells, Plan Header values,
dates, and citation IDs are excluded from the count entirely in both modes.
```

**Both modes as of the North Star 3.0 revision (2026-07-20).** North Star 2.0 measured 100% full-form in the docx (9 full forms, 0 contractions) and this check was disabled in docx mode as a result — applying the brief's rule would have failed the very document that defined "correct" at the time. North Star 3.0 deliberately supersedes that calibration: contractions are now expected in docx narrative prose the same way they're expected in the brief, since the two deliverables are no longer voiced differently on this dimension (see `voice-spec.md`, "Version History and Current Calibration"). What's new relative to the brief's original version of this check is the scope restriction — this only ever evaluates prose paragraphs, never table cells or data fields, since a date or a dollar figure was never meaningfully "full-form" or "contracted" in the first place.

**Why it fails (both modes now):** It's a register drift, not a grammar error. A document that consistently avoids contractions in its narrative sections reads stiffer and more formal than the calibrated North Star 3.0 register, even when every individual sentence looks fine in isolation.

**Fix:** Rewrite full forms as contractions where natural in narrative prose: "do not" → "don't," "is not" → "isn't," "does not" → "doesn't." Leave table cells, Plan Header values, and citation IDs exactly as-is — they were never in scope for this check.

---

## AI Vocabulary Blocklist

These words appear at disproportionately high rates in LLM output relative to professional human writing. Any single instance in a rewritten exec brief is a hard hit.

**Note on this skill's copy:** This list is self-contained, not shared with exec-brief-editor, and has been pruned by two words for this domain specifically. `landscape` is removed because this skill's own fixed template requires section headers named "Customer Landscape" and "Competitive Landscape" (see `sfdc-template-map.md`) — banning it would block every single account plan regardless of prose quality. `champion` is removed because it's standard, correct sales-methodology vocabulary for a Relationship Map's role column ("technical champion"), not filler AI-speak in this context. Both exclusions were found during the 2026-07 Deere diagnostic, where the inherited generic list produced false-positive blocks on the skill's own required structure.

```
delve, leverage, robust, seamless, holistic, synergy, paradigm,
empower, harness, streamline, cutting-edge, best-in-class, ecosystem,
game-changer, unlock, elevate, disrupt, tapestry, notably,
moreover, furthermore, utilize, underscore, pivotal, transcend, navigate,
testament, realm, elucidate, illuminate, foster, cultivate, spearhead,
drive, stakeholder, deliverable, actionable, scalable,
innovative, transformative, visionary, groundbreaking

**Note:** `drive`, `stakeholder`, and `deliverable` are included because they appear at disproportionately high rates in LLM-generated executive content and are rarely used by practitioners who write without AI assistance. `drive` as a verb is almost always replaceable with a specific mechanism (*"caused," "produced," "pushed"*). `stakeholder` names a category instead of a person. `deliverable` names the process instead of the thing.
```

**Regex:**
```
\b(delve|leverage|robust|seamless|holistic|synergy|paradigm|empower|harness|streamline|cutting-edge|best-in-class|ecosystem|game-changer|unlock|elevate|disrupt|tapestry|notably|moreover|furthermore|utilize|underscore|pivotal|transcend|elucidate|illuminate|navigate|testament|realm|foster|cultivate|spearhead|actionable|scalable|innovative|transformative|visionary|groundbreaking)\b
```

**Why these specific words:** They are not forbidden because they are bad words. They are blocked because they appear in exec briefs written by LLMs at rates that no human professional writer matches. A single instance creates doubt. Multiple instances confirm AI origin in the reader's mind.

**Fix map:**
- *leverage* → use
- *utilize* → use
- *robust* → strong, reliable, or name the specific quality
- *seamless* → smooth, or describe what makes it smooth
- *holistic* → complete, or name the specific dimensions
- *ecosystem* → name the actual components
- *actionable* → delete (everything should be actionable; saying so adds nothing)
- *innovative* → name the specific innovation
- *transformative* → name the specific change and its magnitude
- *notably, moreover, furthermore* → delete or use "and," "but," "because"

---

## Lint Gate Execution Instructions

### Step 0: Extracting text to lint (docx only)
If linting a built docx (not the brief), never use `pandoc -t plain`. Use `scripts/extract_docx_text.py <docx> <output.txt>` — see Pattern 12's extraction-method note for why. The brief is already plain markdown and needs no extraction step.

### Step 1: Run regex patterns
Apply the 12 active regex patterns to the rewritten output (Patterns 1–10, 14, and 15, excluding Pattern 11 which is manual and Pattern 13 which is retired — see its entry above). Collect every hit with line number and pattern name. Pattern 15 stops applying once the Source Notes and Citation IDs appendix begins (docx only; the brief has no appendix, so it applies throughout).

### Step 2: Run em-dash count
Count total em-dashes in the document. Count total sentences. If under 50 sentences, skip this check entirely — not enough sample to be reliable. Otherwise divide and compare against 0.15 (both brief and docx use the same threshold now) — pass `--doc-type` for the report header either way, but the number applied is currently identical.

### Step 3: Run vocabulary scan
Scan for any word in the AI vocabulary list. Case-insensitive. Add any matches to hit list.

### Step 3b: Run contraction-rate check (Pattern 16) — both modes as of North Star 3.0
Count full forms and contractions in narrative prose only (exclude table cells, Plan Header values, dates, and citation IDs from the count). If full forms exceed 50% of the combined total (and the combined total is at least 4), add to hit list. **This now runs in docx mode too** — North Star 3.0 expects contractions in docx prose the same as the brief; see `voice-spec.md`.

### Step 1b: Manual review — Schema Leaks (Pattern 11)
Read every H2 section header and every **So what:** block. Flag any term that assumes the reader has access to internal systems, stage names, playbook names, or internal classification vocabulary. Add any flagged instances to the hit list manually with pattern name "Schema Leak" and the offending term.

### Step 4: Evaluate hit list
- Zero hits → pass. Proceed to output.
- One or more hits → compile hit list with: pattern name, line number, offending text, suggested fix.

### Step 5: First retry (if hits found)
Pipe the hit list back into the rewriter: *"The following lint violations were found in the previous output. Rewrite the affected sections to eliminate every violation. Do not introduce new violations while fixing these."*

### Step 6: Second lint run
Run all patterns again on the rewritten output.

### Step 7: Two-strike halt (if hits remain)
If any hits remain after the second pass: halt. Surface the failing draft to the user with:
- The complete current hit list
- The sections that contain violations
- Suggested fixes for each

**Never silently bypass.** The user must either edit the draft or explicitly override with a written reason logged in the output.

---

## Lint Gate vs. Voice Rewrite

The lint gate runs **after** the voice rewrite, not before or during. The sequence:

1. Editorial frame scoring → sections are cut, kept, or flagged MISSING
2. Restructure → surviving sections are reordered per output structure
3. Voice rewrite → prose is rewritten for practitioner voice
4. **Lint gate** → AI-tells are caught and blocked
5. Output

Running the lint gate during voice rewrite creates a paradox — the rewriter is trying to improve the prose while the lint gate is catching patterns in the draft. Separate the steps. Voice rewrite first. Lint gate catches what slips through.
