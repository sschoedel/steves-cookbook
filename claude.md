# Steve's Cookbook - Project Context

## Overview
This project converts a collection of ~180 recipe images (photos of handwritten/printed recipes, screenshots from websites, etc.) into structured JSON files suitable for database storage.

## Pipeline Architecture

The processing pipeline has 4 passes:

### Pass 1: Batch OCR ✅ COMPLETE
- **Script:** `ocr_batch.py`
- **Input:** External directory of recipe images (HEIC/JPG/PNG)
- **Output:** `ocr_results/` - one `.txt` file per image
- **Tech:** Uses Mistral's Pixtral vision model for OCR via API

### Pass 2: Unify Multi-Page Recipes ✅ COMPLETE
- **Method:** Interactive Claude session
- **Input:** `ocr_results/`
- **Output:** `ocr_results_unified/` - one `.txt` file per recipe (109 files)
- **Purpose:** Combines consecutive images that belong to the same multi-page recipe, extracts recipe names for filenames

### Pass 3: Determine Section Structure ✅ COMPLETE
- **Method:** Interactive Claude session
- **Output:** `recipe_sections.json` - standardized schema for recipe JSON structure
- **Purpose:** Analyzed all recipes to identify common sections and create a consistent schema

### Pass 4: Structure Recipes ✅ COMPLETE
- **Method:** Interactive Claude session (in-context processing, not API script)
- **Input:** `ocr_results_unified/` + `recipe_sections.json`
- **Output:** `recipes_structured/` - one JSON file per recipe (108 files)
- **Note:** An LLM-based script (`structure_recipes_llm.py`) was created but not used due to API key issues; processing was done directly in conversation context

## Directory Structure
```
steves-cookbook/
├── CLAUDE.md                    # This file - project context
├── recipe_sections.json         # Pass 3: Section schema
├── recipe_order.json            # Cookbook order (generated)
├── pyproject.toml               # Python project config (uses uv)
├── scripts/
│   ├── ocr_batch.py             # Pass 1: Batch OCR script
│   ├── ocr_test.py              # Single image OCR test script
│   ├── unify_recipes.py         # Pass 2: Main unification script
│   ├── merge_pages.py           # Pass 2 helper: Merge multi-page recipes
│   ├── rename_helper.py         # Pass 2 helper: Rename poorly-named files
│   ├── cleanup_html_entities.py # Pass 2 helper: Clean HTML entities
│   ├── generate_recipe_order.py # Generates recipe_order.json
│   ├── import_recipes_to_indesign.jsx  # InDesign import script
│   └── install_indesign_script.sh      # Installs jsx to InDesign
├── prompts/
│   └── structuring-prompt.md    # Prompt for Pass 4 recipe structuring
├── ocr_results/                 # Pass 1 output: Raw OCR (1 txt per image)
├── ocr_results_unified/         # Pass 2 output: Combined recipes (109 txt files)
└── recipes_structured/          # Pass 4 output: Final JSON (108 files)
```

## Recipe JSON Schema

Each structured recipe JSON file follows this format:

```json
{
  "name": "Recipe Name",
  "source": "Website or cookbook name (optional)",
  "source_file": "Original filename.txt",
  "author": "Author name (optional)",
  "description": "Brief description of the dish",
  "prep_time": "15 minutes (optional)",
  "cook_time": "30 minutes (optional)",
  "total_time": "45 minutes (optional)",
  "servings": "4",
  "difficulty": "easy/medium/hard (optional)",
  "ingredients": [
    "1 cup flour",
    "2 eggs",
    "..."
  ],
  "ingredient_groups": {
    "Sauce": ["ingredient 1", "..."],
    "Main": ["ingredient 1", "..."]
  },
  "instructions": [
    "Step 1...",
    "Step 2...",
    "..."
  ],
  "notes": [
    "Tip or variation...",
    "..."
  ],
  "nutrition": {
    "calories": "350",
    "protein": "25g",
    "..."
  },
  "category": null,
  "tags": ["dinner", "chicken", "italian", "quick", "healthy"]
}
```

### Tag Vocabulary
Tags are auto-assigned based on recipe content:
- **Meal type:** breakfast, lunch, dinner, snack, dessert, appetizer
- **Dish type:** salad, soup, stew, pasta, casserole, sandwich, etc.
- **Protein:** chicken, beef, pork, seafood, fish, tofu, vegetarian, vegan
- **Cuisine:** italian, mexican, asian, indian, french, american, etc.
- **Dietary:** healthy, low-calorie, gluten-free, dairy-free
- **Other:** quick, make-ahead, one-pot, comfort food, spicy, fall, winter, summer, spring

### Category Field
The `category` field is `null` by default. User should manually update to classify recipes as:
- `"Steve's Signatures"` - Steve's own creations or heavily modified recipes
- `"Steve Approved"` - Recipes from other sources that Steve likes

## What's Done
- ✅ All 4 passes of the pipeline complete
- ✅ 108 recipes structured as JSON in `recipes_structured/`
- ✅ Recipes include ingredients, instructions, notes, nutrition (when available), and auto-generated tags
- ✅ InDesign import script created for cookbook layout

## Recipe Breakdown by Category

| Category | Count | Notes |
|----------|-------|-------|
| **Appetizers & Dips** | 5 | Olives, crab dip, queso, carrot dip, tomato burrata |
| **Salads** | 5 | Mix of side salads (excludes main-course salads) |
| **Soups** | 8 | Various soups including chili |
| **Main Courses** | ~70 | See breakdown below |
| **Side Dishes** | 14 | Potatoes, vegetables, grains |
| **Desserts** | 7 | Cakes, pies, pudding, bars |

### Main Course Breakdown
- **Chicken & Turkey:** 36 recipes
- **Beef:** 8 recipes
- **Pork:** 4 recipes
- **Seafood & Fish:** 13 recipes
- **Vegetarian & Vegan:** 7 recipes
- **Pasta:** 1 recipe (not categorized by protein)

**Note:** No dedicated breakfast items in the collection.

## Cookbook Order

Recipes are ordered for a logical meal progression:

1. **Appetizers & Dips** (5)
2. **Salads** (5)
3. **Soups** (8)
4. **Main Courses** - organized by protein:
   - Chicken & Turkey
   - Beef
   - Pork
   - Seafood & Fish
   - Vegetarian & Vegan
   - Pasta
5. **Side Dishes** (14)
6. **Desserts** (7)

The ordered list is stored in `recipe_order.json` and used by the InDesign import script.

To regenerate the order (e.g., after adding recipes):
```bash
python3 scripts/generate_recipe_order.py
```

## InDesign Export

### Scripts
- `scripts/import_recipes_to_indesign.jsx` - Main InDesign script
- `scripts/install_indesign_script.sh` - Copies script to InDesign Scripts Panel
- `scripts/generate_recipe_order.py` - Generates `recipe_order.json`

### Usage
1. Run `python3 scripts/generate_recipe_order.py` to create/update recipe order
2. Run `./scripts/install_indesign_script.sh` to install the InDesign script
3. In InDesign: Window > Utilities > Scripts
4. Double-click `import_recipes_to_indesign.jsx`
5. Select the `recipes_structured` folder
6. Edit paragraph styles in Window > Styles > Paragraph Styles

### Document Settings (for print)
- **Page size:** 8.25" × 10.25" (trims to 8" × 10" finished)
- **Margins:** Top/bottom 0.5", Left/right 1"
- **Single pages** (not facing)

### Paragraph Styles Created
- Recipe Title
- Recipe Meta
- Recipe Description
- Section Header - Ingredients
- Section Header - Instructions
- Section Header - Notes
- Ingredient Group
- Ingredient
- Instruction
- Note
- Tags
- Nutrition Info

After import, modify any style in InDesign and all text using that style updates automatically.

## What's Left To Do
1. **Manual categorization:** Update `category` field in each JSON to classify as "Steve's Signatures" vs "Steve Approved"
2. **Database import:** Load JSON files into whatever database system is chosen
3. **Quality review:** Spot-check some recipes to verify accuracy of extraction
4. **Tag refinement:** User may want to edit/refine auto-generated tags

## Technical Notes

### Dependencies
- Python package management via `uv`
- Mistral API for OCR (requires `MISTRAL_API_KEY`)
- Anthropic API available but not used for structuring (requires `ANTHROPIC_API_KEY`)

### Why Heuristic Approach Failed
An initial attempt at regex-based extraction failed due to:
- Varied formats (markdown, handwritten-style, two-column layouts, plain text)
- Inconsistent ingredient formatting across recipes
- OCR artifacts and formatting variations

The solution was to process each recipe directly using Claude's semantic understanding, which handled all format variations successfully.

### File Count Discrepancy
- `ocr_results_unified/`: 109 files
- `recipes_structured/`: 108 files
- The 1-file difference is due to filename normalization (e.g., "CAPS NAMES" → "Title Case Names", removing special characters)

## Resuming Work

To continue working on this project:
1. Review this file for context
2. Check `recipes_structured/` for the final output
3. For any new recipes, follow the same pipeline or process directly in conversation
4. The plan file at `~/.claude/plans/eager-percolating-yao.md` contains the original detailed plan (may be outdated)
