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
├── claude.md                    # This file - project context
├── ocr_test.py                  # Single image OCR test script
├── ocr_batch.py                 # Pass 1: Batch OCR script
├── structure_recipes.py         # Heuristic-based structuring (deprecated - didn't work well)
├── structure_recipes_llm.py     # LLM-based structuring script (not used)
├── recipe_sections.json         # Pass 3: Section schema
├── ocr_results/                 # Pass 1 output: Raw OCR (1 txt per image)
├── ocr_results_unified/         # Pass 2 output: Combined recipes (109 txt files)
├── recipes_structured/          # Pass 4 output: Final JSON (108 files)
└── pyproject.toml               # Python project config (uses uv)
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

### Why Heuristic Script Failed
The initial `structure_recipes.py` used regex-based extraction but failed due to:
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
