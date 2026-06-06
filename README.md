# Hedge Fund Healthcare Jobs Monitor

Codex skill for collecting active buy-side healthcare analyst recruiting leads across Xiaohongshu, LinkedIn, WeChat public-account articles, and specialist recruiter websites.

## What It Does

- Searches hedge fund, asset-management, family-office, and secondary-market healthcare analyst recruiting posts.
- Prioritizes Shanghai first, then Singapore, then Hong Kong.
- Keeps LinkedIn jobs only when they are visibly active or accepting applications.
- Removes stopped, closed, expired, or no-longer-accepting postings.
- Generates recent-month PDF or HTML reports with clickable source buttons.
- Supports the trigger phrase `我要找工作`.

## Included Files

- `SKILL.md` - skill instructions and routing rules.
- `agents/openai.yaml` - default agent prompt.
- `scripts/monitor_jobs.py` - query generation, filtering, sorting, and report formatting helper.

## Privacy

This public package includes only the reusable skill instructions, agent prompt, and helper script.

## Validate

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## Example

```bash
python3 scripts/monitor_jobs.py --queries
python3 scripts/monitor_jobs.py --format-pdf < findings.json
```
