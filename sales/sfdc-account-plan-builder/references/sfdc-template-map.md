# SFDC Account Plan — Template Map

This is the fixed target structure every account plan docx must follow, and where each section's content comes from in the source ledger `.md`. The section names and order below don't change between accounts — what varies is the content and the number of rows in each table.

The ledger `.md` this skill expects follows a consistent numbered structure (Plan Header, Account Metrics, Account Vision, Account Notes, SWOT, Customer Landscape, Competitive Landscape, Account Objectives, Strategic Tracker, Relationship Map, Curriculum Targeting, Plan Refresh Log) — the same shape as the Deere source document. If an incoming `.md` uses different section numbers or slightly different headers, match by content and intent, not by exact string — the mapping below tells you what each section is *for*, so you can find the right content even if a header is phrased differently.

## Missing-Section Handling

If the expected content for any row below has no corresponding material anywhere in the source `.md`: do not invent it. Set that field/section to a flagged placeholder in the JSON (see schema notes) so it renders visibly in the docx as:

`⚠ [Section/field name] not provided in source data — needs input from account owner.`

This applies at the section level (an entire missing SWOT quadrant) and at the field level (one relationship-map row missing a verification status). Never leave a table cell blank with no explanation — a blank cell reads as an oversight; a flagged placeholder reads as an honest gap.

## Section Mapping

| Docx Section | Source in Ledger `.md` | Notes |
|---|---|---|
| Plan Header | Section 1 (Plan Header) | Account Name, Plan Owner, Plan Status, Segment, Plan Start/End, Account Type, SFDC Account ID |
| Account Metrics | Section 2 (Account Metrics) | The spend/metrics table, plus one synthesized Read: paragraph folding together the interpretive read AND the open-pipeline/spend-alert information — these no longer get separate callout boxes (see "Two Required Structural Moves Retired" below) |
| Account Vision | Section 3 (Account Vision) | One paragraph, rewritten in voice, not compressed. As of North Star 3.0, no longer bolded (see `voice-spec.md`) |
| Account Notes — Current Situation | Section 4a (Current Situation) — every Data/Read sub-topic | **As of North Star 3.0, this section is built via per-atom routing, not a flat rewrite of the ledger's sub-topics.** See `references/atomization-method.md` and `voice-spec.md`, "Per-Atom Routing." Atoms the brief covers inherit the brief's own grouping and wording; atoms it doesn't (cut for space, or belonging to material the brief has no room for) get grouped by downstream destination and atomized directly from the ledger. Each group is a JSON array entry: either a plain string (a full flowing paragraph, for groups of ~6 atoms or fewer) or an object `{ "lead": "...", "bullets": [...] }` (a short prose lead-in plus 3-5 supporting bullets, for denser groups). In both shapes, exactly one sentence per group, its Judgment/payoff, is marked with `**bold markdown**` in the string and rendered bold; every other sentence in the group is unlabeled prose (no inline Read:/Judgment: tags stacked sentence-by-sentence — that was the pre-3.0 pattern and is what made this section read dense) |
| Account Notes — Key Risks | Section 4b (Key Risks) | **Always atomized directly from the ledger** via `references/atomization-method.md` — the brief has no Key Risks equivalent (it dissolves risk atoms into its other sections instead of isolating them), so there is nothing to route from here. Each risk is one bulleted item, Read:/Judgment:/Required response:/Hypothesis: as applicable, per the existing taxonomy. This section is the calibration example atomization is measured against — see the "why this method exists" note in `references/atomization-method.md` |
| Account Notes — Internal Alignment | Section 4c (Internal SANS Alignment Needed) | One paragraph. Not in scope for the North Star 3.0 atomization pass — still a flat rewrite, not routed or atomized (revisit separately if it starts showing the same density symptom) |
| SWOT Analysis | Section 5 (SWOT) | **Always atomized directly from the ledger** — exec-brief-editor's own editorial-frame scoring typically cuts SWOT from the brief entirely (redundant with narrative), so there's nothing to route from. Four-quadrant table, all four quadrants uniformly colored (header + content share one color per quadrant) |
| Customer Landscape — Priorities/KPIs | Section 6a | Two-column table, green header |
| Customer Landscape — Challenges/Trends | Section 6b | Two-column table, green header |
| Competitive Landscape | Section 7 | Reframe as Strengths/Weaknesses at [Account], green header, plus a footer paragraph |
| Account Objectives | Section 8 | Table: Objective, Current Value, Target Value, Start, End Date, Owner. Zebra-striped |
| Strategic Tracker | Section 9 | Table: Action/Task (with embedded Start/Status sub-lines), Linked Objective, Contact, Due Date (with source/derived provenance tag), Owner. Zebra-striped |
| Relationship Map | Section 10 | Table: Name/Title, Role in Decision, SANS Sentiment, Our Access, Next Action. Zebra-striped |
| SANS Curriculum Targeting | Section 11 | Table, zebra-striped |
| Plan Refresh Log | Section 12 | **Now an array of entries**, not a single row — accumulates across runs. Fact/contact/lint-status numbers get woven into the first entry's summary text as prose, not a separate callout |
| Source Notes and Citation IDs | The ledger's own `[bracket-id]` citations, grouped by category | **New section.** Bracket citations are banned from the main body (Pattern 15 still applies there) but expected and required here |

## Two Required Structural Moves Retired

The original "Data Integrity callout" and "Pipeline/Spend Alert callout" (both rendered as bordered, titled boxes) are retired as of the North Star 2.0 reboot. The Data Integrity signal now lives in the Plan Refresh Log's first entry, as prose, not a boxed callout. The Pipeline Alert is now folded into the Account Metrics section's Read: paragraph. **Risks framed as called out, not hidden remains required** — it's now expressed via the Read:/Required response: labels rather than an unlabeled bullet, but the underlying requirement (state the risk, state what the plan does about it) hasn't changed.

## JSON Schema for `build_docx.js`

Extract the account's content into a single JSON file matching this shape. Every array can be any length — the script builds table rows dynamically, so a 3-row Objectives table and a 15-row Strategic Tracker both work without code changes.

Use the literal string `"__MISSING__"` as a value (or as an item in an array) anywhere content wasn't in the source — the script renders it as the flagged placeholder automatically.

```json
{
  "account_name": "string",
  "plan_owner": "string",
  "plan_status": "string",
  "segment": "string",
  "plan_start": "MM/DD/YYYY",
  "plan_end": "MM/DD/YYYY",
  "account_type": "string",
  "sfdc_id": "string",
  "plan_window_note": "string — why this window was chosen, what it depends on being confirmed",

  "metrics": {
    "columns": [
      { "label": "string, e.g. 'SANS Spend 2024'", "value": "string, e.g. '$62,951'", "sublabel": "string, e.g. '-81% vs. 2023'" }
    ],
    "read": "string — one synthesized paragraph combining the interpretive read AND the open-pipeline/spend-alert information. Replaces the old separate 'pipeline_alert' field — there is no dedicated callout box anymore, this renders as a single highlighted paragraph."
  },

  "vision": "string — one paragraph, no bold as of North Star 3.0",

  "current_situation_paragraphs": [
    "EITHER a plain string — one flowing paragraph, for a destination-group of ~6 atoms or fewer, treated as ledger-sourced by default (no provenance tag). Its Judgment/payoff sentence is wrapped in **bold markdown** (rendered bold, asterisks stripped); every other sentence is unlabeled prose.",
    "OR an object { \"text\": \"string, same **bold** convention\", \"_source\": \"brief\"|\"ledger\", \"_brief_refs\": [\"h1_thesis\"|\"recommendation_block\"|\"h2:<exact title>\"|\"next_steps\", ...] } — same one-paragraph shape, WITH provenance tagged. Use this form whenever the group is brief-sourced, so cross_check.py can verify it (see references/atomization-method.md, 'Recording Provenance').",
    "OR an object { \"lead\": \"string, 1-2 sentences, usually the **bolded** Judgment atom\", \"bullets\": [\"string\", \"...\"], \"_source\": \"brief\"|\"ledger\", \"_brief_refs\": [...] } — a short prose lead-in plus 3-5 supporting bullets, for a destination-group of ~7+ atoms.",
    "_source and _brief_refs are read-and-discarded by build_docx.js — they never render. Omit them (plain string) only for groups you're confident are ledger-only; when in doubt, tag explicitly rather than relying on the default.",
    "See references/atomization-method.md for the full grouping and formatting procedure — groups are formed by shared downstream destination, not by ledger topic."
  ],

  "key_risks": ["string — each uses Read:/Required response:/Hypothesis: as applicable, per voice-spec.md"],

  "internal_alignment": "string",

  "swot": {
    "strengths": ["string"],
    "weaknesses": ["string"],
    "opportunities": ["string"],
    "threats": ["string"]
  },

  "customer_landscape": {
    "priorities": ["string"],
    "kpis": ["string"],
    "challenges": ["string"],
    "trends": ["string"]
  },

  "competitive": {
    "strengths": ["string"],
    "weaknesses": ["string"],
    "footer": "string"
  },

  "objectives": [
    { "objective": "string", "current": "string", "target": "string", "start": "MM/YYYY", "end": "MM/DD/YYYY", "owner": "string" }
  ],

  "tracker": [
    {
      "action": "string — the task description",
      "start_date": "string",
      "status": "string, e.g. 'Not started' or 'Blocked pending access verification'",
      "linked_obj": "string, e.g. '1' or '1, 2'",
      "contact": "string — Deere-side contact, or 'Unknown from source'",
      "due": "string — the date",
      "due_provenance": "string, e.g. 'source: This week' or 'derived: 30 days from plan refresh'",
      "owner": "string — internal owner"
    }
  ],

  "relationship_map": {
    "note": "string — the 'every access level is none' style finding, if applicable, else '__MISSING__'",
    "contacts": [
      { "name_title": "string", "role": "string", "sentiment": "string, e.g. 'Unknown from source'", "access": "string", "next_action": "string" }
    ],
    "dropped_note": "string, or '__MISSING__' if nothing was dropped"
  },

  "curriculum": {
    "note": "string — code validation note, or '__MISSING__'",
    "rows": [
      { "role_team": "string", "curriculum": "string", "courses": "string", "persona_fit": "string", "status": "string" }
    ],
    "footer": "string, or '__MISSING__'"
  },

  "refresh_log": [
    {
      "date": "MM/DD/YYYY",
      "updated_by": "string",
      "summary": "string — weave the fact count, contact count, and lint/QC status into this entry's prose (only the entry documenting the ledger build needs to)"
    }
  ],

  "source_notes": {
    "source_file": "string — the ledger .md filename this plan was built from",
    "intro": "string, e.g. 'The main plan is intentionally readable; citation identifiers below preserve the research trail.'",
    "citation_groups": [
      { "label": "string, e.g. 'Account header and metrics'", "ids": ["string", "..."] }
    ],
    "corrections_retained": "string, or '__MISSING__' if this is a net-new plan with no prior version to reference — do not fabricate a corrections narrative for a first-time plan",
    "unknown_from_source": "string — a plain-language list of open unknowns, or '__MISSING__'"
  }
}
```
