#!/usr/bin/env python3
"""
Generate an ordered list of recipes for the cookbook.
Order: Appetizers -> Salads -> Soups -> Main Courses (by protein) -> Sides -> Desserts
"""

import json
from pathlib import Path

RECIPES_DIR = Path(__file__).parent.parent / "recipes_structured"
OUTPUT_FILE = Path(__file__).parent.parent / "recipe_order.json"


def categorize_recipe(recipe: dict) -> tuple[str, str]:
    """
    Returns (category, subcategory) for sorting.
    Categories are numbered for sort order.
    """
    tags = set(recipe.get("tags", []))
    name = recipe.get("name", "").lower()

    # 1. Appetizers & Dips
    if "appetizer" in tags or "dip" in tags:
        return ("1_appetizers", "")

    # 2. Salads (but not main-course salads with protein as primary)
    if "salad" in tags:
        # Check if it's primarily a main course
        if "dinner" in tags and any(p in tags for p in ["chicken", "salmon", "fish", "beef"]):
            pass  # Will be categorized as main course below
        else:
            return ("2_salads", "")

    # 3. Soups (standalone soups, not dinner-tagged main courses)
    if "soup" in tags and "dinner" not in tags:
        return ("3_soups", "")

    # Check for chili
    if "chili" in tags:
        return ("3_soups", "")

    # 7. Desserts
    if "dessert" in tags:
        # Some are tagged as both side dish and dessert (like cranberry sauce)
        # If it's sweet, it's dessert
        if "sweet" in tags or any(word in name for word in ["cake", "pie", "pudding", "bar", "cookie"]):
            return ("7_desserts", "")

    # 6. Side Dishes (if tagged as side dish and not a main)
    if "side dish" in tags and "dinner" not in tags:
        # Exclude items that are really desserts
        if "dessert" not in tags:
            return ("6_sides", "")
        elif "sweet" not in tags:
            return ("6_sides", "")

    # 4. Main Courses - categorize by protein
    # Chicken
    if "chicken" in tags or "turkey" in tags:
        return ("4_mains", "a_chicken")

    # Beef
    if "beef" in tags:
        return ("4_mains", "b_beef")

    # Pork
    if "pork" in tags:
        return ("4_mains", "c_pork")

    # Seafood/Fish
    if any(tag in tags for tag in ["seafood", "fish", "shrimp", "salmon", "crab"]):
        return ("4_mains", "d_seafood")

    # Vegetarian/Vegan mains
    if any(tag in tags for tag in ["vegetarian", "vegan", "tofu", "lentils"]):
        if "dinner" in tags or "stew" in tags:
            return ("4_mains", "e_vegetarian")

    # Pasta (if not already categorized)
    if "pasta" in tags:
        return ("4_mains", "f_pasta")

    # Remaining dinner items
    if "dinner" in tags:
        return ("4_mains", "g_other")

    # Soups that are also mains
    if "soup" in tags:
        return ("3_soups", "")

    # Fallback for sides
    if "side dish" in tags:
        return ("6_sides", "")

    # Salads as fallback
    if "salad" in tags:
        return ("2_salads", "")

    # Everything else
    return ("5_other", "")


def main():
    recipes = []

    # Load all recipes
    for json_file in RECIPES_DIR.glob("*.json"):
        with open(json_file) as f:
            recipe = json.load(f)
            recipe["_filename"] = json_file.name
            category, subcategory = categorize_recipe(recipe)
            recipe["_category"] = category
            recipe["_subcategory"] = subcategory
            recipes.append(recipe)

    # Sort by category, subcategory, then name
    recipes.sort(key=lambda r: (r["_category"], r["_subcategory"], r["name"]))

    # Print summary and generate ordered list
    print("=" * 60)
    print("COOKBOOK ORDER")
    print("=" * 60)

    current_category = None
    current_subcategory = None
    ordered_filenames = []

    category_names = {
        "1_appetizers": "APPETIZERS & DIPS",
        "2_salads": "SALADS",
        "3_soups": "SOUPS",
        "4_mains": "MAIN COURSES",
        "5_other": "OTHER",
        "6_sides": "SIDE DISHES",
        "7_desserts": "DESSERTS",
    }

    subcategory_names = {
        "a_chicken": "Chicken & Turkey",
        "b_beef": "Beef",
        "c_pork": "Pork",
        "d_seafood": "Seafood & Fish",
        "e_vegetarian": "Vegetarian & Vegan",
        "f_pasta": "Pasta",
        "g_other": "Other",
    }

    for recipe in recipes:
        cat = recipe["_category"]
        subcat = recipe["_subcategory"]

        if cat != current_category:
            current_category = cat
            current_subcategory = None
            print(f"\n{'=' * 40}")
            print(f"{category_names.get(cat, cat)}")
            print(f"{'=' * 40}")

        if subcat and subcat != current_subcategory:
            current_subcategory = subcat
            print(f"\n  --- {subcategory_names.get(subcat, subcat)} ---")

        print(f"  • {recipe['name']}")
        ordered_filenames.append(recipe["_filename"])

    # Save ordered list
    with open(OUTPUT_FILE, "w") as f:
        json.dump(ordered_filenames, f, indent=2)

    print(f"\n\nOrdered list saved to: {OUTPUT_FILE}")
    print(f"Total recipes: {len(recipes)}")


if __name__ == "__main__":
    main()
