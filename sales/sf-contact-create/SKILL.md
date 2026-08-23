---
name: sf-contact-create
description: Create Salesforce Contact records — one contact or a list — via sf-cli, matching manual creation exactly.
disable-model-invocation: true
---

# sf-contact-create

Creates live Contact records in production Salesforce via `sf data create record`. Works for a single contact described inline, or a CSV/list of contacts.

This writes real records to shared org data. There is no sandbox here — confirm before any bulk run.

## Setup (fill once per install)

| Variable | Value | Notes |
|---|---|---|
| `SF_ORG` | `<your org alias>` | `sf org list` to find it; `sf org login web --alias <alias>` to authenticate |
| Instance URL | `<https://yourorg.my.salesforce.com>` | For record links; or derive live via `sf org display --target-org $SF_ORG --json` |

If your network intercepts TLS and `sf` throws certificate errors: `export NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem` (or your corporate CA bundle) first.

**Org schema note:** the layout-required fields below (`LeadSource`, `Lead_Source_Detail__c`) and the server-side defaults come from the authoring org. Verify against your own org's Contact page layout on first use — create one contact by hand in the UI, note which fields the layout forces, and update the mapping table to match.

## Field mapping

Only `LastName` is required by the Salesforce API. The page layout typically requires more that the API doesn't enforce — skip any of these and the record won't match what a human would have made by hand:

| Field | Required | Notes |
|---|---|---|
| `LastName` | yes | API + layout |
| `AccountId` | yes (layout) | 18-char Id, not the account name. Resolve by querying: `sf data query -q "SELECT Id,Name FROM Account WHERE Name='<name>'" -o $SF_ORG`. If you maintain a local account-to-Id lookup file, check it first as a fast path. |
| `LeadSource` | yes (layout) | Picklist. Default to `'Hunted lead'` for target-list contacts unless told otherwise |
| `Lead_Source_Detail__c` | yes (layout) | Free text. Default to `'LinkedIn'` unless told otherwise |
| `FirstName`, `Title`, `Email`, `Phone`, `MobilePhone` | no | Fill whatever data is available |

**Never set** fields that default server-side in your org (in the authoring org: `Contact_Status__c` → `Qualified`, `Contact_Type__c` → `Sales`) — setting them manually can diverge from what manual creation produces.

## Steps

1. **Gather input.** Either a single contact's details from the prompt, or a CSV path plus which rows to include (e.g. only `NEW` status).
2. **Resolve each `AccountId`** per the mapping above. If any account name can't be resolved, stop and ask — don't guess an Id.
3. **Print the field mapping table** for every contact about to be created (Name, Account, LeadSource, Lead_Source_Detail__c, plus any optional fields populated) and get explicit confirmation before creating anything. For more than 5 contacts, state the count and warn this writes that many live records.
4. **Create records:**
   ```bash
   sf data create record -s Contact -o $SF_ORG -v "LastName='<x>' FirstName='<x>' AccountId='<id>' Title='<x>' Email='<x>' Phone='<x>' MobilePhone='<x>' LeadSource='Hunted lead' Lead_Source_Detail__c='LinkedIn'"
   ```
   Omit any optional field with no value — don't pass empty strings.
5. **Report results**: for each contact, the returned record Id and a direct link (`<instance URL>/<Id>`). Flag any failures with the sf-cli error verbatim — don't retry silently.
