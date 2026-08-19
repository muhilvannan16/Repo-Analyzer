# 🔍 GitHub Repo Analyzer — Automated Repository Health Scoring

**GitHub Repo Analyzer** is a full-stack tool that computes a 0–100 health score for any public GitHub repository, based on real commit activity, issue responsiveness, and project hygiene — computed live from GitHub's own API, not surface-level stats like stars alone.

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

[![Tests](https://github.com/muhilvannan16/Repo-Analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/muhilvannan16/Repo-Analyzer/actions/workflows/tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://repo-analyzer-ts4d.onrender.com)

🔗 **[Try it live →](https://repo-analyzer-ts4d.onrender.com)**
⭐ **If you find this project useful or interesting, consider giving it a star — it helps others discover it too.**

---

## ✨ Key Features

- **Ten-Signal Scoring Engine**: Every score is broken into three categories — Commits, Issues, and Metadata — each built from multiple individually-designed signals, not a single generic metric.
- **Real API Data**: Every signal is computed live from GitHub's REST API at request time, not cached surface stats.
- **Fair to Small Projects**: Repos with too little data for a signal to be meaningful (few stars, few commits, no issues) get a neutral score instead of being unfairly penalized.
- **Smart Caching**: Results are cached in SQLite for one hour, so repeat lookups are near-instant without hammering GitHub's rate limit.
- **Fully Tested**: 82 pytest tests cover the scoring engine, caching layer, and every API endpoint.
- **Production-Ready**: Hardened error handling, Docker support, and automated CI/CD with Claude-powered PR review.

---

## 📊 How the Score Works

**🔨 Commits — 33 points**
| Signal | What it measures |
|---|---|
| Recency | How recently the repo was last pushed to |
| Frequency | How consistently commits happen over time |
| Momentum | Whether commit activity is accelerating or slowing down |

**💬 Issues — 33 points**
| Signal | What it measures |
|---|---|
| Engagement | Average comments per issue |
| Resolution rate | Share of issues genuinely completed, not just closed |
| Time to close | How quickly completed issues get resolved |

**📄 Metadata — 34 points**
| Signal | What it measures |
|---|---|
| Fork ratio | Forks relative to stars, as a signal of real engagement |
| License | Whether the repo has one |
| Recent releases | How recently a formal GitHub Release was published |
| README | Whether one exists |

Full scoring logic: [`core/scoring.py`](./core/scoring.py)

---

## 🛠️ Built With

- **Backend**: Python, FastAPI, SQLite (1-hour result caching)
- **Frontend**: Pure HTML5, CSS3, Vanilla JavaScript (ES6+) — no framework
- **Testing**: pytest, 82 tests covering scoring, caching, and API endpoints
- **CI/CD**: GitHub Actions (automated tests + Claude-powered PR review)
- **Containerization**: Docker, non-root user, split runtime/dev dependencies

---

## 🚀 Getting Started

**Run locally:**

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

Set a `GITHUB_TOKEN` environment variable, then:

uvicorn main:app --reload

Visit `http://127.0.0.1:8000`.

**Run with Docker:**

docker build -t repo-analyzer -f docker/Dockerfile .
docker run -p 8000:8000 -e GITHUB_TOKEN=<your_token> repo-analyzer


**Run the tests:**

pip install -r requirements-dev.txt
pytest


---

## 📄 License

Apache License 2.0

---

## 👤 Author

**Muhilvannan Elavazhagan** ([@muhilvannan16](https://github.com/muhilvannan16))
