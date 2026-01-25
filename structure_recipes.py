#!/usr/bin/env python3
"""Pass 4: Convert unified recipe text files to structured JSON.

Parses recipe text files and extracts sections according to recipe_sections.json schema.
Auto-generates tags based on recipe content.
"""

import json
import re
from pathlib import Path


def extract_name(text: str, filename: str) -> str:
    """Extract recipe name from text or filename."""
    lines = text.strip().split('\n')

    # Look for "RECIPE FOR:" pattern
    for line in lines[:10]:
        match = re.search(r'RECIPE FOR:\s*(.+)', line, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Look for markdown H1 or H2 that's a title (not a section header)
    section_headers = {'ingredients', 'instructions', 'directions', 'notes', 'steps',
                       'equipment', 'preparation', 'nutrition', 'method', 'tips'}
    for line in lines[:15]:
        line = line.strip()
        if line.startswith('# ') or line.startswith('## '):
            title = line.lstrip('#').strip()
            if title.lower() not in section_headers and len(title) > 3:
                # Skip website names
                if title.lower() not in {'eatingwell', 'epicurious', 'food52', 'food&wine', 'allrecipes'}:
                    return title

    # Fallback to filename
    return filename.replace('.txt', '')


def extract_description(text: str) -> str | None:
    """Extract recipe description/intro text."""
    lines = text.strip().split('\n')

    # Look for descriptive paragraph before ingredients
    description_lines = []
    in_description = False

    for i, line in enumerate(lines[:30]):
        line_lower = line.lower().strip()

        # Stop at section headers
        if any(header in line_lower for header in ['ingredient', 'instruction', 'direction', '## ', '### ']):
            if line_lower.startswith('#'):
                break

        # Skip metadata lines
        if re.match(r'^(prep|cook|total|active)\s*time', line_lower):
            continue
        if re.match(r'^(serves?|yield|servings?|course|cuisine|author)', line_lower):
            continue
        if line.startswith('|') or line.startswith('---'):
            continue
        if line.startswith('!['):  # Image
            continue
        if re.match(r'^\d+\s*(min|hr|hour)', line_lower):
            continue

        # Start collecting after title
        if in_description and line.strip():
            description_lines.append(line.strip())
        elif line.startswith('#'):
            in_description = True

    # Get first paragraph-like text
    if description_lines:
        desc = ' '.join(description_lines[:3])
        if len(desc) > 50:
            return desc[:500] if len(desc) > 500 else desc

    return None


def extract_times(text: str) -> dict:
    """Extract prep, cook, and total times."""
    times = {}

    # Pattern: "Prep Time: 15 mins" or "Prep: 15 min"
    prep_match = re.search(r'(?:Prep(?:aration)?\s*(?:Time)?)\s*[:\s]+(\d+\s*(?:min|minute|hr|hour|mins|minutes|hrs|hours)[^\n|]*)', text, re.IGNORECASE)
    if prep_match:
        times['prep_time'] = prep_match.group(1).strip()

    cook_match = re.search(r'(?:Cook(?:ing)?\s*(?:Time)?)\s*[:\s]+(\d+\s*(?:min|minute|hr|hour|mins|minutes|hrs|hours)[^\n|]*)', text, re.IGNORECASE)
    if cook_match:
        times['cook_time'] = cook_match.group(1).strip()

    total_match = re.search(r'(?:Total\s*(?:Time)?)\s*[:\s]+(\d+\s*(?:min|minute|hr|hour|mins|minutes|hrs|hours)[^\n|]*)', text, re.IGNORECASE)
    if total_match:
        times['total_time'] = total_match.group(1).strip()

    return times


def extract_servings(text: str) -> str | None:
    """Extract servings/yield."""
    patterns = [
        r'(?:Serves?|Servings?|Yield)\s*[:\s]+(\d+(?:\s*[-–]\s*\d+)?(?:\s*(?:people|servings?|portions?))?)',
        r'SERVES:\s*(\d+(?:\s*[-–]\s*\d+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def extract_source(text: str) -> str | None:
    """Extract recipe source."""
    # Look for author
    author_match = re.search(r'(?:Author|By)[:\s]+([A-Z][a-zA-Z\s]+?)(?:\s*\||$|\n)', text)
    if author_match:
        return author_match.group(1).strip()

    # Look for website in URL
    url_match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9-]+)\.(?:com|org|net)', text)
    if url_match:
        return url_match.group(1)

    # Look for common sources
    sources = ['epicurious', 'allrecipes', 'food52', 'bon appétit', 'food & wine',
               'eatingwell', 'serious eats', 'nyt cooking']
    text_lower = text.lower()
    for source in sources:
        if source in text_lower:
            return source.title()

    return None


def extract_ingredients(text: str) -> tuple[list[str], dict | None]:
    """Extract ingredients list and optional groups."""
    lines = text.strip().split('\n')
    ingredients = []
    ingredient_groups = {}
    current_group = None

    # First, try standard markdown format
    in_ingredients = False
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Detect ingredients section start
        if re.match(r'^#{1,3}\s*ingredients?', line_lower) or line_lower == 'ingredients':
            in_ingredients = True
            continue

        # Detect end of ingredients
        if in_ingredients and re.match(r'^#{1,3}\s*(instructions?|directions?|method|preparation|steps?)', line_lower):
            break

        if not in_ingredients:
            continue

        # Skip empty lines and non-ingredient patterns
        if not line_stripped:
            continue
        if line_stripped.startswith('!['):
            continue
        if line_stripped.startswith('|') and '---' in line_stripped:
            continue

        # Detect ingredient subgroups
        if line_stripped.startswith('###') or (line_stripped.endswith(':') and len(line_stripped) < 50):
            current_group = line_stripped.lstrip('#').rstrip(':').strip()
            if current_group:
                ingredient_groups[current_group] = []
            continue

        # Extract ingredient
        # Remove bullet points, numbers, dashes
        ingredient = re.sub(r'^[-*•]\s*', '', line_stripped)
        ingredient = re.sub(r'^\d+[\.\)]\s*', '', ingredient)

        # Skip if too short or looks like a header
        if len(ingredient) < 3:
            continue
        if ingredient.startswith('#'):
            continue
        # Skip noise
        if 'cook mode' in ingredient.lower() or 'screen' in ingredient.lower():
            continue

        # Clean up table format
        if '|' in ingredient:
            parts = [p.strip() for p in ingredient.split('|') if p.strip()]
            for part in parts:
                if part and not part.startswith('---'):
                    if current_group and current_group in ingredient_groups:
                        ingredient_groups[current_group].append(part)
                    else:
                        ingredients.append(part)
        else:
            if current_group and current_group in ingredient_groups:
                ingredient_groups[current_group].append(ingredient)
            else:
                ingredients.append(ingredient)

    # If no ingredients found, try "RECIPE FOR:" format (handwritten style)
    if not ingredients:
        in_recipe = False
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Start after "RECIPE FOR:" line
            if 'RECIPE FOR:' in line.upper():
                in_recipe = True
                continue

            if not in_recipe:
                continue

            # Stop at instruction paragraphs (longer lines that start with verbs)
            if len(line_stripped) > 100 and re.match(r'^(In |Add |Heat |Pour |Cook |Place |Season |Transfer )', line_stripped):
                break

            # Stop at "PREPARATION TIME" or "DSS" markers
            if line_stripped in ('DSS', '') and i > 5:
                if not line_stripped:  # Empty line might signal end of ingredients
                    # Check if next non-empty line looks like instructions
                    for next_line in lines[i+1:i+3]:
                        if next_line.strip() and len(next_line.strip()) > 80:
                            break
                    else:
                        continue
                    break
                continue
            if 'PREPARATION TIME' in line_stripped.upper():
                break

            # Skip empty lines and markers
            if not line_stripped or line_stripped == 'DSS':
                continue

            # Check if this looks like an ingredient line (contains measurements)
            if re.search(r'\d+\s*(c\.|cup|tsp|tbs|tbsp|oz|lb|pound|teaspoon|tablespoon|inch|clove|sprig)', line_stripped, re.IGNORECASE):
                # This line might have multiple ingredients (two-column format)
                # Try to split on double spaces or tabs
                parts = re.split(r'\s{2,}|\t', line_stripped)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 3:
                        ingredients.append(part)
            elif line_stripped.isupper() and len(line_stripped) < 30:
                # This is likely a section header like "CHICKEN" or "TURNIP PUREE"
                current_group = line_stripped.title()
                ingredient_groups[current_group] = []
            elif current_group and len(line_stripped) > 3:
                # Add to current group
                parts = re.split(r'\s{2,}|\t', line_stripped)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 3:
                        if current_group in ingredient_groups:
                            ingredient_groups[current_group].append(part)
                        else:
                            ingredients.append(part)

    # Return groups only if there are multiple
    if len(ingredient_groups) > 1:
        return ingredients, ingredient_groups
    elif ingredient_groups:
        # Merge single group into main list
        for group_ingredients in ingredient_groups.values():
            ingredients.extend(group_ingredients)

    return ingredients, None


def extract_instructions(text: str) -> list[str]:
    """Extract cooking instructions."""
    lines = text.strip().split('\n')
    instructions = []

    in_instructions = False
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Detect instructions section start
        if re.match(r'^#{1,3}\s*(instructions?|directions?|method|preparation|steps?)', line_lower):
            in_instructions = True
            continue

        # Also start if we see numbered steps
        if re.match(r'^[1]\s*[\.\)]\s*\w', line_stripped) and not in_instructions:
            in_instructions = True

        # Detect end of instructions
        if in_instructions and re.match(r'^#{1,3}\s*(notes?|tips?|nutrition|equipment)', line_lower):
            break

        if not in_instructions:
            continue

        # Skip empty lines, images
        if not line_stripped or line_stripped.startswith('!['):
            continue

        # Skip step headers like "## Step 1"
        if re.match(r'^#{1,3}\s*step\s*\d+', line_lower):
            continue

        # Clean up instruction
        instruction = line_stripped

        # Remove leading numbers/bullets
        instruction = re.sub(r'^[-*•]\s*', '', instruction)
        instruction = re.sub(r'^\d+[\.\)]\s*', '', instruction)

        # Skip if too short
        if len(instruction) < 10:
            continue

        instructions.append(instruction)

    return instructions


def extract_notes(text: str) -> list[str]:
    """Extract notes, tips, and variations."""
    lines = text.strip().split('\n')
    notes = []

    in_notes = False
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Detect notes section
        if re.match(r'^#{1,3}\s*(notes?|tips?|cook.?s?\s*notes?|variations?)', line_lower):
            in_notes = True
            continue

        # End at nutrition or next major section
        if in_notes and re.match(r'^#{1,3}\s*(nutrition|equipment)', line_lower):
            break

        if not in_notes:
            continue

        if not line_stripped or line_stripped.startswith('!['):
            continue

        note = re.sub(r'^[-*•]\s*', '', line_stripped)
        note = re.sub(r'^\d+[\.\)]\s*', '', note)

        if len(note) > 10:
            notes.append(note)

    return notes


def extract_nutrition(text: str) -> dict | None:
    """Extract nutrition information."""
    nutrition = {}

    patterns = {
        'calories': r'Calories?\s*[:\s]+(\d+)',
        'protein': r'Protein\s*[:\s]+(\d+\.?\d*\s*g)',
        'carbohydrates': r'Carbohydrates?\s*[:\s]+(\d+\.?\d*\s*g)',
        'fat': r'Fat\s*[:\s]+(\d+\.?\d*\s*g)',
        'fiber': r'Fiber\s*[:\s]+(\d+\.?\d*\s*g)',
        'sodium': r'Sodium\s*[:\s]+(\d+\.?\d*\s*mg)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            nutrition[key] = match.group(1)

    return nutrition if nutrition else None


def generate_tags(name: str, ingredients: list[str], instructions: list[str], text: str) -> list[str]:
    """Auto-generate tags based on recipe content."""
    tags = set()
    all_text = (name + ' ' + ' '.join(ingredients) + ' ' + ' '.join(instructions) + ' ' + text).lower()

    # Protein tags
    proteins = {
        'chicken': ['chicken', 'poultry'],
        'beef': ['beef', 'steak', 'short rib'],
        'pork': ['pork', 'bacon', 'pancetta', 'prosciutto'],
        'fish': ['salmon', 'cod', 'halibut', 'tilapia', 'snapper', 'bass', 'fish'],
        'seafood': ['shrimp', 'prawn', 'scallop', 'mussel', 'clam', 'crab', 'lobster', 'squid'],
        'turkey': ['turkey'],
        'lamb': ['lamb'],
        'tofu': ['tofu'],
    }
    for tag, keywords in proteins.items():
        if any(kw in all_text for kw in keywords):
            tags.add(tag)

    # Dish type tags
    dish_types = {
        'soup': ['soup', 'broth'],
        'stew': ['stew', 'braised', 'braise'],
        'salad': ['salad'],
        'pasta': ['pasta', 'spaghetti', 'penne', 'pappardelle', 'noodle', 'orzo'],
        'stir-fry': ['stir fry', 'stir-fry', 'wok'],
        'roast': ['roast', 'roasted'],
        'grilled': ['grill', 'grilled'],
        'skillet': ['skillet'],
        'one-pot': ['one-pot', 'one pot', 'dutch oven'],
        'slow cooker': ['slow cooker', 'crock pot', 'crockpot'],
        'casserole': ['casserole', 'bake'],
    }
    for tag, keywords in dish_types.items():
        if any(kw in all_text for kw in keywords):
            tags.add(tag)

    # Cuisine tags
    cuisines = {
        'italian': ['italian', 'parmesan', 'parmigiano', 'bolognese', 'carbonara', 'pesto'],
        'mexican': ['mexican', 'taco', 'salsa', 'cilantro', 'jalapeño', 'chipotle', 'cumin'],
        'asian': ['asian', 'soy sauce', 'sesame', 'ginger', 'bok choy'],
        'chinese': ['chinese', 'hoisin', 'oyster sauce', 'five spice'],
        'thai': ['thai', 'fish sauce', 'thai basil', 'coconut milk curry'],
        'indian': ['indian', 'curry', 'garam masala', 'turmeric', 'tikka', 'masala', 'vindaloo'],
        'korean': ['korean', 'gochujang', 'kimchi', 'galbi'],
        'mediterranean': ['mediterranean', 'olive oil', 'feta', 'hummus'],
        'cajun': ['cajun', 'creole', 'jambalaya', 'gumbo', 'andouille'],
        'french': ['french', 'bourguignon', 'provençal', 'herbes de provence'],
        'southern': ['southern', 'grits', 'cornbread'],
    }
    for tag, keywords in cuisines.items():
        if any(kw in all_text for kw in keywords):
            tags.add(tag)

    # Meal type
    if any(word in all_text for word in ['dessert', 'cake', 'pie', 'cookie', 'chocolate', 'sweet']):
        tags.add('dessert')
    elif any(word in all_text for word in ['breakfast', 'brunch', 'egg', 'pancake']):
        tags.add('breakfast')
    elif any(word in all_text for word in ['appetizer', 'dip', 'snack', 'starter']):
        tags.add('appetizer')
    elif any(word in all_text for word in ['side dish', 'side']):
        tags.add('side dish')
    else:
        tags.add('dinner')

    # Other tags
    if any(word in all_text for word in ['vegetarian', 'veggie', 'meatless']) and 'chicken' not in tags and 'beef' not in tags:
        tags.add('vegetarian')
    if 'vegan' in all_text:
        tags.add('vegan')
    if any(word in all_text for word in ['healthy', 'low-calorie', 'light']):
        tags.add('healthy')
    if any(word in all_text for word in ['comfort food', 'hearty', 'cozy']):
        tags.add('comfort food')
    if any(word in all_text for word in ['quick', 'easy', '30 min', '20 min', '15 min']):
        tags.add('quick')
    if any(word in all_text for word in ['spicy', 'hot sauce', 'chili', 'cayenne', 'jalapeño']):
        tags.add('spicy')
    if any(word in all_text for word in ['creamy', 'cream', 'cheese']):
        tags.add('creamy')

    return sorted(list(tags))


def process_recipe(file_path: Path) -> dict:
    """Process a single recipe file and return structured data."""
    text = file_path.read_text()
    filename = file_path.name

    # Extract all components
    name = extract_name(text, filename)
    ingredients, ingredient_groups = extract_ingredients(text)
    instructions = extract_instructions(text)

    recipe = {
        'name': name,
        'source_file': filename,
    }

    # Add optional fields if present
    source = extract_source(text)
    if source:
        recipe['source'] = source

    description = extract_description(text)
    if description:
        recipe['description'] = description

    times = extract_times(text)
    recipe.update(times)

    servings = extract_servings(text)
    if servings:
        recipe['servings'] = servings

    recipe['ingredients'] = ingredients
    if ingredient_groups:
        recipe['ingredient_groups'] = ingredient_groups

    recipe['instructions'] = instructions

    notes = extract_notes(text)
    if notes:
        recipe['notes'] = notes

    nutrition = extract_nutrition(text)
    if nutrition:
        recipe['nutrition'] = nutrition

    # Category is null by default (to be filled manually)
    recipe['category'] = None

    # Generate tags
    recipe['tags'] = generate_tags(name, ingredients, instructions, text)

    return recipe


def main():
    unified_dir = Path(__file__).parent / 'ocr_results_unified'
    output_dir = Path(__file__).parent / 'recipes_structured'
    output_dir.mkdir(exist_ok=True)

    files = sorted(unified_dir.glob('*.txt'))

    print(f"Processing {len(files)} recipes...\n")

    for i, f in enumerate(files, 1):
        recipe = process_recipe(f)

        # Create output filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '', recipe['name'])
        safe_name = safe_name[:80] if len(safe_name) > 80 else safe_name
        output_file = output_dir / f"{safe_name}.json"

        # Handle duplicates
        counter = 1
        while output_file.exists():
            output_file = output_dir / f"{safe_name} ({counter}).json"
            counter += 1

        # Write JSON
        with open(output_file, 'w') as out:
            json.dump(recipe, out, indent=2)

        ing_count = len(recipe['ingredients'])
        inst_count = len(recipe['instructions'])
        tag_count = len(recipe['tags'])
        print(f"[{i}/{len(files)}] {recipe['name'][:50]:<50} ({ing_count} ing, {inst_count} steps, {tag_count} tags)")

    print(f"\nDone! Created {len(files)} JSON files in {output_dir}")


if __name__ == '__main__':
    main()
