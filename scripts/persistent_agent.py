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
# run so the automation can react immediately when new guidance is added.
PATCH_FILENAMES: Tuple[str, ...] = (
    "Patches 1-25 – Pantheon of Oracles GPT.JSON",
    "Patches 26-41 – Pantheon of Oracles GPT.JSON",
)

# Default location to store the digest of the last run so we can tell when the
# patch files change.
STATE_PATH = Path("state/persistent_agent_state.json")
# Directory where snapshots of changed patches will be persisted for auditing
# and follow-up processing by future automation steps.
SNAPSHOT_DIR = Path("state/patch_snapshots")
# Human-readable and machine-readable reports that summarize the latest run and
# current digests for downstream automation.
REPORT_PATH = Path("state/persistent_agent_report.md")
STATUS_JSON_PATH = Path("state/persistent_agent_status.json")
HEARTBEAT_PATH = Path("state/persistent_agent_heartbeat.txt")


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


def compute_patch_digests(base_dir: Path) -> Tuple[Dict[str, str], List[str]]:
    digests: Dict[str, str] = {}
    missing: List[str] = []
    for name in PATCH_FILENAMES:
        path = base_dir / name
        if not path.exists():
            logging.warning("Patch file missing: %s", path)
            missing.append(name)
            continue
        digests[name] = hash_file(path)
    return digests, missing


def detect_changes(prev: AgentState, current: Dict[str, str]) -> List[str]:
    updated: List[str] = []
    for name, digest in current.items():
        if prev.digests.get(name) != digest:
            updated.append(name)
    return updated


def snapshot_patches(
    base_dir: Path, snapshot_dir: Path, changed_files: List[str]
) -> Path | None:
    if not changed_files:
        return None

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    destination = snapshot_dir / timestamp
    destination.mkdir(parents=True, exist_ok=True)

    for name in changed_files:
        source = base_dir / name
        if source.exists():
            shutil.copy2(source, destination / name)

    return destination


def apply_plan(
    base_dir: Path, snapshot_dir: Path, changed_files: List[str]
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
    return snapshot_patches(base_dir, snapshot_dir, changed_files)


def render_report(
    report_path: Path,
    run_timestamp: float,
    digests: Dict[str, str],
    changed_files: List[str],
    snapshot_path: Path | None,
    missing_files: List[str],
) -> None:
    """Write a human-readable summary of the latest agent execution."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    readable_time = datetime.fromtimestamp(run_timestamp).isoformat()

    lines = [
        "# Pantheon Persistent Agent Report",
        "",
        f"Last run: {readable_time}",
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


def run_once(base_dir: Path, state_path: Path, snapshot_dir: Path) -> RunResult:
    state = AgentState.load(state_path)
    current, missing = compute_patch_digests(base_dir)
    changed = detect_changes(state, current)
    snapshot_path = apply_plan(base_dir, snapshot_dir, changed)
    state.digests.update(current)
    state.record_run(changed)
    state.save(state_path)
    render_report(
        REPORT_PATH,
        state.history[-1].timestamp,
        current,
        changed,
        snapshot_path,
        missing,
    )
    render_status_json(
        STATUS_JSON_PATH,
        state.history[-1].timestamp,
        current,
        changed,
        snapshot_path,
        missing,
        state.history,
        error=None,
    )

    return RunResult(
        timestamp=state.history[-1].timestamp,
        digests=current,
        changed_files=changed,
        snapshot_path=snapshot_path,
        missing_files=missing,
        history=list(state.history),
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
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = parse_args()
    base_dir = Path.cwd()

    if args.loop:
        logging.info(
            "Starting persistent agent loop with %s-second interval and %s-second backoff",
            args.interval,
            args.backoff,
        )
        while True:
            try:
                result = run_once(base_dir, args.state, args.snapshots)
            except Exception as exc:  # pragma: no cover - defensive loop guard
                logging.exception("Persistent agent iteration failed: %s", exc)
                write_heartbeat(HEARTBEAT_PATH, success=False, message=str(exc))
                fallback_state = AgentState.load(args.state)
                now = time.time()
                render_status_json(
                    STATUS_JSON_PATH,
                    now,
                    fallback_state.digests,
                    [],
                    snapshot_path=None,
                    missing_files=[],
                    history=fallback_state.history,
                    error=str(exc),
                )
                time.sleep(max(args.backoff, 1))
                continue

            write_heartbeat(HEARTBEAT_PATH, success=True, message="loop iteration")
            write_github_summary(result)
            time.sleep(args.interval)
    else:
        result = run_once(base_dir, args.state, args.snapshots)
        write_heartbeat(HEARTBEAT_PATH, success=True, message="single run")
        write_github_summary(result)


if __name__ == "__main__":
    main()
