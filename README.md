# CE-I Newsletter

Automated Python news-digest pipelines that collect articles from multiple sources, summarize them locally, and deliver topic-specific email digests.

## What it does

The repository contains separate workflows for general news, international news, Texas news, and curated topics. Each pipeline keeps a record of previously processed URLs to reduce duplicate coverage.

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`
- GitHub Actions secrets required by the email-sending configuration

## Run locally

```bash
python -m pip install -r requirements.txt
python main.py
```

Use the corresponding `*_main.py` script for a specific digest. Review configuration and email credentials before running.

## Automation

GitHub Actions schedules the digest workflows and also allows manual runs from the Actions tab.

## Notes

Generated URL-history files are application state. Do not commit credentials; use repository secrets for automated runs.
