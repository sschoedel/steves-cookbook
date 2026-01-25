#!/usr/bin/env python3
"""Batch OCR: Process all images in a directory using Mistral OCR.

Usage:
    uv run ocr_batch.py /path/to/images/
    uv run ocr_batch.py /path/to/images/ --workers 8

Output:
    ocr_results/ - One .txt file per image with extracted text
"""

import argparse
import base64
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

from mistralai import Mistral

SUPPORTED_EXTENSIONS = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".gif", ".webp"}

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

# Thread-safe print lock
print_lock = Lock()


def convert_heic_to_jpg(heic_path: Path) -> Path:
    """Convert HEIC to JPG using macOS sips command. Returns temp file path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    output_path = Path(tmp.name)

    subprocess.run(
        ["sips", "-s", "format", "jpeg", str(heic_path), "--out", str(output_path)],
        check=True,
        capture_output=True,
    )
    return output_path


def ocr_image(image_path: Path, client: Mistral) -> str:
    """Extract text from an image using Mistral OCR."""
    # Build base64 data URL
    image_data = base64.b64encode(image_path.read_bytes()).decode()
    mime_type = MIME_TYPES.get(image_path.suffix.lower(), "image/jpeg")
    data_url = f"data:{mime_type};base64,{image_data}"

    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "image_url", "image_url": data_url},
    )

    return "\n\n".join(page.markdown for page in response.pages if page.markdown)


def find_images(directory: Path) -> list[Path]:
    """Find all supported image files in directory."""
    images = []
    for ext in SUPPORTED_EXTENSIONS:
        images.extend(directory.glob(f"*{ext}"))
        images.extend(directory.glob(f"*{ext.upper()}"))
    return sorted(images, key=lambda p: p.name.lower())


def process_single_image(
    image_path: Path,
    output_dir: Path,
    client: Mistral,
    skip_existing: bool,
) -> tuple[str, str, str | None]:
    """Process a single image. Returns (filename, status, error_msg)."""
    output_file = output_dir / f"{image_path.stem}.txt"

    # Skip if already processed
    if skip_existing and output_file.exists():
        return (image_path.name, "skipped", None)

    try:
        # Convert HEIC if needed
        if image_path.suffix.lower() in (".heic", ".heif"):
            temp_jpg = convert_heic_to_jpg(image_path)
            try:
                text = ocr_image(temp_jpg, client)
            finally:
                temp_jpg.unlink(missing_ok=True)
        else:
            text = ocr_image(image_path, client)

        # Save result
        output_file.write_text(text)
        return (image_path.name, "success", None)

    except Exception as e:
        return (image_path.name, "error", str(e))


def main():
    parser = argparse.ArgumentParser(
        description="Batch OCR: Process all images in a directory using Mistral OCR."
    )
    parser.add_argument(
        "image_dir",
        type=Path,
        help="Directory containing images to OCR",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for OCR results (default: ./ocr_results)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip images that already have OCR output files",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )
    args = parser.parse_args()

    # Validate input directory
    if not args.image_dir.exists():
        parser.error(f"Directory not found: {args.image_dir}")
    if not args.image_dir.is_dir():
        parser.error(f"Not a directory: {args.image_dir}")

    # Setup output directory
    output_dir = args.output_dir or Path(__file__).parent / "ocr_results"
    output_dir.mkdir(exist_ok=True)

    # Check API key
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print(
            "Error: MISTRAL_API_KEY environment variable not set.\n"
            "Get your API key from https://console.mistral.ai/",
            file=sys.stderr,
        )
        sys.exit(1)

    # Find all images
    images = find_images(args.image_dir)
    if not images:
        print(f"No supported images found in {args.image_dir}")
        print(f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        sys.exit(0)

    print(f"Found {len(images)} images in {args.image_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Workers: {args.workers}")
    print()

    # Initialize client once (thread-safe for I/O operations)
    client = Mistral(api_key=api_key)

    # Process images in parallel
    success_count = 0
    skip_count = 0
    error_count = 0
    completed = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_single_image, img, output_dir, client, args.skip_existing
            ): img
            for img in images
        }

        # Process results as they complete
        for future in as_completed(futures):
            completed += 1
            filename, status, error_msg = future.result()

            with print_lock:
                if status == "skipped":
                    print(f"[{completed}/{len(images)}] {filename} - skipped (exists)")
                    skip_count += 1
                elif status == "success":
                    print(f"[{completed}/{len(images)}] {filename} - done")
                    success_count += 1
                else:
                    print(f"[{completed}/{len(images)}] {filename} - ERROR: {error_msg}")
                    error_count += 1

    # Summary
    print()
    print("=" * 50)
    print(f"Complete! Processed {success_count} images.")
    if skip_count:
        print(f"  Skipped: {skip_count} (already existed)")
    if error_count:
        print(f"  Errors: {error_count}")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
