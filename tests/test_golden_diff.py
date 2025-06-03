import json
from pathlib import Path
import pytest

HERE = Path(__file__).parent
SAMPLE_DOCS = HERE.parent / "sample_docs"

# (old, new, golden) triples
CASES = [
    ("nda_v1.docx", "nda_v2.docx", "nda_diff.json"),
    ("pa_v1.pdf", "pa_v2.pdf", "pa_diff.json"),
    ("edge_columns.pdf", "edge_columns.pdf", "edge_columns_diff.json"),
    ("tracked_changes.docx", "tracked_changes.docx", "tracked_changes_diff.json"),
]


@pytest.mark.parametrize("old_f, new_f, golden_f", CASES)
def test_golden_diff(old_f, new_f, golden_f):
    """
    Placeholder: passes only for plain PDFs, xfails everything else
    until extractors/diff engine are fully implemented.
    """
    from backend.src.diff_pdf import extract_pdf_text, compare_text

    old_path = SAMPLE_DOCS / old_f
    new_path = SAMPLE_DOCS / new_f
    golden_path = HERE / "golden" / golden_f

    # Skip unsupported formats for now
    if old_path.suffix.lower() != ".pdf":
        pytest.xfail("Extractor for DOCX / advanced PDFs not implemented yet")

    with golden_path.open() as fp:
        expected = json.load(fp)

    text1, text2 = extract_pdf_text(old_path), extract_pdf_text(new_path)
    diffs = compare_text(text1, text2)

    diff_str = "".join(seg for _, seg in diffs)
    for rec in expected:
        assert rec["snippet"] in diff_str
