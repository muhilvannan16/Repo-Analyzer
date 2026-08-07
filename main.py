
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core import (
    score_recency,
    score_frequency,
    score_momentum,
    score_fork_ratio,
    score_issue_engagement,
    score_license,
    score_resolution_rate,
    score_time_to_close,
    score_recent_releases,
    score_readme,
    init_db,
    get_cached_repo,
    save_to_cache,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


app = FastAPI()
init_db()  # ensures the table exists before any requests come in

token = os.environ.get("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

class RepoRequest(BaseModel):
    repo_url: str

@app.post("/analyze")
def analyze_repo(request: RepoRequest):
    parts = request.repo_url.rstrip("/").split("/")
    if len(parts) < 2 or not parts[-1] or not parts[-2]:
        raise HTTPException(status_code=400, detail="Invalid repository URL")

    owner = parts[-2]
    repo = parts[-1]
    repo_key = f"{owner}/{repo}"

    cached = get_cached_repo(repo_key)

    if cached is not None:
        metadata = cached["metadata"]
        commits = cached["commits"]
        issues = cached["issues"]
        releases = cached["releases"]
        readme_status = cached["readme_status"]
    else:
        metadata_response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
        if metadata_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        if metadata_response.status_code == 403:
            raise HTTPException(status_code=429, detail="GitHub rate limit exceeded, try again later")
        metadata = metadata_response.json()

        commits_response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/commits", headers=headers)
        if commits_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Commits not found")
        if commits_response.status_code == 403:
            raise HTTPException(status_code=429, detail="GitHub rate limit exceeded, try again later")
        commits = commits_response.json()

        issues_response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/issues?state=all", headers=headers)
        if issues_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Issues not found")
        if issues_response.status_code == 403:
            raise HTTPException(status_code=429, detail="GitHub rate limit exceeded, try again later")
        issues = issues_response.json()

        releases_response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases", headers=headers)
        if releases_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Releases not found")
        if releases_response.status_code == 403:
            raise HTTPException(status_code=429, detail="GitHub rate limit exceeded, try again later")
        releases = releases_response.json()

        readme_response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/readme", headers=headers)
        if readme_response.status_code == 403:
            raise HTTPException(status_code=429, detail="GitHub rate limit exceeded, try again later")
        readme_status = readme_response.status_code

        save_to_cache(repo_key, metadata, commits, issues, releases, readme_status)

    recency_score = score_recency(metadata["pushed_at"])
    frequency_score = score_frequency(commits, metadata["created_at"])
    momentum_score = score_momentum(commits, metadata["created_at"])
    fork_ratio_score = score_fork_ratio(metadata["stargazers_count"], metadata["forks_count"])
    issue_engagement_score = score_issue_engagement(issues)
    license_score = score_license(metadata)
    resolution_rate_score = score_resolution_rate(issues)
    time_to_close_score = score_time_to_close(issues)
    recent_releases_score = score_recent_releases(releases)
    readme_score = score_readme(readme_status)

    total_score = (
        recency_score + frequency_score + momentum_score
        + fork_ratio_score + issue_engagement_score + license_score
        + resolution_rate_score + time_to_close_score
        + recent_releases_score + readme_score
    )

    return {
        "owner": owner,
        "repo": repo,
        "from_cache": cached is not None,
        "total_score": total_score,
        "max_possible": 100,
        "breakdown": {
            "recency": recency_score,
            "frequency": frequency_score,
            "momentum": momentum_score,
            "fork_ratio": fork_ratio_score,
            "issue_engagement": issue_engagement_score,
            "license": license_score,
            "resolution_rate": resolution_rate_score,
            "time_to_close": time_to_close_score,
            "recent_releases": recent_releases_score,
            "readme": readme_score,
        }
    }