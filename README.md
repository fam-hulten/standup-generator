# Standup Generator

Genererar standup-rapporter för Discord från git commits och memory-filer.

## Användning

```bash
python3 standup.py --since=YYYY-MM-DD
```

## Exempel

```bash
python3 standup.py --since=2026-04-04
```

## Output

```markdown
## 📅 Igår (2026-04-04)

- [studywise-api] Fixed bug in CLI handler
- [shared-workspace] Added documentation

## 🔨 Idag

- Continue work on...

## ⚠️ Blocker

- Inga kända
```

## Installation

Klona och kör direkt:

```bash
git clone https://github.com/fam-hulten/standup-generator.git
cd standup-generator
python3 standup.py --since=$(date -v-1d +%Y-%m-%d)
```

## Konfiguration

Redigera `DEFAULT_REPOS` och `DEFAULT_MEMORY_DIR` i `standup.py` för att anpassa.
