---
name: hermes
description: Push cadences to SalesLoft, assign them to team members, and bulk-resolve contact lists to SalesLoft person IDs. Creates cadences via cadence_imports, sets cadence ownership, adds prospects under a specific teammate's name, and performs bulk person lookups from name/email/company lists.
---

# Push Cadence to SalesLoft

Create a cadence and all its email steps in SalesLoft using a single `cadence_imports` API call.

## Setup (fill once per install)

1. **API keys.** Create two env files in this skill's folder (SalesLoft > Settings > API Keys — one read-scoped key, one write-scoped key for cadence creation). Copy the provided examples:
   ```bash
   cp read.env.example read.env    # then fill in SALESLOFT_API_KEY=<your read key>
   cp write.env.example write.env  # then fill in SALESLOFT_API_KEY_CADENCES=<your write key>
   chmod 600 read.env write.env
   ```
   Never commit these files or paste key values into chat/output.

2. **Local defaults.** Fill this table with your values on first use — the workflows below reference it:

| Variable | Value | Notes |
|---|---|---|
| Default cadence owner email | `<you@yourorg.com>` | Used when the operator doesn't name an owner |
| Default assignee user_id | `<your SalesLoft user id>` | Find it via the users endpoint below |
| Org email domain | `<yourorg.com>` | For resolving teammate emails |

## API Key loading

Keys live alongside this skill in the hermes folder. **Do NOT use `export $(grep ... | xargs)`** — it leaks all env vars into output.

**Write key** (for creating cadences):
```bash
SALESLOFT_KEY_WRITE=$(grep '^SALESLOFT_API_KEY_CADENCES=' "$(dirname "$SKILL_PATH")/write.env" | cut -d'=' -f2)
```

**Read key** (for pulling down / reading cadences):
```bash
SALESLOFT_KEY=$(grep '^SALESLOFT_API_KEY=' "$(dirname "$SKILL_PATH")/read.env" | cut -d'=' -f2)
```

(If `$SKILL_PATH` isn't set in your harness, substitute the skill folder's absolute path, e.g. `~/.claude/skills/hermes/`.)

**IMPORTANT:** The variable names differ between files. Write env uses `SALESLOFT_API_KEY_CADENCES`, read env uses `SALESLOFT_API_KEY`.

Both files are `chmod 600` (owner-only).

## Dynamic Tags

SalesLoft uses dot-notation for sender ("My") fields. These are the valid tags for email templates:

| Tag | Description |
|-----|-------------|
| `{{first_name}}` | Recipient's first name |
| `{{last_name}}` | Recipient's last name |
| `{{title}}` | Recipient's job title |
| `{{company}}` | Recipient's company name |
| `{{city}}` | Recipient's city |
| `{{state}}` | Recipient's state |
| `{{My.first_name}}` | Sender's first name |
| `{{My.last_name}}` | Sender's last name |
| `{{My.email_address}}` | Sender's email |
| `{{My.phone}}` | Sender's phone |
| `{{My.title}}` | Sender's title |

**IMPORTANT:** The sender tag is `{{My.first_name}}` (capital M, dot notation). NOT `{{my_first_name}}` — that will be rejected by the API as an invalid dynamic tag.

## HTML Body Formatting

Wrap each paragraph in `<p>` tags. Do NOT use `<div>` with `<br>` tags.

**Correct:**
```html
<p>{{first_name}},</p><p>First paragraph here.</p><p>Second paragraph here.</p><p>{{My.first_name}}</p>
```

**Wrong:**
```html
<div>{{first_name}},<br><br>First paragraph here.<br><br>{{my_first_name}}</div>
```

## Endpoint

**POST** `https://api.salesloft.com/v2/cadence_imports`

This is NOT `/v2/cadences` (that endpoint is read-only). The `cadence_imports` endpoint creates the cadence and all steps in a single call.

**Headers (write operations):**
```
Authorization: Bearer ${SALESLOFT_KEY_WRITE}
Content-Type: application/json
Accept: application/json
```

## Payload Structure

```json
{
  "settings": {
    "name": "Cadence Name",
    "cadence_owner": "teammate@yourorg.com",
    "target_daily_people": 0,
    "remove_replied": true,
    "remove_bounced": true,
    "remove_people_when_meeting_booked": true,
    "external_identifier": "unique-slug-for-cadence",
    "cadence_function": "outbound",
    "added_stage_setting": "Working",
    "bounced_stage_setting": "Bounced",
    "finished_stage_setting": "Closed - No Response",
    "replied_stage_setting": "Replied"
  },
  "sharing_settings": {
    "team_cadence": false,
    "shared": false
  },
  "cadence_content": {
    "step_groups": []
  }
}
```

### Settings Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Cadence display name |
| `target_daily_people` | Yes | Daily target (0 = unlimited) |
| `remove_replied` | Yes | Remove people who reply |
| `remove_bounced` | Yes | Remove people who bounce |
| `remove_people_when_meeting_booked` | No | Remove on meeting booked |
| `external_identifier` | Yes | Unique slug (e.g., "rsac-2026-planning") |
| `cadence_function` | Yes | Always `"outbound"` |
| `cadence_owner` | No | Email of the SalesLoft user who should own this cadence. Defaults to the API key holder if omitted. |
| `added_stage_setting` | No | Stage when added (default: "Working") |
| `bounced_stage_setting` | No | Stage on bounce |
| `finished_stage_setting` | No | Stage when finished |
| `replied_stage_setting` | No | Stage on reply |

Note: the stage-setting values must match your SalesLoft instance's configured person stages — check Settings > Stages if the API rejects them.

### Sharing Settings

| Field | Description |
|-------|-------------|
| `team_cadence` | `true` for team, `false` for personal |
| `shared` | Required. Must be `true` or `false`. Set to same value as `team_cadence`. |

### Step Groups

Each step group represents one day in the cadence. Each group contains one or more steps.

**A/B Testing:** To create A/B variants, put multiple steps inside the same step group. SalesLoft automatically splits traffic evenly between them. Each variant gets its own `email_template` with its own subject/body. All variants in a group share the same `day` and `previous_email_step_group_reference_id`.

```json
{
  "automated_settings": {},
  "automated": false,
  "day": 1,
  "due_immediately": false,
  "reference_id": "UNIQUE_ID",
  "steps": [
    {
      "enabled": true,
      "name": "Step Name",
      "type": "Email",
      "type_settings": {
        "previous_email_step_group_reference_id": null,
        "email_template": {
          "title": "Template Title",
          "subject": "Subject line here",
          "body": "<p>HTML body here</p>",
          "open_tracking": true,
          "click_tracking": false
        }
      }
    }
  ]
}
```

**A/B variant example (two steps in one group):**
```json
{
  "day": 1,
  "reference_id": "UNIQUE_ID",
  "steps": [
    {
      "enabled": true,
      "name": "Variant A",
      "type": "Email",
      "type_settings": {
        "previous_email_step_group_reference_id": null,
        "email_template": {
          "title": "Variant A",
          "subject": "Subject line",
          "body": "<p>Variant A body</p>",
          "open_tracking": true,
          "click_tracking": false
        }
      }
    },
    {
      "enabled": true,
      "name": "Variant B",
      "type": "Email",
      "type_settings": {
        "previous_email_step_group_reference_id": null,
        "email_template": {
          "title": "Variant B",
          "subject": "Different subject",
          "body": "<p>Variant B body</p>",
          "open_tracking": true,
          "click_tracking": false
        }
      }
    }
  ]
}
```

### Step Group Fields

| Field | Required | Description |
|-------|----------|-------------|
| `automated_settings` | Yes | Empty object `{}` for manual steps |
| `automated` | Yes | `false` for manual, `true` for auto-send |
| `day` | Yes | Day number in cadence (1, 5, 9, etc.) |
| `due_immediately` | Yes | Usually `false` |
| `reference_id` | Yes | Unique ID for this group (used for step chaining) |
| `steps` | Yes | Array of steps for this day |

### Step Chaining

Steps are chained together using `previous_email_step_group_reference_id`:
- **First step group:** set to `null`
- **All subsequent step groups:** set to the `reference_id` of the previous step group

This creates the sequential flow in SalesLoft.

### Reference ID Generation

Use timestamp-based IDs to guarantee uniqueness:
```bash
REF1=$(date +%s)001
REF2=$(date +%s)002
REF3=$(date +%s)003
REF4=$(date +%s)004
```

### Step Types

| Type | type_settings |
|------|---------------|
| `Email` | `email_template` with `title`, `subject`, `body` |
| `Phone` | `instructions` string |
| `Other` | `instructions` string |

## Consuming Structured Cadence Input

If an upstream skill or document provides cadence copy as JSON, parse it to build the API payload.

### Expected JSON structure:
```json
{
  "cadence_name": "RSAC 2026 - Planning Session",
  "steps": [
    {
      "step": 1,
      "day": 1,
      "subject": "Planning gap",
      "body": "{{first_name}},\n\nFirst paragraph.\n\nSecond paragraph.\n\nThank you,\n{{My.first_name}}",
      "thread": "new"
    },
    {
      "step": 2,
      "day": 5,
      "body": "{{first_name}},\n\nBody text here.\n\nThank you,\n{{My.first_name}}",
      "thread": "reply"
    }
  ]
}
```

### A/B variant JSON structure:

Steps with the same `step` number and `day` are A/B variants. They go into the same step group as separate steps. Use the `variant` field to label them.

```json
{
  "cadence_name": "OSINT Summit 2026",
  "steps": [
    {
      "step": 1,
      "day": 1,
      "variant": "A",
      "subject": "March intelligence",
      "body": "{{first_name}},\n\nVariant A body.\n\nThank you,\n{{My.first_name}}",
      "thread": "new"
    },
    {
      "step": 1,
      "day": 1,
      "variant": "B",
      "subject": "March intelligence",
      "body": "{{first_name}},\n\nVariant B body.\n\nThank you,\n{{My.first_name}}",
      "thread": "new"
    },
    {
      "step": 2,
      "day": 5,
      "body": "{{first_name}},\n\nNext step body.\n\nThank you,\n{{My.first_name}}",
      "thread": "reply"
    }
  ]
}
```

**Grouping rule:** Steps with the same `step` number are A/B variants and go into a single `step_group` with multiple entries in the `steps` array. Steps without a `variant` field are solo (one step per group, no A/B split).

### Mapping rules:

| Input JSON field | SalesLoft API field |
|---------------------|---------------------|
| `cadence_name` | `settings.name` |
| `step.day` | `step_group.day` |
| `step.subject` | `email_template.subject` (only on step 1) |
| `step.body` | `email_template.body` (after HTML conversion) |
| `step.thread: "new"` | `previous_email_step_group_reference_id: null` |
| `step.thread: "reply"` | `previous_email_step_group_reference_id: [previous ref_id]` |
| `step.variant` | Step name label (e.g., "Variant A"). Multiple steps with same `step` number → same step group |
| (always) | `email_template.open_tracking: true` — set on every step |
| (always) | `email_template.click_tracking: false` — set on every step |

### Body text to HTML conversion

Input arrives as plain text with `\n` between paragraphs. Convert to HTML by wrapping each non-empty line in `<p>` tags:

```
Input:  "{{first_name}},\n\nFirst paragraph.\n\nSecond paragraph.\n\nThank you,\n{{My.first_name}}"
Output: "<p>{{first_name}},</p><p>First paragraph.</p><p>Second paragraph.</p><p>Thank you,</p><p>{{My.first_name}}</p>"
```

Split on newlines, filter empty lines, wrap each in `<p>` tags, join.

### Subject line handling

- **`thread: "new"`** — Use the `subject` field from the JSON. This is the only step with a subject.
- **`thread: "reply"`** — Do NOT set a subject. SalesLoft auto-generates "Re: [Email 1 subject]" when `previous_email_step_group_reference_id` is set. Passing a subject with "Re:" would produce "Re: Re: [subject]" — a double-up. Pass the same subject as email 1 (without "Re:") or omit it.

## Pull Down Workflow (Read Cadences)

When the user says "pull down" + cadence ID(s), fetch and display existing cadences. This is a **read-only** operation.

### Trigger
Arguments like `pull down 1839742` or `pull down 1839742 and 1817850`. Any numeric IDs in the args = pull-down mode.

### Steps

1. **Load read key** (see API Key loading above).

2. **Fetch cadence metadata + steps in parallel** (for each ID):
```bash
curl -s "https://api.salesloft.com/v2/cadences/{id}" -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
curl -s "https://api.salesloft.com/v2/steps?cadence_id={id}&per_page=25" -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```

3. **For each email step**, get the template ID:
```bash
curl -s "https://api.salesloft.com/v2/action_details/email_details/{step_id}" -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```
Extract `email_template.id` from the response.

4. **Fetch email templates** (subject + body) — batch all template IDs:
```bash
curl -s "https://api.salesloft.com/v2/email_templates/{template_id}" -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```

5. **For phone steps**, fetch call instructions:
```bash
curl -s "https://api.salesloft.com/v2/action_details/call_instructions/{step_id}" -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```

6. **Present a summary** for each cadence:
   - Cadence name, status, people count, created date, personal/team
   - Step table: step number, day, type, name, subject (email 1 only), body preview
   - Send stats per step: sent, views, clicks, replies, bounces

### API Call Chain
```
cadences/{id}  ──┐
                  ├──→ summary
steps?cadence_id={id} ──→ action_details/email_details/{step_id} ──→ email_templates/{template_id}
                         action_details/call_instructions/{step_id}
```

Parallelize: fetch all cadence metadata + steps simultaneously across IDs. Then batch all email_details calls, then batch all template calls.

---

## Push Workflow (Create Cadences)

1. **Check for structured cadence JSON in conversation.** If a cadence JSON block exists from an upstream step, use it directly. Otherwise, ask the user for the steps.

2. **Ask the user for:**
   - Cadence name (default: `cadence_name` from JSON)
   - Whether it's a team or personal cadence (default: **personal** — `team_cadence: false, shared: false`)
   - Cadence owner email and assignee user_id for memberships (defaults: the Setup table's values)

3. **Build the full payload:**
   - Group steps by `step` number. Steps sharing the same `step` number are A/B variants in a single step group.
   - Generate one reference ID per step group (not per variant)
   - Convert body text to HTML (`<p>` tags)
   - Set threading via `previous_email_step_group_reference_id` (all variants in a group share the same previous ref)
   - Name each variant using the `variant` field (e.g., "Variant A", "Variant B"). Solo steps use the step name.
   - Set `external_identifier` as a slugified version of the cadence name

4. **POST to `/v2/cadence_imports`** in a single call.

5. On success, the response returns:
```json
{
  "data": {
    "cadence": {
      "_href": "https://api.salesloft.com/v2/cadences/CADENCE_ID",
      "id": CADENCE_ID
    }
  }
}
```

6. **Verify** by listing steps:
```bash
curl -s "https://api.salesloft.com/v2/steps?cadence_id=${CADENCE_ID}" \
  -H "Authorization: Bearer ${SALESLOFT_KEY}"
```

7. Show the user a summary table and remind them the cadence is in **draft** state until activated in the SalesLoft UI.

## Assign Workflow (Add People to Cadence Under a Teammate's Name)

Use this workflow to add prospects to a cadence with a specific team member as the assignee. Emails send from the assignee's connected inbox, tasks appear in their to-do list, and `{{My.first_name}}` resolves to their name.

### Trigger
User says "assign", "add people", or asks to put prospects into a cadence under someone's name.

### Requirements
- The cadence MUST be a **team cadence** (`team_cadence: true`) for cross-user assignment
- You need the **SalesLoft user ID** of the assignee (not their email — resolve it live, below)
- You need the **SalesLoft person IDs** of the prospects to add

### Team Roster (resolve live)

Fetch the current user list and match teammate names/emails to their user IDs:
```bash
curl -s "https://api.salesloft.com/v2/users?per_page=100" -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```

Optionally cache the frequently-used subset in a local `roster.md` next to this skill (name | user_id | email) — treat the live endpoint as the source of truth and the cache as a convenience.

### Endpoint

**POST** `https://api.salesloft.com/v2/cadence_memberships`

**Headers:**
```
Authorization: Bearer ${SALESLOFT_KEY_WRITE}
Content-Type: application/json
Accept: application/json
```

### Single Person Payload

```json
{
  "person_id": 12345,
  "cadence_id": 67890,
  "user_id": 101878
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `person_id` | Yes | SalesLoft person ID of the prospect |
| `cadence_id` | Yes | SalesLoft cadence ID |
| `user_id` | No | SalesLoft user ID of the teammate to assign as runner. Defaults to API key holder if omitted. |
| `step_id` | No | ID of the step to start on (defaults to first step) |

### Bulk Endpoint

**POST** `https://api.salesloft.com/v2/cadence_bulk_memberships`

For adding multiple people at once:
```json
{
  "cadence_id": 67890,
  "user_id": 101878,
  "person_ids": [12345, 12346, 12347]
}
```

### What `user_id` Controls

- Automated emails send **from the assignee's connected email account**
- Tasks appear in **the assignee's** SalesLoft to-do list
- `{{My.first_name}}` resolves to **the assignee's** first name
- `{{My.email_address}}` resolves to **the assignee's** email

### Steps

1. **Identify the cadence** — get the cadence ID (from a previous push or by name lookup)
2. **Identify the assignee** — match the teammate name to their user ID via the users endpoint (or the local roster cache)
3. **Identify the prospects** — get SalesLoft person IDs (search by name/email if needed):
```bash
curl -s "https://api.salesloft.com/v2/people?search=jane.doe@company.com" \
  -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```
4. **Add to cadence** with the assignee's user_id
5. **Confirm** the membership was created (201 response)

## Bulk Person Lookup (Find SalesLoft Person IDs)

Resolve a list of contacts to their SalesLoft person IDs. Use when the user provides a spreadsheet/list of names and wants to find who already exists in SalesLoft.

### Trigger
User provides a list of contacts (names, emails, phones, companies) and asks to "look up", "find", "resolve", or "get SalesLoft IDs".

### Input Format
User typically provides tab-separated or comma-separated data with some combination of: email, first_name, last_name, title, company, phone, city, state, country. Parse whatever format they give you.

### Lookup Strategy (Two-Phase)

**Phase 1 — Name search (parallel):**
```bash
curl -s "https://api.salesloft.com/v2/people?first_name=Jane&last_name=Smith&per_page=5" \
  -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```
- Run ALL name lookups in parallel (15+ simultaneous curl calls is fine)
- The `first_name` + `last_name` filter is exact match and the most reliable method
- Returns all people matching that name across all companies

**Phase 2 — Email fallback (parallel, for misses only):**
```bash
curl -s "https://api.salesloft.com/v2/people?email_addresses=jane@company.com&per_page=5" \
  -H "Authorization: Bearer ${SALESLOFT_KEY}" -H "Accept: application/json"
```
- Run for contacts that returned zero results in Phase 1
- Also run for ambiguous Phase 1 results where multiple people matched but none had the right company
- The `email_addresses` filter is exact match on the email field

### What Works and What Doesn't

| Filter Parameter | Works? | Notes |
|-----------------|--------|-------|
| `first_name` + `last_name` | **Yes** | Best primary method. Exact match. |
| `email_addresses` | **Yes** | Best fallback. Exact match on email. |
| `search` | **No** | Full-text search, returns random unrelated results. Do NOT use. |
| `phone` | **No** | Does not filter by phone number. Returns random results. Do NOT use as a filter. |

### Name Variation Handling

When Phase 1 returns no results, try common name variants before falling back to email:
- Steve/Steven, Jeff/Jeffrey, Dan/Daniel, Mike/Michael, Bob/Robert, Bill/William
- Mindy/Melinda, Liz/Lizz/Elizabeth, Kate/Katherine, Jenny/Jennifer
- Only try the variant the user provided + one obvious alternative

### Disambiguating Multiple Results

Common names (Jeffrey Davis, Scott Schmidt, Keith Alexander) often return multiple people. Match the right one by checking these fields in priority order:
1. `email_address` — exact match against user's input email
2. `phone` — compare digits only (strip formatting)
3. `person_company_name` — fuzzy match against user's company name
4. `city` / `state` — geographic match

If no field matches confidently, flag it as ambiguous in the results table.

### Parallelization

- Batch all Phase 1 calls into a single message with parallel Bash tool calls (up to ~15 at once)
- Batch all Phase 2 calls into a second parallel round
- No rate limit issues observed at these volumes

### Output Format

Present results as a markdown table:

```
| Name | Person ID | Email in SalesLoft | Company in SL | Match |
|------|-----------|-------------------|---------------|-------|
| Jane Smith | **12345** | jane@co.com | Acme Corp | Exact |
| John Doe | -- | *Not in SalesLoft* | -- | No record |
```

End with a summary:
- **X found** — list of names and IDs ready for cadence assignment
- **Y not found** — these need to be created in SalesLoft first (via import or manual entry)

### Notes
- Person IDs are what you need for `cadence_memberships` and `cadence_bulk_memberships`
- Contacts not in SalesLoft cannot be added to cadences — they must be created first
- The `do_not_contact` field in results indicates DNC status — flag these for the user
- The `contact_restrictions` array may contain `"call"` or `"email"` — flag these too
- `bouncing: true` means their email is bouncing — flag for the user

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `sharing_settings.shared: must be true or false` | Missing `shared` field | Add `"shared": true` (or false) to sharing_settings |
| `step_groups.reference_id: is required` | Missing reference_id on step groups | Add unique `reference_id` to every step group |
| `body: contains invalid dynamic tags {{my_first_name}}` | Wrong tag syntax for sender fields | Use `{{My.first_name}}` (capital M, dot notation) |
| HTTP 404 on POST `/v2/cadences` | Wrong endpoint | Use `/v2/cadence_imports` instead |
| `external_identifier: is required` | Missing external_identifier | Add a unique slug string to settings |
| `person_id: has contact restrictions` (422) | Person is marked Do Not Contact | Skip this person — SalesLoft blocks DNC adds server-side |

## Limitations

- API keys typically do NOT have delete scope. Test/duplicate cadences must be cleaned up in the SalesLoft UI.
- Cadences are created in **draft** state. Activation happens in the UI.
- The `/v2/cadences` endpoint is **read-only** — all creation goes through `/v2/cadence_imports`.

## Bundled tools

- `export_cadence.py` — exports a SalesLoft cadence to a shareable text document. Reads the key from the `SALESLOFT_API_KEY` env var.
