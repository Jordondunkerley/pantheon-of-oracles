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
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

_openai_spec = importlib.util.find_spec("openai")
OpenAI = importlib.import_module("openai").OpenAI if _openai_spec else None  # type: ignore


DEFAULT_PATCH_GLOB = "Patches *.JSON"

STATE_PATH = Path("autonomous/state.json")


def get_repo_metadata() -> dict[str, str]:
    """Return best-effort git metadata for traceability."""

    def run_git(args: list[str]) -> Optional[str]:
        try:
            return (
                subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
        except Exception:
            return None

    return {
        "commit": run_git(["rev-parse", "HEAD"]) or "unknown",
        "branch": run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        "dirty": "true" if run_git(["status", "--porcelain"]) else "false",
    }


def read_patch(path: Path, limit: int) -> Dict[str, str]:
    """Return text preview and SHA256 digest for a patch file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    preview = text[:limit]
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return {"path": str(path), "digest": digest, "preview": preview}

def find_patch_files(glob_pattern: str) -> list[Path]:
    """Return sorted patch files matching the glob pattern."""

    return sorted(Path(".").glob(glob_pattern))


def load_patch_payload(path: Path) -> Optional[Any]:
    """Best-effort JSON loader that tolerates leading metadata lines."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    decoder = json.JSONDecoder()
    items: list[Any] = []
    cursor = 0
    while cursor < len(text):
        match = re.search(r"[\[{]", text[cursor:])
        if not match:
            break
        start = cursor + match.start()
        try:
            obj, consumed = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            cursor = start + 1
            continue
        items.append(obj)
        cursor = start + consumed

    if not items:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    if len(items) == 1:
        return items[0]
    return items


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
    payload = load_patch_payload(path)
    if payload is None:
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


def validate_patch_files(patch_paths: list[Path]) -> list[str]:
    logs: list[str] = []
    if not patch_paths:
        return ["No patch files discovered; nothing to validate."]

    for path in patch_paths:
        payload = load_patch_payload(path)
        if payload is None:
            logs.append(f"{path}: invalid JSON or unreadable content")
            continue

        patches = maybe_iter(payload)
        if not patches:
            logs.append(f"{path}: JSON did not contain patch objects")
            continue

        patch_entries = 0
        missing_oracle_codes = 0
        for idx, patch in enumerate(patches, start=1):
            if not isinstance(patch, dict):
                continue
            patch_entries += 1
            oracles = maybe_iter(patch.get("oracles", []))
            for oracle_idx, oracle in enumerate(oracles, start=1):
                if not isinstance(oracle, dict):
                    continue
                if not (oracle.get("code") or oracle.get("name")):
                    missing_oracle_codes += 1

        if missing_oracle_codes:
            logs.append(
                f"{path}: {missing_oracle_codes} oracle definition(s) missing code or name"
            )
        else:
            logs.append(f"{path}: loaded {patch_entries} patch entries without oracle ID issues")

    if not logs:
        return ["All patch files passed validation."]
    return logs


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

    try:
        client = create_client(supabase_url, supabase_key)
        merged: dict[str, dict[str, Any]] = {}
        for path in patch_paths:
            merged.update(extract_oracles_from_patch(path))

        if not merged:
            return ["No oracles found in patch files; nothing to sync."]

        for row in merged.values():
            client.table("oracles").upsert(row, on_conflict="code").execute()
    except Exception as exc:  # pragma: no cover - resilience for scheduled runs
        return [f"Supabase sync failed: {exc}"]

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


def run_model(prompt: str, model: str) -> tuple[Optional[str], Optional[str]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None, "OPENAI_API_KEY missing or openai package unavailable; using offline plan."
    try:
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
        return resp.choices[0].message.content if resp.choices else None, None
    except Exception as exc:  # pragma: no cover - resilience for scheduled runs
        return None, f"Model call failed: {exc}"


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


def write_step_summary(lines: list[str]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    try:
        with Path(summary_path).open("a", encoding="utf-8") as fp:
            fp.write("\n".join(lines) + "\n")
    except OSError:
        pass


def write_step_outputs(outputs: dict[str, str]) -> None:
    """Append key/value pairs to GITHUB_OUTPUT when available."""

    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    try:
        with Path(output_path).open("a", encoding="utf-8") as fp:
            for key, value in outputs.items():
                fp.write(f"{key}<<EOF\n{value}\nEOF\n")
    except OSError:
        pass


def write_report(
    body: str,
    contexts: List[Dict[str, str]],
    output_dir: Path,
    changes: List[str],
    supabase_log: Optional[List[str]] = None,
    smoke_log: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    validation_log: Optional[List[str]] = None,
    write_summary: bool = False,
    repo_metadata: Optional[dict[str, str]] = None,
    run_status: Optional[str] = None,
    status_reason: Optional[str] = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    report_path = output_dir / f"autonomous-plan-{timestamp}.md"
    header = "# Pantheon Autonomous Builder Report\n\n"
    meta = [
        f"Generated: {timestamp}",
        f"OpenAI enabled: {'OPENAI_API_KEY' in os.environ}",
        "\n## Repository",
    ]
    if repo_metadata:
        meta.extend(
            [
                f"- Branch: {repo_metadata.get('branch', 'unknown')}",
                f"- Commit: {repo_metadata.get('commit', 'unknown')}",
                f"- Dirty: {repo_metadata.get('dirty', 'unknown')}",
            ]
        )
    else:
        meta.append("- Not a git checkout or git unavailable")
    if run_status:
        meta.append("\n## Run Status")
        meta.append(f"- Status: {run_status}")
        if status_reason:
            meta.append(f"- Reason: {status_reason}")
    meta.append("\n## Patch Digests")
    for ctx in contexts:
        meta.append(f"- {ctx['path']}: {ctx['digest']}")
    if changes:
        meta.append("\n## Patch Changes")
        meta.extend(f"- {change}" for change in changes)
    if validation_log:
        meta.append("\n## Patch Validation")
        meta.extend(f"- {line}" for line in validation_log)
    if supabase_log:
        meta.append("\n## Supabase Sync")
        meta.extend(f"- {line}" for line in supabase_log)
    if smoke_log:
        meta.append("\n## Smoke Tests")
        meta.extend(f"- {line}" for line in smoke_log)
    if warnings:
        meta.append("\n## Warnings")
        meta.extend(f"- {line}" for line in warnings)
    content = header + "\n".join(meta) + "\n\n## Plan\n\n" + body + "\n"
    report_path.write_text(content, encoding="utf-8")
    # Keep an easy-to-read latest report for operators.
    latest_text = output_dir.parent / "last_report.md"
    latest_json = output_dir.parent / "last_report.json"
    latest_text.write_text(content, encoding="utf-8")

    artifact = {
        "generated": timestamp,
        "openai_enabled": "OPENAI_API_KEY" in os.environ,
        "repository": repo_metadata or {},
        "status": run_status or "unknown",
        "status_reason": status_reason or "",
        "patches": contexts,
        "changes": changes,
        "validation": validation_log or [],
        "supabase_sync": supabase_log or [],
        "smoke_tests": smoke_log or [],
        "warnings": warnings or [],
        "plan_text": body,
        "tasks": parse_tasks(body),
        "report_path": str(report_path),
    }
    json_payload = json.dumps(artifact, indent=2)
    (output_dir / f"autonomous-plan-{timestamp}.json").write_text(
        json_payload, encoding="utf-8"
    )
    latest_json.write_text(json_payload, encoding="utf-8")

    if write_summary:
        summary_lines = [
            "# Pantheon Autonomous Builder",
            f"- Generated: {timestamp}",
            f"- OpenAI enabled: {'OPENAI_API_KEY' in os.environ}",
        ]
        if run_status:
            summary_lines.append("- Run status:")
            summary_lines.append(
                f"  - {run_status}{f' ({status_reason})' if status_reason else ''}"
            )
        if changes:
            summary_lines.append("- Patch changes:")
            summary_lines.extend(f"  - {change}" for change in changes)
        else:
            summary_lines.append("- Patch changes: none detected")
        if repo_metadata:
            summary_lines.append("- Repository:")
            summary_lines.append(f"  - Branch: {repo_metadata.get('branch', 'unknown')}")
            summary_lines.append(f"  - Commit: {repo_metadata.get('commit', 'unknown')}")
            summary_lines.append(f"  - Dirty: {repo_metadata.get('dirty', 'unknown')}")
        if validation_log:
            summary_lines.append("- Patch validation:")
            summary_lines.extend(f"  - {line}" for line in validation_log)
        if supabase_log:
            summary_lines.append("- Supabase sync:")
            summary_lines.extend(f"  - {line}" for line in supabase_log)
        if smoke_log:
            summary_lines.append("- Smoke tests:")
            summary_lines.extend(f"  - {line}" for line in smoke_log)
        if warnings:
            summary_lines.append("- Warnings:")
            summary_lines.extend(f"  - {line}" for line in warnings)
        summary_lines.append(f"- Report: {report_path}")
        write_step_summary(summary_lines)
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
        "--only-on-change",
        action="store_true",
        help=(
            "Skip report generation when no patch digest changes are detected after the first baseline run"
        ),
    )
    parser.add_argument(
        "--validate-patches",
        action="store_true",
        help=(
            "Validate patch files for JSON correctness and required metadata; results are captured in reports"
        ),
    )
    parser.add_argument(
        "--require-patches",
        action="store_true",
        help=(
            "Exit non-zero when no patch files are discovered for the configured glob"
        ),
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help=(
            "Exit non-zero when warnings are generated (e.g., OpenAI missing, Supabase or smoke-test issues)"
        ),
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
    parser.add_argument(
        "--smoke-tests",
        action="store_true",
        help="Run lightweight FastAPI smoke checks against the configured base URL",
    )
    parser.add_argument(
        "--smoke-base-url",
        default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"),
        help="Base URL used for smoke tests (default: http://localhost:8000 or SMOKE_BASE_URL)",
    )
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Write a compact summary to GITHUB_STEP_SUMMARY when available (for GitHub Actions)",
    )
    parser.add_argument(
        "--write-outputs",
        action="store_true",
        help="Write run metadata (status, reason, report path) to GITHUB_OUTPUT when available",
    )
    parser.add_argument(
        "--fail-on-validation-errors",
        action="store_true",
        help="Exit with status 1 when validation detects malformed patch files",
    )
    args = parser.parse_args()
    previous_state = load_state()
    validation_errors_detected = False
    last_warnings: list[str] = []
    last_run_status: str = "unknown"
    last_status_reason: Optional[str] = None
    def run_smoke_tests(base_url: str) -> list[str]:
        url = base_url.rstrip("/") + "/healthz"
        try:
            response = httpx.get(url, timeout=5)
            summary = f"GET {url} -> {response.status_code}"
            try:
                payload = response.json()
                details = f"status={payload.get('status')}, service={payload.get('service')}"
            except (ValueError, TypeError):
                details = "non-JSON response"
            return [summary, details]
        except Exception as exc:
            return [f"Smoke test failed for {url}: {exc}"]

    def run_once(prior_state: Dict[str, str]) -> Dict[str, str]:
        nonlocal validation_errors_detected, last_run_status, last_status_reason
        validation_errors_detected = False
        last_warnings.clear()
        last_run_status = "ok"
        last_status_reason = "no warnings detected"
        repo_metadata = get_repo_metadata()
        contexts = gather_context(args.preview_limit, args.patch_glob)
        warnings: list[str] = []

        def record_warnings() -> None:
            last_warnings.clear()
            last_warnings.extend(warnings)

        def record_outputs(
            status: str,
            reason: Optional[str],
            report_path: Optional[Path],
            changes: list[str],
            validation_log: Optional[list[str]] = None,
        ) -> None:
            if not args.write_outputs:
                return

            outputs: dict[str, str] = {
                "run_status": status,
                "changes_detected": "true" if changes else "false",
            }
            if reason:
                outputs["status_reason"] = reason
            if repo_metadata:
                outputs.update(
                    {
                        "repo_branch": repo_metadata.get("branch", "unknown"),
                        "repo_commit": repo_metadata.get("commit", "unknown"),
                        "repo_dirty": repo_metadata.get("dirty", "unknown"),
                    }
                )
            if contexts:
                outputs["patch_digests"] = "\n".join(
                    f"{ctx['path']}={ctx['digest']}" for ctx in contexts
                )
            if changes:
                outputs["patch_changes"] = "\n".join(changes)
            if report_path:
                outputs["report_path"] = str(report_path)
            if warnings:
                outputs["warnings"] = "\n".join(warnings)
            if validation_log:
                outputs["validation"] = "\n".join(validation_log)
            write_step_outputs(outputs)

        if not contexts:
            message = (
                "No patch files found matching "
                f"{args.patch_glob!r}; pass --patch-glob to override"
            )
            warnings.append(message)
            if args.require_patches:
                record_warnings()
                last_run_status = "error"
                last_status_reason = "patch discovery failed"
                record_outputs(last_run_status, last_status_reason, None, [], None)
                print(message)
                if args.write_summary:
                    summary_lines = ["# Pantheon Autonomous Builder", f"- {message}"]
                    if repo_metadata:
                        summary_lines.append("- Repository:")
                        summary_lines.append(
                            f"  - Branch: {repo_metadata.get('branch', 'unknown')}"
                        )
                        summary_lines.append(
                            f"  - Commit: {repo_metadata.get('commit', 'unknown')}"
                        )
                        summary_lines.append(
                            f"  - Dirty: {repo_metadata.get('dirty', 'unknown')}"
                        )
                    summary_lines.append("- Run status:")
                    summary_lines.append("  - error (patch discovery failed)")
                    summary_lines.append("- Exiting because --require-patches is set")
                    write_step_summary(summary_lines)
                raise SystemExit(message)
        prompt = build_prompt(contexts)
        model_response, model_warning = run_model(prompt, args.model)
        if model_warning:
            warnings.append(model_warning)
        plan = model_response or offline_plan(contexts)

        changes, new_state = summarize_changes(prior_state, contexts)

        validation_log = None
        if args.validate_patches:
            validation_log = validate_patch_files([Path(ctx["path"]) for ctx in contexts])
            if validation_log:
                issue_lines = [
                    line for line in validation_log if re.search(r"invalid|missing", line, re.IGNORECASE)
                ]
                warnings.extend(issue_lines)
                if issue_lines:
                    validation_errors_detected = True

        if args.only_on_change and prior_state and not changes:
            message = "No patch changes detected; skipping report because --only-on-change is set."
            print(message)
            if validation_log:
                print("Patch validation:\n" + "\n".join(validation_log))
            if warnings:
                print("Warnings:\n" + "\n".join(warnings))
            last_run_status = "skipped"
            last_status_reason = "no patch changes detected"
            record_outputs(last_run_status, last_status_reason, None, changes, validation_log)
            if args.write_summary:
                summary_lines = ["# Pantheon Autonomous Builder", "- " + message]
                if repo_metadata:
                    summary_lines.append("- Repository:")
                    summary_lines.append(f"  - Branch: {repo_metadata.get('branch', 'unknown')}")
                    summary_lines.append(f"  - Commit: {repo_metadata.get('commit', 'unknown')}")
                    summary_lines.append(f"  - Dirty: {repo_metadata.get('dirty', 'unknown')}")
                summary_lines.append("- Run status:")
                summary_lines.append(
                    f"  - {last_run_status}{f' ({last_status_reason})' if last_status_reason else ''}"
                )
                if validation_log:
                    summary_lines.append("- Patch validation:")
                    summary_lines.extend(f"  - {line}" for line in validation_log)
                if warnings:
                    summary_lines.append("- Warnings:")
                    summary_lines.extend(f"  - {line}" for line in warnings)
                write_step_summary(summary_lines)
            record_warnings()
            return prior_state

        target_dir = Path(
            "autonomous/outputs" if args.workflow_mode else "autonomous/reports"
        )
        supabase_log = None
        smoke_log = None
        if args.sync_supabase:
            supabase_log = sync_supabase_oracles([Path(ctx["path"]) for ctx in contexts])
            if any("failed" in line.lower() for line in supabase_log):
                warnings.extend(supabase_log)
        if args.smoke_tests:
            smoke_log = run_smoke_tests(args.smoke_base_url)
            if any("failed" in line.lower() for line in smoke_log):
                warnings.extend(smoke_log)
        if validation_errors_detected:
            last_run_status = "error"
            last_status_reason = "validation errors detected"
        elif warnings:
            last_run_status = "warning"
            last_status_reason = "warnings present"
        else:
            last_run_status = "ok"
            last_status_reason = "no warnings detected"
        report_path = write_report(
            plan,
            contexts,
            target_dir,
            changes,
            supabase_log,
            smoke_log,
            warnings if warnings else None,
            validation_log,
            write_summary=args.write_summary,
            repo_metadata=repo_metadata,
            run_status=last_run_status,
            status_reason=last_status_reason,
        )
        save_state(new_state)
        print(f"Report written to {report_path}")
        if changes:
            print("Detected patch changes:\n" + "\n".join(changes))
        if supabase_log:
            print("Supabase sync:\n" + "\n".join(supabase_log))
        if smoke_log:
            print("Smoke tests:\n" + "\n".join(smoke_log))
        if warnings:
            print("Warnings:\n" + "\n".join(warnings))
        record_warnings()
        record_outputs(
            last_run_status, last_status_reason, report_path, changes, validation_log
        )
        return new_state

    previous_state = run_once(previous_state)
    if args.fail_on_warnings and last_warnings:
        raise SystemExit(
            "Warnings detected; exiting due to --fail-on-warnings"
        )

    if args.fail_on_validation_errors and validation_errors_detected:
        raise SystemExit(
            "Patch validation errors detected; exiting due to --fail-on-validation-errors"
        )

    if args.watch:
        print(f"Entering watch mode (interval={args.interval}s)... Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(args.interval)
                previous_state = run_once(previous_state)
                if args.fail_on_warnings and last_warnings:
                    raise SystemExit(
                        "Warnings detected; exiting due to --fail-on-warnings"
                    )
                if args.fail_on_validation_errors and validation_errors_detected:
                    raise SystemExit(
                        "Patch validation errors detected; exiting due to --fail-on-validation-errors"
                    )
        except KeyboardInterrupt:
            print("Watch mode stopped.")


if __name__ == "__main__":
    main()
