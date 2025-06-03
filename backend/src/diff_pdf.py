import sys
from pdfminer.high_level import extract_text
from diff_match_patch import diff_match_patch
from pathlib import Path


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
