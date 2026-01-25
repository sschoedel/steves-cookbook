# Steve's Cookbook

A project to digitize and organize Steve's recipe collection using OCR and AI-powered structuring.

## Overview

This repository contains a 4-pass pipeline that converts ~180 recipe images (photos of handwritten recipes, screenshots from websites, etc.) into structured JSON files suitable for database storage.

**Status:** Pipeline complete! 108 recipes structured as JSON in `recipes_structured/`

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Mistral API key from https://console.mistral.ai/

### Installation

```bash
cd steves-cookbook
uv sync
export MISTRAL_API_KEY=your_api_key_here
```

## Pipeline Overview

| Pass | Description | Script/Method | Output |
|------|-------------|---------------|--------|
| 1 | Batch OCR | `scripts/ocr_batch.py` | `ocr_results/` (184 txt files) |
| 2 | Unify multi-page recipes | Interactive Claude + helper scripts | `ocr_results_unified/` (109 txt files) |
| 3 | Determine section schema | Interactive Claude | `recipe_sections.json` |
| 4 | Structure recipes | Interactive Claude | `recipes_structured/` (108 JSON files) |

## Project Structure

```
steves-cookbook/
├── README.md                    # This file
├── claude.md                    # Detailed project context for Claude sessions
├── recipe_sections.json         # Schema for recipe JSON structure
├── recipe_mapping.json          # Maps original images to recipes
├── pyproject.toml               # Python dependencies (uses uv)
├── scripts/
│   ├── ocr_batch.py             # Pass 1: Batch OCR using Mistral Pixtral
│   ├── ocr_test.py              # Single image OCR for testing
│   ├── unify_recipes.py         # Pass 2: Main unification script
│   ├── merge_pages.py           # Pass 2 helper: Merge multi-page recipes
│   ├── rename_helper.py         # Pass 2 helper: Rename files
│   └── cleanup_html_entities.py # Pass 2 helper: Clean HTML entities
├── prompts/
│   └── structuring-prompt.md    # Prompt for Pass 4 recipe structuring
├── ocr_results/                 # Raw OCR output (1 txt per image)
├── ocr_results_unified/         # Combined recipes (1 txt per recipe)
└── recipes_structured/          # Final JSON output (1 file per recipe)
```

## Recipe JSON Format

Each recipe in `recipes_structured/` follows this schema:

```json
{
  "name": "Recipe Name",
  "source": "Website or cookbook name",
  "author": "Author name",
  "description": "Brief description",
  "prep_time": "15 minutes",
  "cook_time": "30 minutes",
  "servings": "4",
  "ingredients": ["1 cup flour", "2 eggs"],
  "ingredient_groups": {"Sauce": ["..."], "Main": ["..."]},
  "instructions": ["Step 1...", "Step 2..."],
  "notes": ["Tip or variation..."],
  "nutrition": {"calories": "350", "protein": "25g"},
  "category": null,
  "tags": ["dinner", "chicken", "italian", "quick"]
}
```

## What's Next

1. **Manual categorization:** Update `category` field in each JSON ("Steve's Signatures" vs "Steve Approved")
2. **Database import:** Load JSON files into your database of choice
3. **Quality review:** Spot-check recipes to verify extraction accuracy

## Documentation

See `claude.md` for detailed project context, tag vocabulary, and technical notes.
