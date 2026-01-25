#!/bin/bash

# Copy the InDesign script to Adobe's Scripts Panel folder

SOURCE="/Users/samschoedel/git/steves-cookbook/scripts/import_recipes_to_indesign.jsx"
DEST="/Users/samschoedel/Library/Preferences/Adobe InDesign/Version 21.0/en_US/Scripts/Scripts Panel"

cp "$SOURCE" "$DEST/"

echo "Copied import_recipes_to_indesign.jsx to InDesign Scripts Panel"
