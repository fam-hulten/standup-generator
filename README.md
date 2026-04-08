# Standup Generator

Generate daily standup reports from git commits and memory notes.

## Usage

```bash
# Auto-discover everything (recommended!)
python3 standup.py --auto

# With explicit paths
python3 standup.py --repos ~/projects --memory-dir ~/.openclaw/workspace/memory/

# Custom days back
python3 standup.py --auto --days 3
```

## Arguments

- `--auto` – Auto-discover repos and memory directory
- `--repos` – Comma-separated repo paths (or parent dirs containing repos)
- `--memory-dir` – Path to memory files
- `--days` – Days to look back (default: 1)

## Auto-Discovery

When using `--auto`:
- **Lilly (gateway container)**: Scans `/home/johanna/.openclaw/repos/`
- **Robert (WSL)**: Scans `~/projects/`

## Output Format

```markdown
## 📅 Igår (7 april)

### standup-generator
- Add Swedish date formatting
- Add standup generator CLI

## 🔨 Idag

- Fortsätt med pågående arbete baserat på gårdagens commits.

## ⚠️ Blocker

- Inga blocker just nu.
```

## Installation

```bash
git clone https://github.com/fam-hulten/standup-generator.git
cd standup-generator
python3 standup.py --auto
```
