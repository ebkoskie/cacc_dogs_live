"""Local OCR test harness for pavilion walk sheets.

Sends a photo of a CACC walk sheet to Gemini Vision and prints the extracted
pavilion + kennel->name mapping. This is a developer tool for checking OCR
quality and tuning the prompt; it is NOT part of the build (the production OCR
runs in the serverless worker). Kept deliberately minimal — location only, no
walk telemetry.

Usage:
    GEMINI_API_KEY=... uv run --with google-genai \\
        python scripts/process_pavilion_sheet.py path/to/sheet.jpg [--names dogs_active.csv]

`--names` (optional) points at a CSV with a "Name" column; the active names are
fed to the model as reference context so it snaps handwriting to real dogs.
"""

import argparse
import json
import os
import sys

MODEL = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

SYSTEM_INSTRUCTION = (
    "You are an OCR system for animal-shelter walk sheets. Read the photo of a "
    "CACC dog walking sheet and return ONLY JSON matching the schema. "
    "Identify the pavilion letter (A, B, C, or D), usually printed at the top. "
    "For each kennel row, read the printed kennel number and the handwritten dog "
    "name. Ignore crossed-out names when a replacement is written. If you are "
    "given a reference list of current dog names, snap each handwritten name to "
    "the closest real name from that list. Skip rows with no legible name."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "pavilion": {"type": "string", "description": "Pavilion letter A, B, C, or D"},
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kennel": {
                        "type": "string",
                        "description": "Printed kennel number",
                    },
                    "name": {"type": "string", "description": "Handwritten dog name"},
                },
                "required": ["kennel", "name"],
            },
        },
    },
    "required": ["pavilion", "entries"],
}


def _load_reference_names(path):
    import csv

    names = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                n = (row.get("Name") or "").strip()
                if n and n.lower() != "unknown":
                    names.append(n)
    except (FileNotFoundError, OSError) as e:
        print(f"  (could not read names from {path}: {e})", file=sys.stderr)
    return names


def main():
    ap = argparse.ArgumentParser(description="OCR a pavilion walk sheet via Gemini.")
    ap.add_argument("image", help="Path to the sheet photo (jpg/png).")
    ap.add_argument(
        "--names", help="Optional CSV with a 'Name' column for reference context."
    )
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Set GEMINI_API_KEY in the environment.")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit(
            "google-genai not installed. Try: uv run --with google-genai python scripts/process_pavilion_sheet.py ..."
        )

    if not os.path.isfile(args.image):
        sys.exit(f"Error: '{args.image}' not found or is not a regular file.")
    with open(args.image, "rb") as f:
        image_bytes = f.read()
    mime = "image/png" if args.image.lower().endswith(".png") else "image/jpeg"

    prompt = "Extract the pavilion and kennel->name mappings from this walk sheet."
    if args.names:
        names = _load_reference_names(args.names)
        if names:
            prompt += "\n\nCurrent dog names for reference:\n" + ", ".join(
                sorted(set(names))
            )

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime), prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )
    except Exception as e:
        sys.exit(f"Gemini API call failed: {e}")

    if not getattr(response, "text", None):
        sys.exit(
            "Gemini returned no text (the response may have been blocked by safety filters)."
        )
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as e:
        sys.exit(
            f"Could not parse the model response as JSON: {e}\nRaw: {response.text[:500]}"
        )
    kennels = {
        e["kennel"]: e["name"]
        for e in data.get("entries", [])
        if e.get("kennel") and e.get("name")
    }
    out = {"pavilion": data.get("pavilion"), "kennels": kennels}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(
        f"\n{len(kennels)} kennel rows read for pavilion {out['pavilion']}.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
