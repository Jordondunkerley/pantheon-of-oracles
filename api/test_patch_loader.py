"""Unit tests for patch loader helpers."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from api import patch_loader


def test_filter_patches_by_query_and_range():
    patches = [
        {"patch_number": 1, "patch_name": "Alpha", "source_file": "a.json"},
        {"patch_number": 2, "patch_name": "Beta", "source_file": "b.json"},
        {"patch_number": 3, "patch_name": "Gamma", "source_file": "a.json"},
    ]

    results = patch_loader.filter_patches(
        patches, query="beta", min_patch=2, max_patch=3, source_file="b.json"
    )

    assert len(results) == 1
    assert results[0]["patch_number"] == 2


def test_filter_patches_by_metadata_fields():
    patches = [
        {
            "patch_number": 10,
            "patch_name": "Applies",
            "applies_to": ["Oracle Chamber System"],
            "system_tags": ["visualstacking", "oraclechamber"],
            "status": "Live",
        },
        {
            "patch_number": 11,
            "patch_name": "Other",
            "applies_to": "Different System",
            "system_tags": ["backend"],
            "status": "Draft",
        },
    ]

    results = patch_loader.filter_patches(
        patches,
        applies_to="chamber",
        system_tag="OracleChamber",
        status="live",
    )

    assert [p["patch_number"] for p in results] == [10]


def test_latest_patch_prefers_highest_number():
    patches = [
        {"patch_number": 5},
        {"patch_number": 2},
        {"patch_number": 10},
    ]

    assert patch_loader.latest_patch(patches)["patch_number"] == 10


def test_parse_patch_file_skips_invalid_blocks(tmp_path):
    contents = """
Intro text that should be ignored
Patch 1
{"name": "Alpha"}
Patch 2
not-json
Patch 3
{"name": "Gamma"}
"""
    patch_file = tmp_path / "patches.txt"
    patch_file.write_text(contents)

    patches = patch_loader.parse_patch_file(patch_file)

    assert len(patches) == 2
    numbers = sorted(p["patch_number"] for p in patches)
    assert numbers == [1, 3]
    assert all(p["source_file"] == patch_file.name for p in patches)


def test_summarize_sources_groups_by_file():
    patches = [
        {"patch_number": 1, "source_file": "a.json"},
        {"patch_number": 2, "source_file": "a.json"},
        {"patch_number": 4, "source_file": "b.json"},
    ]

    summaries = patch_loader.summarize_sources(patches)

    assert summaries == [
        {"source_file": "a.json", "count": 2, "min_patch": 1, "max_patch": 2},
        {"source_file": "b.json", "count": 1, "min_patch": 4, "max_patch": 4},
    ]


def test_parse_patch_file_recovers_truncated_json(tmp_path):
    contents = """
Patch 19

{
  "patches": [
    {
      "patch_name": "Patch 19 – Throne Worlds & Sovereign Systems Expansion",
      "description": "Example description",
      "systems": {
        "throne_worlds": {
          "enabled": true
        }
      }
    },
    {
"""

    patch_file = tmp_path / "patches.txt"
    patch_file.write_text(contents)

    patches = patch_loader.parse_patch_file(patch_file)

    assert len(patches) == 1
    patch = patches[0]
    assert patch["patch_number"] == 19
    assert patch["patch_name"].startswith("Patch 19")
    assert patch["source_file"] == patch_file.name


def test_summarize_patches_inferrs_primary_block_details():
    patch = {
        "NexusGPT": {"description": "Core multiplayer nexus"},
        "source_file": "example.json",
        "patch_number": 1,
    }

    summaries = patch_loader.summarize_patches([patch])

    assert summaries[0]["patch_name"] == "NexusGPT"
    assert summaries[0]["description"] == "Core multiplayer nexus"


def test_enrich_patches_sorts_and_fills_metadata():
    patches = [
        {"patch_number": 2, "Beta": {"description": "beta"}},
        {"patch_number": 1, "Alpha": {"description": "alpha"}},
    ]

    enriched = patch_loader.enrich_patches(patches)

    assert [p["patch_number"] for p in enriched] == [1, 2]
    assert enriched[0]["patch_name"] == "Alpha"
    assert enriched[0]["description"] == "alpha"


def test_parse_patch_file_expands_nested_patches(tmp_path):
    contents = """
Patch 5

{
  "version": "5.0",
  "patches": [
    {"patch_name": "Alpha", "description": "Alpha desc"},
    {"patch_name": "Beta", "version": "5.1"}
  ]
}
"""

    patch_file = tmp_path / "patches.txt"
    patch_file.write_text(contents)

    patches = patch_loader.parse_patch_file(patch_file)

    assert len(patches) == 2
    assert {p["patch_name"] for p in patches} == {"Alpha", "Beta"}
    assert all(p["patch_number"] == 5 for p in patches)
    assert all(p["source_file"] == patch_file.name for p in patches)
    versions = {p["patch_name"]: p.get("version") for p in patches}
    assert versions["Alpha"] == "5.0"
    assert versions["Beta"] == "5.1"
