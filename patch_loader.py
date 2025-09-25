"""Utilities for loading Pantheon of Oracles patch instruction files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import json
import logging
import re

logger = logging.getLogger(__name__)


class PatchNotFoundError(KeyError):
    """Raised when a patch identifier cannot be resolved."""


@dataclass(slots=True)
class PatchSection:
    number: int
    source_file: Path
    raw_text: str
    patch_name: Optional[str] = None
    version: Optional[str] = None
    parsed: Optional[dict] = None
    parse_error: Optional[str] = None

    def summary(self) -> dict:
        return {
            "number": self.number,
            "patch_name": self.patch_name,
            "version": self.version,
            "source_file": str(self.source_file.name),
            "has_structured_data": self.parsed is not None,
            "parse_error": self.parse_error,
        }

    def as_dict(self) -> dict:
        return {
            **self.summary(),
            "raw_text": self.raw_text,
            "parsed": self.parsed,
        }

    @property
    def identifier(self) -> str:
        return f"Patch {self.number}"

    @property
    def slug(self) -> str:
        if self.patch_name:
            cleaned = re.sub(r"[^a-z0-9]+", "-", self.patch_name.lower())
            cleaned = cleaned.strip("-")
            if cleaned:
                return cleaned
        return f"patch-{self.number}"


@dataclass
class PatchRegistry:
    sections: List[PatchSection] = field(default_factory=list)
    _by_number: Dict[int, PatchSection] = field(init=False, default_factory=dict)
    _by_slug: Dict[str, PatchSection] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        for section in sorted(self.sections, key=lambda s: s.number):
            self._by_number[section.number] = section
            self._by_slug[section.slug] = section
            self._by_slug[f"patch-{section.number}"] = section

    def all(self) -> List[PatchSection]:
        return list(sorted(self.sections, key=lambda s: s.number))

    def summaries(self) -> List[dict]:
        return [section.summary() for section in self.all()]

    def resolve(self, identifier: str | int) -> PatchSection:
        if isinstance(identifier, int):
            try:
                return self._by_number[identifier]
            except KeyError as exc:
                raise PatchNotFoundError(identifier) from exc

        match = re.search(r"\d+", identifier)
        if match:
            number = int(match.group())
            if number in self._by_number:
                return self._by_number[number]

        slug = re.sub(r"[^a-z0-9]+", "-", identifier.lower()).strip("-")
        if slug in self._by_slug:
            return self._by_slug[slug]

        raise PatchNotFoundError(identifier)


def _extract_patch_name(text: str) -> Optional[str]:
    match = re.search(r'"patch_name"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return None


def _extract_version(text: str) -> Optional[str]:
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return None


def _attempt_parse(text: str) -> tuple[Optional[dict], Optional[str]]:
    candidate = text.strip()
    if not candidate:
        return None, "empty patch section"

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None, "no JSON object detected"

    snippet = candidate[start : end + 1]
    try:
        parsed = json.loads(snippet)
        return parsed, None
    except json.JSONDecodeError as exc:
        return None, f"json decode error: {exc}"


def _load_patch_sections_from_file(path: Path) -> Iterable[PatchSection]:
    sections: List[PatchSection] = []
    current_number: Optional[int] = None
    buffer: List[str] = []

    pattern = re.compile(r"^Patch\s+(\d+)$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        match = pattern.fullmatch(line)
        if match:
            if current_number is not None:
                raw_text = "\n".join(buffer).strip("\n")
                sections.append(_build_section(current_number, path, raw_text))
            current_number = int(match.group(1))
            buffer = []
        else:
            if current_number is not None:
                buffer.append(raw_line)
    if current_number is not None:
        raw_text = "\n".join(buffer).strip("\n")
        sections.append(_build_section(current_number, path, raw_text))
    return sections


def _build_section(number: int, path: Path, raw_text: str) -> PatchSection:
    patch_name = _extract_patch_name(raw_text)
    version = _extract_version(raw_text)
    parsed, error = _attempt_parse(raw_text)
    if error:
        logger.debug("Failed to parse patch %s from %s: %s", number, path.name, error)
    return PatchSection(
        number=number,
        source_file=path,
        raw_text=raw_text,
        patch_name=patch_name,
        version=version,
        parsed=parsed,
        parse_error=error,
    )


def load_default_registry() -> PatchRegistry:
    base_path = Path(__file__).resolve().parent
    patch_files = sorted(base_path.glob("Patches*JSON"))
    sections: List[PatchSection] = []
    for patch_file in patch_files:
        sections.extend(_load_patch_sections_from_file(patch_file))
    return PatchRegistry(sections)


patch_registry = load_default_registry()

__all__ = [
    "PatchRegistry",
    "PatchSection",
    "PatchNotFoundError",
    "load_default_registry",
    "patch_registry",
]
