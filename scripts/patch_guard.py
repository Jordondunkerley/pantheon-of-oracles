"""
Pantheon Patch Guard

Continuously inspects local patch artifacts (diff files) to determine whether
instructions still need to be applied, are already present in the codebase, or
have merge conflicts. When provided with a GitHub token, it maintains a
persistent tracking issue summarizing the current patch status so automation and
maintainers can react without manual prompting.

The CLI supports optional failure gates (for CI enforcement) and allows disabling
remote issue management when a simple local status check is desired.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import requests


ISSUE_TITLE = "Pantheon Patch Guard"


@dataclass
class PatchStatus:
    path: Path
    status: str
    message: str


def find_diff_files(root: Path) -> List[Path]:
    patterns = ["*.diff", "**/*.diff"]
    files: List[Path] = []
    seen = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            resolved = path.resolve()
            if resolved in seen or not path.is_file():
                continue
            seen.add(resolved)
            files.append(path)
    files.sort(key=lambda p: str(p))
    return files


def _run_git_apply(args: List[str], patch_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "apply", *args, str(patch_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def inspect_patch(patch_path: Path) -> PatchStatus:
    """Classify whether a patch can be applied, is already present, or conflicts."""
    forward = _run_git_apply(["--check"], patch_path)
    if forward.returncode == 0:
        return PatchStatus(
            path=patch_path,
            status="pending",
            message="Patch applies cleanly; instructions likely not implemented yet.",
        )

    reverse = _run_git_apply(["--reverse", "--check"], patch_path)
    if reverse.returncode == 0:
        return PatchStatus(
            path=patch_path,
            status="applied",
            message="Patch appears already present in the codebase (reverse apply succeeds).",
        )

    detail = forward.stderr.strip() or reverse.stderr.strip() or "Patch cannot be applied automatically."
    return PatchStatus(path=patch_path, status="conflict", message=detail)


def summarize_statuses(statuses: Iterable[PatchStatus]) -> str:
    rows = []
    for status in statuses:
        cleaned = status.message.replace("\n", " ")
        rows.append(f"- **{status.path}** — `{status.status}` — {cleaned}")
    return "\n".join(rows) if rows else "- No patch diff files found"


def combined_signature(statuses: Iterable[PatchStatus]) -> str:
    digest = hashlib.sha256()
    for status in statuses:
        digest.update(str(status.path).encode())
        digest.update(status.status.encode())
        digest.update(status.message.encode())
        digest.update(status.path.read_bytes())
    return digest.hexdigest()


def format_issue_body(statuses: List[PatchStatus], signature: str) -> str:
    content = summarize_statuses(statuses)
    return textwrap.dedent(
        f"""
        # Pantheon Patch Guard

        Patch diff status (auto-scanned):
        {content}

        <!-- signature:{signature} -->
        """
    ).strip() + "\n"


def get_repo_slug() -> Optional[str]:
    slug = os.getenv("GITHUB_REPOSITORY")
    if slug:
        return slug
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    if remote_url.startswith("git@"):
        parts = remote_url.split(":", 1)[-1]
    elif remote_url.startswith("https://"):
        parts = remote_url.split("github.com/", 1)[-1]
    else:
        return None
    return parts


def extract_signature(body: str) -> Optional[str]:
    marker = "signature:"
    if marker not in body:
        return None
    start = body.find(marker) + len(marker)
    maybe = body[start : start + 64]
    return maybe if len(maybe) == 64 else None


def ensure_issue(token: str, repo: str, body: str, signature: str) -> None:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})

    search_resp = session.get(
        "https://api.github.com/search/issues",
        params={"q": f"repo:{repo} type:issue in:title \"{ISSUE_TITLE}\""},
        timeout=30,
    )
    search_resp.raise_for_status()
    items = search_resp.json().get("items", [])
    issue = items[0] if items else None

    if issue:
        issue_number = issue["number"]
        existing_body = issue.get("body") or ""
        if extract_signature(existing_body) == signature:
            print("Patch guard issue already up to date.")
            return
        print("Updating patch guard issue with new status.")
        session.patch(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}",
            json={"body": body, "state": "open"},
            timeout=30,
        ).raise_for_status()
        session.post(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
            json={"body": "Patch status changed. Guard refreshed."},
            timeout=30,
        ).raise_for_status()
    else:
        print("Creating patch guard issue.")
        create_resp = session.post(
            f"https://api.github.com/repos/{repo}/issues",
            json={"title": ISSUE_TITLE, "body": body},
            timeout=30,
        )
        create_resp.raise_for_status()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pantheon patch diff inspector")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory to scan for .diff artifacts (default: current working directory).",
    )
    parser.add_argument(
        "--fail-on",
        action="append",
        choices=["pending", "applied", "conflict"],
        default=[],
        help="Exit with status 1 if any patch has a matching status. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--no-issue",
        action="store_true",
        help="Skip creating/updating the GitHub tracking issue even when a token is provided.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    diffs = find_diff_files(args.root)
    statuses = [inspect_patch(path) for path in diffs]
    signature = combined_signature(statuses)
    issue_body = format_issue_body(statuses, signature)

    print(issue_body)

    exit_code = 0
    fail_set = set(args.fail_on)
    if fail_set:
        failing = [s for s in statuses if s.status in fail_set]
        if failing:
            print(
                "Failing due to statuses: "
                + ", ".join(sorted({s.status for s in failing}))
                + f" ({len(failing)} patch(es) matched)."
            )
            exit_code = 1

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not provided; skipping issue update.")
    elif args.no_issue:
        print("Issue update disabled via --no-issue; skipping remote sync.")
    else:
        repo = get_repo_slug()
        if not repo:
            print("Could not determine repository slug; aborting issue update.")
            exit_code = max(exit_code, 1)
        else:
            ensure_issue(token=token, repo=repo, body=issue_body, signature=signature)

    print("Patch guard run complete.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
