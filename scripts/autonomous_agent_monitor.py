"""
Pantheon Autonomous Build Monitor

This script provides a lightweight background monitor that inspects the
local patch and sync files that guide Pantheon of Oracles development. When
run with a GitHub token, it will ensure a persistent tracking issue exists
and keep it updated with the latest patch file signatures. The goal is to
facilitate continuous awareness of backend GPT patch instructions so that
scheduled automation (via GitHub Actions) can react to any changes without
human prompting.
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import sys
import textwrap

import requests


@dataclass
class PatchSignature:
    path: Path
    sha256: str
    size: int

    @classmethod
    def from_path(cls, path: Path) -> "PatchSignature":
        data = path.read_bytes()
        return cls(path=path, sha256=hashlib.sha256(data).hexdigest(), size=len(data))


def find_patch_files(root: Path) -> List[Path]:
    """Return a deterministic list of patch-related files to monitor."""
    patterns = ["*Patch*.JSON", "*patch*.diff", "*patch*.json", "*patches*.json"]
    results: List[Path] = []
    for pattern in patterns:
        results.extend(root.glob(pattern))
        results.extend(root.glob(f"**/{pattern}"))
    # Deduplicate while preserving order
    seen = set()
    unique: List[Path] = []
    for path in results:
        resolved = path.resolve()
        if resolved not in seen and path.is_file():
            seen.add(resolved)
            unique.append(path)
    unique.sort(key=lambda p: str(p))
    return unique


def collect_signatures(paths: Iterable[Path]) -> List[PatchSignature]:
    return [PatchSignature.from_path(path) for path in paths]


def combined_hash(signatures: Iterable[PatchSignature]) -> str:
    digest = hashlib.sha256()
    for sig in signatures:
        digest.update(sig.sha256.encode())
        digest.update(str(sig.size).encode())
        digest.update(str(sig.path).encode())
    return digest.hexdigest()


def format_issue_body(signatures: List[PatchSignature], signature_hash: str) -> str:
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    rows = [f"- **{sig.path}** — {sig.size} bytes — `{sig.sha256}`" for sig in signatures]
    content = "\n".join(rows) if rows else "- No patch files detected"
    return textwrap.dedent(
        f"""
        # Pantheon Autonomous Build Monitor

        Last scan: {now.isoformat()}

        Patch signatures (size and SHA-256):
        {content}

        <!-- signature:{signature_hash} -->
        """
    ).strip() + "\n"


ISSUE_TITLE = "Pantheon Autonomous Build Monitor"
SIGNATURE_PATTERN = re.compile(r"signature:([a-f0-9]{64})")


def extract_signature(body: str) -> Optional[str]:
    match = SIGNATURE_PATTERN.search(body)
    return match.group(1) if match else None


def get_repo_slug() -> Optional[str]:
    slug = os.getenv("GITHUB_REPOSITORY")
    if slug:
        return slug
    # Attempt to infer from git config when running locally
    try:
        import subprocess

        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], stderr=subprocess.DEVNULL
        ).decode().strip()
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        if remote_url.startswith("git@"):
            parts = remote_url.split(":", 1)[-1]
        elif remote_url.startswith("https://"):
            parts = remote_url.split("github.com/", 1)[-1]
        else:
            return None
        return parts
    except Exception:
        return None


def ensure_issue(token: str, repo: str, body: str, signature_hash: str) -> None:
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
        recorded_signature = extract_signature(existing_body)
        if recorded_signature == signature_hash:
            print("No patch changes detected; issue already up to date.")
            return
        print("Updating existing monitor issue with new signature.")
        session.patch(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}",
            json={"body": body, "state": "open"},
            timeout=30,
        ).raise_for_status()
        session.post(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
            json={"body": "Detected new patch signatures. Monitor refreshed."},
            timeout=30,
        ).raise_for_status()
    else:
        print("Creating monitor issue for the first time.")
        create_resp = session.post(
            f"https://api.github.com/repos/{repo}/issues",
            json={"title": ISSUE_TITLE, "body": body},
            timeout=30,
        )
        create_resp.raise_for_status()


def main() -> int:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not provided; skipping remote monitoring.")
        return 0

    repo = get_repo_slug()
    if not repo:
        print("Repository slug could not be determined; aborting monitor run.")
        return 1

    patches = find_patch_files(Path("."))
    signatures = collect_signatures(patches)
    signature_hash = combined_hash(signatures)
    issue_body = format_issue_body(signatures, signature_hash)

    ensure_issue(token=token, repo=repo, body=issue_body, signature_hash=signature_hash)
    print("Monitor run complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
