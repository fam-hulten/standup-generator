# Standup Generator

Generate daily standup reports from git commits and memory notes.

## Usage

```bash
python standup.py --repos /path/to/repos --memory-dir /path/to/memory [--days 1]
```

### Arguments

- `--repos` – Comma-separated repo paths (or parent directories containing repos)
- `--memory-dir` – Path to memory files
- `--days` – Days to look back (default: 1)

### Example

```bash
python standup.py --repos /home/robert/projects/shared-workspace --memory-dir /home/robert/.openclaw/workspace/memory
```

## Output Format

```
## 📅 Igår
- commit messages grouped by repo

## 🔨 Idag
- planned tasks from memory files

## ⚠️ Blocker
- any blockers mentioned
```
