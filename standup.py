#!/usr/bin/env python3
"""
Standup Generator - Generates standup reports from git commits and memory files.
Usage: python standup.py --since=YYYY-MM-DD [--memory-dir ~/.openclaw/workspace/memory/]
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_MEMORY_DIR = os.path.expanduser("~/.openclaw/workspace/memory/")

# Default repos for Lilly (gateway container)
LILLY_REPOS = [
    "/home/johanna/.openclaw/repos/lilly-ops",
    "/home/johanna/.openclaw/repos/studywise-workspace",
    "/home/johanna/.openclaw/repos/shared-workspace",
    "/home/johanna/.openclaw/repos/openclaw-infrastructure",
]

# Default repos for Robert (WSL)
ROBERT_REPOS = [
    "~/projects/studywise-api",
    "~/projects/shared-workspace",
    "~/projects/grocy-discord-bot",
]

# Try to auto-detect environment
if os.path.exists("/home/johanna/.openclaw/repos"):
    DEFAULT_REPOS = LILLY_REPOS
else:
    DEFAULT_REPOS = ROBERT_REPOS

# Worktree patterns for auto-discovery
WORKTREE_PATTERNS = {
    "studywise-api": "~/projects/studywise-api-*",
}


def get_commits(repo_path: str, since: str) -> list[tuple[str, str]]:
    """Get commits since given date from repo. Returns list of (repo_name, commit_message)."""
    repo_name = os.path.basename(os.path.abspath(os.path.expanduser(repo_path)))
    commits = []
    
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--format=%s"],
            cwd=os.path.expanduser(repo_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line:
                    commits.append((repo_name, line))
    except Exception as e:
        print(f"Warning: Could not read {repo_path}: {e}", file=sys.stderr)
    
    return commits


def discover_worktrees(repo_name: str, pattern: str) -> list[str]:
    """Discover worktrees matching pattern. Returns list of worktree paths."""
    import glob
    worktrees = []
    expanded = os.path.expanduser(pattern)
    for path in glob.glob(expanded):
        if os.path.isdir(path):
            worktrees.append(path)
    return worktrees


def get_memory_notes(memory_dir: str, since: str) -> str:
    """Extract notes from memory file for given date."""
    memory_path = Path(memory_dir) / f"{since}.md"
    if not memory_path.exists():
        return ""
    
    try:
        content = memory_path.read_text()
        # Extract sections (lines starting with ## or ###)
        lines = []
        for line in content.split("\n"):
            if line.startswith("##"):
                lines.append(line.strip())
        return "\n".join(lines[:10])  # Limit to first 10 sections
    except Exception as e:
        print(f"Warning: Could not read {memory_path}: {e}", file=sys.stderr)
        return ""


def format_report(commits: list[tuple[str, str]], memory_notes: str, since: str) -> str:
    """Format the standup report as Discord-friendly markdown."""
    yesterday = datetime.strptime(since, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    report = f"""📅 **Igår ({yesterday}):**

"""
    
    if commits:
        # Group by repo
        by_repo = {}
        for repo, msg in commits:
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(msg)
        
        for repo, messages in by_repo.items():
            for msg in messages[:5]:  # Max 5 per repo
                report += f"- [{repo}] {msg}\n"
    else:
        report += "- Inga commits hittade\n"
    
    report += "\n🔨 **Idag:**\n\n"
    report += "- Fortsätt med pågående arbete\n"
    
    report += "\n⚠️ **Blockers:**\n"
    report += "- Inga kända\n"
    
    if memory_notes:
        report += f"\n---\n**Anteckningar från igår:**\n{memory_notes}"
    
    # Truncate if too long
    if len(report) > 500:
        report = report[:497] + "..."
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate standup reports for Discord")
    parser.add_argument("--since", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR, help="Memory files directory")
    parser.add_argument("--repos", nargs="+", default=DEFAULT_REPOS, help="Repos to scan")
    parser.add_argument("--worktrees", action="store_true", help="Auto-discover worktrees for default repos")
    
    args = parser.parse_args()
    
    all_commits = []
    repos_to_scan = list(args.repos)
    
    # Auto-discover worktrees if requested
    if args.worktrees:
        for repo_name, pattern in WORKTREE_PATTERNS.items():
            worktrees = discover_worktrees(repo_name, pattern)
            repos_to_scan.extend(worktrees)
    
    for repo in repos_to_scan:
        commits = get_commits(repo, args.since)
        all_commits.extend(commits)
    
    memory_notes = get_memory_notes(args.memory_dir, args.since)
    
    report = format_report(all_commits, memory_notes, args.since)
    print(report)


if __name__ == "__main__":
    main()
