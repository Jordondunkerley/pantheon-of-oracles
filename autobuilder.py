#!/usr/bin/env python3
"""
Autobuilder for the Pantheon of Oracles project.

This script reads the consolidated patch document (e.g.,
``Patches 1-50 – Pantheon of Oracles GPT.JSON``) and extracts
high‑level feature descriptions as individual tasks. It then writes
these tasks to a JSON file for further processing by build
orchestration tools.

The patch document is not valid JSON; it contains human‑readable
headings (e.g., "Patch 1") followed by JSON‑like definitions. This
parser relies on simple heuristics: it splits the file on "Patch N"
markers and then scans each section for lines that look like
``"feature_name": "Description"``. Nested objects and complex
structures are ignored—only top‑level key–value pairs with string
values are extracted. While this approach does not capture every
detail, it provides a large set of actionable tasks for an
autonomous builder to consume.
"""

import argparse
import json
import os
import re
from typing import List, Dict


def find_patch_file(default: str = 'Patches 1-50 – Pantheon of Oracles GPT.JSON') -> str:
    """Return a patch file path if the default exists, otherwise search for a similar name."""
    if os.path.exists(default):
        return default
    # search for a file starting with 'patches 1-50' (case-insensitive) and ending with .json
    for fname in os.listdir('.'):
        lower = fname.lower()
        if lower.startswith('patches 1-50') and lower.endswith('.json'):
            return fname
    raise FileNotFoundError('Could not find patch file')


def parse_patches(file_path: str) -> List[Dict[str, object]]:
    """Parse the patch document into a list of task dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Split text into sections using markers like "Patch 1", "Patch 2", ...
    # This regex captures the patch number for use in tasks.
    patch_regex = re.compile(r'Patch\s*(\d+)', re.IGNORECASE)
    sections = re.split(patch_regex, text)
    tasks: List[Dict[str, object]] = []
    # sections layout: [intro_text, patch1_num, patch1_content, patch2_num, patch2_content, ...]
    for i in range(1, len(sections), 2):
        patch_num_str = sections[i]
        content = sections[i + 1] if i + 1 < len(sections) else ''
        try:
            patch_num = int(patch_num_str.strip())
        except ValueError:
            # Skip if patch number isn't valid
            continue
        for line in content.splitlines():
            # Match lines that look like: "key": "value",
            m = re.match(r'\s*"([^\"]+)"\s*:\s*"([^\"]*)"', line)
            if m:
                feature_name, description = m.groups()
                tasks.append({
                    'patch': patch_num,
                    'feature': feature_name.strip(),
                    'description': description.strip()
                })
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description='Extract tasks from Pantheon of Oracles patch document.')
    parser.add_argument('--patch_file', default=None,
                        help='Path to the patch document (default: search for a file starting with "Patches 1-50").')
    parser.add_argument('--output', default='tasks.json',
                        help='Output path for the generated tasks JSON file (default: tasks.json).')
    args = parser.parse_args()
    patch_file = args.patch_file or find_patch_file()
    tasks = parse_patches(patch_file)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f'Extracted {len(tasks)} tasks from {patch_file} and wrote them to {args.output}')


if __name__ == '__main__':
    main()
