# GitHub Repo Analyzer

A full-stack tool that computes a 100-point health score for any public GitHub repository, based on real commit activity, issue responsiveness, and project hygiene.

## How it works

Paste a repo URL, and the tool pulls live data from GitHub's REST API and scores it across three categories:

**Commits (33 points)**
- Recency — how recently the repo was last pushed to
- Frequency — how consistently commits happen over time
- Momentum — whether commit activity is accelerating or slowing down

**Issues (33 points)**
- Engagement — average comments per issue
- Resolution rate — share of issues that get properly completed
- Time to close — how quickly completed issues get resolved

**Metadata (34 points)**
- Fork ratio — forks relative to stars, as a signal of real engagement
- License — whether the repo has one
- Recent releases — how recently a formal release was published
- README — whether one exists

## Tech stack

- **Backend:** Python, FastAPI, SQLite (1-hour result caching)
- **Frontend:** HTML, CSS, and vanilla JavaScript — no framework
- **Data source:** GitHub REST API

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

## License

Apache License 2.0
