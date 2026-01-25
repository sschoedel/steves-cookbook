#!/usr/bin/env python3
"""Clean up HTML entities in recipe files."""

import html
import re
from pathlib import Path


def clean_file(file_path: Path) -> tuple[bool, int]:
    """Clean HTML entities in a file. Returns (changed, count)."""
    original = file_path.read_text()

    # Use Python's html.unescape to handle all HTML entities
    cleaned = html.unescape(original)

    # Also handle some common patterns that might slip through
    replacements = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&#39;': "'",
        '&#34;': '"',
        '&nbsp;': ' ',
        '–': '-',  # en-dash to hyphen
        '—': ' - ',  # em-dash to spaced hyphen
        ''': "'",  # smart quote
        ''': "'",  # smart quote
        '"': '"',  # smart quote
        '"': '"',  # smart quote
        '…': '...',  # ellipsis
        '°': ' degrees ',  # degree symbol (optional, might want to keep)
    }

    # Keep degree symbol as-is actually, it's useful for cooking
    del replacements['°']

    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    # Count changes
    changes = sum(1 for a, b in zip(original, cleaned) if a != b)

    if cleaned != original:
        file_path.write_text(cleaned)
        return True, changes

    return False, 0


def main():
    unified_dir = Path(__file__).parent / 'ocr_results_unified'

    files = sorted(unified_dir.glob('*.txt'))

    print(f"Cleaning HTML entities in {len(files)} files...\n")

    changed_count = 0
    for f in files:
        changed, count = clean_file(f)
        if changed:
            print(f"  Cleaned: {f.name}")
            changed_count += 1

    print(f"\nDone! Cleaned {changed_count} files.")


if __name__ == '__main__':
    main()
