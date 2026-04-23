#!/usr/bin/env python3
"""Build dist/index.html by injecting resume.json into the HTML template."""

import json
import os
import re
import sys
from datetime import datetime, timezone


def build(data_path: str = "data/resume.json", template_path: str = "src/template.html", output_path: str = "dist/index.html") -> None:
    if not os.path.isfile(data_path):
        print(f"Error: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(template_path):
        print(f"Error: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(data_path, "r") as f:
        resume_data = json.load(f)

    with open(template_path, "r") as f:
        template = f.read()

    # Build the injection block
    json_str = json.dumps(resume_data, indent=2)
    inject_block = (
        '<!-- RESUME_DATA_INJECT -->\n'
        '<script id="resume-data" type="application/json">\n'
        f'{json_str}\n'
        '</script>\n'
        '<!-- /RESUME_DATA_INJECT -->'
    )

    # Replace between markers
    pattern = r'<!-- RESUME_DATA_INJECT -->.*?<!-- /RESUME_DATA_INJECT -->'
    result = re.sub(pattern, inject_block, template, flags=re.DOTALL)

    # Add build timestamp comment at the top
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    build_comment = f"<!-- Built: {timestamp} from resume.json -->\n"
    result = build_comment + result

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(result)

    print(f"[{timestamp}] Successfully built {output_path}")


if __name__ == "__main__":
    build()
