# 🔍 GitHub Repo Analyzer

**A full-stack tool that scores any public GitHub repository's health — from 0 to 100 — based on real commit activity, issue responsiveness, and project hygiene.**

[![Tests](https://github.com/muhilvannan16/Repo-Analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/muhilvannan16/Repo-Analyzer/actions/workflows/tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://repo-analyzer-ts4d.onrender.com)

🔗 **[Try it live →](https://repo-analyzer-ts4d.onrender.com)**

---

## What it does

Paste any public GitHub repo URL, and get back a health score out of 100 — broken down across three categories, ten individual signals, all computed from live data pulled directly from GitHub's API.

## How the score works

**🔨 Commits — 33 points**
| Signal | What it measures |
|---|---|
| Recency | How recently the repo was last pushed to |
| Frequency | How consistently commits happen over time (measured via standard deviation of gaps) |
| Momentum | Whether commit activity is accelerating or slowing down recently |

**💬 Issues — 33 points**
| Signal | What it measures |
|---|---|
| Engagement | Average comments per issue |
| Resolution rate | Share of issues that get genuinely completed, not just closed |
| Time to close | How quickly completed issues get resolved |

**📄 Metadata — 34 points**
| Signal | What it measures |
|---|---|
| Fork ratio | Forks relative to stars, as a signal of real engagement |
| License | Whether the repo has one |
| Recent releases | How recently a formal GitHub Release was published |
| README | Whether one exists |

Repos with too little data for a signal to be meaningful (e.g. very few stars, very few commits) get a neutral score for that signal rather than being unfairly penalized — see the full scoring logic in [`core/scoring.py`](./core/scoring.py).

## Tech stack

- **Backend:** Python, FastAPI, SQLite (1-hour result caching)
- **Frontend:** HTML, CSS, and vanilla JavaScript — no framework
- **Testing:** pytest, 82 tests covering scoring logic, caching, and API endpoints
- **CI/CD:** GitHub Actions (automated tests + Claude-powered PR review)
- **Containerization:** Docker
- **Deployment:** Render

## Running it locally

1. Clone the repo and create a virtual environment:

python -m venv venv
venv\Scripts\activate

2. Install dependencies:

pip install -r requirements.txt

3. Set a `GITHUB_TOKEN` environment variable (a fine-grained personal access token with "Public Repositories (read-only)" access works)
4. Run the server:

uvicorn main:app --reload

5. Visit `http://127.0.0.1:8000` in your browser

## Running with Docker

docker build -t repo-analyzer .
docker run -p 8000:8000 -e GITHUB_TOKEN=<your_token> repo-analyzer


Then visit `http://localhost:8000`.

## Running the tests

Tests require a couple of extra dev-only dependencies not included in the base `requirements.txt`:

pip install -r requirements-dev.txt
pytest


## License

Apache License 2.0

## Author

**Muhil** ([@muhilvannan16](https://github.com/muhilvannan16))
