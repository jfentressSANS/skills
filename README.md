# skills

Shared directory of Claude Code skills that are actively used or in development across the team.

## Structure

- `sales/` — skills used by the sales org (e.g. account planning)
- `customer-support/` — skills used by the customer support org

Each skill lives in its own subdirectory containing a `SKILL.md` file.

## Adding a skill

1. Create a subdirectory under the relevant category folder, named after the skill (e.g. `sales/account-plan/`).
2. Copy in the skill's `SKILL.md` (and any supporting files).
3. Commit and push.

Skills here are copies for sharing and review — installed skills live locally under `~/.claude/skills/` and are not affected by changes in this repo.

## Status

| Skill | Category | Status |
|---|---|---|
| [account-plan](sales/account-plan/SKILL.md) | sales | active |
| [hermes](sales/hermes/SKILL.md) | sales | active |
| [sf-campaign](sales/sf-campaign/SKILL.md) | sales | active |
| [sf-contact-create](sales/sf-contact-create/SKILL.md) | sales | active |
| [sfdc-account-plan-builder](sales/sfdc-account-plan-builder/SKILL.md) | sales | active |

## Setup convention

Every published skill opens with a **Setup** section — the only install-specific values (org alias, instance URL, key file paths, defaults) live there, and the rest of the skill references them. Credentials are never stored in a skill: env files stay local (`*.env` is gitignored here; only `*.env.example` templates ship).
