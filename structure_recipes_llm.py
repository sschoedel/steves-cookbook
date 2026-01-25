#!/usr/bin/env python3
"""Pass 4: Convert unified recipe text files to structured JSON using Claude.

Uses Claude API to intelligently extract recipe components from varied formats.
"""

import json
import re
import time
from pathlib import Path

import anthropic


EXTRACTION_PROMPT = """Extract the recipe information from the following text and return it as JSON.

The JSON should have these fields:
- "name": Recipe title (string, required)
- "source": Original source like website or cookbook (string, optional)
- "description": Brief description of the dish (string, optional)
- "prep_time": Preparation time (string, optional)
- "cook_time": Cooking time (string, optional)
- "total_time": Total time (string, optional)
- "servings": Number of servings (string, optional)
- "ingredients": List of ingredients with quantities (array of strings, required)
- "ingredient_groups": If ingredients are grouped (e.g., "For the sauce:", "For the meat:"), use this object with group names as keys and arrays of ingredients as values (object, optional)
- "instructions": Step-by-step cooking instructions (array of strings, required)
- "notes": Tips, variations, storage info (array of strings, optional)
- "nutrition": Nutritional info if present (object with keys like "calories", "protein", etc., optional)
- "tags": Auto-generate 5-10 relevant tags from this vocabulary:
  - Meal type: breakfast, brunch, lunch, dinner, snack, dessert, appetizer, side dish
  - Dish type: soup, stew, salad, sandwich, pasta, casserole, stir-fry, roast, grilled, baked, fried, braised, slow cooker, one-pot, skillet
  - Protein: chicken, beef, pork, lamb, fish, seafood, shrimp, tofu, eggs, turkey
  - Cuisine: italian, mexican, asian, chinese, japanese, korean, thai, indian, mediterranean, french, american, cajun, southern, greek, middle eastern
  - Dietary: vegetarian, vegan, gluten-free, dairy-free, low-carb, keto, healthy
  - Flavor: savory, sweet, spicy, tangy, smoky, creamy, fresh, rich
  - Occasion: weeknight, meal prep, entertaining, holiday, comfort food, quick, make-ahead, summer, fall, winter

Important:
- Extract ALL ingredients, even if formatting is unusual (two-column, inline, etc.)
- Extract ALL instruction steps, even if they're in paragraph form (split into logical steps)
- Clean up OCR artifacts and formatting issues
- If servings looks wrong (e.g., "60" for a home recipe), use your judgment to correct it
- Return ONLY valid JSON, no other text

Recipe text:
"""


def extract_recipe_with_llm(text: str, client: anthropic.Anthropic) -> dict:
    """Use Claude to extract structured recipe data from text."""
    message = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT + text
            }
        ]
    )

    # Parse the JSON response
    response_text = message.content[0].text

    # Try to extract JSON from response (in case there's any wrapper text)
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        return json.loads(json_match.group())

    raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")


def main():
    unified_dir = Path(__file__).parent / 'ocr_results_unified'
    output_dir = Path(__file__).parent / 'recipes_structured'
    output_dir.mkdir(exist_ok=True)

    # Initialize Anthropic client
    client = anthropic.Anthropic()

    files = sorted(unified_dir.glob('*.txt'))

    print(f"Processing {len(files)} recipes with Claude...\n")

    failed = []

    for i, f in enumerate(files, 1):
        text = f.read_text()
        filename = f.name

        try:
            recipe = extract_recipe_with_llm(text, client)

            # Add source file reference
            recipe['source_file'] = filename

            # Add category field (null by default, to be filled manually)
            recipe['category'] = None

            # Create output filename from recipe name
            name = recipe.get('name', filename.replace('.txt', ''))
            safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
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

            ing_count = len(recipe.get('ingredients', []))
            inst_count = len(recipe.get('instructions', []))
            tag_count = len(recipe.get('tags', []))
            print(f"[{i}/{len(files)}] {name[:50]:<50} ({ing_count} ing, {inst_count} steps, {tag_count} tags)")

            # Small delay to avoid rate limits
            time.sleep(0.1)

        except Exception as e:
            print(f"[{i}/{len(files)}] FAILED: {filename} - {e}")
            failed.append((filename, str(e)))

    print(f"\nDone! Processed {len(files) - len(failed)}/{len(files)} recipes")

    if failed:
        print(f"\nFailed recipes ({len(failed)}):")
        for name, error in failed:
            print(f"  - {name}: {error}")


if __name__ == '__main__':
    main()
