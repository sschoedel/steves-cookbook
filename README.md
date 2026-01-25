# Steve's Cookbook

A project to digitize and organize Steve's recipe collection.

## Overview

This repository contains tools for creating a personalized cookbook from a collection of recipes. The initial focus is on digitizing paper recipes using OCR (Optical Character Recognition) via Mistral AI.

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

## Usage

### OCR a single recipe image

```bash
uv run ocr_test.py /path/to/recipe_image.jpg
```

Supports HEIC files from iPhone (auto-converts to JPG):
```bash
uv run ocr_test.py IMG_1234.HEIC
```

To save the intermediate JPG conversion:
```bash
uv run ocr_test.py IMG_1234.HEIC --save-intermediate-jpg
```

Output is saved to `ocr_results/<image_name>.txt`

## Project Structure

```
steves-cookbook/
├── ocr_test.py        # Single-image OCR script
├── ocr_results/       # Output directory for extracted text
├── pyproject.toml     # Project dependencies
└── README.md
```
