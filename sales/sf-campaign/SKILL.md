---
name: sf-campaign
description: Create a Salesforce Standard campaign via the sf CLI with your team's standard defaults — parent campaign, Description duplicated from the campaign name, and required picklist values. Replaces the manual Campaigns > New > Standard Campaign click path. Idempotent (reuses an existing campaign with the same name), verified by read-back. Usage - /sf-campaign <campaign name> [--parent "Name"] [--dry-run]
---

# /sf-campaign — create a Standard campaign with the house defaults

Creates one Salesforce Campaign the way the operator would click it in the UI:
**Campaigns > New > Standard campaign > name > parent > description=name > required picklists > activate.**

One run = one campaign created, activated, and verified by read-back. Blast radius: a single production Campaign record — writes are gated by an operator confirm of the preview.

## Setup (fill once per install)

Edit this table with your values — everything below references it.

| Variable | Value | Notes |
|---|---|---|
| `SF_ORG` | `<your org alias>` | `sf org list` shows your aliases; `sf org login web --alias <alias>` to authenticate |
| Instance URL | `<https://yourorg.lightning.force.com>` | Or derive live: `sf org display --target-org $SF_ORG --json` → `result.instanceUrl` |
| Default parent campaign | `<exact campaign name>` | The parent every new campaign nests under unless `--parent` overrides |

If your network intercepts TLS (Netskope/Zscaler etc.) and `sf` throws certificate errors, export the CA bundle before any call:

```bash
export NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem   # or your corporate CA bundle path
```

**Org schema note:** the defaults below reference custom fields from the authoring org (`Requestor_Team__c`, `Requestor_Team_Detailed__c`, `Goal__c`). If your org's Campaign object differs, discover required-on-create fields with `sf sobject describe --sobject Campaign --target-org $SF_ORG` and swap them in the defaults table and Step 5.

## Defaults (operator-editable here, in this file)

| Field | Value |
|---|---|
| Record type | `Standard campaign` |
| Parent campaign | the Setup table's default parent |
| `Description` | duplicate of the campaign name |
| `Requestor_Team__c` | `Sales` |
| `Requestor_Team_Detailed__c` | `NA` |
| `Goal__c` | `Leads` |
| `IsActive` | `true` (activated immediately after create) |

When the default parent changes, edit the Setup table — it is the single source of the default.

## Cached org facts (verify before trusting — Step 2 re-resolves both live)

On first run in a new org, record the resolved IDs here so later runs can sanity-check against them:

- Standard campaign RecordTypeId: `<record on first run>`
- Default parent campaign Id: `<record on first run>`
- Required-on-create Campaign fields for your org: `<record on first run>`
- `Status` defaults to `Planned`, `IsActive` to `false` — same as the UI path; do not set them on create.

## Inputs

- **Campaign name** (required) — taken from the invocation, verbatim. The operator may revise it at the preview step; use whatever they designate.
- `--parent "Exact Campaign Name"` — override the default parent.
- `--dry-run` — do everything except the create; print the preview and stop.

## CLI posture

`--json` output is clean on stdout, but the CLI prints update warnings on **stderr** — never merge with `2>&1` before parsing JSON; use `2>/dev/null`.

## Steps

### 1. Preflight (fail loud, don't proceed on failure)

```bash
sf data query --query "SELECT COUNT() FROM Campaign" --target-org $SF_ORG --json 2>/dev/null
```

Check the **exit code and** `"status": 0` in the JSON — do not pipe through `tail`/`head` before checking. On auth failure, stop and tell the operator the exact recovery: `sf org login web --alias $SF_ORG`.

### 2. Resolve live IDs (never trust the cache blind)

In one round, query both:

```sql
SELECT Id FROM RecordType WHERE SobjectType = 'Campaign' AND Name = 'Standard campaign'
SELECT Id, Name, IsActive FROM Campaign WHERE Name = '<parent name>'
```

- Parent: expect **exactly 1** row. 0 rows → stop, show the operator the name searched and ask for the correct parent (offer a `LIKE` search of similar names). >1 rows → stop, list them with Ids, let the operator pick.
- If a resolved Id differs from the cached value above, use the live one and update the cache in this file.

### 3. Idempotency check

```sql
SELECT Id, Name, Parent.Name, Requestor_Team__c, Requestor_Team_Detailed__c, Goal__c FROM Campaign WHERE Name = '<campaign name>'
```

If it exists: **do not create a duplicate.** Show the existing record and its field values, note any that differ from the defaults, and stop (offer the link `<instance URL>/lightning/r/Campaign/<Id>/view`). A re-run of the same invocation must be a no-op.

### 4. Preview + confirm (HITL gate — this is a production write)

Show the operator exactly what will be created:

```
Name:                    <name>
Record type:             Standard campaign
Parent:                  <parent name> (<parent Id>)
Description:             <name — duplicated>
Requestor Team:          Sales
Requestor Team Detailed: NA
Goal:                    Leads
```

The name may need adjusting — accept an edited name here and re-run Step 3 against it. With `--dry-run`, stop after the preview. Otherwise wait for an explicit yes (AskUserQuestion: create / edit name / cancel).

### 5. Create

```bash
sf data create record --sobject Campaign --values "Name='<name>' RecordTypeId='<rtId>' ParentId='<parentId>' Description='<name>' Requestor_Team__c='Sales' Requestor_Team_Detailed__c='NA' Goal__c='Leads'" --target-org $SF_ORG --json 2>/dev/null
```

Quoting: names often contain `|` pipes — keep each value inside single quotes within the double-quoted `--values` string, exactly as above. If a name ever contains an apostrophe, escape it as `\'`.

On a non-zero status: report the raw `message` from the JSON error verbatim, retry **at most once** only if the error is transient (network/timeout); otherwise stop and escalate to the operator with the error and the exact command. Never retry a validation error.

### 6. Activate

```bash
sf data update record --sobject Campaign --record-id <newId> --values "IsActive=true" --target-org $SF_ORG --json 2>/dev/null
```

Required step — `IsActive` defaults to `false` on create, which makes the campaign inaccessible in the standard Salesforce UI ("no longer available, ask admin"). On non-zero status: report the error and stop; do not proceed to verify.

### 7. Verify (Definition of Done — independent of the create call's claim)

Read the record back by the returned Id:

```sql
SELECT Id, Name, RecordType.Name, Parent.Name, Description, Requestor_Team__c, Requestor_Team_Detailed__c, Goal__c, Status, IsActive, Owner.Name FROM Campaign WHERE Id = '<newId>'
```

**DoD: every read-back field equals the previewed value.** Any mismatch = the run failed — report the diff; do not silently accept.

### 8. Report

```
✅ Campaign created and verified
   Name:   <name>
   Id:     <Id>   →  <instance URL>/lightning/r/Campaign/<Id>/view
   Parent: <parent name>
   Status: Planned | Active: true
```

## What this skill does NOT do

- No CampaignMembers (adding people to campaigns is a separate workflow).
- No updates/deletes of existing campaigns — if the operator wants to change one, that's a separate explicit request.
- Never more than one campaign per invocation unless the operator passes an explicit list, in which case run Steps 3–6 per name with one combined preview/confirm.
