# Steve's Cookbook

A project to digitize and organize Steve's recipe collection.

## Overview

This repository contains tools and resources for creating a personalized cookbook from a collection of recipes. The initial focus is on digitizing paper recipes using OCR (Optical Character Recognition).

## Setup

### Prerequisites

- Python 3.9+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Install via Homebrew:
  ```bash
  brew install tesseract
  ```

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd steves-cookbook

# Install dependencies with uv
uv sync
```

## Usage

### OCR a single recipe image

```bash
uv run python ocr_test.py /path/to/recipe_image.jpg
```

This will:
- Extract text from the image using Tesseract
- Print the extracted text to the terminal
- Save the text to `ocr_results/<image_name>.txt`

## Project Structure

```
steves-cookbook/
├── ocr_test.py        # Single-image OCR script
├── ocr_results/       # Output directory for extracted text
├── pyproject.toml     # Project dependencies
└── README.md
```
