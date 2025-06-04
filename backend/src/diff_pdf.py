import sys
from pathlib import Path
import difflib

from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTTextLine
from diff_match_patch import diff_match_patch


def extract_pdf_text(file_path):
    return extract_text(file_path)


def compare_text(text1, text2):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(text1, text2)
    dmp.diff_cleanupSemantic(diffs)
    return diffs


def print_diff(diffs):
    for op, data in diffs:
        if op == -1:
            print(f"\033[91m[- {data}]\033[0m", end="")  # Red for deletions
        elif op == 1:
            print(f"\033[92m[+ {data}]\033[0m", end="")  # Green for insertions
        else:
            print(data, end="")


def extract_line_bboxes(file_path):
    """Return mapping of page number to LTTextLine bounding boxes."""
    pages = {}
    for page_num, page in enumerate(extract_pages(file_path), start=1):
        boxes = []
        for element in page:
            if isinstance(element, LTTextContainer):
                for obj in element:
                    if isinstance(obj, LTTextLine):
                        boxes.append(tuple(obj.bbox))
        pages[page_num] = boxes
    return pages


def extract_lines_with_coords(file_path):
    """Extract text lines with their bounding boxes for each page."""
    pages = {}
    for page_num, page in enumerate(extract_pages(file_path), start=1):
        lines = []
        for element in page:
            if isinstance(element, LTTextContainer):
                for obj in element:
                    if isinstance(obj, LTTextLine):
                        text = obj.get_text().strip()
                        if text:
                            x0, y0, x1, y1 = obj.bbox
                            lines.append({
                                "text": text,
                                "bbox": [x0, y0, x1, y1],
                            })
        pages[page_num] = lines
    return pages


def _flatten_pages(pages, full_text):
    """Return lines with start/end offsets for easier lookup."""
    flat = []
    offset = 0
    for page in sorted(pages.keys()):
        for line in pages[page]:
            idx = full_text.find(line["text"], offset)
            if idx == -1:
                idx = full_text.find(line["text"])
                if idx == -1:
                    continue
            line_rec = {
                "page": page,
                "bbox": line["bbox"],
                "text": line["text"],
                "start": idx,
                "end": idx + len(line["text"]),
            }
            flat.append(line_rec)
            offset = idx + len(line["text"])
    flat.sort(key=lambda r: r["start"])
    return flat


def _boxes_for_range(lines, start, end):
    boxes = []
    for line in lines:
        if line["end"] <= start:
            continue
        if line["start"] >= end:
            break
        boxes.append({"page": line["page"], "bbox": line["bbox"], "text": line["text"]})
    return boxes


def map_diffs_to_bboxes(diffs, text1, text2, pages1, pages2):
    """Map diff_match_patch results to bounding boxes."""
    lines1 = _flatten_pages(pages1, text1)
    lines2 = _flatten_pages(pages2, text2)

    idx1 = 0
    idx2 = 0
    records = []
    for op, data in diffs:
        length = len(data)
        if op == 0:
            idx1 += length
            idx2 += length
            continue
        if op == -1:
            boxes = _boxes_for_range(lines1, idx1, idx1 + length)
            for b in boxes:
                b["type"] = "DELETE"
            records.extend(boxes)
            idx1 += length
        elif op == 1:
            boxes = _boxes_for_range(lines2, idx2, idx2 + length)
            for b in boxes:
                b["type"] = "INSERT"
            records.extend(boxes)
            idx2 += length
    return records


def dmp_diff_with_coords(file1, file2):
    """Convenience wrapper to diff two PDFs with bounding boxes."""
    text1 = extract_pdf_text(file1)
    text2 = extract_pdf_text(file2)
    diffs = compare_text(text1, text2)
    pages1 = extract_lines_with_coords(file1)
    pages2 = extract_lines_with_coords(file2)
    return map_diffs_to_bboxes(diffs, text1, text2, pages1, pages2)


def diff_with_coords(file1, file2):
    """Return list of diff records with bounding boxes."""
    pages1 = extract_lines_with_coords(file1)
    pages2 = extract_lines_with_coords(file2)

    seq1 = []
    seq1_meta = []
    for pnum, lines in pages1.items():
        for line in lines:
            seq1.append(line["text"])
            seq1_meta.append((pnum, line))

    seq2 = []
    seq2_meta = []
    for pnum, lines in pages2.items():
        for line in lines:
            seq2.append(line["text"])
            seq2_meta.append((pnum, line))

    matcher = difflib.SequenceMatcher(None, seq1, seq2)
    records = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag in ("replace", "delete"):
            for idx in range(i1, i2):
                p, line = seq1_meta[idx]
                rec_type = "DELETE" if tag == "delete" else "MODIFY"
                records.append({
                    "page": p,
                    "bbox": line["bbox"],
                    "type": rec_type,
                    "text": line["text"],
                })
        if tag in ("replace", "insert"):
            for idx in range(j1, j2):
                p, line = seq2_meta[idx]
                rec_type = "INSERT" if tag == "insert" else "MODIFY"
                records.append({
                    "page": p,
                    "bbox": line["bbox"],
                    "type": rec_type,
                    "text": line["text"],
                })
    return records


def main():
    """Simple CLI for debugging and manual diff generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Diff two PDFs")
    parser.add_argument("file1")
    parser.add_argument("file2")
    parser.add_argument("--json", action="store_true", help="Output JSON with coordinates")
    args = parser.parse_args()

    file1, file2 = args.file1, args.file2

    if not Path(file1).is_file() or not Path(file2).is_file():
        print("One or both files do not exist.")
        sys.exit(1)

    if args.json:
        records = dmp_diff_with_coords(file1, file2)
        import json

        print(json.dumps(records, indent=2))
    else:
        text1 = extract_pdf_text(file1)
        text2 = extract_pdf_text(file2)
        diffs = compare_text(text1, text2)
        print_diff(diffs)


if __name__ == "__main__":
    main()
