"""
Autonomous builder loop for Pantheon of Oracles.

This script is designed to run on a schedule (via GitHub Actions) to keep
an always-on planning loop alive. It reads the Pantheon GPT patch files,
computes digests for traceability, and (optionally) asks OpenAI to suggest
prioritized next actions for the system. The resulting report is written to
`autonomous/outputs` when running in CI, or `autonomous/reports` for local
runs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_openai_spec = importlib.util.find_spec("openai")
OpenAI = importlib.import_module("openai").OpenAI if _openai_spec else None  # type: ignore


DEFAULT_PATCH_GLOB = "Patches *.JSON"

STATE_PATH = Path("autonomous/state.json")


def read_patch(path: Path, limit: int) -> Dict[str, str]:
    """Return text preview and SHA256 digest for a patch file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    preview = text[:limit]
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return {"path": str(path), "digest": digest, "preview": preview}

def find_patch_files(glob_pattern: str) -> list[Path]:
    """Return sorted patch files matching the glob pattern."""

    return sorted(Path(".").glob(glob_pattern))


def gather_context(limit: int, glob_pattern: str) -> List[Dict[str, str]]:
    contexts: List[Dict[str, str]] = []
    for path in find_patch_files(glob_pattern):
        if path.exists():
            contexts.append(read_patch(path, limit))
    return contexts


def maybe_iter(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def extract_oracles_from_patch(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    acc: dict[str, dict[str, Any]] = {}
    for patch in maybe_iter(payload):
        for oracle in maybe_iter(patch.get("oracles", [])):
            code = oracle.get("code") or oracle.get("name")
            if not code:
                continue
            acc[str(code)] = {
                "code": str(code),
                "name": oracle.get("name") or str(code).title(),
                "role": oracle.get("role"),
                "rules": oracle.get("rules", {}),
            }
    return acc


def sync_supabase_oracles(patch_paths: list[Path]) -> list[str]:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not patch_paths:
        return ["No patch files discovered; skipped Supabase sync."]
    if not (supabase_url and supabase_key):
        return ["SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing; skipped Supabase sync."]

    supabase_spec = importlib.util.find_spec("supabase")
    if supabase_spec is None:
        return ["supabase client not installed; run `pip install -r requirements.txt` to enable syncing."]
    from supabase import create_client

    client = create_client(supabase_url, supabase_key)
    merged: dict[str, dict[str, Any]] = {}
    for path in patch_paths:
        merged.update(extract_oracles_from_patch(path))

    if not merged:
        return ["No oracles found in patch files; nothing to sync."]

    for row in merged.values():
        client.table("oracles").upsert(row, on_conflict="code").execute()

    file_list = ", ".join(path.name for path in patch_paths)
    return [
        f"Supabase URL: {supabase_url}",
        f"Synced {len(merged)} oracle definitions from {len(patch_paths)} patch file(s): {file_list}",
    ]


def build_prompt(contexts: List[Dict[str, str]]) -> str:
    headings = []
    for ctx in contexts:
        headings.append(
            f"File: {ctx['path']}\nDigest: {ctx['digest']}\nPreview:\n{ctx['preview']}\n---\n"
        )
    patch_section = "\n".join(headings) or "No patch files found."
    return (
        "You are the autonomous Pantheon Builder responsible for keeping the "
        "Pantheon of Oracles development loop active without human prompts. "
        "Use the patch file previews to propose concrete, incremental tasks "
        "that keep the system aligned with the full vision. Focus on work "
        "items that can be executed automatically in a CI environment using "
        "Supabase + FastAPI stack already in the repo. "
        "Provide a numbered backlog with owners (e.g., `autobot`), inputs, "
        "and expected outputs. Keep each item concise and executable.\n\n"
        "Patch context:\n" + patch_section
    )


def run_model(prompt: str, model: str) -> Optional[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Produce concise, actionable build steps for the Pantheon of "
                    "Oracles system. Assume continuous integration capabilities "
                    "and avoid actions requiring manual review."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content if resp.choices else None


def offline_plan(contexts: List[Dict[str, str]]) -> str:
    bullets = [
        "Inventory patch files and ensure digests are tracked for change detection.",
        "Use the seeding script to mirror GPT patch oracle definitions into Supabase.",
        "Run FastAPI smoke tests (auth, oracle sync) to keep the API green.",
        "Regenerate router docs for GPT integrations based on latest endpoints.",
        "Open a PR with any automated adjustments discovered during scheduled runs.",
    ]
    patch_info = "\n".join(f"- {ctx['path']} (sha256={ctx['digest']})" for ctx in contexts)
    return (
        "Autonomous planner executed without OpenAI connectivity. "
        "Default maintenance backlog:\n\n"
        + "\n".join(f"{idx+1}. {item}" for idx, item in enumerate(bullets))
        + ("\n\nTracked patch inputs:\n" + patch_info if patch_info else "")
    )


def load_state() -> Dict[str, str]:
    """Load the last recorded patch digests (best effort)."""
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):  # pragma: no cover - resilience only
        return {}


def save_state(digests: Dict[str, str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(digests, indent=2), encoding="utf-8")


def summarize_changes(previous: Dict[str, str], contexts: List[Dict[str, str]]) -> tuple[list[str], Dict[str, str]]:
    current = {ctx["path"]: ctx["digest"] for ctx in contexts}
    changes: list[str] = []
    for path, digest in current.items():
        prior = previous.get(path)
        if prior is None:
            changes.append(f"+ {path} (new)")
        elif prior != digest:
            changes.append(f"* {path} (updated)")
    for path in previous:
        if path not in current:
            changes.append(f"- {path} (missing)")
    return changes, current


def parse_tasks(plan: str) -> list[dict[str, str]]:
    """Extract structured tasks from a textual plan.

    The heuristic captures common numbered lists ("1. ..." or "1) ...") as well
    as dash bullets. Each task is preserved as a simple summary string.
    """

    tasks: list[dict[str, str]] = []
    for line in plan.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^(?:-\s+)?(?P<idx>\d+)[).:-]?\s+(?P<task>.+)$", stripped)
        if match:
            tasks.append(
                {
                    "order": int(match.group("idx")),
                    "summary": match.group("task").strip(),
                    "raw": stripped,
                }
            )
            continue
        if stripped.startswith("- "):
            tasks.append({"order": len(tasks) + 1, "summary": stripped[2:], "raw": stripped})
    return tasks


def write_report(
    body: str,
    contexts: List[Dict[str, str]],
    output_dir: Path,
    changes: List[str],
    supabase_log: Optional[List[str]] = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    report_path = output_dir / f"autonomous-plan-{timestamp}.md"
    header = "# Pantheon Autonomous Builder Report\n\n"
    meta = [
        f"Generated: {timestamp}",
        f"OpenAI enabled: {'OPENAI_API_KEY' in os.environ}",
        "\n## Patch Digests",
    ]
    for ctx in contexts:
        meta.append(f"- {ctx['path']}: {ctx['digest']}")
    if changes:
        meta.append("\n## Patch Changes")
        meta.extend(f"- {change}" for change in changes)
    if supabase_log:
        meta.append("\n## Supabase Sync")
        meta.extend(f"- {line}" for line in supabase_log)
    content = header + "\n".join(meta) + "\n\n## Plan\n\n" + body + "\n"
    report_path.write_text(content, encoding="utf-8")
    # Keep an easy-to-read latest report for operators.
    latest_text = output_dir.parent / "last_report.md"
    latest_json = output_dir.parent / "last_report.json"
    latest_text.write_text(content, encoding="utf-8")

    artifact = {
        "generated": timestamp,
        "openai_enabled": "OPENAI_API_KEY" in os.environ,
        "patches": contexts,
        "changes": changes,
        "supabase_sync": supabase_log or [],
        "plan_text": body,
        "tasks": parse_tasks(body),
        "report_path": str(report_path),
    }
    json_payload = json.dumps(artifact, indent=2)
    (output_dir / f"autonomous-plan-{timestamp}.json").write_text(
        json_payload, encoding="utf-8"
    )
    latest_json.write_text(json_payload, encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Pantheon autonomous builder")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use for planning",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=20000,
        help="Number of characters to include from each patch file",
    )
    parser.add_argument(
        "--workflow-mode",
        action="store_true",
        help="Write outputs to autonomous/outputs for CI runs",
    )
    parser.add_argument(
        "--patch-glob",
        default=DEFAULT_PATCH_GLOB,
        help="Glob used to discover GPT patch files (default: 'Patches *.JSON')",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously poll patch files and regenerate reports when they change",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Seconds to wait between checks in watch mode",
    )
    parser.add_argument(
        "--sync-supabase",
        action="store_true",
        help=(
            "Upsert oracle definitions from discovered patch files into Supabase "
            "when SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set"
        ),
    )
    args = parser.parse_args()
    previous_state = load_state()

    def run_once(prior_state: Dict[str, str]) -> Dict[str, str]:
        contexts = gather_context(args.preview_limit, args.patch_glob)
        prompt = build_prompt(contexts)
        model_response = run_model(prompt, args.model)
        plan = model_response or offline_plan(contexts)

        changes, new_state = summarize_changes(prior_state, contexts)

        target_dir = Path(
            "autonomous/outputs" if args.workflow_mode else "autonomous/reports"
        )
        supabase_log = None
        if args.sync_supabase:
            supabase_log = sync_supabase_oracles([Path(ctx["path"]) for ctx in contexts])
        report_path = write_report(plan, contexts, target_dir, changes, supabase_log)
        save_state(new_state)
        print(f"Report written to {report_path}")
        if changes:
            print("Detected patch changes:\n" + "\n".join(changes))
        if supabase_log:
            print("Supabase sync:\n" + "\n".join(supabase_log))
        return new_state

    previous_state = run_once(previous_state)

    if args.watch:
        print(f"Entering watch mode (interval={args.interval}s)... Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(args.interval)
                previous_state = run_once(previous_state)
        except KeyboardInterrupt:
            print("Watch mode stopped.")


if __name__ == "__main__":
    main()
