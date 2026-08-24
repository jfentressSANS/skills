#!/usr/bin/env python3
"""
extract_docx_text.py — Clean text extraction for lint scanning

Extracts all paragraph and table-cell text from a .docx in document order,
one item per line, with NO table-border rendering. This exists specifically
because `pandoc -t plain` renders tables as ASCII grids
(+-----------------------------------------------------------------------+),
and long hyphen runs in those borders get miscounted as em-dashes by
lint_gate.py's em-dash scanner (confirmed during the Deere diagnostic:
pandoc extraction reported 1,219 "em-dashes" in a docx containing zero
actual em-dash characters). Reading the docx's own paragraph/table model
directly avoids the whole class of border-artifact false positives.

Usage:
    python extract_docx_text.py <input.docx> <output.txt>
"""

import sys
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table


def iter_block_items(parent):
    """Yield each paragraph and table in document order (top-level body only)."""
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


def extract_text(docx_path: str) -> str:
    doc = Document(docx_path)
    lines = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                lines.append(text)
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        # Tagged distinctly from prose paragraphs so downstream
                        # checks (e.g. the North Star 3.0 contraction rule,
                        # which only applies to narrative prose) can exclude
                        # table cells, Plan Header values, and data fields.
                        # The tag is stripped before any text-content checks —
                        # it only affects which bucket a line counts toward.
                        lines.append(f"[TABLE] {cell_text}")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_docx_text.py <input.docx> <output.txt>")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: file not found: {input_path}")
        sys.exit(2)

    text = extract_text(str(input_path))
    output_path.write_text(text, encoding="utf-8")
    print(f"Extracted {len(text.splitlines())} lines to {output_path}")


if __name__ == "__main__":
    main()
