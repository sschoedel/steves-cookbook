#!/usr/bin/env python3
"""Helper script to rename poorly-named recipe files.

Analyzes file contents to extract better recipe titles.
"""

import re
from pathlib import Path


def is_poor_name(filename: str) -> bool:
    """Check if filename is a poor auto-extracted name."""
    name = filename.replace('.txt', '')

    # Known bad patterns
    patterns = [
        r'^\d+$',  # Just numbers (dates)
        r'^\d+/\d+/\d+',  # Date patterns
        r'^\d+, \d+',  # Date/time patterns
        r'^allrecipes',
        r'^epicurious',
        r'^FOOD',
        r'^Eating',
        r'^\d+\)',  # Starts with "2)" etc
        r'^\d+ of \d+',  # "2 of 4"
        r'^In a ',
        r'^Set aside',
        r'^Put all',
        r'^\d+\. ',  # Starts with step number
        r'^\d+ [A-Z]',  # "1 Preheat" etc
        r'^\d+T ',  # "3T CHIPOTLE"
        r'^\d+ c\.',  # "4 c. cooked"
        r'^\d+ onion',
        r'contd$',  # ends with "contd"
        r'^\d+and',  # "502 and Quille"
        r'^Step \d',  # "Step 4"
        r'^Preparation',  # "Preparation Time"
        r'^Tips$',
        r'^For variations',
        r'^Do ahead',
        r'^Exclusive',
        r'^Alexia',
        r'Pm$',  # ends with "Pm"
        r'Recipe.*Esquire',
        r'DELICIOUS TEAM',
    ]

    for pattern in patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False


def extract_better_title(text: str) -> str | None:
    """Try multiple strategies to extract a recipe title from text."""
    lines = text.strip().split('\n')

    # Known website H1 headers to skip
    website_headers = {'eatingwell', 'food52', 'epicurious', 'allrecipes', 'allrecipes!',
                       'foodandwine', 'food&wine', 'bon appétit', 'bonappetit', 'food and wine'}

    # Bad title patterns to reject
    bad_titles = {'step', 'ingredients', 'instructions', 'directions', 'notes',
                  'equipment', 'preparation', 'nutrition', 'tips', 'cook mode',
                  'do ahead', 'for variations', 'exclusive offers', 'preparation time'}

    # Strategy 1: Look for "Recipe Title | Website" or "Recipe Title Recipe | Website" in first few lines
    for line in lines[:5]:
        line = line.strip()
        # Match patterns like "Brothy Chicken with Ginger | Bon Appétit"
        match = re.match(r'^([^|]+?)\s*(?:Recipe\s*)?\|\s*\w+', line)
        if match:
            title = match.group(1).strip()
            if len(title) > 5 and title.lower() not in bad_titles:
                return title
        # Match patterns like "Recipe Title recipe | website"
        match = re.match(r'^(.+?)\s+recipe\s*\|', line, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            if len(title) > 5:
                return title

    # Strategy 2: Look for H2 headers (## ) - these are often the actual recipe titles
    for line in lines[:30]:
        line = line.strip()
        if line.startswith('## '):
            title = line[3:].strip()
            title_lower = title.lower()
            # Skip common section headers
            if title_lower in bad_titles or title_lower.startswith('step'):
                continue
            if len(title) > 3:
                return title

    # Strategy 3: Look for H1 headers that aren't website names
    for line in lines[:20]:
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            if title.lower() not in website_headers and len(title) > 3:
                # Check it's not a date or number
                if not re.match(r'^[\d/\-\s]+$', title):
                    return title

    # Strategy 4: Look for "RECIPE FOR:" pattern
    for line in lines[:15]:
        match = re.search(r'RECIPE FOR:\s*(.+)', line, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Strategy 5: Look for all-caps title line that looks like a recipe
    for line in lines[:20]:
        line = line.strip()
        if re.match(r'^\d+[\.\)]', line):
            continue
        if line.isupper() and 10 < len(line) < 80:
            # Skip ingredient-like lines
            if not any(word in line.lower() for word in ['cup', 'tbsp', 'tsp', 'oz', 'lb', 'step']):
                return line.title()

    # Strategy 6: Look for title in URL pattern
    for line in lines[:10]:
        # Match recipe name from URL like "food52.com/recipes/77452-skillet-chicken"
        match = re.search(r'/recipes?/[^/]*?([a-z\-]+chicken[a-z\-]*|[a-z\-]+salmon[a-z\-]*|[a-z\-]+beef[a-z\-]*)', line, re.IGNORECASE)
        if match:
            title = match.group(1).replace('-', ' ').title()
            if len(title) > 5:
                return title

    return None


def sanitize_filename(name: str) -> str:
    """Convert recipe name to safe filename."""
    # Remove/replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'&amp;', 'and', name)
    name = re.sub(r'&', 'and', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    # Remove trailing periods
    name = name.rstrip('.')
    # Truncate if too long
    if len(name) > 80:
        name = name[:80].rsplit(' ', 1)[0]
    return name


def main():
    unified_dir = Path(__file__).parent / 'ocr_results_unified'

    if not unified_dir.exists():
        print(f"Error: Directory not found: {unified_dir}")
        return 1

    files = sorted(unified_dir.glob('*.txt'))

    # Find files with poor names
    poor_files = [(f, f.stem) for f in files if is_poor_name(f.name)]

    print(f"Found {len(poor_files)} files with poor names to fix.\n")

    renamed = 0
    failed = []

    for file_path, old_name in poor_files:
        text = file_path.read_text()
        new_title = extract_better_title(text)

        if new_title:
            new_name = sanitize_filename(new_title)
            new_path = unified_dir / f"{new_name}.txt"

            # Handle duplicates
            counter = 1
            while new_path.exists() and new_path != file_path:
                new_path = unified_dir / f"{new_name} ({counter}).txt"
                counter += 1

            if new_path != file_path:
                print(f"  {old_name[:50]:<50} -> {new_name}")
                file_path.rename(new_path)
                renamed += 1
            else:
                print(f"  {old_name[:50]:<50} -> (no change needed)")
        else:
            failed.append((file_path, old_name))
            print(f"  {old_name[:50]:<50} -> [COULD NOT EXTRACT TITLE]")

    print(f"\n{'='*60}")
    print(f"Renamed: {renamed}")
    print(f"Failed:  {len(failed)}")

    if failed:
        print(f"\nFiles that still need manual renaming:")
        for f, name in failed:
            print(f"  - {name}.txt")
            # Show first few lines to help identify
            text = f.read_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()][:5]
            for line in lines:
                print(f"    {line[:80]}")
            print()

    return 0


if __name__ == '__main__':
    exit(main())
