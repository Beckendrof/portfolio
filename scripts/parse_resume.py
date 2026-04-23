#!/usr/bin/env python3
"""Parse resume.pdf using the Anthropic API and extract structured JSON."""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def parse_resume(resume_path: str, output_path: str) -> None:
    # Validate resume file exists
    if not os.path.isfile(resume_path):
        print(f"Error: Resume file not found: {resume_path}", file=sys.stderr)
        sys.exit(1)

    # Validate API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set in environment", file=sys.stderr)
        sys.exit(1)

    # Read and encode the PDF
    with open(resume_path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Call the Anthropic API
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    schema = """{
  "name": "string",
  "title": "string",
  "location": "string",
  "email": "string",
  "phone": "string",
  "github": "string (username only, no URL prefix)",
  "linkedin": "string (slug only, e.g. abhinav-parameshwaran)",
  "summary": "string",
  "experience": [
    {
      "title": "string",
      "company": "string",
      "location": "string",
      "start": "string",
      "end": "string (or Present)",
      "bullets": ["string"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "school": "string",
      "date": "string"
    }
  ],
  "skills": {
    "category_name": ["skill1", "skill2"]
  },
  "projects": [
    {
      "name": "string",
      "slug": "string (lowercase, hyphenated, for use as command argument)",
      "description": "string (2-3 sentences)",
      "tech": ["string"],
      "url": "string (full GitHub URL if present, else empty string)"
    }
  ]
}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"""Extract all information from this resume into the following JSON schema. Return ONLY valid JSON, no markdown fences or extra text.

{schema}

Important:
- For "github", extract just the username (e.g. "Beckendrof"), not the full URL.
- For "linkedin", extract just the slug (e.g. "abhinav-parameshwaran"), not the full URL.
- For project "slug", create a lowercase hyphenated version suitable for use as a CLI argument.
- For project "url", include the full GitHub URL if present in the resume, otherwise use an empty string.
- For "summary", write a 2-3 sentence professional summary based on the resume content.
- Preserve all bullet points from experience sections exactly as written.""",
                        },
                    ],
                }
            ],
        )
    except anthropic.APIError as e:
        print(f"Error: Anthropic API error: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse the response
    raw_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON from API response: {e}", file=sys.stderr)
        print(f"Raw response:\n{raw_text}", file=sys.stderr)
        sys.exit(1)

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{timestamp}] Successfully parsed resume -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse resume PDF to JSON")
    parser.add_argument("--resume", default="resume.pdf", help="Path to resume PDF")
    parser.add_argument(
        "--output", default="data/resume.json", help="Output JSON path"
    )
    args = parser.parse_args()
    parse_resume(args.resume, args.output)
