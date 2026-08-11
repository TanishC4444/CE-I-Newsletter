# CE-I Newsletter

A set of automated Python news-digest pipelines that collect articles, summarize them locally, and deliver topic-specific email newsletters.

## Overview

The repository contains separate workflows for general, international, Texas, and curated news. Each pipeline tracks processed URLs to reduce duplicate coverage and can run through GitHub Actions.

## Features

- Multi-source news collection
- Topic-specific digest pipelines
- Local summarization
- Email delivery
- Processed-URL tracking
- Scheduled and manual GitHub Actions execution

## Prerequisites

- Python 3.10+
- pip
- Dependencies in `requirements.txt`
- Email configuration supplied through GitHub Actions secrets or a local environment

## Installation

```bash
git clone https://github.com/TanishC4444/CE-I-Newsletter.git
cd CE-I-Newsletter
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

## Quick Start

Run the default pipeline:

```bash
python main.py
```

Use the corresponding `*_main.py` script for a specific digest after reviewing its configuration.

## Automation

GitHub Actions can schedule the digest workflows and supports manual runs from the Actions tab.

## Configuration

Keep email credentials and API keys out of source control. Use repository secrets for automated execution and local environment variables for development.

## Project Structure

```text
CE-I-Newsletter/
├── main.py
├── *_main.py
├── requirements.txt
└── generated URL-history/state files
```

## Responsible Use

Respect source websites' terms and rate limits. Generated URL-history files represent application state and should be committed only when intentionally required.

## License

No separate license is currently specified in the repository.

## Support

Use GitHub Issues for bugs and project questions.
