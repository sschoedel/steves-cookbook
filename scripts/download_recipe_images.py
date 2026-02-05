#!/usr/bin/env python3
"""
Download food images from Unsplash for recipes.
Uses Unsplash Source API for direct image downloads.
"""

import json
import os
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent.parent
FOOD_IMAGES_DIR = BASE_DIR / "food_images"
RECIPE_MAPPING_FILE = BASE_DIR / "recipe_mapping.json"
RECIPE_ORDER_FILE = BASE_DIR / "recipe_order.json"

# Unsplash Source API (no auth required, returns random matching image)
UNSPLASH_SOURCE = "https://source.unsplash.com/800x600/?{query}"

def sanitize_filename(name: str) -> str:
    """Convert recipe name to safe folder/file name."""
    name = name.replace(".json", "")
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

def get_search_term(recipe_name: str) -> str:
    """Extract a good search term from recipe name."""
    name = recipe_name.replace(".json", "")
    # Map specific dishes to better search terms
    search_mappings = {
        "Fried Green Olives": "fried olives appetizer",
        "Maryland Hot Crab Dip": "crab dip",
        "Philly Cheesesteak Queso": "cheese dip",
        "Champagne Vinaigrette": "salad dressing",
        "Rosy Chicken": "roasted chicken",
        "Misoyaki Butterfish": "miso fish",
        "Ginataang Gulay": "vegetable coconut stew",
        "BB's Apple Cake": "apple cake",
    }

    for key, term in search_mappings.items():
        if key in name:
            return term

    # Remove common filler words
    remove_words = ["with", "and", "the", "in", "a", "an", "style", "easy", "quick",
                    "perfect", "classic", "best", "one-pan", "skillet", "slow", "cooker"]
    words = name.split()
    filtered = [w for w in words if w.lower() not in remove_words]

    # Add "food" to improve results
    term = " ".join(filtered[:3])
    return f"{term} food"

def download_image(url: str, filepath: Path, timeout: int = 15) -> bool:
    """Download an image from URL to filepath."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Check if we got an actual image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                return False

            with open(filepath, 'wb') as f:
                f.write(response.read())
            return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False

def download_images_for_recipe(recipe_name: str, num_images: int = 3) -> list:
    """Download images for a single recipe."""
    search_term = get_search_term(recipe_name)
    folder_name = sanitize_filename(recipe_name)
    folder_path = FOOD_IMAGES_DIR / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    downloaded = []
    query = urllib.parse.quote(search_term)

    for i in range(1, num_images + 1):
        filename = f"{folder_name}_{i}.jpg"
        filepath = folder_path / filename

        # Skip if already exists
        if filepath.exists() and filepath.stat().st_size > 1000:
            print(f"    [{i}] Already exists: {filename}")
            downloaded.append(filename)
            continue

        # Add timestamp to get different images each time
        url = UNSPLASH_SOURCE.format(query=query) + f"&sig={i}{int(time.time())}"

        print(f"    [{i}] Downloading: {search_term}...")
        if download_image(url, filepath):
            # Verify file is valid (not too small)
            if filepath.stat().st_size > 5000:
                downloaded.append(filename)
                print(f"    [{i}] Saved: {filename}")
            else:
                filepath.unlink()  # Delete invalid file
                print(f"    [{i}] Invalid image, skipped")

        # Small delay to be nice to the API
        time.sleep(0.5)

    return downloaded

def update_mapping(recipe_name: str, folder_name: str, images: list):
    """Update recipe_mapping.json with image info."""
    mapping = {}
    if RECIPE_MAPPING_FILE.exists():
        with open(RECIPE_MAPPING_FILE) as f:
            mapping = json.load(f)

    status = "complete" if len(images) >= 3 else ("partial" if images else "pending")
    mapping[recipe_name] = {
        "folder": folder_name,
        "images": images,
        "status": status
    }

    with open(RECIPE_MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

def main():
    import sys

    # Load recipes
    with open(RECIPE_ORDER_FILE) as f:
        recipes = json.load(f)

    # Allow specifying start index
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(recipes)

    print(f"Downloading images for recipes {start_idx+1} to {end_idx}...")

    total_downloaded = 0
    for i, recipe in enumerate(recipes[start_idx:end_idx], start_idx + 1):
        folder_name = sanitize_filename(recipe)
        print(f"\n[{i}/{len(recipes)}] {recipe.replace('.json', '')}")

        images = download_images_for_recipe(recipe)
        update_mapping(recipe, folder_name, images)
        total_downloaded += len(images)

    print(f"\n\nDone! Downloaded {total_downloaded} images.")
    print(f"Mapping saved to {RECIPE_MAPPING_FILE}")

if __name__ == "__main__":
    main()
