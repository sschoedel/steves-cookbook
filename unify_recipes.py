#!/usr/bin/env python3
"""Pass 2: Unify multi-page recipes into single files.

This script helps identify and combine multi-page recipes from OCR results.
It analyzes consecutive files and presents them for review.

Usage:
    uv run unify_recipes.py              # Interactive mode
    uv run unify_recipes.py --auto       # Auto-detect and suggest groupings
"""

import argparse
import json
import re
from pathlib import Path


def extract_recipe_title(text: str) -> str | None:
    """Try to extract recipe title from OCR text."""
    lines = text.strip().split('\n')

    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        # Skip empty lines and common noise
        if not line or line.startswith('http') or line.startswith('!['):
            continue
        # Look for markdown headers
        if line.startswith('# '):
            return line[2:].strip()
        # Look for "RECIPE FOR:" pattern
        if 'RECIPE FOR:' in line.upper():
            match = re.search(r'RECIPE FOR:\s*(.+)', line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    # Fallback: first non-empty line that looks like a title
    for line in lines[:5]:
        line = line.strip()
        if line and not line.startswith(('http', '!', '|', '-', '*', '#')) and len(line) > 3:
            # Clean up common prefixes
            line = re.sub(r'^(W/\s*)', '', line)
            if len(line) > 3:
                return line

    return None


def looks_like_continuation(text: str) -> bool:
    """Check if text looks like a continuation (not a new recipe start)."""
    lines = text.strip().split('\n')
    first_line = lines[0].strip().lower() if lines else ''
    first_lines = '\n'.join(lines[:5]).lower()
    first_10_lines = '\n'.join(lines[:10]).lower()

    # Signs of continuation (strong indicators)
    continuation_signs = [
        re.match(r'^\d+\.', lines[0].strip()) if lines else False,  # Starts with numbered step
        first_line.startswith(('## step', '### step')),  # Step header
        first_line.startswith(('once ', 'pour ', 'add ', 'cook ', 'stir ', 'heat ', 'mix ', 'place ', 'meanwhile')),
        '## step' in first_lines and '# ' not in first_lines[:20],
        first_line.startswith(('3.', '4.', '5.', '6.', '7.', '8.', '9.')),  # Mid-recipe step numbers
        first_lines.startswith('step '),
        # URL/page indicator without title
        bool(re.match(r'^https?://', first_line)) and '# ' not in first_10_lines,
        # Starts with lowercase indicating mid-sentence
        lines[0].strip()[:1].islower() if lines and lines[0].strip() else False,
    ]

    # Signs of new recipe (strong indicators)
    new_recipe_signs = [
        '# ' in '\n'.join(lines[:3]) and 'step' not in lines[0].lower() and 'instructions' not in lines[0].lower(),
        'prep time' in first_lines and 'cook time' in first_lines,
        '## ingredients' in first_lines,
        'recipe for:' in first_lines,
        bool(re.search(r'^\s*#\s+[A-Z]', lines[0])) if lines else False,  # Markdown H1 with capitalized title
    ]

    return any(continuation_signs) and not any(new_recipe_signs)


def has_recipe_ending(text: str) -> bool:
    """Check if text appears to end a recipe (has notes, nutrition, etc.)."""
    lower_text = text.lower()
    last_500 = lower_text[-500:] if len(lower_text) > 500 else lower_text

    ending_signs = [
        '## notes' in lower_text,
        '## nutrition' in lower_text,
        'calories:' in last_500,
        'serving:' in last_500 and ('calories' in last_500 or 'carbohydrates' in last_500),
        'find it online:' in last_500,
        'recipe from' in last_500,
        'can be made' in last_500 and 'ahead' in last_500,
    ]

    return any(ending_signs)


def sanitize_filename(name: str) -> str:
    """Convert recipe name to safe filename."""
    # Remove/replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'&amp;', 'and', name)
    name = re.sub(r'&', 'and', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    # Truncate if too long
    if len(name) > 80:
        name = name[:80].rsplit(' ', 1)[0]
    return name


def analyze_files(ocr_dir: Path) -> list[dict]:
    """Analyze all OCR files and group into recipes."""
    files = sorted(ocr_dir.glob('*.txt'), key=lambda p: p.name)

    recipes = []
    current_recipe = None

    for f in files:
        text = f.read_text()
        title = extract_recipe_title(text)
        is_continuation = looks_like_continuation(text)
        has_ending = has_recipe_ending(text)

        if current_recipe is None or (not is_continuation and title):
            # Start new recipe
            if current_recipe:
                recipes.append(current_recipe)
            current_recipe = {
                'title': title or f.stem,
                'files': [f.name],
                'source_stems': [f.stem],
                'complete': has_ending,
            }
        else:
            # Continue current recipe
            current_recipe['files'].append(f.name)
            current_recipe['source_stems'].append(f.stem)
            if has_ending:
                current_recipe['complete'] = True

    if current_recipe:
        recipes.append(current_recipe)

    return recipes


def combine_recipe_files(ocr_dir: Path, output_dir: Path, recipe: dict) -> Path:
    """Combine multiple OCR files into a single recipe file."""
    combined_text = []

    for filename in recipe['files']:
        file_path = ocr_dir / filename
        text = file_path.read_text()
        combined_text.append(text)

    # Join with double newline
    full_text = '\n\n'.join(combined_text)

    # Create output filename
    safe_name = sanitize_filename(recipe['title'])
    output_file = output_dir / f"{safe_name}.txt"

    # Handle duplicates
    counter = 1
    while output_file.exists():
        output_file = output_dir / f"{safe_name} ({counter}).txt"
        counter += 1

    output_file.write_text(full_text)
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Unify multi-page recipes")
    parser.add_argument('--ocr-dir', type=Path, default=Path(__file__).parent / 'ocr_results')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).parent / 'ocr_results_unified')
    parser.add_argument('--auto', action='store_true', help='Auto-process without confirmation')
    parser.add_argument('--analyze-only', action='store_true', help='Only show analysis, do not combine')
    parser.add_argument('--save-mapping', type=Path, help='Save recipe mapping to JSON file')
    args = parser.parse_args()

    if not args.ocr_dir.exists():
        print(f"Error: OCR directory not found: {args.ocr_dir}")
        return 1

    args.output_dir.mkdir(exist_ok=True)

    print(f"Analyzing {args.ocr_dir}...")
    recipes = analyze_files(args.ocr_dir)

    print(f"\nFound {len(recipes)} recipes:\n")

    multi_page = [r for r in recipes if len(r['files']) > 1]
    single_page = [r for r in recipes if len(r['files']) == 1]

    print(f"Multi-page recipes: {len(multi_page)}")
    print(f"Single-page recipes: {len(single_page)}")
    print()

    # Show multi-page recipes
    if multi_page:
        print("=" * 60)
        print("MULTI-PAGE RECIPES:")
        print("=" * 60)
        for i, r in enumerate(multi_page, 1):
            status = "✓" if r['complete'] else "?"
            print(f"{i:3}. [{status}] {r['title']}")
            print(f"     Files: {', '.join(r['files'])}")
        print()

    # Save mapping if requested
    if args.save_mapping:
        mapping = {
            'recipes': recipes,
            'summary': {
                'total': len(recipes),
                'multi_page': len(multi_page),
                'single_page': len(single_page),
            }
        }
        args.save_mapping.write_text(json.dumps(mapping, indent=2))
        print(f"Saved mapping to: {args.save_mapping}")

    if args.analyze_only:
        return 0

    # Process recipes
    if not args.auto:
        response = input(f"\nCombine all {len(recipes)} recipes to {args.output_dir}? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            return 0

    print(f"\nCombining recipes to {args.output_dir}...")

    for recipe in recipes:
        output_file = combine_recipe_files(args.ocr_dir, args.output_dir, recipe)
        page_info = f"({len(recipe['files'])} pages)" if len(recipe['files']) > 1 else ""
        print(f"  Created: {output_file.name} {page_info}")

    print(f"\nDone! Created {len(recipes)} unified recipe files.")
    return 0


if __name__ == '__main__':
    exit(main())
