#!/usr/bin/env python3
"""OCR a single image and save the extracted text."""

import sys
from pathlib import Path

import pytesseract
from PIL import Image


def ocr_image(image_path: Path) -> str:
    """Extract text from an image using Tesseract OCR."""
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text


def main():
    if len(sys.argv) != 2:
        print("Usage: python ocr_test.py <image_path>")
        sys.exit(1)

    image_path = Path(sys.argv[1])

    if not image_path.exists():
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    # Extract text
    text = ocr_image(image_path)

    # Print to stdout
    print(text)

    # Save to ocr_results/
    output_dir = Path(__file__).parent / "ocr_results"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{image_path.stem}.txt"
    output_file.write_text(text)

    print(f"\n--- Saved to: {output_file} ---")


if __name__ == "__main__":
    main()
