/**
 * build_docx.js — SFDC Account Plan Builder
 *
 * Usage: node build_docx.js <account_data.json> <output.docx>
 *
 * Renders the fixed 12-section SFDC account plan structure from a JSON file
 * matching the schema in references/sfdc-template-map.md. Table lengths are
 * driven entirely by the JSON — this script never assumes a fixed number of
 * objectives, tracker actions, relationship-map contacts, or curriculum rows.
 *
 * Any value equal to "__MISSING__" (or an empty/absent array where one is
 * expected) renders as a visible flagged placeholder instead of blank space
 * or fabricated content.
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, WidthType, ShadingType, BorderStyle, AlignmentType,
  VerticalAlign, Header, Footer, PageNumber
} = require("docx");
const fs = require("fs");
const path = require("path");

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  console.error("Usage: node build_docx.js <account_data.json> <output.docx>");
  process.exit(1);
}
const data = JSON.parse(fs.readFileSync(inputPath, "utf-8"));

// ---- brand colors (SANS) ----
// Palette replaced 2026-07 to match the hand-edited "North Star 2.0" reboot
// document, reverse-engineered from its docx XML and a reference SWOT image.
const NAVY = "1F3864";        // was 00132C — universal table header color
const CORE_BLUE = "2E75B6";   // was 005580 — H1 borders, H2 text
const HEADER_GREEN = "D9EAD3"; // header color specifically for Customer/Competitive Landscape tables
const ZEBRA_GREY = "F2F2F2";  // alternating row shading on long multi-row tables
const VALUE_TINT = "EBF3FB";  // pale-blue tint for metric value cells and intro notes
const CALLOUT_YELLOW = "FFF2CC"; // unified Read:/Judgment: highlight background (was two near-identical hexes, FFF2CC/FFF8E1)
// SWOT quadrant colors — sampled from the user's reference image and matched
// against the docx's own hex values (which had header/content cross-wired
// within each quadrant); these are the corrected, uniform-per-quadrant values.
const SWOT_STRENGTHS = "E2EFDA";     // green
const SWOT_WEAKNESSES = "FFF2CC";    // yellow (same as CALLOUT_YELLOW)
const SWOT_OPPORTUNITIES = "DEEAF1"; // blue
const SWOT_THREATS = "FCE4D6";       // peach
const WHITE = "FFFFFF";
const GREY = "D2D2D2"; // header/footer divider line only — unrelated to table shading
const FLAG_COLOR = "9A5B00"; // amber — visually distinct for flagged placeholders, unchanged: no equivalent concept exists in the reference doc

const MISSING = "__MISSING__";
const isMissing = (v) => v === undefined || v === null || v === MISSING || (Array.isArray(v) && v.length === 0) || v === "";

function flagText(label) {
  return `\u26A0 ${label} not provided in source data. Needs input from account owner.`;
}

// Resolve a scalar value: returns {text, flagged}
function resolve(value, label) {
  if (isMissing(value)) return { text: flagText(label), flagged: true };
  return { text: String(value), flagged: false };
}

const borderAll = {
  top: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
  bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
  left: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
  right: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
};

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 140 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: CORE_BLUE, space: 4 } },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 30 })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 220, after: 100 },
    children: [new TextRun({ text, bold: true, color: CORE_BLUE, size: 24 })],
  });
}

// Parses **bold** segments out of a plain string into an array of
// {text, bold} run descriptors. Added for the North Star 3.0 "payoff-only
// labeling" pattern (see references/atomization-method.md): a Current
// Situation group is mostly unlabeled prose, with exactly one sentence
// (its Judgment, the payoff) marked bold via **double asterisks** in the
// JSON string. Not a general markdown parser — only handles this one
// convention, since that's the only one this schema needs.
function parseInlineBold(text) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  // split() on a capturing group alternates [plain, bold, plain, bold, ...]
  return parts.map((chunk, i) => ({ text: chunk, bold: i % 2 === 1 })).filter(r => r.text.length > 0);
}

function richRuns(text, size, opts = {}) {
  return parseInlineBold(text).map(r => new TextRun({
    text: r.text, size,
    bold: r.bold || opts.bold,
    italics: opts.italics,
    color: opts.color,
  }));
}

function p(textOrObj, opts = {}) {
  const isFlagged = typeof textOrObj === "object" && textOrObj.flagged;
  const text = typeof textOrObj === "object" ? textOrObj.text : textOrObj;
  if (isFlagged) {
    return new Paragraph({
      spacing: { after: 140, line: 276 },
      children: [new TextRun({ text, size: 21, italics: true, color: FLAG_COLOR })],
    });
  }
  return new Paragraph({
    spacing: { after: 140, line: 276 },
    children: richRuns(text, 21, opts),
  });
}

// Normalize any raw item that might be the literal "__MISSING__" string
// into a {text, flagged} object. Passes through already-resolved objects
// and ordinary strings unchanged.
function normalizeItem(item, label) {
  if (item === MISSING) return { text: flagText(label), flagged: true };
  return item;
}

function bullet(textOrObj, label) {
  const normalized = normalizeItem(textOrObj, label || "item");
  const isFlagged = typeof normalized === "object" && normalized.flagged;
  const text = typeof normalized === "object" ? normalized.text : normalized;
  if (isFlagged) {
    return new Paragraph({
      bullet: { level: 0 },
      spacing: { after: 80, line: 270 },
      children: [new TextRun({ text, size: 21, italics: true, color: FLAG_COLOR })],
    });
  }
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 80, line: 270 },
    children: richRuns(text, 21),
  });
}

function labelCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    borders: borderAll,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, size: 19, color: NAVY })] })],
  });
}

function valueCell(valueObj, width) {
  const isFlagged = valueObj.flagged;
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    borders: borderAll,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: valueObj.text, size: 19, italics: isFlagged, color: isFlagged ? FLAG_COLOR : undefined })] })],
  });
}

function headCell(text, width, opts = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: opts.color || NAVY },
    verticalAlign: VerticalAlign.CENTER,
    borders: borderAll,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, size: 19, color: opts.textColor || WHITE })] })],
  });
}

function bodyCell(content, width, opts = {}) {
  const items = Array.isArray(content) ? content : [content];
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.TOP,
    borders: borderAll,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    shading: opts.shade ? { type: ShadingType.CLEAR, fill: opts.shade } : undefined,
    children: items.map(t => {
      if (t instanceof Paragraph) return t;
      const flagged = typeof t === "object" && t.flagged;
      const text = typeof t === "object" ? t.text : t;
      return new Paragraph({ children: [new TextRun({ text, size: 18, bold: !!opts.bold, italics: flagged, color: flagged ? FLAG_COLOR : undefined })] });
    }),
  });
}

// Returns ZEBRA_GREY or WHITE alternating by zero-indexed data-row number,
// for long multi-row tables (Objectives, Tracker, Relationship Map,
// Curriculum, Refresh Log) — matches the reference document's explicit
// per-row shading rather than leaving alternate rows unshaded.
function zebraShade(rowIndex) {
  return rowIndex % 2 === 0 ? WHITE : ZEBRA_GREY;
}

function bulletListCell(items, width, label, opts = {}) {
  if (isMissing(items)) {
    return bodyCell([{ text: flagText(label), flagged: true }], width, opts);
  }
  return bodyCell(items.map(t => bullet(t, label)), width, opts);
}

function calloutBox(title, textObj) {
  const isFlagged = typeof textObj === "object" && textObj.flagged;
  const text = typeof textObj === "object" ? textObj.text : textObj;
  const titleParagraph = title
    ? [new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, size: 19, color: NAVY })] })]
    : [];
  return new Table({
    width: { size: 9350, type: WidthType.DXA },
    columnWidths: [9350],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: 9350, type: WidthType.DXA },
            shading: { type: ShadingType.CLEAR, fill: CALLOUT_YELLOW },
            borders: {
              top: { style: BorderStyle.SINGLE, size: 12, color: CORE_BLUE },
              bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
              left: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
              right: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
            },
            margins: { top: 140, bottom: 140, left: 180, right: 180 },
            children: [
              ...titleParagraph,
              new Paragraph({ children: [new TextRun({ text, size: 19, italics: isFlagged, color: isFlagged ? FLAG_COLOR : undefined })] }),
            ],
          }),
        ],
      }),
    ],
  });
}

// ---- section builders driven by JSON ----

function buildPlanHeader(d) {
  const w1 = 1550, w2 = 3125;
  return new Table({
    width: { size: 9350, type: WidthType.DXA },
    columnWidths: [w1, w2, w1, w2],
    rows: [
      new TableRow({ children: [labelCell("Account Name", w1), valueCell(resolve(d.account_name, "Account Name"), w2), labelCell("Plan Owner", w1), valueCell(resolve(d.plan_owner, "Plan Owner"), w2)] }),
      new TableRow({ children: [labelCell("Plan Status", w1), valueCell(resolve(d.plan_status, "Plan Status"), w2), labelCell("Segment", w1), valueCell(resolve(d.segment, "Segment"), w2)] }),
      new TableRow({ children: [labelCell("Plan Start Date", w1), valueCell(resolve(d.plan_start, "Plan Start Date"), w2), labelCell("Plan End Date", w1), valueCell(resolve(d.plan_end, "Plan End Date"), w2)] }),
      new TableRow({ children: [labelCell("Account Type", w1), valueCell(resolve(d.account_type, "Account Type"), w2), labelCell("SFDC Account ID", w1), valueCell(resolve(d.sfdc_id, "SFDC Account ID"), w2)] }),
    ],
  });
}

function buildMetricsTable(columns) {
  if (isMissing(columns)) {
    return calloutBox(null, flagText("Account Metrics"));
  }
  const n = columns.length;
  const w = Math.floor(9350 / n);
  return new Table({
    width: { size: 9350, type: WidthType.DXA },
    columnWidths: columns.map(() => w),
    rows: [
      new TableRow({ children: columns.map(c => headCell(c.label || "\u2014", w)) }),
      new TableRow({ children: columns.map(c => bodyCell([{ text: c.value || "\u2014" }, { text: c.sublabel || "" }], w, { bold: true, shade: VALUE_TINT })) }),
    ],
  });
}

function buildTwoColTable(headerLeft, headerRight, leftItems, rightItems, leftLabel, rightLabel, opts = {}) {
  const w = 4675;
  const headColor = opts.headerColor || undefined;
  return new Table({
    width: { size: 9350, type: WidthType.DXA },
    columnWidths: [w, w],
    rows: [
      new TableRow({ children: [headCell(headerLeft, w, { color: headColor }), headCell(headerRight, w, { color: headColor })] }),
      new TableRow({ children: [bulletListCell(leftItems, w, leftLabel), bulletListCell(rightItems, w, rightLabel)] }),
    ],
  });
}

function buildObjectivesTable(objectives) {
  const widths = [2200, 1500, 1700, 900, 1150, 1900];
  const headers = ["Objective", "Current Value", "Target Value", "Start", "End Date", "Owner"];
  const rows = [new TableRow({ children: headers.map((hh, i) => headCell(hh, widths[i])) })];
  if (isMissing(objectives)) {
    rows.push(new TableRow({ children: [bodyCell([{ text: flagText("Account Objectives"), flagged: true }], 9350)] }));
    return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: [9350], rows: [rows[0], rows[1]] });
  }
  objectives.forEach((o, i) => {
    const shade = zebraShade(i);
    rows.push(new TableRow({ children: [
      bodyCell(resolve(o.objective, "Objective"), widths[0], { shade }),
      bodyCell(resolve(o.current, "Current Value"), widths[1], { shade }),
      bodyCell(resolve(o.target, "Target Value"), widths[2], { shade }),
      bodyCell(resolve(o.start, "Start"), widths[3], { shade }),
      bodyCell(resolve(o.end, "End Date"), widths[4], { shade }),
      bodyCell(resolve(o.owner, "Owner"), widths[5], { shade }),
    ]}));
  });
  return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: widths, rows });
}

function buildTrackerTable(tracker) {
  const widths = [3200, 1300, 1650, 1400, 1800];
  const headers = ["Action / Task", "Linked Obj.", "Contact", "Due Date", "Owner"];
  const rows = [new TableRow({ children: headers.map((hh, i) => headCell(hh, widths[i])) })];
  if (isMissing(tracker)) {
    rows.push(new TableRow({ children: [bodyCell([{ text: flagText("Strategic Tracker"), flagged: true }], 9350)] }));
    return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: [9350], rows: [rows[0], rows[1]] });
  }
  tracker.forEach((t, i) => {
    const shade = zebraShade(i);
    const actionResolved = resolve(t.action, "Action/Task");
    const actionLines = actionResolved.flagged
      ? [actionResolved]
      : [
          actionResolved,
          { text: `Start: ${isMissing(t.start_date) ? flagText("Start Date") : t.start_date}`, flagged: isMissing(t.start_date) },
          { text: `Status: ${isMissing(t.status) ? flagText("Status") : t.status}`, flagged: isMissing(t.status) },
        ];
    const dueResolved = resolve(t.due, "Due");
    const dueLines = dueResolved.flagged
      ? [dueResolved]
      : [dueResolved, { text: `(${isMissing(t.due_provenance) ? flagText("Due Provenance") : t.due_provenance})`, flagged: isMissing(t.due_provenance) }];
    rows.push(new TableRow({ children: [
      bodyCell(actionLines, widths[0], { shade }),
      bodyCell(resolve(t.linked_obj, "Linked Objective"), widths[1], { shade }),
      bodyCell(resolve(t.contact, "Contact"), widths[2], { shade }),
      bodyCell(dueLines, widths[3], { shade }),
      bodyCell(resolve(t.owner, "Owner"), widths[4], { shade }),
    ]}));
  });
  return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: widths, rows });
}

function buildRelationshipTable(rm) {
  const widths = [2000, 1400, 1500, 1250, 2200];
  const headers = ["Name / Title", "Role in Decision", "SANS Sentiment", "Our Access", "Next Action"];
  const rows = [new TableRow({ children: headers.map((hh, i) => headCell(hh, widths[i])) })];
  const contacts = rm && rm.contacts;
  if (isMissing(contacts)) {
    rows.push(new TableRow({ children: [bodyCell([{ text: flagText("Relationship Map"), flagged: true }], 9350)] }));
    return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: [9350], rows: [rows[0], rows[1]] });
  }
  contacts.forEach((c, i) => {
    const shade = zebraShade(i);
    rows.push(new TableRow({ children: [
      bodyCell(resolve(c.name_title, "Name/Title"), widths[0], { shade }),
      bodyCell(resolve(c.role, "Role in Decision"), widths[1], { shade }),
      bodyCell(resolve(c.sentiment, "SANS Sentiment"), widths[2], { shade }),
      bodyCell(resolve(c.access, "Our Access"), widths[3], { shade }),
      bodyCell(resolve(c.next_action, "Next Action"), widths[4], { shade }),
    ]}));
  });
  return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: widths, rows });
}

function buildCurriculumTable(curr) {
  const widths = [2100, 1600, 1900, 1750, 2000];
  const headers = ["Customer Role / Team", "SANS Curriculum", "Priority Courses", "Buyer / Persona Fit", "Status / Next Step"];
  const rows = [new TableRow({ children: headers.map((hh, i) => headCell(hh, widths[i])) })];
  const dataRows = curr && curr.rows;
  if (isMissing(dataRows)) {
    rows.push(new TableRow({ children: [bodyCell([{ text: flagText("SANS Curriculum Targeting"), flagged: true }], 9350)] }));
    return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: [9350], rows: [rows[0], rows[1]] });
  }
  dataRows.forEach((r, i) => {
    const shade = zebraShade(i);
    rows.push(new TableRow({ children: [
      bodyCell(resolve(r.role_team, "Customer Role/Team"), widths[0], { shade }),
      bodyCell(resolve(r.curriculum, "SANS Curriculum"), widths[1], { shade }),
      bodyCell(resolve(r.courses, "Priority Courses"), widths[2], { shade }),
      bodyCell(resolve(r.persona_fit, "Buyer/Persona Fit"), widths[3], { shade }),
      bodyCell(resolve(r.status, "Status/Next Step"), widths[4], { shade }),
    ]}));
  });
  return new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: widths, rows });
}

// ---- assemble document ----

const accountName = isMissing(data.account_name) ? "[Account Name Missing]" : data.account_name;

const children = [];

children.push(
  new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "SANS Sales Account Plan", bold: true, size: 40, color: NAVY })] }),
  new Paragraph({ spacing: { after: 260 }, children: [new TextRun({ text: `${accountName}  |  Account Plan  |  ${isMissing(data.segment) ? "Segment TBD" : data.segment}`, size: 22, color: CORE_BLUE })] }),
);

children.push(h1("Plan Header"));
children.push(buildPlanHeader(data));
children.push(p(""));
children.push(p(resolve(data.plan_window_note, "Plan Window Note"), { italics: true, color: "444444" }));

children.push(h1("Account Metrics"));
children.push(buildMetricsTable(data.metrics && data.metrics.columns));
children.push(p(""));
children.push(calloutBox(null, resolve(data.metrics && data.metrics.read, "Account Metrics Read")));

children.push(h1("Account Vision"));
children.push(p(resolve(data.vision, "Account Vision"), { bold: true }));

children.push(h1("Account Notes"));
children.push(h2("Current Situation"));
if (isMissing(data.current_situation_paragraphs)) {
  children.push(p({ text: flagText("Current Situation"), flagged: true }));
} else {
  // Each entry is either a plain string, or an object in one of two shapes:
  //   { text, _source, _brief_refs }                — one flowing paragraph
  //   { lead, bullets, _source, _brief_refs }         — lead-in + bullets
  // _source ("brief" | "ledger") and _brief_refs (array of brief element
  // IDs) are provenance metadata, not rendering content — added North Star
  // 3.0 so cross_check.py can scope its docx-vs-brief check to real
  // per-group routing instead of guessing from section names (see
  // scripts/cross_check.py and voice-spec.md, "Per-Atom Routing"). They
  // are read here only to be ignored; nothing below renders them.
  // See references/atomization-method.md, Step 7. In both shapes, the
  // group's one Judgment/payoff sentence is marked with **bold** in the
  // JSON string and rendered bold via parseInlineBold() — every other
  // sentence in the group runs unlabeled.
  data.current_situation_paragraphs.forEach(entry => {
    if (entry === MISSING) {
      children.push(p({ text: flagText("Current Situation paragraph"), flagged: true }));
    } else if (typeof entry === "object" && entry !== null && !entry.flagged && Array.isArray(entry.bullets)) {
      children.push(p(entry.lead));
      entry.bullets.forEach(b => children.push(bullet(b)));
    } else if (typeof entry === "object" && entry !== null && !entry.flagged && typeof entry.text === "string") {
      children.push(p(entry.text));
    } else {
      children.push(p(normalizeItem(entry, "Current Situation paragraph")));
    }
  });
}

children.push(h2("Key Risks"));
if (isMissing(data.key_risks)) {
  children.push(p({ text: flagText("Key Risks"), flagged: true }));
} else {
  data.key_risks.forEach(r => children.push(bullet(r)));
}

children.push(h2("Internal SANS Alignment Needed"));
children.push(p(resolve(data.internal_alignment, "Internal SANS Alignment Needed")));

children.push(h1("SWOT Analysis"));
const swot = data.swot || {};
children.push(new Table({
  width: { size: 9350, type: WidthType.DXA },
  columnWidths: [4675, 4675],
  rows: [
    new TableRow({ children: [
      headCell("Strengths", 4675, { color: SWOT_STRENGTHS, textColor: NAVY }),
      headCell("Weaknesses", 4675, { color: SWOT_WEAKNESSES, textColor: NAVY }),
    ]}),
    new TableRow({ children: [
      bulletListCell(swot.strengths, 4675, "Strengths", { shade: SWOT_STRENGTHS }),
      bulletListCell(swot.weaknesses, 4675, "Weaknesses", { shade: SWOT_WEAKNESSES }),
    ]}),
    new TableRow({ children: [
      headCell("Opportunities", 4675, { color: SWOT_OPPORTUNITIES, textColor: NAVY }),
      headCell("Threats", 4675, { color: SWOT_THREATS, textColor: NAVY }),
    ]}),
    new TableRow({ children: [
      bulletListCell(swot.opportunities, 4675, "Opportunities", { shade: SWOT_OPPORTUNITIES }),
      bulletListCell(swot.threats, 4675, "Threats", { shade: SWOT_THREATS }),
    ]}),
  ],
}));

children.push(h1("Customer Landscape"));
children.push(h2("Strategic Priorities and KPIs"));
const cl = data.customer_landscape || {};
children.push(buildTwoColTable("Customer Strategic Priorities", "Customer KPIs / Success Metrics", cl.priorities, cl.kpis, "Strategic Priorities", "KPIs", { headerColor: HEADER_GREEN }));
children.push(p(""));
children.push(h2("Challenges and Industry Trends"));
children.push(buildTwoColTable("Challenges Facing the Customer", "Industry Trends Relevant to SANS", cl.challenges, cl.trends, "Challenges", "Trends", { headerColor: HEADER_GREEN }));

children.push(h1("Competitive Landscape"));
const comp = data.competitive || {};
children.push(buildTwoColTable(`SANS Competitive Strengths at ${accountName}`, `SANS Competitive Weaknesses at ${accountName}`, comp.strengths, comp.weaknesses, "Competitive Strengths", "Competitive Weaknesses", { headerColor: HEADER_GREEN }));
children.push(p(""));
children.push(p(resolve(comp.footer, "Competitive Landscape Footer")));

children.push(h1("Account Objectives"));
children.push(buildObjectivesTable(data.objectives));

children.push(h1("Strategic Tracker (Action Plan)"));
children.push(buildTrackerTable(data.tracker));

children.push(h1("Relationship Map"));
const rm = data.relationship_map || {};
if (!isMissing(rm.note)) {
  children.push(calloutBox("FINDING", rm.note));
  children.push(p(""));
}
children.push(buildRelationshipTable(rm));
if (!isMissing(rm.dropped_note)) {
  children.push(p(""));
  children.push(p(rm.dropped_note, { italics: true, color: "444444" }));
}

children.push(h1("SANS Curriculum Targeting"));
const curr = data.curriculum || {};
if (!isMissing(curr.note)) {
  children.push(p(curr.note, { italics: true, color: "444444" }));
}
children.push(buildCurriculumTable(curr));
if (!isMissing(curr.footer)) {
  children.push(p(""));
  children.push(p(curr.footer, { italics: true, color: "444444" }));
}

children.push(h1("Plan Refresh Log"));
const refreshLog = Array.isArray(data.refresh_log) ? data.refresh_log : (isMissing(data.refresh_log) ? [] : [data.refresh_log]);
if (refreshLog.length === 0) {
  children.push(calloutBox(null, { text: flagText("Plan Refresh Log"), flagged: true }));
} else {
  const rlRows = [new TableRow({ children: [headCell("Date", 1400), headCell("Updated By", 1800), headCell("What Changed / Key Insight", 6150)] })];
  refreshLog.forEach((entry, i) => {
    const shade = zebraShade(i);
    rlRows.push(new TableRow({ children: [
      bodyCell(resolve(entry.date, "Date"), 1400, { shade }),
      bodyCell(resolve(entry.updated_by, "Updated By"), 1800, { shade }),
      bodyCell(resolve(entry.summary, "Summary"), 6150, { shade }),
    ]}));
  });
  children.push(new Table({ width: { size: 9350, type: WidthType.DXA }, columnWidths: [1400, 1800, 6150], rows: rlRows }));
}

children.push(h1("Source Notes and Citation IDs"));
const sn = data.source_notes || {};
if (!isMissing(sn.source_file) || !isMissing(sn.intro)) {
  const sourceLine = `Source-of-truth: ${isMissing(sn.source_file) ? flagText("Source File").text : sn.source_file}. ${isMissing(sn.intro) ? "" : sn.intro}`;
  children.push(p(sourceLine));
}
const citationGroups = sn.citation_groups;
if (isMissing(citationGroups)) {
  children.push(p({ text: flagText("Source Notes and Citation IDs"), flagged: true }));
} else {
  citationGroups.forEach(group => {
    const idsResolved = isMissing(group.ids) ? flagText(`${group.label || "Citation group"} IDs`) : group.ids.join(", ");
    children.push(p(`${resolve(group.label, "Citation group label").text}: [${idsResolved}].`));
  });
}
if (!isMissing(sn.corrections_retained)) {
  children.push(p(`Template corrections retained from source: ${sn.corrections_retained}`));
}
if (!isMissing(sn.unknown_from_source)) {
  children.push(p(`Unknown from source: ${sn.unknown_from_source}`));
}

children.push(new Paragraph({ spacing: { before: 300 }, children: [] }));

const doc = new Document({
  sections: [
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 900, bottom: 900, left: 900, right: 900 } } },
      headers: {
        default: new Header({
          children: [new Paragraph({
            children: [
              new TextRun({ text: "SANS Sales Account Plan", bold: true, size: 16, color: NAVY }),
              new TextRun({ text: `   |   ${accountName}   |   ${isMissing(data.segment) ? "" : data.segment}`, size: 16, color: "555555" }),
            ],
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: GREY, space: 4 } },
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: `SANS Institute \u2014 BD Account Plan | Internal Use Only | ${accountName} | Sync objectives to Salesforce | Page `, size: 15, color: "777777" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 15, color: "777777" }),
            ],
          })],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outputPath, buf);
  console.log(`Wrote ${outputPath}`);
});
