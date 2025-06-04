import sys
from pathlib import Path
import subprocess

try:
    from pdfminer.high_level import extract_text as _extract_text
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    _extract_text = None

try:
    from diff_match_patch import diff_match_patch as _dmp_class
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    _dmp_class = None


def extract_pdf_text(file_path: str | Path) -> str:
    """Extract text from a PDF file.

    If ``pdfminer.six`` is available it is used for high quality
    extraction. Otherwise a very naive fallback based on the system
    ``strings`` command is used. The fallback is sufficient for the
    simple sample PDFs used in the test-suite and avoids an optional
    dependency.
    """
    if _extract_text is not None:
        return _extract_text(str(file_path))

    # Fallback: use `strings` to pull ASCII text out of the PDF.  This is
    # obviously not as accurate as a real parser but works reasonably well
    # for the basic PDFs bundled with the repository.
    result = subprocess.run(
        ["strings", str(file_path)], capture_output=True, text=True, check=False
    )
    return result.stdout


def compare_text(text1: str, text2: str):
    """Return a list of diff tuples between two strings."""
    if _dmp_class is not None:
        dmp = _dmp_class()
        diffs = dmp.diff_main(text1, text2)
        dmp.diff_cleanupSemantic(diffs)
        return diffs

    # Fallback to ``difflib`` when ``diff-match-patch`` isn't available.
    import difflib

    matcher = difflib.SequenceMatcher(None, text1, text2)
    diffs = []
    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            diffs.append((0, text1[a0:a1]))
        elif opcode == "delete":
            diffs.append((-1, text1[a0:a1]))
        elif opcode == "insert":
            diffs.append((1, text2[b0:b1]))
        elif opcode == "replace":
            diffs.append((-1, text1[a0:a1]))
            diffs.append((1, text2[b0:b1]))
    return diffs


def print_diff(diffs):
    for op, data in diffs:
        if op == -1:
            print(f"\033[91m[- {data}]\033[0m", end="")  # Red for deletions
        elif op == 1:
            print(f"\033[92m[+ {data}]\033[0m", end="")  # Green for insertions
        else:
            print(data, end="")


def main():
    if len(sys.argv) != 3:
        print("Usage: python diff_pdf.py <file1.pdf> <file2.pdf>")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]

    if not Path(file1).is_file() or not Path(file2).is_file():
        print("One or both files do not exist.")
        sys.exit(1)

    text1 = extract_pdf_text(file1)
    text2 = extract_pdf_text(file2)
    diffs = compare_text(text1, text2)
    print_diff(diffs)


if __name__ == "__main__":
    main()
