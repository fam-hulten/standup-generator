# Standup Generator

Genererar standup-rapporter för Discord från git commits och memory-filer.

## Användning

```bash
# Standard: scanna default repos
python3 standup.py --since=2026-04-05

# Med worktree auto-discovery (Robert's miljö)
python3 standup.py --since=2026-04-05 --worktrees

# Med egna repos (Lilly's miljö)
python3 standup.py --since=2026-04-05 \
  --repos /home/johanna/.openclaw/repos/lilly-ops \
          /home/johanna/.openclaw/repos/studywise-workspace \
          /home/johanna/.openclaw/repos/shared-workspace \
          /home/johanna/.openclaw/repos/openclaw-infrastructure \
  --memory-dir /home/johanna/.openclaw/workspace/memory/
```

## Output

```markdown
📅 **Igår (2026-04-05):**

- [repo] Commit message
- ...

🔨 **Idag:**

- Fortsätt med pågående arbete

⚠️ **Blockers:**

- Inga kända
```

## Auto-discovery

Verktyget auto-detectar miljö:
- Lilly (gateway container): `/home/johanna/.openclaw/repos/`
- Robert (WSL): `~/projects/`

Worktree scanning med `--worktrees` hittar:
- `studywise-api-*` worktrees i `~/projects/`

## Installation

```bash
git clone https://github.com/fam-hulten/standup-generator.git
cd standup-generator
python3 standup.py --since=$(date +%Y-%m-%d)
```

## Konfiguration

Redigera `DEFAULT_REPOS` i `standup.py` för att anpassa.
