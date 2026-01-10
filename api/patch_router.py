"""
FastAPI router exposing Pantheon GPT patch data.

This allows the GPT-side agent to introspect patch metadata and pull the
full payloads one patch at a time so it can keep building autonomously.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional

from .patch_loader import (
    enrich_patches,
    fill_patch_metadata,
    filter_patches,
    latest_patch,
    load_all_patches,
    summarize_sources,
    summarize_patches,
)

router = APIRouter(prefix="/gpt/patches", tags=["GPT Patches"])


@router.get("")
def list_patches() -> Dict[str, Any]:
    patches = load_all_patches()
    return {"ok": True, "patches": summarize_patches(patches)}


@router.get("/sources")
def list_sources() -> Dict[str, Any]:
    patches = load_all_patches()
    return {"ok": True, "sources": summarize_sources(patches)}


@router.get("/latest")
def get_latest_patch() -> Dict[str, Any]:
    patches = load_all_patches()
    patch = latest_patch(patches)
    if patch:
        return {"ok": True, "patch": fill_patch_metadata(patch)}
    raise HTTPException(status_code=404, detail="No patches available")


@router.get("/search")
def search_patches(
    q: str = Query(..., description="Case-insensitive substring to search"),
    min_patch: Optional[int] = Query(None, description="Minimum patch number inclusive"),
    max_patch: Optional[int] = Query(None, description="Maximum patch number inclusive"),
    source_file: Optional[str] = Query(None, description="Filter by source file name"),
    applies_to: Optional[str] = Query(
        None, description="Substring to match against applies_to entries"
    ),
    system_tag: Optional[str] = Query(
        None, description="Case-insensitive tag match for system_tags entries"
    ),
    status: Optional[str] = Query(None, description="Case-insensitive status match"),
) -> Dict[str, Any]:
    patches = load_all_patches()
    results = filter_patches(
        patches,
        query=q,
        min_patch=min_patch,
        max_patch=max_patch,
        source_file=source_file,
        applies_to=applies_to,
        system_tag=system_tag,
        status=status,
    )
    return {"ok": True, "patches": summarize_patches(results)}


@router.get("/search/full")
def search_patches_full(
    q: str = Query(..., description="Case-insensitive substring to search"),
    min_patch: Optional[int] = Query(None, description="Minimum patch number inclusive"),
    max_patch: Optional[int] = Query(None, description="Maximum patch number inclusive"),
    source_file: Optional[str] = Query(None, description="Filter by source file name"),
    applies_to: Optional[str] = Query(
        None, description="Substring to match against applies_to entries"
    ),
    system_tag: Optional[str] = Query(
        None, description="Case-insensitive tag match for system_tags entries"
    ),
    status: Optional[str] = Query(None, description="Case-insensitive status match"),
) -> Dict[str, Any]:
    """Return full patch payloads for search results."""

    patches = load_all_patches()
    results = filter_patches(
        patches,
        query=q,
        min_patch=min_patch,
        max_patch=max_patch,
        source_file=source_file,
        applies_to=applies_to,
        system_tag=system_tag,
        status=status,
    )
    return {"ok": True, "patches": enrich_patches(results)}


@router.get("/{patch_number}")
def get_patch(patch_number: int) -> Dict[str, Any]:
    patches = load_all_patches()
    for patch in patches:
        if patch.get("patch_number") == patch_number:
            return {"ok": True, "patch": fill_patch_metadata(patch)}
    raise HTTPException(status_code=404, detail="Patch not found")
