---
name: account-plan
description: Build or refresh a SANS Sales Account Plan (NA Enterprise) end-to-end — SFDC pull, Tableau orders, Crawford research, ledger-first synthesis. Use when the user says /account-plan, "build an account plan for X", "refresh the X plan", or "run the playbook on X". Usage - /account-plan <company name> [refresh]
---

# /account-plan — ledger-first account plan builder

**The whole skill in one line:** pull internal facts (SFDC pack → Tableau
orders), research externals (Crawford under the ledger-emit contract +
ZoomInfo signals), keep every claim typed in the account's fact ledger, then
synthesize the plan through the template's registers and run the quality
gates.

**Home:** `/Users/jfentress/Projects/playbooks`. Scope: **North America
Enterprise** (other business lines get variants later). If invoked on a
non-NA account (it happens — Tesco, UK&I), ask the user up front how to
handle the mismatch (run as-is / light-touch adapt / stop and scope a
variant) rather than silently forcing NA assumptions.

## 0. Canon (read before running — source of truth, do not duplicate here)

| File | What it governs |
|---|---|
| `Account_Plan_Template_Recipe.md` | Part 0 claim taxonomy + section registers; Part 1 the 12 sections; Part 3 quality gates |
| `Fact_Ledger_Schema.md` | facts.yaml record shapes, folder convention, lint rules L1–L10 |
| `Source_Alignment.md` | Per-source decisions (lanes, trust rules, sharp edges) + open items |
| `Crawford_Ledger_Emit_Contract.md` | Output contract + route-yield block for all Crawford missions |
| `Ideas_Log.md` | Parking lot — append one-liners, never act on them mid-run |

Non-negotiables burned in during alignment (2026-07):
- **Spend = Cash In** (`Invoice_Payment__c`, paid not PO'd). Bookings are the
  cross-check. **Cert Add Rate = GIAC bundle attach** on decided PAID seats.
- Aggregator ceiling: ZoomInfo/TheOrg alone never mints "Confirmed" (2+
  independent non-aggregator sources).
- Salesforce is READ-ONLY. Screenshots are never a data source.
- Synthesis only in Phase 6; Crawford/ZoomInfo emit facts, never reads.
- Prior-plan numbers are `unverified` until reproduced in an aligned lane.

## 1. Preflight — kick off Tableau auth now, non-blocking

```bash
sf org list   # expect codex-salesforce Connected; if not: sf org login web
gtm lookup --field management-levels | head -3   # real JSON = ZoomInfo live
```

Then check whether the nag is even needed — cheap, no network:

```bash
cd /Users/jfentress/SDR1/tabagent && python3 ops/cli/manage_tableau_cookie.py status
```

Read the `Updated:` timestamp. **If it's within the last ~60 minutes, skip
the reauth nudge entirely** — that's the signature of a reauth this session
(or a parallel `/account-plan` session) already ran; log one line ("Tableau
cookie updated <timestamp>, skipping reauth nudge") and go straight to Phase
1a. This is the multi-session case: when the user kicks off several accounts
in parallel and authed on the first one, `status` alone is enough to spare
every later session from repeating the ask — no need to re-nag once per run.

`status` only reports Keychain metadata, so a recent timestamp is a real
signal (unlike `doctor`, which **false-greens** — Learned 2026-07-16, it can
exit 0 against a genuinely expired session). Don't upgrade `status` into a
live-validity check; it only tells you "was this refreshed recently," which
is exactly what the skip decision needs and no more.

If `Updated:` is stale (or the profile/Keychain read fails), assume the
session may be cold and get the user reauth'ing in parallel from message
one, before touching the account folder. Post this verbatim, once, then
move straight into Phase 1a — don't wait for a reply:

> Kicking off the SFDC pull and research now. In parallel, run this in
> another terminal so Tableau is warm by the time I need it (headed SSO —
> I can't run this one myself):
> `bash /Users/jfentress/SDR1/tabagent/ops/cli/reauth.sh`
> No need to tell me when it's done — I'll check right before the Tableau
> pull and only follow up if it's still cold then.

This is why Phase 1b (Tableau) is now the **last** data-gathering step
instead of the second: Phase 1a + Phases 2–5 + the AE interview are all
Tableau-independent, so running them first buys the reauth the maximum
wall-clock time to land before it's actually needed. Skip the proactive
nudge on a `refresh` run where Phase 1b's facts are being superseded and a
fresh pull isn't imminent — confirm scope with the user first, same as any
refresh.

## 2. Run state gate (BEFORE touching the account folder)

State lives in `accounts/<slug>/<slug>run.yaml` (shape: `Fact_Ledger_Schema.md`)
— never infer run state from which files happen to exist.

### File naming convention

**All output files are prefixed with the account slug.** This keeps files
identifiable when opened outside their folder context.

| File type | Naming pattern | Example (slug: dcma) |
|-----------|---------------|----------------------|
| Run manifest | `<slug>run.yaml` | `dcmarun.yaml` |
| Fact ledger | `<slug>facts.yaml` | `dcmafacts.yaml` |
| Account plan | `<slug>plan.md` | `dcmaplan.md` |
| SFDC pack output | `<slug>sfdc-facts.yaml` | `dcmasfdc-facts.yaml` |
| Evidence folder | `<slug>evidence/` | `dcmaevidence/` |

| Folder state | Action |
|---|---|
| No folder | Fresh run: create folder, write `<slug>run.yaml` (status: in-progress), go |
| `<slug>run.yaml` status: complete | This is a **refresh** — confirm with the user, bump `ledger_version`, supersede facts, new run.yaml |
| `<slug>run.yaml` in-progress / abandoned | ASK: resume from last stamped phase, or archive + restart |
| Files but NO `<slug>run.yaml` | Pre-manifest debris — archive to `_archive/<date>-<why>/` with `ARCHIVE_NOTE.md`, then fresh run |

Stamp each phase in `<slug>run.yaml` as it completes; set `completed` only after
the quality gates pass. Abandoning mid-run? Set `status: abandoned` + a note
— the next session will thank you.

## 3. Phase 1a — Salesforce pack (minutes)

```bash
cd /Users/jfentress/Projects/playbooks
python3 sfdc-pack/pull_sfdc_facts.py --name "<Company>"     # resolve duplicates — ASK the user which ID if >1 has opps
python3 sfdc-pack/pull_sfdc_facts.py --account-id <ID> --slug <slug>
```

If `--name` resolves to **multiple real accounts** (a federation like
NAVSURFWARCEN's 7 divisions, not mere duplicates), that's an ask-first fork:
confirm scope with the user (all-divisions rollup / one division / top-N)
*before* pulling anything — rollup mechanics (nested slugs, fact-id
namespacing, derived rollup facts): `Fact_Ledger_Schema.md` §1.

**Then always pull open pipeline** — sfdc-pack v1 pulls closed-won ONLY, and
on Deere the un-run query would have cost the plan its premise (Learned
2026-07-16). Until pack v2 ships, run by hand and emit the results as ledger
facts:

```bash
sf data query -q "SELECT Id, Name, StageName, Amount, CloseDate, CreatedDate,
  Owner.Name, Probability, NextStep FROM Opportunity
  WHERE AccountId='<id>' AND IsClosed=false"
```

Output: `accounts/<slug>/<slug>sfdc-facts.yaml` + `<slug>evidence/` folder with CSVs.
Rename the pack's default output files to follow the naming convention. Record the
chosen SFDC ID in the ledger identity map. Caveats live in `sfdc-pack/README.md`.
Accounts with international exposure: verify the pack emitted per-currency
amounts and never infer deal currency from the account header — query
transaction-level `CurrencyIsoCode` (Learned 2026-07-20, Tesco).

## 4. Phases 2–5 — external research

- **Crawford** (default engine): company research (10-K/earnings/newsroom),
  cyber-org mapping, hiring signals, competitive sweep. EVERY mission gets
  the preamble from `Crawford_Ledger_Emit_Contract.md` §2 and ends with the
  route-yield block appended to `crawford-yield-log.yaml`.
- **ZoomInfo** (`gtm` CLI): structured endpoints only — contact validation
  (secondary), `intent`/`scoops`/`news` as dated aggregator facts. Record
  `zoominfo_company_id` in the identity map. Never `gtm research`.
- Merge per `Crawford_Ledger_Emit_Contract.md` §4 (no id collisions, no
  overwrites — freshness arbitration decides active vs superseded).
- Course codes for S11: validate via course-compass before they enter facts.
- **Federal/DoD accounts:** the commercial recipe (10-K, earnings, Wikidata)
  has no equivalent — substitute DoD policy PDFs, USAJOBS postings (hiring
  signals + org-unit mapping), and SAM.gov (JS-SPA fetch caveat) per the
  Federal/DoD open items in `Source_Alignment.md`. Expect no named
  CISO/ISSM/ISSO; record ONE consolidated could-not-verify.

## 5. AE input (one short interview, still before Tableau/synthesis)

Relationship history comes from spend patterns + AE interview, NOT SFDC
activity logs. Interview the **account owner from `account-header`** — the
invoker only if they are the owner (Learned 2026-07-16). Ask: existing
relationships, in-flight conversations, known politics. Record as
`observed-internal` facts, `kind: interview`, with the date. "I don't know"
is a successful outcome (a named, owned open question), and the user may
skip the interview on purpose — either way, record one ledger fact naming
why it's missing and who owns the gap, surfaced in S4a/9/12; never fabricate
relationship context. SFDC contact titles can't corroborate external titles
(provenance unknown, often bulk-imported) — CRM presence proves
reachability, never relationship.

## 6. Phase 1b — Tableau orders (last data-gather step, on purpose)

This runs last, after Phase 1a + Phases 2–5 + the AE input, so the reauth
posted back in Preflight (§1) has had the most possible wall-clock time to
land before it's needed — the common case should be a silent pull with no
follow-up message.

Real auth check happens HERE, not in Preflight — treat the pull itself as
the test, since `doctor` gives false greens (Learned 2026-07-16):

```bash
cd /Users/jfentress/SDR1 && python3 outbound/cli/pull_tableau.py \
  --org "<Exact Org String>" --since <plan-window-start> --until <today> \
  --no-pii --skip-preflight --out <scratchpad>/<slug>-orders
```
- Succeeds → proceed silently, no message needed. This is the path the whole
  Preflight reorder exists to make the normal case.
- Fails (auth) → this is the **one** blocking follow-up in the whole skill.
  Tell the user verbatim to run `bash /Users/jfentress/SDR1/tabagent/ops/cli/reauth.sh`
  (headed SSO — never reauth yourself), wait for their confirmation, then
  retry the pull once.
- Org filter is exact + case-sensitive (strip suffixes; confirmed strings:
  `~/.claude/skills-archive/pull-tableau-orders/org-aliases.md`).
- Compute: PAID seat count, **bundle attach = Yes/(Yes+No) on PAID seats**,
  COMP-row count (engagement signal for S4a). Emit as `observed-internal`
  facts (system: tableau) into the ledger — Tableau is a SANS system
  (corrected 2026-07-16; this text previously said observed-external).
- No dollars in RecentOrders; per-org dollar views are interaction-gated —
  do not chase them. Cash In already came from Phase 1a.
- Cross-check: Tableau PAID seats ≈ SFDC course line items. >15% apart →
  data-quality note on both facts. Gaps can run >90% or to zero — before
  writing a data-quality footnote, run the full due-diligence pass (org-string
  discovery scan across ALL eras + voucher-ID cross-match unfiltered —
  `Source_Alignment.md` §2 sharp edges). If both come up empty, record
  the gap as its own ledger fact, route it to the AE by name, and have S2/S4a
  say seat/attach data is unavailable — never default it to zero.

## 7. Phase 6 — synthesize & gate

1. Build the plan per the template: registers respected, Data/Read pairs in
   mixed sections, every synthesis claim citing ledger ids, process
   narrative only in Section 12.
2. Run quality gates 1–15 (template Part 3) against the ledger; fix or flag.
3. Deliverable: `accounts/<slug>/<slug>plan.md`. The user reviews
   Vision/Objectives/SWOT — their judgment is the last mile.

## Refresh mode (`/account-plan <company> refresh`)

Same flow; bump `ledger_version`, supersede changed facts (never overwrite),
Section 12 entry = the ledger diff.

## Learn (on exit)

New sharp edges land below, dated. Source-lane decisions belong in
`Source_Alignment.md`; one-liner ideas in `Ideas_Log.md`.

### Graduation (keeps this block short enough to actually get read)

**Graduation point** — an entry is *stable* and must move out once ALL
three hold:
1. Its operative rule lives at its point of use (this file's body, or the
   right canon file);
2. A later run confirmed it, or it's pure changelog with nothing left to
   instruct;
3. Any still-open remainder is filed as an open item in
   `Source_Alignment.md`.

**Graduation flow** — run as a maintenance pass whenever this block exceeds
~10 entries or carries anything older than ~30 days:
1. For each stable entry, verify the destination actually carries the rule;
   fold it in first if not. Routing: procedure → this file's body at the
   step it affects; ledger/file/naming conventions → `Fact_Ledger_Schema.md`;
   source-lane decisions, sharp edges, open questions →
   `Source_Alignment.md`; tool behavior → the owning tool's README.
2. Move the entry VERBATIM to `Learned_Archive.md` under a dated batch
   header with a destination map. The archive is append-only history —
   never edit entries there, and never let a rule live *only* there.
3. Leave here: entries from the most recent run(s) and anything not yet
   folded or confirmed. Append one dated entry recording the sweep.

Never delete an entry without archiving it. The failure mode this exists to
prevent (seen 2026-07-16 → 2026-08-21): corrections pile up in the appendix
while the body keeps giving the uncorrected instruction.

<!-- BEGIN LEARNED -->
## Learned patterns

Entries 2026-07-16 → 2026-08-03 graduated 2026-08-21 → `Learned_Archive.md`
(verbatim, with a destination map). Everything operative from them now
lives in this file's body, `Fact_Ledger_Schema.md` §1, or
`Source_Alignment.md`.

2026-08-21: **Doc-consistency pass: folded body-contradicting Learned entries
            into the body at their point of use.** No goals, outcomes, or
            execution order changed. Folded: Tableau facts observed-internal
            (§6, was misstated as observed-external); open-pipeline query
            promoted into Phase 1a (§3); federation ask-first fork and
            multi-currency check added to §3; Federal/DoD source-recipe fork
            added to §4; AE-interview owner/skip/CRM-title rules folded into
            §5; seat-count cross-check in §6 now points at the full
            due-diligence pass. Learned entries stay as history — when a
            Learned entry contradicts the body, fold it in rather than letting
            the appendix silently override the instructions people actually
            follow. (This pass was prompted by the playbook-wiki ingestion,
            which surfaced the drift.)
2026-08-21: **First graduation sweep.** Defined the graduation point + flow
            (see "Learn (on exit)" above) and graduated all 22 entries from
            2026-07-16 → 2026-08-03 to `Learned_Archive.md`. Destinations
            folded in the same pass: slug-prefix naming, tooling filename
            fallback, and the federated-accounts rollup mechanics moved into
            `Fact_Ledger_Schema.md` §1 (whose folder tree still showed
            pre-convention bare names); multi-currency rules and the Tableau
            workbook-name/due-diligence caveats moved into
            `Source_Alignment.md` §1/§2; the non-NA scope fork moved into
            this file's header. Also closed two Source_Alignment open items
            resolved by the 2026-08-21 doc pass (observed-internal, AE owner)
            and annotated the doctor false-green item as adopted skill-side.
            Dated "Learned YYYY-MM-DD" attributions remaining in the body
            resolve via the archive.
<!-- END LEARNED -->
