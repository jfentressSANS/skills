#!/usr/bin/env python3
"""Export a SalesLoft cadence to a shareable text document."""

import json
import os
import re
import subprocess
import sys

API_KEY = os.environ.get("SALESLOFT_API_KEY", "")
BASE = "https://api.salesloft.com/v2"


def api_get(path):
    result = subprocess.run(
        ["curl", "-s", f"{BASE}{path}", "-H", f"Authorization: Bearer {API_KEY}"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


def strip_html(html):
    """Convert HTML body to plain text, one line per <p> block."""
    # Remove wrapper div
    text = re.sub(r'<div[^>]*>', '', html)
    text = text.replace('</div>', '')
    # Replace </p><p> with newlines
    text = re.sub(r'</p>\s*<p>', '\n\n', text)
    # Remove remaining tags
    text = re.sub(r'</?p>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up entities and whitespace
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('\u2014', '—').replace('\u2019', "'")
    return text.strip()


def export_cadence(cadence_id):
    # Get cadence metadata
    cadence = api_get(f"/cadences/{cadence_id}")["data"]
    name = cadence["name"]
    owner = cadence.get("creator", {})
    team = "Team" if cadence.get("team_cadence") else "Personal"
    draft = "Draft" if cadence.get("draft") else "Active"

    # Get steps sorted by step_number
    steps_data = api_get(f"/steps?cadence_id={cadence_id}&per_page=100")["data"]
    steps_data.sort(key=lambda s: s["step_number"])

    # Build output
    lines = []
    lines.append("=" * 65)
    lines.append(f"CADENCE: {name}")
    lines.append("=" * 65)
    lines.append("")
    lines.append(f"ID: {cadence_id}")
    lines.append(f"Status: {draft} | Visibility: {team}")
    lines.append(f"Steps: {len(steps_data)}")
    lines.append("")

    for step in steps_data:
        step_num = step["step_number"]
        day = step["day"]
        step_type = step["type"]
        step_name = step.get("name", f"Step {step_num}")

        lines.append("-" * 65)
        lines.append(f"STEP {step_num} | Day {day} | {step_name}")
        lines.append("-" * 65)

        if step_type == "email":
            detail_id = step["details"]["id"]
            detail = api_get(f"/action_details/email_details/{detail_id}")["data"]
            template_id = detail["email_template"]["id"]
            template = api_get(f"/email_templates/{template_id}")["data"]

            subject = template.get("subject", "")
            body_html = template.get("body", "")
            body_text = strip_html(body_html)

            if subject:
                lines.append(f"SUBJECT: {subject}")
                lines.append("")
            lines.append(body_text)
        elif step_type in ("phone", "other"):
            lines.append(f"[{step_type.upper()} STEP]")

        lines.append("")

    lines.append("=" * 65)

    return "\n".join(lines), name


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: export_cadence.py <cadence_id> [output_path]")
        sys.exit(1)

    cid = sys.argv[1]
    text, name = export_cadence(cid)

    if len(sys.argv) >= 3:
        out_path = sys.argv[2]
    else:
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        out_path = os.path.expanduser(f"~/Desktop/{slug}.txt")

    with open(out_path, "w") as f:
        f.write(text)

    print(f"Exported to: {out_path}")
