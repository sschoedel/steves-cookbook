# Recipe Structuring Prompt

Use this prompt to instruct Claude to convert OCR'd recipe text files into structured JSON.

---

## The Prompt

You are converting recipe text files into structured JSON. The input files are in `ocr_results_unified/` and output should go to `recipes_structured/`.

### Process

1. Read recipe text files in batches of 5 using the Read tool
2. Extract structured data from each recipe
3. Write JSON files using the Write tool
4. Repeat until all files are processed

### JSON Schema

For each recipe, create a JSON file with this structure:

```json
{
  "name": "Recipe Name",
  "source": "Website or cookbook (if mentioned)",
  "source_file": "Original Filename.txt",
  "author": "Author name (if mentioned)",
  "description": "Brief 1-2 sentence description of the dish",
  "prep_time": "X minutes (if mentioned)",
  "cook_time": "X minutes (if mentioned)",
  "total_time": "X minutes (if mentioned)",
  "servings": "X (if mentioned)",
  "ingredients": [
    "Full ingredient with quantity and preparation notes",
    "..."
  ],
  "instructions": [
    "Complete step 1...",
    "Complete step 2...",
    "..."
  ],
  "notes": [
    "Tips, variations, make-ahead instructions...",
    "..."
  ],
  "nutrition": {
    "calories": "X",
    "protein": "Xg",
    "carbohydrates": "Xg",
    "fat": "Xg",
    "fiber": "Xg",
    "sodium": "Xmg"
  },
  "category": null,
  "tags": ["tag1", "tag2", "..."]
}
```

### Field Guidelines

- **name**: Clean recipe title (fix OCR errors, proper capitalization)
- **source**: Extract from URL, header, or attribution if present
- **source_file**: The exact input filename
- **author**: Only include if explicitly mentioned
- **description**: Write one if not provided, based on ingredients/method
- **times/servings**: Only include if explicitly stated
- **ingredients**: Preserve exact quantities and notes; one ingredient per array item
- **ingredient_groups**: Use this instead of flat `ingredients` if recipe has sections (e.g., "For the sauce:", "For the filling:")
- **instructions**: Clean up formatting, one step per array item, preserve all details
- **notes**: Include tips, variations, storage instructions, make-ahead notes
- **nutrition**: Only include fields that are provided; omit entire object if no nutrition info
- **category**: Always set to `null` (user will fill in later)
- **tags**: Auto-generate 5-10 relevant tags

### Tag Categories

Assign tags from these categories as appropriate:

- **Meal**: breakfast, lunch, dinner, snack, dessert, appetizer, side dish
- **Dish type**: soup, stew, salad, pasta, casserole, sandwich, dip, roast, stir-fry, grilled, baked, braised
- **Protein**: chicken, beef, pork, seafood, fish, salmon, shrimp, tofu, vegetarian, vegan
- **Cuisine**: italian, mexican, asian, chinese, thai, korean, japanese, indian, french, american, mediterranean, cuban, hawaiian
- **Attributes**: healthy, quick, easy, comfort food, spicy, creamy, one-pot, sheet pan, make-ahead, meal prep, gluten-free, low-calorie
- **Season**: fall, winter, spring, summer

### Handling OCR Issues

- Fix obvious typos and OCR errors
- Interpret abbreviated measurements (TBS → tablespoons, tsp → teaspoon, C → cup, oz → ounces)
- Clean up formatting artifacts (random line breaks, garbled characters)
- If instructions are numbered inconsistently, renumber them properly
- If a recipe appears truncated, include what's available and note it in `notes`

### Filename Convention

Name the output JSON file based on the cleaned recipe name:
- `Honey Glazed Carrots.json`
- `Thai Basil Chicken (Pad Krapow Gai).json`
- `Mom's Apple Pie.json`

### Example Workflow

```
1. Read 5 files from ocr_results_unified/
2. For each file:
   - Parse the text to identify all recipe components
   - Structure into JSON following the schema
   - Generate appropriate tags
   - Write to recipes_structured/[Recipe Name].json
3. Report progress (e.g., "5 done, continuing...")
4. Repeat until complete
```

### Getting Started

First, list the files in `ocr_results_unified/` to see what needs processing, then check `recipes_structured/` to see what's already done. Process remaining files in batches.

---

## Usage

Copy the prompt above and give it to Claude along with access to the file system. Claude will read the OCR text files, extract structured data, and write JSON files.

The key insight is that LLM-based extraction handles varied formats (markdown, plain text, two-column layouts, handwritten-style notes) much better than regex/heuristic approaches.
