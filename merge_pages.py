#!/usr/bin/env python3
"""Merge multi-page recipe files into single files."""

import re
from pathlib import Path


def find_base_file(unified_dir: Path, name_pattern: str) -> Path | None:
    """Find the base file matching a pattern."""
    # Try exact match first
    for f in unified_dir.glob('*.txt'):
        if f.stem.lower().startswith(name_pattern.lower()):
            # Skip if it's a page/continued file itself
            if re.search(r'\(page|\(continued|\(\d+\)', f.stem, re.IGNORECASE):
                continue
            return f
    return None


def merge_files(base_file: Path, continuation_file: Path, delete_continuation: bool = True) -> None:
    """Append continuation file content to base file."""
    base_content = base_file.read_text()
    continuation_content = continuation_file.read_text()

    # Add separator and merge
    merged = base_content.rstrip() + "\n\n" + continuation_content
    base_file.write_text(merged)

    if delete_continuation:
        continuation_file.unlink()

    print(f"  Merged: {continuation_file.name} -> {base_file.name}")


def main():
    unified_dir = Path(__file__).parent / 'ocr_results_unified'

    # Define explicit merges (continuation -> base)
    merges = [
        # (continuation file pattern, base file pattern)
        ("Bacon Wrapped Shrimp with Grits (page 1)", "Bacon Wrapped Shrimp w Grits"),
        ("Bacon Wrapped Shrimp with Grits (page 2)", "Bacon Wrapped Shrimp w Grits"),
        ("Beef Tenderloin (page 2)", "Beef Tenderloin with Creamy Mushroom Sauce"),
        ("Brothy Chicken with Ginger and Bok Choy (1)", "Brothy Chicken with Ginger and Bok Choy"),
        ("Chicken Sausage Cassoulet (continued)", "Lazy Chicken-and-Sausage Cassoulet"),
        ("Chicken Wild Mushroom Fricassee (page 2)", "CHICKEN and WILD MUSHROOM FRICASSEE"),
        ("Chicken with Tarragon Sauce (continued)", "Roast Chicken Breasts with Tarragon and Mustard Sauce"),
        ("Chinese Green Beans (continued)", "Chinese Green Beans"),
        ("Classic Chicken Soup (continued)", "CLASSIC CHICKEN SOUP"),
        ("Coconut Vegetable Curry (continued)", "Got Coconut Milk Make Ginataang Gulay"),
        ("Creamed Spinach (continued)", "Perfect Creamed Spinach"),
        ("Fall-Apart Caramelized Cabbage (1)", "Fall-Apart Caramelized Cabbage"),
        ("Honey-Garlic Chicken Thighs with Carrots and Broccoli (1)", "Honey-Garlic Chicken Thighs with Carrots and Broccoli"),
        ("Lentil Soup (continued)", "Lentil Soup"),
        ("Philly Cheesesteak Queso (continued)", "Philly Cheesesteak Queso Recipe - Justin Chapple"),
        ("Seafood Stew for Two recipe (1)", "Seafood Stew for Two recipe"),
        ("Seared Salmon with Summer Vegetables (page 2)", "Seared Salmon with Summer Vegetables"),
        ("Slow Cooker Cuban Mojo Pork (continued)", "SLOW COOKER CUBAN MOJO PORK"),
        ("Smoky Carrot Dip (continued)", "Smoky Carrot Dip"),
        ("Tacos Al Pastor (continued)", "TACOS AL PASTOR"),
        ("Thai Grilled Fish (continued)", "Easy Thai Grilled Fish Fillets Recipe"),
    ]

    print("Merging multi-page recipes...\n")

    merged_count = 0
    for cont_pattern, base_pattern in merges:
        cont_file = unified_dir / f"{cont_pattern}.txt"
        base_file = unified_dir / f"{base_pattern}.txt"

        if not cont_file.exists():
            print(f"  Skip (not found): {cont_pattern}.txt")
            continue

        if not base_file.exists():
            # Try to find a close match
            matches = list(unified_dir.glob(f"{base_pattern}*.txt"))
            matches = [m for m in matches if not re.search(r'\(page|\(continued|\(\d+\)', m.stem)]
            if matches:
                base_file = matches[0]
            else:
                print(f"  WARNING: Base file not found for {cont_pattern}")
                print(f"           Looked for: {base_pattern}.txt")
                continue

        merge_files(base_file, cont_file)
        merged_count += 1

    print(f"\nMerged {merged_count} continuation files.")
    print(f"Remaining files: {len(list(unified_dir.glob('*.txt')))}")


if __name__ == '__main__':
    main()
