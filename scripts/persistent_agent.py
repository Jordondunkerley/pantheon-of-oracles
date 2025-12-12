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


def resolve_patch_paths(base_dir: Path, patch_files: List[str]) -> Dict[str, Path]:
    """Resolve configured patch files relative to the provided base directory."""

    resolved: Dict[str, Path] = {}
    for name in patch_files:
        path = Path(name)
        resolved[name] = path if path.is_absolute() else base_dir / path
    return resolved

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

# The base directory used to resolve relative paths. Defaults to the current
# working directory but can be overridden via environment variable or CLI
# argument to support running the agent from alternate locations.
BASE_DIR = Path(os.getenv("PANTHEON_AGENT_BASE_DIR", Path.cwd()))


@dataclass
class RunRecord:
    """Represents a single execution of the agent."""

    timestamp: float
    changed_files: List[str]


@dataclass
class RunResult:
    """Aggregate information from the most recent agent execution."""

    timestamp: float
    digests: Dict[str, str]
    changed_files: List[str]
    snapshot_path: Path | None
    missing_files: List[str]
    history: List[RunRecord]
    tracked_files: List[str]
    resolved_patches: Dict[str, Path]
    patch_sources: Dict[str, str]
    base_dir: Path
    state_path: Path
    snapshot_dir: Path
    report_path: Path
    status_path: Path
    heartbeat_path: Path


@dataclass
class AgentState:
    """Persisted digests and a small run history."""

    digests: Dict[str, str] = field(default_factory=dict)
    history: List[RunRecord] = field(default_factory=list)

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

        history = [RunRecord(**entry) for entry in data.get("history", [])]
        return cls(digests=data.get("digests", {}), history=history)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "digests": self.digests,
            "history": [vars(entry) for entry in self.history[-20:]],
        }
        with path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2)

    def record_run(self, changed_files: List[str]) -> None:
        self.history.append(RunRecord(timestamp=time.time(), changed_files=changed_files))


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


def detect_changes(prev: AgentState, current: Dict[str, str]) -> List[str]:
    updated: List[str] = []
    for name, digest in current.items():
        if prev.digests.get(name) != digest:
            updated.append(name)
    return updated


def resolve_under_base(base_dir: Path, path: Path) -> Path:
    """Resolve ``path`` relative to ``base_dir`` if it is not absolute."""

    return path if path.is_absolute() else base_dir / path


def snapshot_patches(
    resolved_patches: Dict[str, Path], snapshot_dir: Path, changed_files: List[str]
) -> Path | None:
    if not changed_files:
        return None

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    destination = snapshot_dir / timestamp
    destination.mkdir(parents=True, exist_ok=True)

    for name in changed_files:
        source = resolved_patches.get(name)
        if source and source.exists():
            shutil.copy2(source, destination / name)

    return destination


def apply_plan(
    resolved_patches: Dict[str, Path], snapshot_dir: Path, changed_files: List[str]
) -> Path | None:
    """Initial autonomous hook for responding to patch updates.

    Right now we capture snapshots of the changed patch files to create a durable
    audit trail that future automation can parse without relying on git history
    or artifacts from a single run. This keeps the agent safe but establishes the
    habit of recording every change for downstream processing.
    """
    if not changed_files:
        logging.info("No patch changes detected; agent is idle.")
        return None

    logging.info("Detected patch updates in: %s", ", ".join(changed_files))
    return snapshot_patches(resolved_patches, snapshot_dir, changed_files)


def render_report(
    report_path: Path,
    run_timestamp: float,
    digests: Dict[str, str],
    changed_files: List[str],
    snapshot_path: Path | None,
    missing_files: List[str],
    tracked_files: List[str],
    resolved_patches: Dict[str, Path],
    patch_sources: Dict[str, str],
    base_dir: Path,
    state_path: Path,
    snapshot_dir: Path,
    status_path: Path,
    heartbeat_path: Path,
) -> None:
    """Write a human-readable summary of the latest agent execution."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    readable_time = datetime.fromtimestamp(run_timestamp).isoformat()

    lines = [
        "# Pantheon Persistent Agent Report",
        "",
        f"Last run: {readable_time}",
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
        "## Detected changes",
    ]

    if changed_files:
        lines.append("")
        lines.extend(f"- {name}" for name in changed_files)
    else:
        lines.append("- None")

    lines.append("")

    if snapshot_path:
        lines.append(f"Snapshot directory: {snapshot_path}")
    else:
        lines.append("Snapshot directory: None (no changes detected)")

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


def render_status_json(
    status_path: Path,
    run_timestamp: float,
    digests: Dict[str, str],
    changed_files: List[str],
    snapshot_path: Path | None,
    missing_files: List[str],
    history: List[RunRecord],
    error: str | None = None,
    tracked_files: List[str] | None = None,
    resolved_patches: Dict[str, Path] | None = None,
    patch_sources: Dict[str, str] | None = None,
    base_dir: Path | None = None,
    state_path: Path | None = None,
    snapshot_dir: Path | None = None,
    report_path: Path | None = None,
    heartbeat_path: Path | None = None,
) -> None:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_timestamp": run_timestamp,
        "run_iso": datetime.fromtimestamp(run_timestamp).isoformat(),
        "changed_files": changed_files,
        "missing_files": missing_files,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
        "digests": digests,
        "error": error,
        "tracked_files": tracked_files or [],
        "resolved_patches": {
            name: str(path) for name, path in (resolved_patches or {}).items()
        },
        "patch_sources": patch_sources or {},
        "paths": {
            "base_dir": str(base_dir) if base_dir else None,
            "state": str(state_path) if state_path else None,
            "snapshots": str(snapshot_dir) if snapshot_dir else None,
            "report": str(report_path) if report_path else None,
            "status": str(status_path),
            "heartbeat": str(heartbeat_path) if heartbeat_path else None,
        },
        "history": [
            {
                "timestamp": entry.timestamp,
                "iso": datetime.fromtimestamp(entry.timestamp).isoformat(),
                "changed_files": entry.changed_files,
            }
            for entry in history
        ],
    }
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def render_failure_status(
    state_path: Path,
    status_path: Path,
    tracked_files: List[str],
    resolved_patches: Dict[str, Path],
    patch_sources: Dict[str, str],
    error: str,
    *,
    base_dir: Path,
    snapshot_dir: Path,
    report_path: Path,
    heartbeat_path: Path,
) -> None:
    """Persist a status file describing a failed agent iteration."""

    fallback_state = AgentState.load(state_path)
    now = time.time()
    render_status_json(
        status_path,
        now,
        fallback_state.digests,
        [],
        snapshot_path=None,
        missing_files=[],
        history=fallback_state.history,
        error=error,
        tracked_files=tracked_files,
        resolved_patches=resolved_patches,
        patch_sources=patch_sources,
        base_dir=base_dir,
        state_path=state_path,
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        heartbeat_path=heartbeat_path,
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
        "## Detected changes",
    ]

    if result.changed_files:
        lines.append("")
        lines.extend(f"- {name}" for name in result.changed_files)
    else:
        lines.append("- None")

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
    report_path: Path,
    status_path: Path,
    patch_files: List[str],
    patch_sources: Dict[str, str],
    heartbeat_path: Path,
) -> RunResult:
    state = AgentState.load(state_path)
    resolved_patches = resolve_patch_paths(base_dir, patch_files)
    current, missing = compute_patch_digests(resolved_patches)
    changed = detect_changes(state, current)
    snapshot_path = apply_plan(resolved_patches, snapshot_dir, changed)
    state.digests.update(current)
    state.record_run(changed)
    state.save(state_path)
    render_report(
        report_path,
        state.history[-1].timestamp,
        current,
        changed,
        snapshot_path,
        missing,
        patch_files,
        resolved_patches,
        patch_sources,
        base_dir,
        state_path,
        snapshot_dir,
        status_path,
        heartbeat_path,
    )
    render_status_json(
        status_path,
        state.history[-1].timestamp,
        current,
        changed,
        snapshot_path,
        missing,
        state.history,
        error=None,
        tracked_files=patch_files,
        resolved_patches=resolved_patches,
        patch_sources=patch_sources,
        base_dir=base_dir,
        state_path=state_path,
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        heartbeat_path=heartbeat_path,
    )

    return RunResult(
        timestamp=state.history[-1].timestamp,
        digests=current,
        changed_files=changed,
        snapshot_path=snapshot_path,
        missing_files=missing,
        history=list(state.history),
        tracked_files=patch_files,
        resolved_patches=resolved_patches,
        patch_sources=patch_sources,
        base_dir=base_dir,
        state_path=state_path,
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        status_path=status_path,
        heartbeat_path=heartbeat_path,
    )


def write_heartbeat(path: Path, success: bool, message: str | None = None) -> None:
    """Record a lightweight heartbeat so automation can spot failures quickly."""

    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().isoformat()
    status = "ok" if success else "error"
    note = f" - {message}" if message else ""
    path.write_text(f"{now} UTC | {status}{note}\n", encoding="utf-8")


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
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = parse_args()
    base_dir = args.base_dir or BASE_DIR
    state_path = resolve_under_base(base_dir, args.state)
    snapshot_dir = resolve_under_base(base_dir, args.snapshots)
    report_path = resolve_under_base(base_dir, args.report)
    status_path = resolve_under_base(base_dir, args.status_json)
    heartbeat_path = resolve_under_base(base_dir, args.heartbeat)
    env_patch_files = parse_env_patch_files(os.getenv("PANTHEON_PATCH_FILES"))
    cli_patch_files = args.patch_files or []
    patch_files, patch_sources = merge_patch_sources(
        PATCH_FILENAMES, env_patch_files, cli_patch_files
    )
    resolved_patch_paths = resolve_patch_paths(base_dir, patch_files)

    logging.info(
        "Tracking %s patch file(s): %s",
        len(patch_files),
        ", ".join(patch_files) if patch_files else "(none)",
    )

    logging.info("Base directory: %s", base_dir)
    logging.info("State path: %s", state_path)
    logging.info("Snapshot directory: %s", snapshot_dir)
    logging.info("Report path: %s", report_path)
    logging.info("Status JSON path: %s", status_path)
    logging.info("Heartbeat path: %s", heartbeat_path)
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
                        report_path,
                        status_path,
                        patch_files,
                        patch_sources,
                        heartbeat_path,
                    )
                except Exception as exc:  # pragma: no cover - defensive loop guard
                    logging.exception("Persistent agent iteration failed: %s", exc)
                    write_heartbeat(heartbeat_path, success=False, message=str(exc))
                    render_failure_status(
                        state_path,
                        status_path,
                        patch_files,
                        resolve_patch_paths(base_dir, patch_files),
                        patch_sources,
                        error=str(exc),
                        base_dir=base_dir,
                        snapshot_dir=snapshot_dir,
                        report_path=report_path,
                        heartbeat_path=heartbeat_path,
                    )
                    time.sleep(max(args.backoff, 1))
                    continue

                write_heartbeat(heartbeat_path, success=True, message="loop iteration")
                write_github_summary(result)
                if args.max_iterations and iteration >= args.max_iterations:
                    logging.info(
                        "Reached maximum iterations (%s); exiting loop gracefully.",
                        args.max_iterations,
                    )
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Received interrupt; writing heartbeat and exiting loop.")
            write_heartbeat(heartbeat_path, success=False, message="loop interrupted")
    elif args.max_iterations:
        logging.info("Ignoring --max-iterations because --loop was not provided.")
    else:
        try:
            result = run_once(
                base_dir,
                state_path,
                snapshot_dir,
                report_path,
                status_path,
                patch_files,
                patch_sources,
                heartbeat_path,
            )
        except Exception as exc:  # pragma: no cover - defensive single-run guard
            logging.exception("Persistent agent run failed: %s", exc)
            write_heartbeat(heartbeat_path, success=False, message=str(exc))
            render_failure_status(
                state_path,
                status_path,
                patch_files,
                resolve_patch_paths(base_dir, patch_files),
                patch_sources,
                error=str(exc),
                base_dir=base_dir,
                snapshot_dir=snapshot_dir,
                report_path=report_path,
                heartbeat_path=heartbeat_path,
            )
            raise
        write_heartbeat(heartbeat_path, success=True, message="single run")
        write_github_summary(result)


if __name__ == "__main__":
    main()
