"""
Utility helpers for loading Pantheon GPT patch files.

The patch files are text documents that contain repeated blocks:

Patch 26

{ ...json payload... }

The functions here parse those blocks into Python dictionaries, preserving
metadata like the patch number and source file. The parser is resilient to
non-JSON headers that precede the first patch entry and will skip any blocks
that fail JSON decoding.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Default patch files shipped in the repository
DEFAULT_PATCH_FILES: Tuple[str, ...] = (
    "Patches 1-25 – Pantheon of Oracles GPT.JSON",
    "Patches 26-41 – Pantheon of Oracles GPT.JSON",
)

PATCH_HEADER_RE = re.compile(r"^Patch\s+(\d+)")


def _iter_patch_blocks(text: str) -> Iterable[Tuple[int, str]]:
    """Yield ``(patch_number, json_block)`` pairs from raw patch text."""
    current_number: Optional[int] = None
    buffer: List[str] = []

    def flush() -> Optional[Tuple[int, str]]:
        nonlocal buffer, current_number
        if current_number is None:
            return None
        block = "\n".join(buffer).strip()
        buffer = []
        num = current_number
        current_number = None
        if block:
            return num, block
        return None

    for line in text.splitlines():
        match = PATCH_HEADER_RE.match(line.strip())
        if match:
            flushed = flush()
            if flushed:
                yield flushed
            current_number = int(match.group(1))
            buffer = []
            continue
        if current_number is not None:
            buffer.append(line)
    flushed = flush()
    if flushed:
        yield flushed


def parse_patch_file(path: Path) -> List[Dict[str, Any]]:
    """
    Parse a patch file and return a list of patch dictionaries.

    Each dictionary includes metadata ``patch_number`` and ``source_file`` in
    addition to the decoded JSON payload. Blocks that cannot be decoded are
    skipped to keep the response usable. If a patch payload contains a
    top-level ``patches`` list, each entry is expanded into its own patch while
    inheriting shared metadata from the container.
    """
    content = path.read_text(encoding="utf-8")
    patches: List[Dict[str, Any]] = []
    for patch_number, raw_json in _iter_patch_blocks(content):
        parsed_objects = _decode_patch_payload(raw_json)
        patches.extend(
            _expand_patch_entries(parsed_objects, patch_number, path.name)
        )
    return patches


def _decode_patch_payload(raw_json: str) -> List[Dict[str, Any]]:
    """
    Decode a patch payload, falling back to tolerant parsing when needed.

    Some shipped patch files contain truncated JSON blocks (e.g., unfinished
    lists) or stray characters before the next ``Patch`` header. We attempt a
    normal ``json.loads`` first, then scan for the best balanced JSON object
    inside the block using ``raw_decode`` to recover usable content.
    """

    try:
        return [json.loads(raw_json)]
    except JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    candidates: List[Tuple[Dict[str, Any], int]] = []

    for idx, ch in enumerate(raw_json):
        if ch != "{":
            continue
        try:
            obj, end = decoder.raw_decode(raw_json, idx)
        except JSONDecodeError:
            continue
        candidates.append((obj, end - idx))

    if not candidates:
        return []

    def score(item: Tuple[Dict[str, Any], int]) -> Tuple[int, int, int]:
        obj, span = item
        return (
            1 if ("patch_name" in obj or "patches" in obj) else 0,
            1 if "description" in obj else 0,
            span,
        )

    best_obj = max(candidates, key=score)[0]
    return [best_obj]


def _expand_patch_entries(
    parsed_objects: List[Dict[str, Any]],
    patch_number: int,
    source_file: str,
) -> List[Dict[str, Any]]:
    """Expand a decoded payload into one or more patch entries.

    Some payloads wrap multiple entries under a ``patches`` list. Each entry is
    expanded into its own patch dictionary while inheriting shared metadata from
    the parent payload. If no list is present, the payload is returned as a
    single entry.
    """

    expanded: List[Dict[str, Any]] = []
    for obj in parsed_objects:
        if not isinstance(obj, dict):
            continue

        shared = {k: v for k, v in obj.items() if k != "patches"}
        entries = obj.get("patches") if isinstance(obj.get("patches"), list) else None

        if entries:
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                combined: Dict[str, Any] = {**shared, **entry}
                combined.setdefault("patch_number", patch_number)
                combined.setdefault("source_file", source_file)
                expanded.append(combined)
        else:
            copy = dict(obj)
            copy["patch_number"] = patch_number
            copy["source_file"] = source_file
            expanded.append(copy)

    return expanded


def discover_patch_paths() -> List[Path]:
    """
    Return patch file paths from ``PATCH_FILE_PATHS`` env or defaults that exist.
    """
    env_paths = os.getenv("PATCH_FILE_PATHS")
    if env_paths:
        return [Path(p).expanduser() for p in env_paths.split(":") if p.strip()]
    return [Path(p) for p in DEFAULT_PATCH_FILES if Path(p).exists()]


def load_all_patches() -> List[Dict[str, Any]]:
    """Load and aggregate patch dictionaries from all discovered files."""
    patches: List[Dict[str, Any]] = []
    for path in discover_patch_paths():
        if path.exists():
            patches.extend(parse_patch_file(path))
    return patches


def summarize_patches(patches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return lightweight summaries suitable for listings."""
    return [
        {
            "patch_number": enriched.get("patch_number"),
            "patch_name": enriched.get("patch_name"),
            "version": enriched.get("version"),
            "date_created": enriched.get("date_created"),
            "description": enriched.get("description"),
            "source_file": enriched.get("source_file"),
        }
        for enriched in enrich_patches(patches)
    ]


def enrich_patches(patches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return fully annotated patch payloads sorted by number."""

    sorted_patches = sorted(patches, key=lambda p: p.get("patch_number", 0))
    return [fill_patch_metadata(patch) for patch in sorted_patches]


def summarize_sources(patches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summaries grouped by source file with counts and patch ranges."""

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for patch in patches:
        grouped[patch.get("source_file") or "unknown"].append(patch)

    summaries: List[Dict[str, Any]] = []
    for source, items in grouped.items():
        numbers = [p.get("patch_number") for p in items if isinstance(p.get("patch_number"), int)]
        summaries.append(
            {
                "source_file": source,
                "count": len(items),
                "min_patch": min(numbers) if numbers else None,
                "max_patch": max(numbers) if numbers else None,
            }
        )

    return sorted(summaries, key=lambda s: s["source_file"])


def filter_patches(
    patches: List[Dict[str, Any]],
    query: Optional[str] = None,
    min_patch: Optional[int] = None,
    max_patch: Optional[int] = None,
    source_file: Optional[str] = None,
    applies_to: Optional[str] = None,
    system_tag: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return patches filtered by number range, source, metadata, and fuzzy query."""

    def matches(patch: Dict[str, Any]) -> bool:
        number = patch.get("patch_number")
        if min_patch is not None and (number is None or number < min_patch):
            return False
        if max_patch is not None and (number is None or number > max_patch):
            return False
        if source_file and patch.get("source_file") != source_file:
            return False
        if status:
            patch_status = patch.get("status")
            if not isinstance(patch_status, str) or patch_status.lower() != status.lower():
                return False
        if applies_to:
            applies_field = patch.get("applies_to")
            applies_list = (
                [applies_field]
                if isinstance(applies_field, str)
                else [entry for entry in applies_field if isinstance(entry, str)]
                if isinstance(applies_field, list)
                else []
            )
            if not any(applies_to.lower() in entry.lower() for entry in applies_list):
                return False
        if system_tag:
            tags_field = patch.get("system_tags")
            tags = (
                [tags_field]
                if isinstance(tags_field, str)
                else [tag for tag in tags_field if isinstance(tag, str)]
                if isinstance(tags_field, list)
                else []
            )
            if not any(tag.lower() == system_tag.lower() for tag in tags):
                return False
        if query:
            text = json.dumps(patch, ensure_ascii=False).lower()
            if query.lower() not in text:
                return False
        return True

    return [patch for patch in patches if matches(patch)]


def latest_patch(patches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the highest-numbered patch, if available."""
    if not patches:
        return None
    return max(patches, key=lambda p: p.get("patch_number", 0))


PRIMARY_SKIP_KEYS = {
    "patch_number",
    "source_file",
    "patch_name",
    "name",
    "version",
    "date_created",
    "description",
    "notes",
    "applies_to",
    "implemented_by",
    "status",
    "patches",
}


def _primary_content_key(patch: Dict[str, Any]) -> Optional[str]:
    """Return the first likely content key for a patch payload."""

    for key in patch:
        if key not in PRIMARY_SKIP_KEYS and not key.startswith("_"):
            return key
    return None


def fill_patch_metadata(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of the patch with inferred metadata populated."""

    filled = dict(patch)
    patch_name = filled.get("patch_name") or filled.get("name")
    if not patch_name:
        primary_key = _primary_content_key(filled)
        if primary_key:
            patch_name = primary_key
            filled.setdefault("patch_name", patch_name)

    description = filled.get("description")
    if not description and patch_name and isinstance(filled.get(patch_name), dict):
        nested = filled[patch_name].get("description")
        if isinstance(nested, str):
            description = nested
            filled.setdefault("description", description)

    return filled
