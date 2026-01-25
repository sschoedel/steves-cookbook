#!/usr/bin/env python3
"""OCR a single image using Mistral OCR and save the extracted text."""

import argparse
import base64
import os
import subprocess
import tempfile
from pathlib import Path

from mistralai import Mistral

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def convert_heic_to_jpg(heic_path: Path, output_path: Path | None = None) -> Path:
    """Convert HEIC to JPG using macOS sips command."""
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()
        output_path = Path(tmp.name)

    subprocess.run(
        ["sips", "-s", "format", "jpeg", str(heic_path), "--out", str(output_path)],
        check=True,
        capture_output=True,
    )
    return output_path


def ocr_image(image_path: Path) -> str:
    """Extract text from an image using Mistral OCR."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MISTRAL_API_KEY environment variable not set.\n"
            "Get your API key from https://console.mistral.ai/"
        )

    # Build base64 data URL
    image_data = base64.b64encode(image_path.read_bytes()).decode()
    mime_type = MIME_TYPES.get(image_path.suffix.lower(), "image/jpeg")
    data_url = f"data:{mime_type};base64,{image_data}"

    # Call Mistral OCR
    client = Mistral(api_key=api_key)
    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "image_url", "image_url": data_url},
    )

    return "\n\n".join(page.markdown for page in response.pages if page.markdown)


def main():
    parser = argparse.ArgumentParser(description="OCR an image using Mistral OCR.")
    parser.add_argument("image_path", type=Path, help="Path to the image file")
    parser.add_argument(
        "--save-intermediate-jpg",
        action="store_true",
        help="Save converted JPG (for HEIC files) to ocr_results/",
    )
    args = parser.parse_args()

    if not args.image_path.exists():
        parser.error(f"File not found: {args.image_path}")

    output_dir = Path(__file__).parent / "ocr_results"
    output_dir.mkdir(exist_ok=True)

    # Convert HEIC if needed
    image_path = args.image_path
    if image_path.suffix.lower() in (".heic", ".heif"):
        jpg_output = output_dir / f"{image_path.stem}.jpg" if args.save_intermediate_jpg else None
        image_path = convert_heic_to_jpg(image_path, jpg_output)
        if args.save_intermediate_jpg:
            print(f"Converted HEIC to: {image_path}")

    # OCR and save
    text = ocr_image(image_path)
    print(text)

    output_file = output_dir / f"{args.image_path.stem}.txt"
    output_file.write_text(text)
    print(f"\n--- Saved to: {output_file} ---")


if __name__ == "__main__":
    main()
