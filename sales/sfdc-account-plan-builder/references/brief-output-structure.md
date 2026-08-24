# Output Structure: Required Shape for Executive Briefs

**Purpose:** Define the mandatory structure every rewritten brief must follow. This is not a template — it is an architecture. Every section has a function. Nothing is optional except what is explicitly marked as conditional.

---

## The 30-Second Test

The output passes if a reader with 30 seconds can answer three questions without searching:
1. What is happening?
2. What should I do?
3. By when?

If the answer to any of these questions requires reading past the first screen of content, the structure has failed.

---

## Required Structure

### Element 1: H1 — The BLUF Thesis
**What it is:** One sentence. The governing thought. The answer to "what is this about and what does it mean for me?"

**Format:**
```
# [Specific claim about the situation] — [implication for the reader]
```

**Examples:**
- `# Q3 pipeline is 31% below target — we need two decisions before the board call`
- `# The vendor contract expires in 47 days — approval required to avoid service interruption`
- `# Western region missed Q2 by 22% — three accounts need executive attention this week`

**Rules:**
- One sentence. Hard limit.
- Contains a specific number or named event wherever possible
- Names the implication for the reader directly — do not make the reader infer it
- No LLM openers ("In today's...", "This brief examines...")
- No hedging ("may suggest," "could indicate")
- Active voice

**Minto grounding:** The BLUF thesis is the apex of the Minto Pyramid. Everything below it is support. If the reader reads only this line, they have the governing thought.

---

### Element 2: Recommendation Block
**What it is:** Three lines immediately below the H1. The action layer.

**Format:**
```
**Action:** [specific verb] + [specific artifact or decision] + [by when]
**Why:** [one sentence — the most important supporting fact]
**What I need from you:** [specific ask — approval, input, decision, meeting]
```

**Example:**
```
**Action:** Approve the Q3 headcount freeze exception for the two open AE roles by Friday
**Why:** Pipeline coverage drops below 2.5x if both roles stay open through August
**What I need from you:** A yes/no on the exception before Thursday's offer deadline
```

**Rules:**
- Action line must contain a verb, an artifact or decision, and a date or deadline
- Why line must contain a specific fact — not a general principle
- "What I need from you" must be specific — name the ask, not a general invitation to respond
- All three lines must fit on one screen with the H1

**BLUF grounding:** The three-line block is the operational heart of BLUF. Military communications doctrine requires a clear action, a clear rationale, and a clear ask. Every executive brief is a request for something — the recommendation block names that request explicitly.

---

### Element 3: H2 Sections in Priority Order
**What it is:** Supporting sections, ordered by relevance to the reader's role and decision — most important first.

**Format:**
```
## [Section title — specific, not generic]

[Body content — applies editorial frame scoring, leads with conclusion, evidence follows]

**So what:** [specific verb] + [specific artifact] + [owner] + [by when]
```

**Rules:**
- Every H2 section title must name the specific topic, not a category. *"Western Region Pipeline"* not *"Regional Update."*
- Every H2 section must end with a **So what:** block. No exceptions.
- The **So what:** block is the same format as the recommendation block action line: verb + artifact + owner + deadline.
- Sections are ordered by Q1 (Importance) score from the editorial frame scoring, not by the order they appeared in the source document.
- Maximum 4-5 H2 sections. If more than 5 sections survive the editorial frame, either combine related ones or cut the weakest KEEP.

**So what block examples:**
- `**So what:** Schedule executive sponsor calls for accounts 1, 2, and 3 — [owner name] — by July 15`
- `**So what:** Send revised pricing proposal to [account] — [AE name] — before the competitor's renewal date on July 22`
- `**So what:** Escalate the service interruption risk to the CTO — [owner] — this week`

---

### Element 4: Next Steps Footer
**What it is:** 3–5 bulleted action items. The complete action layer visible in one glance.

**Format:**
```
## Next Steps

- [Verb] + [artifact] + [owner] + [deadline]
- [Verb] + [artifact] + [owner] + [deadline]
- [Verb] + [artifact] + [owner] + [deadline]
```

**Rules:**
- Every bullet has four elements: verb, artifact, owner, deadline. No exceptions.
- Bullets are ordered by urgency — shortest deadline first.
- Maximum 5 bullets. If more than 5 actions are needed, the brief is covering too much ground. Split into two briefs or escalate only the top 5.
- The Next Steps bullets are not new information — they are a consolidated view of the **So what:** blocks from each H2 section, plus the recommendation block ask. The reader should see nothing here they have not already seen.

**Example:**
```
## Next Steps

- Approve Q3 headcount exception — [VP name] — Thursday before 5pm
- Send executive sponsor outreach to accounts 1–3 — [AE names] — by July 15
- Pull Q2 call recordings for the three at-risk accounts — [CSM name] — by end of week
- Schedule competitive pricing review — [team] — July 20
```

---

## Word Count Cap

**Hard cap: 60% of original word count.**

- Calculate the original word count of the input before editing.
- The rewritten output must not exceed 60% of that number.
- If the output is 61–65% of original: refire with the instruction "cut harder, target 50%."
- If the output is above 65% after the second pass: halt and surface to the user. Do not publish an overweight brief.

**Why 60%:** The article's author rebuilt a 3,214-word brief to 1,180 words — 37% of the original. 60% is the ceiling, not the target. Most well-executed rewrites land between 35% and 55%.

**What gets cut to hit the cap:**
1. Methodology sections — always first. The reader does not need to know how the analysis was done.
2. Background sections the reader already has — context they bring, not context the brief provides.
3. Restatements of the recommendation — if the BLUF and recommendation block are right, repetition adds no value.
4. Evidence that supports a point already made by stronger evidence.
5. Qualifications and caveats that do not change the recommendation.

---

## Conditional Elements

### Charts and Visualizations
Include only when removing the chart loses information the prose cannot carry. Apply the viz decision tree (Step 5 of SKILL.md — 12-rule first-match decision tree) before including any chart.

If charts are required, upgrade the output to HTML. Add a warning to the user that HTML output is required for chart rendering.

**Default is no chart.** The chart agent's most important decision is when NOT to make a chart.

### Customer Voice Block
If a meeting transcript is provided via `--transcript` flag: weave the customer's specific concerns and vocabulary into the H2 sections and **So what:** blocks. The reader should encounter the customer's actual language, not a paraphrase.

If no transcript is provided: the brief uses the input's language. Flag to the user that a transcript would strengthen the customer-specificity of the output.

### Appendix
If evidence sections were cut from the body but are likely to be requested, include a brief appendix with the raw data. Label it clearly: `## Appendix: Supporting Data`. Never include methodology sections in the appendix — they were cut for a reason.

---

## Internal Fact-ID Tagging (North Star 3.0 — Not Reader-Facing)

**New requirement, added 2026-07-20.** While drafting the brief, tag each element with the ledger fact-ID(s) it was built from. This is what makes brief-to-docx routing mechanical rather than a reverse-engineered guess after the fact (see `voice-spec.md`, "Per-Atom Routing," and `references/atomization-method.md`, "Recording Provenance").

**This tagging is never reader-facing, in two senses.** First, the rule under "What the Output Never Contains," below, still holds without exception: no bracket IDs, no register tags, nothing citation-shaped anywhere in the brief's markdown. Second, the sidecar file itself (below) is a working artifact, not a deliverable — it stays in the working directory alongside the draft and is never copied to the outputs directory or presented to the user, the same way a scratch file never ships.

**Concrete format.** A JSON sidecar, named `{brief_filename_stem}.factmap.json`, tagging at the *element* level — H1 thesis, recommendation block, each H2 section, Next Steps footer — not per-sentence. Per-sentence tagging was considered and rejected: briefs run 3-6 sentences per H2 section, and sentence-level tags would be brittle against exactly the kind of light editing a two-strike lint pass produces, going stale faster than they'd stay useful. Element-level is the practical grain.

```json
{
  "elements": [
    { "id": "h1_thesis", "text_summary": "one-line paraphrase of what this element claims", "fact_ids": ["spend-2024", "spend-2025", "..."] },
    { "id": "recommendation_block", "text_summary": "...", "fact_ids": ["..."] },
    { "id": "h2:$200K Voucher Is the Vehicle, Not the Ceiling", "text_summary": "...", "fact_ids": ["..."] },
    { "id": "next_steps", "text_summary": "...", "fact_ids": ["..."] }
  ]
}
```

- **`id`** — `h1_thesis`, `recommendation_block`, `h2:<exact section title as written>`, or `next_steps`. These are the same IDs `account_data.json`'s `_brief_refs` field points back to (see `references/atomization-method.md`), so routing and verification both resolve against one shared naming convention.
- **`fact_ids`** — every ledger fact-ID the element's claims are actually built from. An element that legitimately synthesizes several ledger facts into one sentence lists all of them; that's the brief doing its job, not a violation.
- **Tag claims, not connective tissue.** If a sentence doesn't trace to a specific ledger fact-ID (a transition, part of the framing rather than a specific assertion), it doesn't need to be represented in `fact_ids`. Don't force a citation onto connective prose.
- **Re-tag after every revision.** If the brief's text changes during the lint gate's two-strike correction pass, regenerate the fact-map before moving on — a fact-map tagging a sentence that no longer exists, or missing one that's new, is worse than no fact-map, since Step 3b and Step 4 will trust it at face value.

**What the tagging is for:** two downstream consumers, neither of them the brief's reader.
1. **Docx routing** — when the docx is drafted, it needs to know which ledger atoms the brief already covered (inherit that wording/grouping directly, tagging the resulting group `_source: "brief"`) versus which atoms it didn't (atomize those from the ledger instead, tagging `_source: "ledger"`).
2. **Verification** — the brief-against-ledger check (`references/brief-verification-worksheet.md`) re-reads every tagged element against its cited fact-ID(s) to confirm the brief actually said what the source says, before anything gets built from it.

---

**Self-reference.** The brief does not mention itself, the editing process, this skill, or how the output was produced. The polished brief is the brief. The reader has never heard of the editorial frame and does not need to.

**Meta-commentary.** No sentences like "As you can see in the above section..." or "The following data supports the recommendation above." The structure communicates the relationships. The prose does not narrate them.

**Recap language.** No "In summary," "To recap," "Key takeaways." The Next Steps section is the summary — it does not need to be labeled as one.

**Vague action asks.** "Please review and provide feedback" is not a **So what:** block. Name the specific decision, the specific person, and the specific deadline.

---

## Output Format Decision

| Condition | Format |
|---|---|
| No charts required | Markdown |
| Charts required | HTML (auto-upgrade) |
| Delivery surface is email | Markdown (paste into email client) |
| Delivery surface is Google Doc | Markdown (paste, apply heading styles) |
| Delivery surface is Slack | Markdown (Slack renders headers and bold) |
| Delivery surface is slide | Restructure required — brief format does not translate directly to slides |
