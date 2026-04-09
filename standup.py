#!/usr/bin/env python3

"""Generate a daily standup report from git commits and memory notes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path

PLAN_KEYWORDS = ("idag", "today", "plan", "todo", "next")
BLOCKER_KEYWORDS = ("blocker", "blockers", "hinder", "blocked")
SWEDISH_MONTHS = (
    "januari",
    "februari",
    "mars",
    "april",
    "maj",
    "juni",
    "juli",
    "augusti",
    "september",
    "oktober",
    "november",
    "december",
)


def parse_args() -> argparse.Namespace:
    import os
    
    parser = argparse.ArgumentParser(description="Generate a standup report")
    parser.add_argument(
        "--repos",
        help="Comma-separated repo paths (or parent dirs containing repos). Auto-detected if not specified.",
    )
    parser.add_argument("--memory-dir", help="Path to memory files. Auto-detected if not specified.")
    parser.add_argument(
        "--days", type=int, default=1, help="Days to look back (default: 1)"
    )
    parser.add_argument("--auto", action="store_true", help="Auto-discover repos and memory dir")
    args = parser.parse_args()

    if args.days < 1:
        parser.error("--days must be >= 1")
    
    # Auto-detect if --auto or if args not provided
    if args.auto or not args.repos:
        # Discover repos
        if os.path.exists("/home/johanna/.openclaw/repos"):
            repos_base = "/home/johanna/.openclaw/repos"
        else:
            repos_base = os.path.expanduser("~/projects")
        
        repos = []
        for entry in os.listdir(repos_base):
            path = os.path.join(repos_base, entry)
            if os.path.isdir(path) and is_git_repo(Path(path)):
                repos.append(path)
        args.repos = ",".join(repos)
    
    if args.auto or not args.memory_dir:
        if os.path.exists("/home/johanna/.openclaw/workspace/memory/"):
            args.memory_dir = "/home/johanna/.openclaw/workspace/memory/"
        else:
            args.memory_dir = os.environ.get("STANDUP_MEMORY_DIR", os.path.expanduser("~/.openclaw/workspace/memory/"))
    
    return args


def run_git(args: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def is_git_repo(path: Path) -> bool:
    if not path.is_dir():
        return False
    result = run_git(["rev-parse", "--is-inside-work-tree"], path)
    return result.returncode == 0 and result.stdout.strip() == "true"


def resolve_repos(raw_csv: str) -> list[Path]:
    repos: list[Path] = []

    for raw_entry in raw_csv.split(","):
        entry = raw_entry.strip()
        if not entry:
            continue

        path = Path(entry).expanduser().resolve()
        if is_git_repo(path):
            repos.append(path)
            continue

        if path.is_dir():
            for child in sorted(path.iterdir()):
                if child.is_dir() and is_git_repo(child):
                    repos.append(child)

    unique: list[Path] = []
    seen: set[Path] = set()
    for repo in repos:
        if repo not in seen:
            unique.append(repo)
            seen.add(repo)
    return unique


def get_recent_commits(repo: Path, days: int) -> list[str]:
    result = run_git(
        ["log", f"--since={days}.days", "--no-merges", "--pretty=%s"],
        repo,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git error"
        print(f"Warning: Could not read commits from {repo}: {stderr}", file=sys.stderr)
        return []

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def clean_bullet(text: str) -> str:
    without_prefix = re.sub(r"^[-*]\s+(\[[ xX]\]\s+)?", "", text.strip())
    without_numbering = re.sub(r"^\d+[.)]\s+", "", without_prefix)
    return without_numbering.strip()


def extract_section_items(markdown: str, keywords: tuple[str, ...]) -> list[str]:
    items: list[str] = []
    in_target_section = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()

        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        if heading:
            heading_text = heading.group(1).strip().lower()
            in_target_section = any(keyword in heading_text for keyword in keywords)
            continue

        if not in_target_section or not line:
            continue

        if line.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", line):
            cleaned = clean_bullet(line)
            if cleaned:
                items.append(cleaned)

    return items


def dedupe(items: list[str]) -> list[str]:
    return list(OrderedDict((item, None) for item in items).keys())


def format_swedish_date(date_value: datetime) -> str:
    month_name = SWEDISH_MONTHS[date_value.month - 1]
    return f"{date_value.day} {month_name}"


def collect_memory_data(memory_dir: Path, days: int) -> tuple[list[str], list[str]]:
    if not memory_dir.is_dir():
        return [], []

    cutoff = datetime.now() - timedelta(days=days)
    candidates = sorted(
        memory_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    recent_files = [
        p for p in candidates if datetime.fromtimestamp(p.stat().st_mtime) >= cutoff
    ]
    files_to_scan = recent_files or candidates[:3]

    planned: list[str] = []
    blockers: list[str] = []

    for memory_file in files_to_scan:
        try:
            content = memory_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Warning: Could not read {memory_file}: {exc}", file=sys.stderr)
            continue

        planned.extend(extract_section_items(content, PLAN_KEYWORDS))
        blockers.extend(extract_section_items(content, BLOCKER_KEYWORDS))

    return dedupe(planned), dedupe(blockers)


def format_report(
    commits_by_repo: OrderedDict[str, list[str]],
    planned: list[str],
    blockers: list[str],
    yesterday_label: str,
) -> str:
    lines: list[str] = [f"## 📅 Igår ({yesterday_label})", ""]

    has_commits = any(commits_by_repo.values())
    if has_commits:
        for repo_name, commits in commits_by_repo.items():
            if not commits:
                continue
            lines.append(f"### {repo_name}")
            lines.extend([f"- {commit}" for commit in commits])
            lines.append("")
    else:
        lines.append("- Inga commits hittade.")
        lines.append("")

    lines.append("## 🔨 Idag")
    lines.append("")
    if planned:
        lines.extend([f"- {item}" for item in planned])
    else:
        lines.append("- Fortsätt med pågående arbete baserat på gårdagens commits.")

    lines.append("")
    lines.append("## ⚠️ Blocker")
    lines.append("")
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- Inga blocker just nu.")

    return "\n".join(lines).strip()


def main() -> int:
    args = parse_args()

    repos = resolve_repos(args.repos)
    if not repos:
        print("Error: No valid git repositories found from --repos.", file=sys.stderr)
        return 2

    commits_by_repo: OrderedDict[str, list[str]] = OrderedDict()
    for repo in repos:
        commits_by_repo[repo.name] = get_recent_commits(repo, args.days)

    memory_dir = Path(args.memory_dir).expanduser().resolve()
    planned, blockers = collect_memory_data(memory_dir, args.days)
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_label = format_swedish_date(yesterday)

    print(format_report(commits_by_repo, planned, blockers, yesterday_label))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
