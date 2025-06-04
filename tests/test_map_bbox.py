import tempfile
from pathlib import Path

from fpdf import FPDF
from backend.src.diff_pdf import extract_pdf_text, compare_text, extract_lines_with_coords, map_diffs_to_bboxes


def _create_pdf(path: Path, lines):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 10, txt=line, ln=1)
    pdf.output(str(path))


def test_map_diffs(tmp_path):
    pdf1 = tmp_path / "a.pdf"
    pdf2 = tmp_path / "b.pdf"
    _create_pdf(pdf1, ["Hello", "World"])
    _create_pdf(pdf2, ["Hello", "there", "World"])

    text1 = extract_pdf_text(pdf1)
    text2 = extract_pdf_text(pdf2)
    diffs = compare_text(text1, text2)
    pages1 = extract_lines_with_coords(pdf1)
    pages2 = extract_lines_with_coords(pdf2)
    result = map_diffs_to_bboxes(diffs, text1, text2, pages1, pages2)
    types = {r["type"] for r in result}
    assert "INSERT" in types
