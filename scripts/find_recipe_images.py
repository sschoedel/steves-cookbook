#!/usr/bin/env python3
"""
Find and download food images for recipes from free stock photo sites.
Creates links files for manual download when automatic download fails.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent.parent
FOOD_IMAGES_DIR = BASE_DIR / "food_images"
RECIPE_MAPPING_FILE = BASE_DIR / "recipe_mapping.json"
RECIPE_ORDER_FILE = BASE_DIR / "recipe_order.json"

# Free stock photo search URLs
UNSPLASH_SEARCH = "https://unsplash.com/s/photos/{query}"
PEXELS_SEARCH = "https://www.pexels.com/search/{query}/"
PIXABAY_SEARCH = "https://pixabay.com/images/search/{query}/"

def sanitize_filename(name: str) -> str:
    """Convert recipe name to safe folder/file name."""
    # Remove .json extension
    name = name.replace(".json", "")
    # Replace special chars with underscores
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    return name

def get_search_term(recipe_name: str) -> str:
    """Extract a good search term from recipe name."""
    # Remove .json
    name = recipe_name.replace(".json", "")
    # Remove common words that don't help image search
    remove_words = ["with", "and", "the", "in", "a", "an", "style", "easy", "quick", "perfect", "classic", "best"]
    words = name.split()
    filtered = [w for w in words if w.lower() not in remove_words]
    # Take first 3-4 significant words
    return " ".join(filtered[:4])

def create_links_file(recipe_name: str, search_term: str) -> str:
    """Create a text file with links to search for images."""
    folder_name = sanitize_filename(recipe_name)
    folder_path = FOOD_IMAGES_DIR / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    # URL encode the search term
    encoded_term = urllib.parse.quote(search_term.lower().replace(" ", "-"))
    encoded_term_plus = urllib.parse.quote_plus(search_term.lower())

    links_content = f"""Recipe: {recipe_name.replace('.json', '')}
Search Term: {search_term}

Find 3 high-quality food photos from these sites:

1. Unsplash (free, high quality):
   {UNSPLASH_SEARCH.format(query=encoded_term)}

2. Pexels (free, high quality):
   {PEXELS_SEARCH.format(query=encoded_term)}

3. Pixabay (free):
   {PIXABAY_SEARCH.format(query=encoded_term_plus)}

4. Google Images (filter by usage rights):
   https://www.google.com/search?q={encoded_term_plus}+food&tbm=isch&tbs=il:cl

Download 3 images and save them as:
- {folder_name}_1.jpg
- {folder_name}_2.jpg
- {folder_name}_3.jpg
"""

    links_file = folder_path / "image_links.txt"
    with open(links_file, "w") as f:
        f.write(links_content)

    return str(folder_path)

def update_mapping(recipe_name: str, folder_name: str, images: list):
    """Update recipe_mapping.json with image info."""
    mapping = {}
    if RECIPE_MAPPING_FILE.exists():
        with open(RECIPE_MAPPING_FILE) as f:
            mapping = json.load(f)

    mapping[recipe_name] = {
        "folder": folder_name,
        "images": images,
        "status": "links_created" if not images else "downloaded"
    }

    with open(RECIPE_MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

def process_recipe(recipe_name: str) -> dict:
    """Process a single recipe - create folder and links file."""
    search_term = get_search_term(recipe_name)
    folder_name = sanitize_filename(recipe_name)

    # Create links file
    folder_path = create_links_file(recipe_name, search_term)

    # Update mapping
    update_mapping(recipe_name, folder_name, [])

    return {
        "recipe": recipe_name,
        "folder": folder_name,
        "search_term": search_term,
        "status": "links_created"
    }

def main():
    # Load recipes
    with open(RECIPE_ORDER_FILE) as f:
        recipes = json.load(f)

    print(f"Processing {len(recipes)} recipes...")

    # Process each recipe
    for i, recipe in enumerate(recipes, 1):
        result = process_recipe(recipe)
        print(f"[{i}/{len(recipes)}] {result['recipe'][:50]}... -> {result['folder']}")

    print(f"\nDone! Created folders and link files in {FOOD_IMAGES_DIR}")
    print(f"Mapping saved to {RECIPE_MAPPING_FILE}")
    print("\nNext steps:")
    print("1. Open each folder's image_links.txt")
    print("2. Visit the links and download 3 high-quality images")
    print("3. Save them as <folder_name>_1.jpg, _2.jpg, _3.jpg")

if __name__ == "__main__":
    main()
