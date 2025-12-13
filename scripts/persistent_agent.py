"""Continuous background agent scaffolding for Pantheon of Oracles.

This module provides the first step toward a persistent, self-updating
Pantheon of Oracles agent. It is designed to run inside GitHub Actions on a
schedule, continuously hashing the backend patch files and recording whether
anything has changed. Future iterations can hook into ``apply_plan`` to
implement autonomous updates (for example, opening PRs based on new patch
instructions).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Patch files that describe the Pantheon of Oracles plan. We hash them on every
# run so the automation can react immediately when new guidance is added. The
# list can be extended through the PANTHEON_PATCH_FILES environment variable or
# the --patch flag when invoking the agent.
PATCH_FILENAMES: Tuple[str, ...] = (
    "Patches 1-25 – Pantheon of Oracles GPT.JSON",
    "Patches 26-41 – Pantheon of Oracles GPT.JSON",
)

# Simple semantic marker to stamp artifacts and status payloads with the agent
# revision. Update whenever the automation gains new capabilities so downstream
# consumers can reason about the data shape they receive.
AGENT_VERSION = "0.0.10"


DEFAULT_HISTORY_LIMIT = 20


def parse_env_patch_files(env_value: str | None) -> List[str]:
    """Return any patch files defined in the PANTHEON_PATCH_FILES env var."""

    if not env_value:
        return []

    files = []
    for entry in env_value.split(","):
        trimmed = entry.strip()
        if trimmed:
            files.append(trimmed)
    return files


def parse_log_level(value: str | None, default: int = logging.INFO) -> int:
    """Convert a string log level into a logging constant.

    Falls back to ``default`` when the input is empty or unrecognized. Values are
    case-insensitive and may be provided as either names (``info``, ``DEBUG``)
    or integers.
    """

    if not value:
        return default

    if value.isdigit():
        return int(value)

    level = logging.getLevelName(value.upper())
    if isinstance(level, int):
        return level

    logging.warning("Invalid log level %s; defaulting to %s", value, default)
    return default


def merge_patch_sources(
    defaults: Tuple[str, ...], env_files: List[str], cli_files: List[str]
) -> Tuple[List[str], Dict[str, str]]:
    """Combine patch file sources while preserving order and dropping duplicates.

    Returns both the merged list of patch files and a mapping of each patch to the
    source that introduced it (``default``, ``env``, or ``cli``) so reporting can
    surface how configuration was derived.
    """

    combined: List[str] = []
    origins: Dict[str, str] = {}

    def append_unique(name: str, source: str) -> None:
        if name in origins:
            return
        combined.append(name)
        origins[name] = source

    for name in defaults:
        append_unique(name, "default")
    for name in env_files:
        append_unique(name, "env")
    for name in cli_files:
        append_unique(name, "cli")

    return combined, origins


def parse_snapshot_retention(value: str | None) -> int | None:
    """Parse snapshot retention values from environment variables."""

    if value is None or value == "":
        return None

    try:
        parsed = int(value)
    except ValueError:
        logging.warning("Ignoring invalid snapshot retention value: %s", value)
        return None

    return parsed


def parse_history_limit(value: str | None, default: int | None = DEFAULT_HISTORY_LIMIT) -> int | None:
    """Parse a history limit value from environment strings."""

    if value is None or value == "":
        return default

    try:
        parsed = int(value)
    except ValueError:
        logging.warning("Ignoring invalid history limit value: %s", value)
        return default

    if parsed <= 0:
        return None

    return parsed


def resolve_patch_paths(base_dir: Path, patch_files: List[str]) -> Dict[str, Path]:
    """Resolve configured patch files relative to the provided base directory."""

    resolved: Dict[str, Path] = {}
    for name in patch_files:
        path = Path(name)
        resolved[name] = path if path.is_absolute() else base_dir / path
    return resolved


def gather_runtime_info() -> Dict[str, str]:
    """Capture lightweight runtime metadata for reporting and diagnostics."""

    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def gather_ci_metadata() -> Dict[str, str]:
    """Collect CI metadata (when available) for richer diagnostics."""

    keys = {
        "GITHUB_RUN_ID": "github_run_id",
        "GITHUB_RUN_NUMBER": "github_run_number",
        "GITHUB_WORKFLOW": "github_workflow",
        "GITHUB_JOB": "github_job",
        "GITHUB_REF": "github_ref",
        "GITHUB_SHA": "github_sha",
        "GITHUB_REPOSITORY": "github_repository",
    }

    metadata: Dict[str, str] = {}
    for env_key, meta_key in keys.items():
        value = os.getenv(env_key)
        if value:
            metadata[meta_key] = value
    return metadata

# Default location to store the digest of the last run so we can tell when the
# patch files change. Paths can be overridden via environment variables to make
# the agent configurable in CI without CLI arguments.
STATE_PATH = Path(os.getenv("PANTHEON_AGENT_STATE_PATH", "state/persistent_agent_state.json"))
# Directory where snapshots of changed patches will be persisted for auditing
# and follow-up processing by future automation steps.
SNAPSHOT_DIR = Path(os.getenv("PANTHEON_AGENT_SNAPSHOT_DIR", "state/patch_snapshots"))
# Human-readable and machine-readable reports that summarize the latest run and
# current digests for downstream automation.
REPORT_PATH = Path(os.getenv("PANTHEON_AGENT_REPORT_PATH", "state/persistent_agent_report.md"))
STATUS_JSON_PATH = Path(
    os.getenv("PANTHEON_AGENT_STATUS_PATH", "state/persistent_agent_status.json")
)
HEARTBEAT_PATH = Path(
    os.getenv("PANTHEON_AGENT_HEARTBEAT_PATH", "state/persistent_agent_heartbeat.txt")
)
LOG_PATH_ENV = os.getenv("PANTHEON_AGENT_LOG_PATH")
LOG_PATH = Path(LOG_PATH_ENV) if LOG_PATH_ENV else Path("state/persistent_agent.log")
DISABLE_LOG_FILE_ENV = os.getenv("PANTHEON_AGENT_DISABLE_LOG_FILE", "").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

# History retention can be tuned via environment variable or CLI flag. Defaults
# to keeping the latest 20 runs; set to 0 or a negative number for unlimited
# retention.
HISTORY_LIMIT_ENV = os.getenv("PANTHEON_AGENT_HISTORY_LIMIT")

# Snapshot behavior can be tuned via CLI flags or environment variables. Retention
# defaults to unlimited (``None``) but can be limited to the newest ``N``
# snapshots via ``PANTHEON_AGENT_SNAPSHOT_RETENTION``. Snapshots can also be
# disabled entirely with ``PANTHEON_AGENT_DISABLE_SNAPSHOTS`` or
# ``--disable-snapshots``.
SNAPSHOT_RETENTION_ENV = os.getenv("PANTHEON_AGENT_SNAPSHOT_RETENTION")
DISABLE_SNAPSHOTS_ENV = os.getenv("PANTHEON_AGENT_DISABLE_SNAPSHOTS", "").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

# The base directory used to resolve relative paths. Defaults to the current
# working directory but can be overridden via environment variable or CLI
# argument to support running the agent from alternate locations.
BASE_DIR = Path(os.getenv("PANTHEON_AGENT_BASE_DIR", Path.cwd()))


@dataclass
class RunRecord:
    """Represents a single execution of the agent."""

    timestamp: float
    changed_files: List[str]
    duration_seconds: float | None = None
    run_id: int | None = None
    missing_files: List[str] = field(default_factory=list)
    error: str | None = None
    change_details: Dict[str, Dict[str, str | None]] = field(default_factory=dict)
    change_summary: Dict[str, int] = field(default_factory=dict)


@dataclass
class RunResult:
    """Aggregate information from the most recent agent execution."""

    timestamp: float
    log_level: int
    log_level_name: str
    log_path: Path | None
    log_file_enabled: bool
    loop_enabled: bool
    loop_interval: int | None
    loop_backoff: int | None
    max_iterations: int | None
    digests: Dict[str, str]
    changed_files: List[str]
    snapshot_path: Path | None
    pruned_snapshots: List[Path]
    missing_files: List[str]
    change_details: Dict[str, Dict[str, str | None]]
    change_summary: Dict[str, int]
    history: List[RunRecord]
    run_duration: float | None
    run_id: int | None
    next_run_id: int | None
    tracked_files: List[str]
    resolved_patches: Dict[str, Path]
    patch_sources: Dict[str, str]
    base_dir: Path
    state_path: Path
    snapshot_dir: Path
    snapshot_retention: int | None
    snapshots_enabled: bool
    report_path: Path
    status_path: Path
    heartbeat_path: Path
    agent_version: str
    runtime_info: Dict[str, str]
    ci_metadata: Dict[str, str]
    history_limit: int | None


@dataclass
class AgentState:
    """Persisted digests and a small run history."""

    digests: Dict[str, str] = field(default_factory=dict)
    history: List[RunRecord] = field(default_factory=list)
    next_run_id: int = 1

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        if not path.exists():
            return cls()

        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)

        # Backward-compatibility: the initial version stored a flat mapping of
        # digests; migrate it forward automatically.
        if isinstance(data, dict) and "digests" not in data:
            return cls(digests=data)

        raw_history = data.get("history", [])
        history: List[RunRecord] = []
        for index, entry in enumerate(raw_history, start=1):
            history.append(
                RunRecord(
                    timestamp=entry.get("timestamp", 0.0),
                    changed_files=entry.get("changed_files", []),
                    duration_seconds=entry.get("duration_seconds"),
                    run_id=entry.get("run_id") or entry.get("id"),
                    missing_files=entry.get("missing_files", []),
                    error=entry.get("error"),
                    change_details=entry.get("change_details", {}),
                    change_summary=entry.get("change_summary", {}),
                )
            )

        max_run_id = 0
        for index, record in enumerate(history, start=1):
            if record.run_id is None or record.run_id <= 0:
                record.run_id = index
            max_run_id = max(max_run_id, record.run_id)

        next_run_id = data.get("next_run_id") or max_run_id + 1
        return cls(digests=data.get("digests", {}), history=history, next_run_id=next_run_id)

    def save(self, path: Path, *, history_limit: int | None = DEFAULT_HISTORY_LIMIT) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        history = list(self.history)
        if history_limit is not None:
            history = history[-history_limit:]
        payload = {
            "digests": self.digests,
            "history": [vars(entry) for entry in history],
            "next_run_id": self.next_run_id,
        }
        with path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2)

    def record_run(
        self,
        changed_files: List[str],
        duration_seconds: float | None,
        missing_files: List[str],
        *,
        history_limit: int | None = DEFAULT_HISTORY_LIMIT,
        error: str | None = None,
        change_details: Dict[str, Dict[str, str | None]] | None = None,
        change_summary: Dict[str, int] | None = None,
    ) -> int:
        run_id = self.next_run_id
        self.history.append(
            RunRecord(
                run_id=run_id,
                timestamp=time.time(),
                changed_files=changed_files,
                duration_seconds=duration_seconds,
                missing_files=missing_files,
                error=error,
                change_details=change_details or {},
                change_summary=change_summary or {},
            )
        )
        self.next_run_id += 1

        if history_limit is not None and len(self.history) > history_limit:
            self.history = self.history[-history_limit:]

        return run_id


def hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def compute_patch_digests(
    resolved_patches: Dict[str, Path]
) -> Tuple[Dict[str, str], List[str]]:
    digests: Dict[str, str] = {}
    missing: List[str] = []
    for name, resolved in resolved_patches.items():
        if not resolved.exists():
            logging.warning("Patch file missing: %s", resolved)
            missing.append(name)
            continue
        digests[name] = hash_file(resolved)
    return digests, missing


def detect_changes(
    prev: AgentState, current: Dict[str, str], missing: List[str] | None = None
) -> Tuple[List[str], Dict[str, Dict[str, str | None]]]:
    updated: List[str] = []
    details: Dict[str, Dict[str, str | None]] = {}
    missing_set = set(missing or [])
    names = set(prev.digests) | set(current) | missing_set

    for name in names:
        previous_digest = prev.digests.get(name)
        current_digest = current.get(name)
        if previous_digest == current_digest and name not in missing_set:
            continue

        if name in missing_set:
            status = "missing"
        elif previous_digest is None:
            status = "added"
        elif current_digest is None:
            status = "removed"
        else:
            status = "modified"

        updated.append(name)
        details[name] = {
            "previous_digest": previous_digest,
            "current_digest": current_digest,
            "status": status,
        }

    return updated, details


def summarize_change_details(details: Dict[str, Dict[str, str | None]]) -> Dict[str, int]:
    """Aggregate change counts by status for quick diagnostics."""

    summary: Dict[str, int] = {}
    for meta in details.values():
        status = (meta.get("status") or "unknown").lower()
        summary[status] = summary.get(status, 0) + 1
    return summary


def resolve_under_base(base_dir: Path, path: Path) -> Path:
    """Resolve ``path`` relative to ``base_dir`` if it is not absolute."""

    return path if path.is_absolute() else base_dir / path


def prune_snapshots(snapshot_dir: Path, retention: int | None) -> List[Path]:
    """Delete old snapshot directories beyond the configured retention window."""

    if retention is None or retention <= 0 or not snapshot_dir.exists():
        return []

    snapshots = sorted([path for path in snapshot_dir.iterdir() if path.is_dir()])
    if len(snapshots) <= retention:
        return []

    to_remove = snapshots[: -retention]
    for path in to_remove:
        shutil.rmtree(path, ignore_errors=True)
    return to_remove


def snapshot_patches(
    resolved_patches: Dict[str, Path],
    snapshot_dir: Path,
    changed_files: List[str],
    *,
    retention: int | None,
    enabled: bool,
) -> Tuple[Path | None, List[Path]]:
    if not enabled:
        logging.info("Snapshotting disabled; skipping snapshot creation.")
        removed = prune_snapshots(snapshot_dir, retention)
        if removed:
            logging.info("Pruned %s snapshot(s) despite snapshotting being disabled.", len(removed))
        return None, removed

    if not changed_files:
        removed = prune_snapshots(snapshot_dir, retention)
        if removed:
            logging.info("Pruned %s snapshot(s) during idle run.", len(removed))
        return None, removed

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    destination = snapshot_dir / timestamp
    destination.mkdir(parents=True, exist_ok=True)

    for name in changed_files:
        source = resolved_patches.get(name)
        if source and source.exists():
            shutil.copy2(source, destination / name)

    pruned = prune_snapshots(snapshot_dir, retention)
    if pruned:
        logging.info("Pruned %s old snapshot(s) after creating %s.", len(pruned), destination)

    return destination, pruned


def apply_plan(
    resolved_patches: Dict[str, Path],
    snapshot_dir: Path,
    changed_files: List[str],
    *,
    retention: int | None,
    snapshots_enabled: bool,
) -> Tuple[Path | None, List[Path]]:
    """Initial autonomous hook for responding to patch updates.

    Right now we capture snapshots of the changed patch files to create a durable
    audit trail that future automation can parse without relying on git history
    or artifacts from a single run. This keeps the agent safe but establishes the
    habit of recording every change for downstream processing.
    """
    if not changed_files:
        logging.info("No patch changes detected; agent is idle.")
        return snapshot_patches(
            resolved_patches,
            snapshot_dir,
            changed_files,
            retention=retention,
            enabled=snapshots_enabled,
        )

    logging.info("Detected patch updates in: %s", ", ".join(changed_files))
    return snapshot_patches(
        resolved_patches,
        snapshot_dir,
        changed_files,
        retention=retention,
        enabled=snapshots_enabled,
    )


def render_report(
    report_path: Path,
    run_timestamp: float,
    run_duration: float | None,
    run_id: int | None,
    next_run_id: int | None,
    log_level_name: str,
    log_level_numeric: int,
    log_path: Path | None,
    log_file_enabled: bool,
    agent_version: str,
    runtime_info: Dict[str, str],
    loop_enabled: bool,
    loop_interval: int | None,
    loop_backoff: int | None,
    max_iterations: int | None,
    digests: Dict[str, str],
    changed_files: List[str],
    snapshot_path: Path | None,
    pruned_snapshots: List[Path],
    missing_files: List[str],
    change_details: Dict[str, Dict[str, str | None]],
    tracked_files: List[str],
    resolved_patches: Dict[str, Path],
    patch_sources: Dict[str, str],
    base_dir: Path,
    state_path: Path,
    snapshot_dir: Path,
    snapshot_retention: int | None,
    snapshots_enabled: bool,
    status_path: Path,
    heartbeat_path: Path,
    ci_metadata: Dict[str, str],
) -> None:
    """Write a human-readable summary of the latest agent execution."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    readable_time = datetime.fromtimestamp(run_timestamp).isoformat()
    duration_note = f"{run_duration:.3f} seconds" if run_duration is not None else "(unknown)"

    lines = [
        "# Pantheon Persistent Agent Report",
        "",
        f"Last run: {readable_time}",
        f"Run duration: {duration_note}",
        f"Run ID: {run_id}" if run_id is not None else "Run ID: (unknown)",
        f"Next run ID: {next_run_id}" if next_run_id is not None else "Next run ID: (unknown)",
        "",
        "## Agent",
        "",
        f"- Version: {agent_version}",
        f"- Python: {runtime_info.get('python_version', '(unknown)')}",
        f"- Platform: {runtime_info.get('platform', '(unknown)')}",
        "",
        "## CI metadata",
    ]

    if ci_metadata:
        lines.extend(f"- {key}: {value}" for key, value in sorted(ci_metadata.items()))
    else:
        lines.append("- (none detected)")

    lines.extend(
        [
            "",
            "## Resolved paths",
            "",
            f"- Base directory: {base_dir}",
            f"- State file: {state_path}",
            f"- Snapshot directory: {snapshot_dir}",
            f"- Report path: {report_path}",
            f"- Status JSON path: {status_path}",
            f"- Heartbeat path: {heartbeat_path}",
            "",
        "## Logging",
        "",
        f"- Log level: {log_level_name} ({log_level_numeric})",
        (
            f"- Log file: {log_path}"
            if log_path and log_file_enabled
            else "- Log file: (disabled)"
            if not log_file_enabled
            else "- Log file: (none configured)"
        ),
            "",
            "## State history",
            "",
        ]
    )

    if history_limit is None:
        lines.append("- History retention: unlimited")
    else:
        lines.append(f"- History retention: newest {history_limit} run(s)")

    lines.extend(["", "### Recent runs"])

    if history:
        for entry in history[-5:]:
            iso = datetime.fromtimestamp(entry.timestamp).isoformat()
            duration_note = (
                f"{entry.duration_seconds:.3f}s" if entry.duration_seconds is not None else "(unknown)"
            )
            missing_note = ", missing: " + ", ".join(entry.missing_files) if entry.missing_files else ""
            changed_note = ", changed: " + ", ".join(entry.changed_files) if entry.changed_files else ""
            error_note = f", error: {entry.error}" if entry.error else ""
            lines.append(
                f"- Run {entry.run_id}: {iso} ({duration_note}{changed_note}{missing_note}{error_note})"
            )
    else:
        lines.append("- (no history recorded)")

    lines.extend(
        [
            "",
            "## Loop configuration",
            "",
            f"- Loop mode: {'enabled' if loop_enabled else 'disabled'}",
            f"- Loop interval: {loop_interval} second(s)" if loop_interval is not None else "- Loop interval: (not set)",
            f"- Loop backoff: {loop_backoff} second(s)" if loop_backoff is not None else "- Loop backoff: (not set)",
            (
                f"- Max iterations: {max_iterations}"
                if max_iterations is not None
                else "- Max iterations: unlimited"
            ),
            "",
            "## Snapshot settings",
            "",
            f"- Snapshots enabled: {'yes' if snapshots_enabled else 'no'}",
        ]
    )

    if snapshot_retention is None:
        lines.append("- Snapshot retention: unlimited")
    else:
        lines.append(f"- Snapshot retention: newest {snapshot_retention} snapshot(s)")

    lines.append("")

    lines.append("## Detected changes")

    if changed_files:
        lines.append("")
        lines.extend(f"- {name}" for name in changed_files)
    else:
        lines.append("- None")

    if change_details:
        lines.extend(
            [
                "",
                "### Change details",
                "",
                "| Patch file | Status | Previous digest | Current digest |",
                "| --- | --- | --- | --- |",
            ]
        )
        for name, meta in sorted(change_details.items()):
            lines.append(
                "| {name} | {status} | `{prev}` | `{current}` |".format(
                    name=name,
                    status=meta.get("status", "unknown"),
                    prev=meta.get("previous_digest") or "-",
                    current=meta.get("current_digest") or "-",
                )
            )

    lines.append("")

    if snapshot_path:
        lines.append(f"Snapshot directory: {snapshot_path}")
    else:
        lines.append("Snapshot directory: None (no changes detected)")

    lines.extend(["", "## Pruned snapshots"])
    if pruned_snapshots:
        lines.append("")
        lines.extend(f"- {path}" for path in pruned_snapshots)
    else:
        lines.append("- None removed")

    lines.extend(["", "## Missing patch files"])
    if missing_files:
        lines.append("")
        lines.extend(f"- {name}" for name in missing_files)
    else:
        lines.append("- None detected")

    lines.extend(["", "## Tracked patch files"])
    if tracked_files:
        lines.append("")
        for name in tracked_files:
            resolved = resolved_patches.get(name)
            suffix = f" -> {resolved}" if resolved is not None else ""
            origin = patch_sources.get(name, "unknown")
            lines.append(f"- {name} ({origin}){suffix}")
    else:
        lines.append("- _(none configured)_")

    lines.extend(
        [
            "",
            "## Patch digests",
            "",
            "| Patch file | SHA-256 |",
            "| --- | --- |",
        ]
    )

    if digests:
        for name, digest in sorted(digests.items()):
            lines.append(f"| {name} | `{digest}` |")
    else:
        lines.append("| _(none found)_ | - |")

    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def build_status_payload(
    run_timestamp: float,
    run_duration: float | None,
    run_id: int | None,
    next_run_id: int | None,
    log_level: int | None,
    log_level_name: str | None,
    log_path: Path | None,
    log_file_enabled: bool | None,
    digests: Dict[str, str],
    changed_files: List[str],
    change_details: Dict[str, Dict[str, str | None]],
    change_summary: Dict[str, int],
    snapshot_path: Path | None,
    pruned_snapshots: List[Path],
    missing_files: List[str],
    history: List[RunRecord],
    history_limit: int | None,
    error: str | None = None,
    tracked_files: List[str] | None = None,
    resolved_patches: Dict[str, Path] | None = None,
    patch_sources: Dict[str, str] | None = None,
    base_dir: Path | None = None,
    state_path: Path | None = None,
    snapshot_dir: Path | None = None,
    snapshot_retention: int | None = None,
    snapshots_enabled: bool | None = None,
    report_path: Path | None = None,
    status_path: Path | None = None,
    heartbeat_path: Path | None = None,
    *,
    loop_enabled: bool | None = None,
    loop_interval_seconds: int | None = None,
    loop_backoff_seconds: int | None = None,
    max_iterations: int | None = None,
    agent_version: str | None = None,
    runtime_info: Dict[str, str] | None = None,
    ci_metadata: Dict[str, str] | None = None,
) -> Dict[str, object]:
    """Build a machine-readable payload describing the latest agent run."""

    return {
        "run_id": run_id,
        "next_run_id": next_run_id,
        "run_timestamp": run_timestamp,
        "run_iso": datetime.fromtimestamp(run_timestamp).isoformat(),
        "run_duration_seconds": run_duration,
        "logging": {
            "level": log_level_name,
            "level_numeric": log_level,
            "log_file_enabled": log_file_enabled,
            "log_path": str(log_path) if log_path else None,
        },
        "changed_files": changed_files,
        "change_details": change_details,
        "change_summary": change_summary,
        "missing_files": missing_files,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
        "pruned_snapshots": [str(path) for path in pruned_snapshots],
        "digests": digests,
        "error": error,
        "tracked_files": tracked_files or [],
        "resolved_patches": {
            name: str(path) for name, path in (resolved_patches or {}).items()
        },
        "patch_sources": patch_sources or {},
        "snapshot_settings": {
            "enabled": snapshots_enabled,
            "retention": snapshot_retention,
        },
        "loop": {
            "enabled": loop_enabled,
            "interval_seconds": loop_interval_seconds,
            "backoff_seconds": loop_backoff_seconds,
            "max_iterations": max_iterations,
        },
        "paths": {
            "base_dir": str(base_dir) if base_dir else None,
            "state": str(state_path) if state_path else None,
            "snapshots": str(snapshot_dir) if snapshot_dir else None,
            "report": str(report_path) if report_path else None,
            "status": str(status_path) if status_path else None,
            "heartbeat": str(heartbeat_path) if heartbeat_path else None,
            "log": str(log_path) if log_path else None,
        },
        "agent": {
            "version": agent_version,
            "python": (runtime_info or {}).get("python_version"),
            "platform": (runtime_info or {}).get("platform"),
        },
        "ci": ci_metadata or {},
        "history_limit": history_limit,
        "history": [
            {
                "run_id": entry.run_id,
                "timestamp": entry.timestamp,
                "iso": datetime.fromtimestamp(entry.timestamp).isoformat(),
                "changed_files": entry.changed_files,
                "duration_seconds": entry.duration_seconds,
                "missing_files": entry.missing_files,
                "error": entry.error,
                "change_details": entry.change_details,
                "change_summary": entry.change_summary,
            }
            for entry in history
        ],
    }


def render_status_json(
    status_path: Path,
    run_timestamp: float,
    run_duration: float | None,
    run_id: int | None,
    next_run_id: int | None,
    log_level: int | None,
    log_level_name: str | None,
    log_path: Path | None,
    log_file_enabled: bool | None,
    digests: Dict[str, str],
    changed_files: List[str],
    change_details: Dict[str, Dict[str, str | None]],
    change_summary: Dict[str, int],
    snapshot_path: Path | None,
    pruned_snapshots: List[Path],
    missing_files: List[str],
    history: List[RunRecord],
    history_limit: int | None,
    error: str | None = None,
    tracked_files: List[str] | None = None,
    resolved_patches: Dict[str, Path] | None = None,
    patch_sources: Dict[str, str] | None = None,
    base_dir: Path | None = None,
    state_path: Path | None = None,
    snapshot_dir: Path | None = None,
    snapshot_retention: int | None = None,
    snapshots_enabled: bool | None = None,
    report_path: Path | None = None,
    heartbeat_path: Path | None = None,
    *,
    loop_enabled: bool | None = None,
    loop_interval_seconds: int | None = None,
    loop_backoff_seconds: int | None = None,
    max_iterations: int | None = None,
    agent_version: str | None = None,
    runtime_info: Dict[str, str] | None = None,
    ci_metadata: Dict[str, str] | None = None,
) -> Dict[str, object]:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_status_payload(
        run_timestamp,
        run_duration,
        run_id,
        next_run_id,
        log_level,
        log_level_name,
        log_path,
        log_file_enabled,
        digests,
        changed_files,
        change_details,
        change_summary,
        snapshot_path,
        pruned_snapshots,
        missing_files,
        history,
        history_limit,
        error,
        tracked_files,
        resolved_patches,
        patch_sources,
        base_dir,
        state_path,
        snapshot_dir,
        snapshot_retention,
        snapshots_enabled,
        report_path,
        status_path,
        heartbeat_path,
        loop_enabled=loop_enabled,
        loop_interval_seconds=loop_interval_seconds,
        loop_backoff_seconds=loop_backoff_seconds,
        max_iterations=max_iterations,
        agent_version=agent_version,
        runtime_info=runtime_info,
        ci_metadata=ci_metadata,
    )
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def render_failure_status(
    state_path: Path,
    status_path: Path,
    tracked_files: List[str],
    resolved_patches: Dict[str, Path],
    patch_sources: Dict[str, str],
    error: str,
    log_level: int,
    log_level_name: str,
    log_path: Path | None,
    log_file_enabled: bool | None,
    *,
    state: AgentState | None = None,
    failure_run_id: int | None = None,
    change_summary: Dict[str, int] | None = None,
    base_dir: Path,
    snapshot_dir: Path,
    snapshot_retention: int | None,
    snapshots_enabled: bool,
    report_path: Path,
    heartbeat_path: Path,
    history_limit: int | None,
    loop_enabled: bool | None = None,
    loop_interval_seconds: int | None = None,
    loop_backoff_seconds: int | None = None,
    max_iterations: int | None = None,
    agent_version: str | None = None,
    runtime_info: Dict[str, str] | None = None,
    ci_metadata: Dict[str, str] | None = None,
) -> Dict[str, object]:
    """Persist a status file describing a failed agent iteration."""

    fallback_state = state or AgentState.load(state_path)
    now = time.time()
    active_run_id = failure_run_id
    if active_run_id is None and fallback_state.history:
        active_run_id = fallback_state.history[-1].run_id
    return render_status_json(
        status_path,
        now,
        None,
        active_run_id,
        fallback_state.next_run_id,
        log_level,
        log_level_name,
        log_path,
        log_file_enabled,
        fallback_state.digests,
        [],
        {},
        change_summary or {},
        [],
        snapshot_path=None,
        missing_files=[],
        history=fallback_state.history,
        history_limit=history_limit,
        error=error,
        tracked_files=tracked_files,
        resolved_patches=resolved_patches,
        patch_sources=patch_sources,
        base_dir=base_dir,
        state_path=state_path,
        snapshot_dir=snapshot_dir,
        snapshot_retention=snapshot_retention,
        snapshots_enabled=snapshots_enabled,
        report_path=report_path,
        heartbeat_path=heartbeat_path,
        loop_enabled=loop_enabled,
        loop_interval_seconds=loop_interval_seconds,
        loop_backoff_seconds=loop_backoff_seconds,
        max_iterations=max_iterations,
        agent_version=agent_version,
        runtime_info=runtime_info,
        ci_metadata=ci_metadata,
    )


def write_github_outputs(payload: Dict[str, object]) -> None:
    """Emit machine-readable outputs for GitHub Actions consumers."""

    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        logging.info("GITHUB_OUTPUT not set; skipping output emission.")
        return

    changed_files = payload.get("changed_files", []) or []
    missing_files = payload.get("missing_files", []) or []
    change_summary = payload.get("change_summary", {}) or {}
    paths = payload.get("paths", {}) or {}
    snapshot_path = payload.get("snapshot_path") or ""
    agent_info = payload.get("agent", {}) or {}

    try:
        with open(output_path, "a", encoding="utf-8") as fp:
            fp.write(f"pantheon_changed={str(bool(changed_files)).lower()}\n")
            fp.write(f"pantheon_missing={str(bool(missing_files)).lower()}\n")
            fp.write(f"pantheon_snapshot_path={snapshot_path}\n")
            fp.write(f"pantheon_base_dir={paths.get('base_dir', '')}\n")
            fp.write(f"pantheon_state_path={paths.get('state', '')}\n")
            fp.write(f"pantheon_status_path={paths.get('status', '')}\n")
            fp.write(f"pantheon_report_path={paths.get('report', '')}\n")
            fp.write(f"pantheon_heartbeat_path={paths.get('heartbeat', '')}\n")
            fp.write(f"pantheon_history_limit={payload.get('history_limit', '')}\n")
            fp.write(f"pantheon_run_id={payload.get('run_id', '')}\n")
            fp.write(f"pantheon_next_run_id={payload.get('next_run_id', '')}\n")
            fp.write(f"pantheon_run_timestamp={payload.get('run_timestamp', '')}\n")
            fp.write(f"pantheon_run_iso={payload.get('run_iso', '')}\n")
            fp.write(
                f"pantheon_run_duration_seconds={payload.get('run_duration_seconds', '')}\n"
            )
            logging_info = payload.get("logging", {}) or {}
            fp.write(
                f"pantheon_log_level={logging_info.get('level', '')}\n"
            )
            fp.write(
                f"pantheon_log_level_numeric={logging_info.get('level_numeric', '')}\n"
            )
            loop_info = payload.get("loop", {}) or {}
            fp.write(f"pantheon_loop_enabled={loop_info.get('enabled', '')}\n")
            fp.write(
                f"pantheon_loop_interval_seconds={loop_info.get('interval_seconds', '')}\n"
            )
            fp.write(
                f"pantheon_loop_backoff_seconds={loop_info.get('backoff_seconds', '')}\n"
            )
            fp.write(f"pantheon_loop_max_iterations={loop_info.get('max_iterations', '')}\n")
            fp.write(f"pantheon_agent_version={agent_info.get('version', '')}\n")
            fp.write(f"pantheon_python_version={agent_info.get('python', '')}\n")
            fp.write(f"pantheon_platform={agent_info.get('platform', '')}\n")

            delimiter = "PANTHEONEOF"
            fp.write(
                f"pantheon_changed_files<<{delimiter}\n{json.dumps(changed_files)}\n{delimiter}\n"
            )
            fp.write(
                f"pantheon_missing_files<<{delimiter}\n{json.dumps(missing_files)}\n{delimiter}\n"
            )
            fp.write(
                f"pantheon_tracked_files<<{delimiter}\n{json.dumps(payload.get('tracked_files', []))}\n{delimiter}\n"
            )
            fp.write(
                f"pantheon_change_summary<<{delimiter}\n{json.dumps(change_summary)}\n{delimiter}\n"
            )
            fp.write(
                f"pantheon_status_payload<<{delimiter}\n{json.dumps(payload)}\n{delimiter}\n"
            )
    except OSError as exc:  # pragma: no cover - filesystem/environment specific
        logging.error("Failed to write GitHub outputs: %s", exc)


def build_payload_from_result(result: RunResult) -> Dict[str, object]:
    """Build a status payload from a completed run result."""

    return build_status_payload(
        result.timestamp,
        result.run_duration,
        result.run_id,
        result.next_run_id,
        result.log_level,
        result.log_level_name,
        result.log_path,
        result.log_file_enabled,
        result.digests,
        result.changed_files,
        result.change_details,
        result.change_summary,
        result.snapshot_path,
        result.pruned_snapshots,
        result.missing_files,
        result.history,
        result.history_limit,
        None,
        result.tracked_files,
        result.resolved_patches,
        result.patch_sources,
        result.base_dir,
        result.state_path,
        result.snapshot_dir,
        result.snapshot_retention,
        result.snapshots_enabled,
        result.report_path,
        result.status_path,
        result.heartbeat_path,
        loop_enabled=result.loop_enabled,
        loop_interval_seconds=result.loop_interval,
        loop_backoff_seconds=result.loop_backoff,
        max_iterations=result.max_iterations,
        agent_version=result.agent_version,
        runtime_info=result.runtime_info,
        ci_metadata=result.ci_metadata,
    )


def write_github_summary(result: RunResult) -> None:
    """Emit a concise summary to the GitHub Actions step summary if available."""

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        logging.info("GITHUB_STEP_SUMMARY not set; skipping GitHub summary output.")
        return

    lines = [
        "# Pantheon Persistent Agent",
        "",
        f"Last run: {datetime.fromtimestamp(result.timestamp).isoformat()}",
        f"Run duration: {result.run_duration:.3f} seconds" if result.run_duration is not None else "Run duration: (unknown)",
        f"Run ID: {result.run_id}" if result.run_id is not None else "Run ID: (unknown)",
        f"Next run ID: {result.next_run_id}" if result.next_run_id is not None else "Next run ID: (unknown)",
        "",
        "## Agent",
        "",
        f"- Version: {result.agent_version}",
        f"- Python: {result.runtime_info.get('python_version', '(unknown)')}",
        f"- Platform: {result.runtime_info.get('platform', '(unknown)')}",
        "",
        "## CI metadata",
    ]

    if result.ci_metadata:
        lines.extend(
            f"- {key}: {value}" for key, value in sorted(result.ci_metadata.items())
        )
    else:
        lines.append("- (none detected)")

    lines.extend(
        [
            "",
            "## Resolved paths",
            "",
            f"- Base directory: {result.base_dir}",
            f"- State file: {result.state_path}",
            f"- Snapshot directory: {result.snapshot_dir}",
            f"- Report path: {result.report_path}",
            f"- Status JSON path: {result.status_path}",
            f"- Heartbeat path: {result.heartbeat_path}",
            "",
            "## Logging",
            "",
            f"- Log level: {result.log_level_name} ({result.log_level})",
            (
                f"- Log file: {result.log_path}"
                if result.log_path and result.log_file_enabled
                else "- Log file: (disabled)"
                if not result.log_file_enabled
                else "- Log file: (none configured)"
            ),
            "",
            "## State history",
            "",
        ]
    )

    if result.history_limit is None:
        lines.append("- History retention: unlimited")
    else:
        lines.append(f"- History retention: newest {result.history_limit} run(s)")

    lines.extend(["", "### Recent runs"])

    if result.history:
        for entry in result.history[-5:]:
            iso = datetime.fromtimestamp(entry.timestamp).isoformat()
            duration_note = (
                f"{entry.duration_seconds:.3f}s" if entry.duration_seconds is not None else "(unknown)"
            )
            missing_note = ", missing: " + ", ".join(entry.missing_files) if entry.missing_files else ""
            changed_note = ", changed: " + ", ".join(entry.changed_files) if entry.changed_files else ""
            error_note = f", error: {entry.error}" if entry.error else ""
            lines.append(
                f"- Run {entry.run_id}: {iso} ({duration_note}{changed_note}{missing_note}{error_note})"
            )
    else:
        lines.append("- (no history recorded)")

    lines.extend(
        [
            "",
            "## Loop configuration",
            "",
            f"- Loop mode: {'enabled' if result.loop_enabled else 'disabled'}",
            f"- Loop interval: {result.loop_interval} second(s)" if result.loop_interval is not None else "- Loop interval: (not set)",
            f"- Loop backoff: {result.loop_backoff} second(s)" if result.loop_backoff is not None else "- Loop backoff: (not set)",
            (
                f"- Max iterations: {result.max_iterations}"
                if result.max_iterations is not None
                else "- Max iterations: unlimited"
            ),
            "",
            "## Snapshot settings",
            "",
            f"- Snapshots enabled: {'yes' if result.snapshots_enabled else 'no'}",
        ]
    )

    if result.snapshot_retention is None:
        lines.append("- Snapshot retention: unlimited")
    else:
        lines.append(f"- Snapshot retention: newest {result.snapshot_retention} snapshot(s)")

    lines.extend([
        "",
        "## Detected changes",
    ])

    if result.changed_files:
        lines.append("")
        lines.extend(f"- {name}" for name in result.changed_files)
    else:
        lines.append("- None")

    if result.change_summary:
        lines.extend(["", "### Change summary", ""])
        for status, count in sorted(result.change_summary.items()):
            lines.append(f"- {status}: {count}")

    if result.change_details:
        lines.extend(
            [
                "",
                "### Change details",
                "",
                "| Patch file | Status | Previous digest | Current digest |",
                "| --- | --- | --- | --- |",
            ]
        )
        for name, meta in sorted(result.change_details.items()):
            lines.append(
                "| {name} | {status} | `{prev}` | `{current}` |".format(
                    name=name,
                    status=meta.get("status", "unknown"),
                    prev=meta.get("previous_digest") or "-",
                    current=meta.get("current_digest") or "-",
                )
            )

    lines.extend(["", "## Missing patch files"])
    if result.missing_files:
        lines.append("")
        lines.extend(f"- {name}" for name in result.missing_files)
    else:
        lines.append("- None detected")

    lines.extend(["", "## Tracked patch files"])
    if result.tracked_files:
        lines.append("")
        for name in result.tracked_files:
            resolved = result.resolved_patches.get(name)
            suffix = f" -> {resolved}" if resolved is not None else ""
            origin = result.patch_sources.get(name, "unknown")
            lines.append(f"- {name} ({origin}){suffix}")
    else:
        lines.append("- _(none configured)_")

    snapshot_note = (
        f"Snapshot directory: {result.snapshot_path}" if result.snapshot_path else "Snapshot directory: None"
    )
    lines.extend(["", snapshot_note, "", "## Patch digests", "", "| Patch file | SHA-256 |", "| --- | --- |"])

    if result.digests:
        lines.extend(
            f"| {name} | `{digest}` |" for name, digest in sorted(result.digests.items())
        )
    else:
        lines.append("| _(none found)_ | - |")

    with open(summary_path, "a", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
        fp.write("\n")


def run_once(
    base_dir: Path,
    state_path: Path,
    snapshot_dir: Path,
    snapshot_retention: int | None,
    snapshots_enabled: bool,
    report_path: Path,
    status_path: Path,
    patch_files: List[str],
    patch_sources: Dict[str, str],
    heartbeat_path: Path,
    log_level: int,
    log_level_name: str,
    log_path: Path | None,
    log_file_enabled: bool,
    agent_version: str,
    runtime_info: Dict[str, str],
    ci_metadata: Dict[str, str],
    history_limit: int | None,
    loop_enabled: bool,
    loop_interval: int | None,
    loop_backoff: int | None,
    max_iterations: int | None,
    ) -> RunResult:
    start_time = time.time()
    state = AgentState.load(state_path)
    resolved_patches = resolve_patch_paths(base_dir, patch_files)
    current, missing = compute_patch_digests(resolved_patches)
    changed, change_details = detect_changes(state, current, missing)
    change_summary = summarize_change_details(change_details)
    for missing_name in missing:
        state.digests.pop(missing_name, None)
    snapshot_path, pruned_snapshots = apply_plan(
        resolved_patches,
        snapshot_dir,
        changed,
        retention=snapshot_retention,
        snapshots_enabled=snapshots_enabled,
    )
    state.digests.update(current)
    run_duration = time.time() - start_time
    current_run_id = state.record_run(
        changed,
        run_duration,
        missing,
        history_limit=history_limit,
        change_details=change_details,
        change_summary=change_summary,
    )
    state.save(state_path, history_limit=history_limit)
    next_run_id = state.next_run_id
    render_report(
        report_path,
        state.history[-1].timestamp,
        run_duration,
        current_run_id,
        next_run_id,
        log_level_name,
        log_level,
        log_path,
        log_file_enabled,
        agent_version,
        runtime_info,
        history_limit,
        loop_enabled,
        loop_interval,
        loop_backoff,
        max_iterations,
        current,
        changed,
        snapshot_path,
        pruned_snapshots,
        missing,
        change_details,
        patch_files,
        resolved_patches,
        patch_sources,
        base_dir,
        state_path,
        snapshot_dir,
        snapshot_retention,
        snapshots_enabled,
        status_path,
        heartbeat_path,
        ci_metadata,
    )
    render_status_json(
        status_path,
        state.history[-1].timestamp,
        run_duration,
        current_run_id,
        next_run_id,
        log_level,
        log_level_name,
        log_path,
        log_file_enabled,
        current,
        changed,
        change_details,
        change_summary,
        snapshot_path,
        pruned_snapshots,
        missing,
        state.history,
        history_limit,
        error=None,
        tracked_files=patch_files,
        resolved_patches=resolved_patches,
        patch_sources=patch_sources,
        base_dir=base_dir,
        state_path=state_path,
        snapshot_dir=snapshot_dir,
        snapshot_retention=snapshot_retention,
        snapshots_enabled=snapshots_enabled,
        report_path=report_path,
        heartbeat_path=heartbeat_path,
        log_path=log_path,
        loop_enabled=loop_enabled,
        loop_interval_seconds=loop_interval,
        loop_backoff_seconds=loop_backoff,
        max_iterations=max_iterations,
        agent_version=agent_version,
        runtime_info=runtime_info,
        ci_metadata=ci_metadata,
    )

    return RunResult(
        timestamp=state.history[-1].timestamp,
        digests=current,
        changed_files=changed,
        snapshot_path=snapshot_path,
        pruned_snapshots=pruned_snapshots,
        missing_files=missing,
        change_details=change_details,
        change_summary=change_summary,
        history=list(state.history),
        run_duration=run_duration,
        run_id=current_run_id,
        next_run_id=next_run_id,
        log_level=log_level,
        log_level_name=log_level_name,
        log_path=log_path,
        log_file_enabled=log_file_enabled,
        loop_enabled=loop_enabled,
        loop_interval=loop_interval,
        loop_backoff=loop_backoff,
        max_iterations=max_iterations,
        tracked_files=patch_files,
        resolved_patches=resolved_patches,
        patch_sources=patch_sources,
        base_dir=base_dir,
        state_path=state_path,
        snapshot_dir=snapshot_dir,
        snapshot_retention=snapshot_retention,
        snapshots_enabled=snapshots_enabled,
        report_path=report_path,
        status_path=status_path,
        heartbeat_path=heartbeat_path,
        agent_version=agent_version,
        runtime_info=runtime_info,
        ci_metadata=ci_metadata,
        history_limit=history_limit,
    )


def build_heartbeat_metadata(result: RunResult) -> Dict[str, object]:
    """Summarize the latest run for lightweight heartbeat reporting."""

    run_iso = (
        datetime.utcfromtimestamp(result.timestamp).isoformat() if result.timestamp else None
    )
    return {
        "run_id": result.run_id,
        "next_run_id": result.next_run_id,
        "run_timestamp": result.timestamp,
        "run_iso": run_iso,
        "run_duration_seconds": result.run_duration,
        "agent_version": result.agent_version,
        "log_level": result.log_level_name,
        "log_level_numeric": result.log_level,
        "log_file_enabled": result.log_file_enabled,
        "log_path": result.log_path,
        "base_dir": result.base_dir,
        "state_path": result.state_path,
        "snapshot_dir": result.snapshot_dir,
        "snapshot_retention": result.snapshot_retention,
        "snapshots_enabled": result.snapshots_enabled,
        "report_path": result.report_path,
        "status_path": result.status_path,
        "heartbeat_path": result.heartbeat_path,
        "loop_enabled": result.loop_enabled,
        "loop_interval_seconds": result.loop_interval,
        "loop_backoff_seconds": result.loop_backoff,
        "max_iterations": result.max_iterations,
        "changes_detected": bool(result.changed_files),
        "missing_patches": bool(result.missing_files),
        "missing_files": result.missing_files,
        "change_details": result.change_details,
        "change_summary": result.change_summary,
        "snapshot_path": result.snapshot_path,
    }


def build_failure_heartbeat_metadata(
    *,
    run_id: int | None,
    next_run_id: int | None,
    agent_version: str,
    error: str | None,
    log_level: int | None,
    log_level_name: str | None,
    log_path: Path | None,
    log_file_enabled: bool | None,
    base_dir: Path,
    state_path: Path,
    snapshot_dir: Path,
    snapshot_retention: int | None,
    snapshots_enabled: bool,
    report_path: Path,
    status_path: Path,
    heartbeat_path: Path,
    loop_enabled: bool,
    loop_interval_seconds: int | None,
    loop_backoff_seconds: int | None,
    max_iterations: int | None,
    change_summary: Dict[str, int] | None = None,
) -> Dict[str, object]:
    """Consistent heartbeat metadata for failure cases."""

    return {
        "run_id": run_id,
        "next_run_id": next_run_id,
        "agent_version": agent_version,
        "error": error,
        "log_level": log_level_name,
        "log_level_numeric": log_level,
        "log_file_enabled": log_file_enabled,
        "log_path": log_path,
        "base_dir": base_dir,
        "state_path": state_path,
        "snapshot_dir": snapshot_dir,
        "snapshot_retention": snapshot_retention,
        "snapshots_enabled": snapshots_enabled,
        "report_path": report_path,
        "status_path": status_path,
        "heartbeat_path": heartbeat_path,
        "loop_enabled": loop_enabled,
        "loop_interval_seconds": loop_interval_seconds,
        "loop_backoff_seconds": loop_backoff_seconds,
        "max_iterations": max_iterations,
        "recorded_at": datetime.utcnow().isoformat(),
        "change_summary": change_summary or {},
    }


def write_heartbeat(
    path: Path,
    success: bool,
    message: str | None = None,
    *,
    metadata: Dict[str, object] | None = None,
) -> None:
    """Record a lightweight heartbeat so automation can spot failures quickly."""

    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().isoformat()
    status = "ok" if success else "error"
    note = f" - {message}" if message else ""
    lines = [f"{now} UTC | {status}{note}"]

    if metadata:
        for key, value in sorted(metadata.items()):
            rendered = "" if value is None else str(value)
            lines.append(f"{key}={rendered}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pantheon persistent agent loop")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help=(
            "Override the base directory used to resolve patch files and output paths. "
            "Defaults to the current working directory or PANTHEON_AGENT_BASE_DIR."
        ),
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Keep the agent running and checking for changes indefinitely.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("PANTHEON_AGENT_INTERVAL", 300)),
        help="Polling interval in seconds when running in loop mode.",
    )
    parser.add_argument(
        "--backoff",
        type=int,
        default=int(os.getenv("PANTHEON_AGENT_BACKOFF", 60)),
        help="Backoff in seconds after a failed loop iteration.",
    )
    parser.add_argument(
        "--patch",
        dest="patch_files",
        action="append",
        default=None,
        help=(
            "Additional patch files to hash (relative paths). "
            "May be supplied multiple times."
        ),
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help=(
            "Limit loop executions for local testing or CI smoke runs. "
            "If omitted, the loop runs indefinitely."
        ),
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=STATE_PATH,
        help="Path to the persistent state file.",
    )
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=SNAPSHOT_DIR,
        help="Directory to store snapshots of changed patch files.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help="Path to write the human-readable agent report.",
    )
    parser.add_argument(
        "--status-json",
        type=Path,
        default=STATUS_JSON_PATH,
        help="Path to write the machine-readable status JSON file.",
    )
    parser.add_argument(
        "--heartbeat",
        type=Path,
        default=HEARTBEAT_PATH,
        help="Path to write the heartbeat status file.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=LOG_PATH,
        help=(
            "Optional log file path. When provided, agent output is written to both "
            "stdout and the specified file."
        ),
    )
    parser.add_argument(
        "--disable-log-file",
        action="store_true",
        default=DISABLE_LOG_FILE_ENV,
        help=(
            "Disable file logging even if a log path is configured via environment "
            "variables or defaults."
        ),
    )
    parser.add_argument(
        "--snapshot-retention",
        type=int,
        default=parse_snapshot_retention(SNAPSHOT_RETENTION_ENV),
        help=(
            "Limit snapshot directories to the newest N entries. "
            "Defaults to unlimited; set to 0 or a negative number to disable pruning."
        ),
    )
    parser.add_argument(
        "--disable-snapshots",
        action="store_true",
        default=DISABLE_SNAPSHOTS_ENV,
        help="Skip creating snapshots of changed patch files while still pruning old ones if retention is set.",
    )
    parser.add_argument(
        "--print-status",
        action="store_true",
        help="Emit the status JSON payload to stdout after a single run.",
    )
    parser.add_argument(
        "--exit-on-change",
        action="store_true",
        help="Exit with status 1 if any tracked patch files changed during a single run.",
    )
    parser.add_argument(
        "--exit-on-missing",
        action="store_true",
        help="Exit with status 1 if any tracked patch files are missing during a single run.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("PANTHEON_AGENT_LOG_LEVEL"),
        help=(
            "Logging verbosity (e.g., DEBUG, INFO, WARNING). Defaults to INFO unless "
            "PANTHEON_AGENT_LOG_LEVEL is set."
        ),
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=parse_history_limit(HISTORY_LIMIT_ENV),
        help=(
            "Number of recent runs to retain in the persisted state file. "
            "Defaults to 20; set to 0 or a negative value for unlimited history."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env_log_level = parse_log_level(os.getenv("PANTHEON_AGENT_LOG_LEVEL"))
    configured_log_level = parse_log_level(args.log_level, default=env_log_level)
    resolved_log_level_name = logging.getLevelName(configured_log_level)
    base_dir = args.base_dir or BASE_DIR
    log_file_enabled = False
    log_path = None
    if not args.disable_log_file:
        log_path = resolve_under_base(base_dir, args.log_file) if args.log_file else None
        log_file_enabled = log_path is not None
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path))

    logging.basicConfig(
        level=configured_log_level,
        format="[%(levelname)s] %(message)s",
        handlers=handlers,
    )
    state_path = resolve_under_base(base_dir, args.state)
    snapshot_dir = resolve_under_base(base_dir, args.snapshots)
    snapshot_retention = args.snapshot_retention
    snapshots_enabled = not args.disable_snapshots
    report_path = resolve_under_base(base_dir, args.report)
    status_path = resolve_under_base(base_dir, args.status_json)
    heartbeat_path = resolve_under_base(base_dir, args.heartbeat)
    env_patch_files = parse_env_patch_files(os.getenv("PANTHEON_PATCH_FILES"))
    cli_patch_files = args.patch_files or []
    history_limit = args.history_limit
    if history_limit is not None and history_limit <= 0:
        history_limit = None
    patch_files, patch_sources = merge_patch_sources(
        PATCH_FILENAMES, env_patch_files, cli_patch_files
    )
    resolved_patch_paths = resolve_patch_paths(base_dir, patch_files)
    runtime_info = gather_runtime_info()
    ci_metadata = gather_ci_metadata()

    logging.info("Agent version: %s", AGENT_VERSION)
    logging.info("Log level: %s", resolved_log_level_name)
    if args.disable_log_file:
        logging.info("Log file: (disabled)")
    elif log_path:
        logging.info("Log file: %s", log_path)
    else:
        logging.info("Log file: (none configured)")
    if history_limit is None:
        logging.info("History retention: unlimited")
    else:
        logging.info("History retention: newest %s run(s)", history_limit)
    logging.info(
        "Runtime: Python %s on %s",
        runtime_info.get("python_version"),
        runtime_info.get("platform"),
    )
    if ci_metadata:
        logging.info("CI metadata detected:")
        for key, value in sorted(ci_metadata.items()):
            logging.info("- %s: %s", key, value)
    else:
        logging.info("CI metadata: (none detected)")
    logging.info(
        "Tracking %s patch file(s): %s",
        len(patch_files),
        ", ".join(patch_files) if patch_files else "(none)",
    )

    logging.info("Base directory: %s", base_dir)
    logging.info("State path: %s", state_path)
    logging.info("Snapshot directory: %s", snapshot_dir)
    if snapshot_retention is None:
        logging.info("Snapshot retention: unlimited")
    else:
        logging.info("Snapshot retention: newest %s snapshot(s)", snapshot_retention)
    logging.info("Snapshots enabled: %s", "yes" if snapshots_enabled else "no")
    logging.info("Report path: %s", report_path)
    logging.info("Status JSON path: %s", status_path)
    logging.info("Heartbeat path: %s", heartbeat_path)
    if args.disable_log_file:
        logging.info("Log file: (disabled)")
    elif log_path:
        logging.info("Log file: %s", log_path)
    else:
        logging.info("Log file: (none configured)")
    if patch_files:
        logging.info("Resolved patch locations:")
        for name, path in resolved_patch_paths.items():
            logging.info("- %s -> %s", name, path)
            origin = patch_sources.get(name, "unknown")
            logging.info("  source: %s", origin)

    if args.loop:
        logging.info(
            "Starting persistent agent loop with %s-second interval and %s-second backoff",
            args.interval,
            args.backoff,
        )
        iteration = 0
        try:
            while True:
                iteration += 1
                try:
                    result = run_once(
                        base_dir,
                        state_path,
                        snapshot_dir,
                        snapshot_retention,
                        snapshots_enabled,
                        report_path,
                        status_path,
                        patch_files,
                        patch_sources,
                        heartbeat_path,
                        configured_log_level,
                        resolved_log_level_name,
                        log_path,
                        AGENT_VERSION,
                        runtime_info,
                        ci_metadata,
                        history_limit,
                        True,
                        args.interval,
                        args.backoff,
                        args.max_iterations,
                    )
                except Exception as exc:  # pragma: no cover - defensive loop guard
                    logging.exception("Persistent agent iteration failed: %s", exc)
                    failure_state = AgentState.load(state_path)
                    failure_run_id = failure_state.record_run(
                        [],
                        None,
                        [],
                        history_limit=history_limit,
                        error=str(exc),
                    )
                    failure_state.save(state_path, history_limit=history_limit)
                    write_heartbeat(
                        heartbeat_path,
                        success=False,
                        message=str(exc),
                        metadata=build_failure_heartbeat_metadata(
                            run_id=failure_run_id,
                            next_run_id=failure_state.next_run_id,
                            agent_version=AGENT_VERSION,
                            error=str(exc),
                            log_level=configured_log_level,
                            log_level_name=resolved_log_level_name,
                            log_path=log_path,
                            log_file_enabled=log_file_enabled,
                            base_dir=base_dir,
                            state_path=state_path,
                            snapshot_dir=snapshot_dir,
                            snapshot_retention=snapshot_retention,
                            snapshots_enabled=snapshots_enabled,
                            report_path=report_path,
                            status_path=status_path,
                            heartbeat_path=heartbeat_path,
                            loop_enabled=True,
                            loop_interval_seconds=args.interval,
                            loop_backoff_seconds=args.backoff,
                            max_iterations=args.max_iterations,
                            change_summary={},
                        ),
                    )
                    failure_payload = render_failure_status(
                        state_path,
                        status_path,
                        patch_files,
                        resolve_patch_paths(base_dir, patch_files),
                        patch_sources,
                        error=str(exc),
                        log_level=configured_log_level,
                        log_level_name=resolved_log_level_name,
                        log_path=log_path,
                        base_dir=base_dir,
                        snapshot_dir=snapshot_dir,
                        snapshot_retention=snapshot_retention,
                        snapshots_enabled=snapshots_enabled,
                        report_path=report_path,
                        heartbeat_path=heartbeat_path,
                        history_limit=history_limit,
                        loop_enabled=True,
                        loop_interval_seconds=args.interval,
                        loop_backoff_seconds=args.backoff,
                        max_iterations=args.max_iterations,
                        agent_version=AGENT_VERSION,
                        runtime_info=runtime_info,
                        ci_metadata=ci_metadata,
                        state=failure_state,
                        failure_run_id=failure_run_id,
                    )
                    write_github_outputs(failure_payload)
                    time.sleep(max(args.backoff, 1))
                    continue

                write_heartbeat(
                    heartbeat_path,
                    success=True,
                    message="loop iteration",
                    metadata=build_heartbeat_metadata(result),
                )
                write_github_summary(result)
                write_github_outputs(build_payload_from_result(result))
                if args.print_status:
                    logging.info(
                        "Ignoring --print-status while running in loop mode to avoid repeated output."
                    )
                if args.exit_on_change or args.exit_on_missing:
                    logging.info(
                        "Ignoring exit-on-change/missing flags while running in loop mode."
                    )
                if args.max_iterations and iteration >= args.max_iterations:
                    logging.info(
                        "Reached maximum iterations (%s); exiting loop gracefully.",
                        args.max_iterations,
                    )
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Received interrupt; writing heartbeat and exiting loop.")
            write_heartbeat(
                heartbeat_path,
                success=False,
                message="loop interrupted",
                metadata=build_failure_heartbeat_metadata(
                    run_id=None,
                    next_run_id=None,
                    agent_version=AGENT_VERSION,
                    error="KeyboardInterrupt",
                    log_level=configured_log_level,
                    log_level_name=resolved_log_level_name,
                    log_path=log_path,
                    log_file_enabled=log_file_enabled,
                    base_dir=base_dir,
                    state_path=state_path,
                    snapshot_dir=snapshot_dir,
                    snapshot_retention=snapshot_retention,
                    snapshots_enabled=snapshots_enabled,
                    report_path=report_path,
                    status_path=status_path,
                    heartbeat_path=heartbeat_path,
                    loop_enabled=True,
                    loop_interval_seconds=args.interval,
                    loop_backoff_seconds=args.backoff,
                    max_iterations=args.max_iterations,
                    change_summary={},
                ),
            )
    elif args.max_iterations:
        logging.info("Ignoring --max-iterations because --loop was not provided.")
    else:
        try:
            result = run_once(
                base_dir,
                state_path,
                snapshot_dir,
                snapshot_retention,
                snapshots_enabled,
                report_path,
                status_path,
                patch_files,
                patch_sources,
                heartbeat_path,
                configured_log_level,
                resolved_log_level_name,
                log_path,
                log_file_enabled,
                AGENT_VERSION,
                runtime_info,
                ci_metadata,
                history_limit,
                False,
                args.interval,
                args.backoff,
                args.max_iterations,
            )
        except Exception as exc:  # pragma: no cover - defensive single-run guard
            logging.exception("Persistent agent run failed: %s", exc)
            failure_state = AgentState.load(state_path)
            failure_run_id = failure_state.record_run(
                [],
                None,
                [],
                history_limit=history_limit,
                error=str(exc),
            )
            failure_state.save(state_path, history_limit=history_limit)
            write_heartbeat(
                heartbeat_path,
                success=False,
                message=str(exc),
                metadata=build_failure_heartbeat_metadata(
                    run_id=failure_run_id,
                    next_run_id=failure_state.next_run_id,
                    agent_version=AGENT_VERSION,
                    error=str(exc),
                    log_level=configured_log_level,
                    log_level_name=resolved_log_level_name,
                    log_path=log_path,
                    log_file_enabled=log_file_enabled,
                    base_dir=base_dir,
                    state_path=state_path,
                    snapshot_dir=snapshot_dir,
                    snapshot_retention=snapshot_retention,
                    snapshots_enabled=snapshots_enabled,
                    report_path=report_path,
                    status_path=status_path,
                    heartbeat_path=heartbeat_path,
                    loop_enabled=False,
                    loop_interval_seconds=args.interval,
                    loop_backoff_seconds=args.backoff,
                    max_iterations=args.max_iterations,
                    change_summary={},
                ),
            )
            failure_payload = render_failure_status(
                state_path,
                status_path,
                patch_files,
                resolve_patch_paths(base_dir, patch_files),
                patch_sources,
                error=str(exc),
                log_level=configured_log_level,
                log_level_name=resolved_log_level_name,
                log_path=log_path,
                log_file_enabled=log_file_enabled,
                base_dir=base_dir,
                snapshot_dir=snapshot_dir,
                snapshot_retention=snapshot_retention,
                snapshots_enabled=snapshots_enabled,
                report_path=report_path,
                heartbeat_path=heartbeat_path,
                history_limit=history_limit,
                loop_enabled=False,
                loop_interval_seconds=args.interval,
                loop_backoff_seconds=args.backoff,
                max_iterations=args.max_iterations,
                agent_version=AGENT_VERSION,
                runtime_info=runtime_info,
                ci_metadata=ci_metadata,
                state=failure_state,
                failure_run_id=failure_run_id,
            )
            write_github_outputs(failure_payload)
            raise
        write_heartbeat(
            heartbeat_path,
            success=True,
            message="single run",
            metadata=build_heartbeat_metadata(result),
        )
        write_github_summary(result)
        write_github_outputs(build_payload_from_result(result))
        if args.print_status:
            payload = build_status_payload(
                result.timestamp,
                result.run_duration,
                result.run_id,
                result.next_run_id,
                result.log_level,
                result.log_level_name,
                result.log_path,
                result.log_file_enabled,
                result.digests,
                result.changed_files,
                result.change_details,
                result.snapshot_path,
                result.pruned_snapshots,
                result.missing_files,
                result.history,
                result.history_limit,
                result.tracked_files,
                result.resolved_patches,
                result.patch_sources,
                result.base_dir,
                result.state_path,
                result.snapshot_dir,
                result.snapshot_retention,
                result.snapshots_enabled,
                result.report_path,
                result.status_path,
                result.heartbeat_path,
                loop_enabled=result.loop_enabled,
                loop_interval_seconds=result.loop_interval,
                loop_backoff_seconds=result.loop_backoff,
                max_iterations=result.max_iterations,
                agent_version=result.agent_version,
                runtime_info=result.runtime_info,
                ci_metadata=result.ci_metadata,
            )
            print(json.dumps(payload, indent=2))

        exit_due_to_changes = args.exit_on_change and bool(result.changed_files)
        exit_due_to_missing = args.exit_on_missing and bool(result.missing_files)
        if exit_due_to_changes or exit_due_to_missing:
            reason = "change" if exit_due_to_changes else "missing patch"
            logging.info("Exiting with non-zero status due to %s condition.", reason)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
