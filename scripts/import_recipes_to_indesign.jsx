/*
 * Steve's Cookbook - Recipe Import Script for InDesign
 *
 * This script imports recipe JSON files into an InDesign document with
 * paragraph styles applied. After import, you can modify the styles
 * in InDesign and all text will update automatically.
 *
 * USAGE:
 * 1. Open InDesign
 * 2. Run this script from Window > Utilities > Scripts
 * 3. Select the folder containing your recipe JSON files
 * 4. The script creates a new document with all recipes styled
 *
 * After import, edit styles in Window > Styles > Paragraph Styles
 */

// ============================================================================
// CONFIGURATION - Adjust these values as needed
// ============================================================================

var CONFIG = {
    // Page setup (in inches) - 8.25x10.25 trims to 8x10 finished
    pageWidth: 8.25,
    pageHeight: 10.25,
    marginTop: 0.5,         // minimum 0.44" per printer specs
    marginBottom: 0.5,
    marginInside: 1,        // left margin (1" per printer specs)
    marginOutside: 1,       // right margin (1" per printer specs)

    // Text frame inset from margins (in inches)
    frameInset: 0,

    // Space between recipes (in inches)
    recipeSpacing: 0.5,

    // Whether to start each recipe on a new page
    newPagePerRecipe: true
};

// ============================================================================
// MAIN SCRIPT
// ============================================================================

main();

function main() {
    // Prompt user to select folder containing JSON files
    var folder = Folder.selectDialog("Select the folder containing recipe JSON files");
    if (!folder) {
        alert("No folder selected. Script cancelled.");
        return;
    }

    // Get all JSON files in the folder
    var jsonFiles = folder.getFiles("*.json");
    if (jsonFiles.length === 0) {
        alert("No JSON files found in the selected folder.");
        return;
    }

    // Check for recipe_order.json in parent folder to determine sort order
    var orderFile = new File(folder.parent.fsName + "/recipe_order.json");
    var orderedNames = null;

    if (orderFile.exists) {
        orderedNames = readJSONFile(orderFile);
        if (orderedNames && orderedNames.length > 0) {
            // Sort files according to the order file
            jsonFiles.sort(function(a, b) {
                var aIndex = -1, bIndex = -1;
                for (var i = 0; i < orderedNames.length; i++) {
                    if (orderedNames[i] === a.name) aIndex = i;
                    if (orderedNames[i] === b.name) bIndex = i;
                }
                // Files not in order list go to the end
                if (aIndex === -1) aIndex = 9999;
                if (bIndex === -1) bIndex = 9999;
                return aIndex - bIndex;
            });
        }
    } else {
        // Fallback: sort alphabetically by name
        jsonFiles.sort(function(a, b) {
            return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
        });
    }

    // Create new document
    var doc = app.documents.add();

    // Setup document
    setupDocument(doc);

    // Create paragraph styles
    var styles = createParagraphStyles(doc);

    // Create layers
    createLayers(doc);

    // Process each recipe
    var recipeCount = 0;
    for (var i = 0; i < jsonFiles.length; i++) {
        var recipe = readJSONFile(jsonFiles[i]);
        if (recipe) {
            addRecipeToDocument(doc, recipe, styles, recipeCount === 0);
            recipeCount++;
        }
    }

    // Remove any empty pages at the end
    cleanupEmptyPages(doc);

    alert("Import complete!\n\n" + recipeCount + " recipes imported.\n\nEdit paragraph styles in Window > Styles > Paragraph Styles to change formatting.");
}

// ============================================================================
// DOCUMENT SETUP
// ============================================================================

function setupDocument(doc) {
    // Set measurement units to inches
    doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.INCHES;
    doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.INCHES;

    with (doc.documentPreferences) {
        pageWidth = CONFIG.pageWidth;
        pageHeight = CONFIG.pageHeight;
        facingPages = false;
        pagesPerDocument = 1;
    }

    with (doc.marginPreferences) {
        top = CONFIG.marginTop;
        bottom = CONFIG.marginBottom;
        left = CONFIG.marginInside;   // Left margin
        right = CONFIG.marginOutside; // Right margin
    }
}

function createLayers(doc) {
    // Create layers for organization
    var textLayer = doc.layers.itemByName("Recipe Text");
    if (!textLayer.isValid) {
        textLayer = doc.layers.add({name: "Recipe Text"});
    }

    // Move default layer content to Recipe Text layer if needed
    try {
        var defaultLayer = doc.layers.itemByName("Layer 1");
        if (defaultLayer.isValid) {
            defaultLayer.name = "Background";
            defaultLayer.move(LocationOptions.AT_END);
        }
    } catch (e) {}
}

// ============================================================================
// PARAGRAPH STYLES
// ============================================================================

function createParagraphStyles(doc) {
    var styles = {};

    // Helper: convert points to inches (72 points = 1 inch)
    function pt(points) {
        return points / 72;
    }

    // Recipe Title - Large, bold header
    styles.title = createOrGetStyle(doc, "Recipe Title", {
        pointSize: 24,
        fontStyle: "Bold",
        justification: Justification.CENTER_ALIGN,
        spaceBefore: 0,
        spaceAfter: pt(12),
        hyphenation: false
    });

    // Recipe Meta - Source, author, times (smaller, italic)
    styles.meta = createOrGetStyle(doc, "Recipe Meta", {
        pointSize: 10,
        fontStyle: "Italic",
        justification: Justification.CENTER_ALIGN,
        spaceBefore: 0,
        spaceAfter: pt(6),
        hyphenation: false
    });

    // Recipe Description - Intro paragraph
    styles.description = createOrGetStyle(doc, "Recipe Description", {
        pointSize: 11,
        fontStyle: "Regular",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(6),
        spaceAfter: pt(12),
        hyphenation: true
    });

    // Section Headers - separate style for each section type
    styles.sectionHeaderIngredients = createOrGetStyle(doc, "Section Header - Ingredients", {
        pointSize: 14,
        fontStyle: "Bold",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(12),
        spaceAfter: pt(6),
        hyphenation: false
    });

    styles.sectionHeaderInstructions = createOrGetStyle(doc, "Section Header - Instructions", {
        pointSize: 14,
        fontStyle: "Bold",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(12),
        spaceAfter: pt(6),
        hyphenation: false
    });

    styles.sectionHeaderNotes = createOrGetStyle(doc, "Section Header - Notes", {
        pointSize: 14,
        fontStyle: "Bold",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(12),
        spaceAfter: pt(6),
        hyphenation: false
    });

    // Ingredient Group - Subheader for grouped ingredients
    styles.ingredientGroup = createOrGetStyle(doc, "Ingredient Group", {
        pointSize: 11,
        fontStyle: "Bold Italic",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(8),
        spaceAfter: pt(4),
        hyphenation: false
    });

    // Ingredient - Individual ingredient lines
    styles.ingredient = createOrGetStyle(doc, "Ingredient", {
        pointSize: 10,
        fontStyle: "Regular",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: 0,
        spaceAfter: pt(2),
        leftIndent: pt(12),
        hyphenation: false
    });

    // Instruction - Numbered steps
    styles.instruction = createOrGetStyle(doc, "Instruction", {
        pointSize: 10,
        fontStyle: "Regular",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: 0,
        spaceAfter: pt(8),
        leftIndent: pt(18),
        firstLineIndent: pt(-18),
        hyphenation: true
    });

    // Note - Recipe notes/tips
    styles.note = createOrGetStyle(doc, "Note", {
        pointSize: 9,
        fontStyle: "Italic",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: 0,
        spaceAfter: pt(4),
        leftIndent: pt(12),
        hyphenation: true
    });

    // Tags - Tag line at end
    styles.tags = createOrGetStyle(doc, "Tags", {
        pointSize: 8,
        fontStyle: "Regular",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(12),
        spaceAfter: 0,
        hyphenation: false
    });

    // Nutrition - Nutrition info
    styles.nutrition = createOrGetStyle(doc, "Nutrition Info", {
        pointSize: 8,
        fontStyle: "Regular",
        justification: Justification.LEFT_ALIGN,
        spaceBefore: pt(8),
        spaceAfter: 0,
        hyphenation: false
    });

    return styles;
}

function createOrGetStyle(doc, styleName, props) {
    var style;
    try {
        style = doc.paragraphStyles.itemByName(styleName);
        if (!style.isValid) {
            throw "not found";
        }
    } catch (e) {
        style = doc.paragraphStyles.add({name: styleName});
    }

    // Apply properties
    try {
        if (props.pointSize) style.pointSize = props.pointSize;
        if (props.fontStyle) {
            try {
                style.fontStyle = props.fontStyle;
            } catch (e) {
                // Font style might not exist, ignore
            }
        }
        if (props.justification) style.justification = props.justification;
        if (props.spaceBefore !== undefined) style.spaceBefore = props.spaceBefore;
        if (props.spaceAfter !== undefined) style.spaceAfter = props.spaceAfter;
        if (props.leftIndent !== undefined) style.leftIndent = props.leftIndent;
        if (props.firstLineIndent !== undefined) style.firstLineIndent = props.firstLineIndent;
        if (props.hyphenation !== undefined) style.hyphenation = props.hyphenation;
    } catch (e) {
        // Some properties might fail, continue anyway
    }

    return style;
}

// ============================================================================
// RECIPE PROCESSING
// ============================================================================

function addRecipeToDocument(doc, recipe, styles, isFirst) {
    // Get or create page
    var page;
    if (isFirst) {
        page = doc.pages[0];
    } else if (CONFIG.newPagePerRecipe) {
        page = doc.pages.add();
    } else {
        page = doc.pages[-1]; // Last page
    }

    // Calculate text frame bounds based on margins
    var bounds = getTextFrameBounds(page);

    // Create text frame
    var textLayer = doc.layers.itemByName("Recipe Text");
    var frame = page.textFrames.add({
        geometricBounds: bounds,
        itemLayer: textLayer
    });

    // Enable auto-size to grow vertically
    frame.textFramePreferences.autoSizingType = AutoSizingTypeEnum.HEIGHT_ONLY;
    frame.textFramePreferences.autoSizingReferencePoint = AutoSizingReferenceEnum.TOP_CENTER_POINT;

    // Build recipe content
    var content = buildRecipeContent(recipe);

    // Add content to frame
    frame.contents = content.text;

    // Apply styles to ranges
    applyStylesToFrame(frame, content.ranges, styles);

    // Handle overflow - add pages as needed
    handleOverflow(doc, frame, textLayer);
}

function getTextFrameBounds(page) {
    var margin = page.marginPreferences;
    return [
        margin.top + CONFIG.frameInset,
        margin.left + CONFIG.frameInset,
        page.bounds[2] - margin.bottom - CONFIG.frameInset,
        page.bounds[3] - margin.right - CONFIG.frameInset
    ];
}

function buildRecipeContent(recipe) {
    var text = "";
    var ranges = [];
    var pos = 0;

    // Helper to add text with style
    function addText(str, styleName) {
        if (!str || str.length === 0) return;
        var start = pos;
        text += str + "\r";
        pos = text.length;
        ranges.push({start: start, end: pos - 1, style: styleName});
    }

    // Helper to add text without trailing return
    function addTextNoReturn(str, styleName) {
        if (!str || str.length === 0) return;
        var start = pos;
        text += str;
        pos = text.length;
        ranges.push({start: start, end: pos, style: styleName});
    }

    // Recipe Title
    addText(recipe.name, "title");

    // Meta info (source, author, times, servings)
    var metaParts = [];
    if (recipe.source) metaParts.push(recipe.source);
    if (recipe.author) metaParts.push("by " + recipe.author);
    if (metaParts.length > 0) {
        addText(metaParts.join(" | "), "meta");
    }

    var timeParts = [];
    if (recipe.prep_time) timeParts.push("Prep: " + recipe.prep_time);
    if (recipe.cook_time) timeParts.push("Cook: " + recipe.cook_time);
    if (recipe.total_time) timeParts.push("Total: " + recipe.total_time);
    if (recipe.servings) timeParts.push("Serves: " + recipe.servings);
    if (timeParts.length > 0) {
        addText(timeParts.join(" | "), "meta");
    }

    // Description
    if (recipe.description) {
        addText(recipe.description, "description");
    }

    // Ingredients
    addText("Ingredients", "sectionHeaderIngredients");

    // Use ingredient_groups if present, otherwise fall back to flat ingredients list
    if (recipe.ingredient_groups && hasOwnProperties(recipe.ingredient_groups)) {
        // Grouped ingredients - use these exclusively
        for (var groupName in recipe.ingredient_groups) {
            if (recipe.ingredient_groups.hasOwnProperty(groupName)) {
                addText(groupName, "ingredientGroup");
                var groupIngredients = recipe.ingredient_groups[groupName];
                for (var i = 0; i < groupIngredients.length; i++) {
                    addText("• " + groupIngredients[i], "ingredient");
                }
            }
        }
    } else if (recipe.ingredients && recipe.ingredients.length > 0) {
        // Flat ingredients list (only if no groups exist)
        for (var i = 0; i < recipe.ingredients.length; i++) {
            addText("• " + recipe.ingredients[i], "ingredient");
        }
    }

    // Instructions
    addText("Instructions", "sectionHeaderInstructions");
    if (recipe.instructions && recipe.instructions.length > 0) {
        for (var i = 0; i < recipe.instructions.length; i++) {
            addText((i + 1) + ". " + recipe.instructions[i], "instruction");
        }
    }

    // Notes
    if (recipe.notes && recipe.notes.length > 0) {
        addText("Notes", "sectionHeaderNotes");
        for (var i = 0; i < recipe.notes.length; i++) {
            addText("• " + recipe.notes[i], "note");
        }
    }

    // Nutrition (if present)
    if (recipe.nutrition && hasOwnProperties(recipe.nutrition)) {
        var nutritionParts = [];
        var nutritionFields = ["calories", "protein", "carbohydrates", "fat", "fiber", "sodium"];
        for (var i = 0; i < nutritionFields.length; i++) {
            var field = nutritionFields[i];
            if (recipe.nutrition[field]) {
                var label = field.charAt(0).toUpperCase() + field.slice(1);
                nutritionParts.push(label + ": " + recipe.nutrition[field]);
            }
        }
        if (nutritionParts.length > 0) {
            addText("Nutrition: " + nutritionParts.join(" | "), "nutrition");
        }
    }

    // Tags
    if (recipe.tags && recipe.tags.length > 0) {
        addText("Tags: " + recipe.tags.join(", "), "tags");
    }

    return {text: text, ranges: ranges};
}

function applyStylesToFrame(frame, ranges, styles) {
    var story = frame.parentStory;

    for (var i = 0; i < ranges.length; i++) {
        var range = ranges[i];
        var style = null;

        switch (range.style) {
            case "title": style = styles.title; break;
            case "meta": style = styles.meta; break;
            case "description": style = styles.description; break;
            case "sectionHeaderIngredients": style = styles.sectionHeaderIngredients; break;
            case "sectionHeaderInstructions": style = styles.sectionHeaderInstructions; break;
            case "sectionHeaderNotes": style = styles.sectionHeaderNotes; break;
            case "ingredientGroup": style = styles.ingredientGroup; break;
            case "ingredient": style = styles.ingredient; break;
            case "instruction": style = styles.instruction; break;
            case "note": style = styles.note; break;
            case "tags": style = styles.tags; break;
            case "nutrition": style = styles.nutrition; break;
        }

        if (style) {
            try {
                var textRange = story.characters.itemByRange(range.start, range.end);
                textRange.appliedParagraphStyle = style;
            } catch (e) {
                // Range might be invalid, skip
            }
        }
    }
}

function handleOverflow(doc, frame, textLayer) {
    // If text overflows, add linked frames on new pages
    var maxPages = 10; // Safety limit per recipe
    var pageCount = 0;

    while (frame.overflows && pageCount < maxPages) {
        // Add new page
        var newPage = doc.pages.add();
        var bounds = getTextFrameBounds(newPage);

        // Create new frame
        var newFrame = newPage.textFrames.add({
            geometricBounds: bounds,
            itemLayer: textLayer
        });

        // Link frames
        frame.nextTextFrame = newFrame;
        frame = newFrame;
        pageCount++;
    }
}

function cleanupEmptyPages(doc) {
    // Remove empty pages at the end (but keep at least one)
    for (var i = doc.pages.length - 1; i > 0; i--) {
        var page = doc.pages[i];
        if (page.textFrames.length === 0 && page.allPageItems.length === 0) {
            page.remove();
        } else {
            break;
        }
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// ExtendScript doesn't have Object.keys, so we need a helper
function hasOwnProperties(obj) {
    if (!obj) return false;
    for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
            return true;
        }
    }
    return false;
}

// ============================================================================
// JSON READING
// ============================================================================

function readJSONFile(file) {
    try {
        file.open("r");
        var content = file.read();
        file.close();

        // Parse JSON (ExtendScript doesn't have JSON.parse, so we use eval)
        // This is safe for our controlled recipe files
        var recipe = eval("(" + content + ")");
        return recipe;
    } catch (e) {
        alert("Error reading file: " + file.name + "\n" + e.message);
        return null;
    }
}
