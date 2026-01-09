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

try:
    import openai  # type: ignore
except ImportError:
    # openai is optional and only required for code generation
    openai = None  # type: ignore


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
            m = re.match(r'\s*"([^"]+)"\s*:\s*"([^"]*)"', line)
            if m:
                feature_name, description = m.groups()
                tasks.append({
                    'patch': patch_num,
                    'feature': feature_name.strip(),
                    'description': description.strip()
                })
    return tasks


def generate_code_for_task(task: Dict[str, object], model: str = 'gpt-4', temperature: float = 0.3) -> str:
    """
    Generate Python code for a given task using OpenAI's ChatCompletion API.

    This function constructs a prompt that describes the feature and its
    purpose, then sends it to the specified OpenAI model. The response
    content (assumed to be code) is returned as a string.

    Note: This requires the ``openai`` package and an API key set in the
    ``OPENAI_API_KEY`` environment variable. If the key is not set or the
    package is unavailable, a ``RuntimeError`` is raised.
    """
    if openai is None:
        raise RuntimeError("The openai package is not installed. Install it to generate code.")
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable not set.')
    openai.api_key = api_key
    prompt = (
        f"Generate Python code to implement the feature '{task['feature']}' "
        f"for the Pantheon of Oracles project. Description: {task['description']}. "
        "Provide only the code without explanations."
    )
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=temperature,
    )
    # Extract the generated code from the first choice
    return response.choices[0].message['content']


def generate_code_stub(task: Dict[str, object]) -> str:
    """
    Generate a minimal Python stub for a given task when OpenAI code generation is unavailable.

    This function sanitizes the feature name to create a valid Python function name, includes
    metadata about the patch and description, and returns a simple function definition
    with a TODO note. It avoids reliance on external services and ensures that every
    task produces at least a placeholder file in the generated_code directory.
    """
    patch = task.get('patch')
    feature = task.get('feature', '')
    description = str(task.get('description', '')).strip()
    import re as _re
    func_name = _re.sub(r'[^0-9a-zA-Z_]+', '_', str(feature).strip()).lower()
    stub_lines = [
        f"# Auto-generated stub for {feature}",
        f"# Patch: {patch}",
        f"# Description: {description}",
        "",
        f"def {func_name}():",
        f"    \"\"\"TODO: implement {feature}\"\"\"",
        f"    pass",
        "",
    ]
    return "\n".join(stub_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description='Extract tasks from Pantheon of Oracles patch document.')
    parser.add_argument('--patch_file', default=None,
                        help='Path to the patch document (default: search for a file starting with "Patches 1-50").')
    parser.add_argument('--output', default='tasks.json',
                        help='Output path for the generated tasks JSON file (default: tasks.json).')
    parser.add_argument('--generate-code', action='store_true',
                        help='If set, generate code scaffolds for each extracted task using the OpenAI API.')
    args = parser.parse_args()
    patch_file = args.patch_file or find_patch_file()
    tasks = parse_patches(patch_file)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f'Extracted {len(tasks)} tasks from {patch_file} and wrote them to {args.output}')

    # Optionally generate code for each task
    if args.generate_code:
        os.makedirs('generated_code', exist_ok=True)
        for task in tasks:
            # Create a safe filename based on patch and feature name
            feat_name = str(task['feature']).replace(' ', '_').replace('/', '_').replace(':', '_')
            file_name = f"patch{task['patch']}_{feat_name}.py"
            try:
                # Attempt to generate code using OpenAI if available
                code = generate_code_for_task(task)
            except Exception as e:
                # Fall back to a simple stub if code generation fails
                print(f"Failed to generate code for {task['feature']}: {e}, generating stub instead.")
                code = generate_code_stub(task)
            # Write the generated or stub code to the appropriate file
            with open(os.path.join('generated_code', file_name), 'w', encoding='utf-8') as cf:
                cf.write(code)
            print(f"Generated code for patch {task['patch']} feature '{task['feature']}' -> {file_name}")


if __name__ == '__main__':
    main()