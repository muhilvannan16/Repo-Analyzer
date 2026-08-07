from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────

def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _days_ago(n):
    return _iso(datetime.now(timezone.utc) - timedelta(days=n))


def _make_mock_response(status_code, json_data):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


# ── fixtures ─────────────────────────────────────────────────────

FAKE_METADATA = {
    "stargazers_count": 100,
    "forks_count": 20,
    "pushed_at": _days_ago(3),
    "created_at": _days_ago(200),
    "default_branch": "main",
    "license": {"key": "mit"},
}

FAKE_COMMITS = [
    {"commit": {"author": {"date": _days_ago(i)}, "message": f"commit {i}"}}
    for i in range(10)
]

FAKE_ISSUES = [
    {
        "number": 1,
        "comments": 5,
        "state_reason": "completed",
        "created_at": _days_ago(30),
        "closed_at": _days_ago(25),
    },
    {
        "number": 2,
        "comments": 3,
        "created_at": _days_ago(20),
        "closed_at": _days_ago(15),
        "state_reason": "completed",
    },
]

FAKE_RELEASES = [
    {"tag_name": "v1.0", "published_at": _days_ago(30),
     "draft": False, "prerelease": False},
]


def _mock_get_side_effect(url, **kwargs):
    """Route mocked requests.get calls based on URL suffix."""
    if "/commits" in url:
        return _make_mock_response(200, FAKE_COMMITS)
    elif "/issues" in url:
        return _make_mock_response(200, FAKE_ISSUES)
    elif "/releases" in url:
        return _make_mock_response(200, FAKE_RELEASES)
    elif "/readme" in url:
        return _make_mock_response(200, {"content": "base64stuff"})
    else:
        # metadata endpoint (bare /repos/owner/repo)
        return _make_mock_response(200, FAKE_METADATA)


@pytest.fixture()
def client():
    """Create a TestClient with init_db and get_cached_repo patched."""
    with patch("main.init_db"), \
         patch("main.get_cached_repo", return_value=None), \
         patch("main.save_to_cache"):
        from main import app
        with TestClient(app) as c:
            yield c


# ═══════════════════════════════════════════════════════════════
# Successful /analyze call
# ═══════════════════════════════════════════════════════════════

class TestAnalyzeSuccess:
    @patch("main.requests.get", side_effect=_mock_get_side_effect)
    def test_returns_total_and_breakdown(self, mock_get, client):
        resp = client.post("/analyze",
                           json={"repo_url": "https://github.com/owner/repo"})
        assert resp.status_code == 200
        data = resp.json()

        assert data["owner"] == "owner"
        assert data["repo"] == "repo"
        assert isinstance(data["total_score"], int)
        assert 0 <= data["total_score"] <= 100

        expected_keys = {
            "recency", "frequency", "momentum", "fork_ratio",
            "issue_engagement", "license", "resolution_rate",
            "time_to_close", "recent_releases", "readme",
        }
        assert set(data["breakdown"].keys()) == expected_keys

        # Verify total is the sum of all breakdown values
        assert data["total_score"] == sum(data["breakdown"].values())


# ═══════════════════════════════════════════════════════════════
# 400 — malformed URL
# ═══════════════════════════════════════════════════════════════

class TestAnalyze400:
    def test_malformed_url(self, client):
        resp = client.post("/analyze", json={"repo_url": "not-a-url"})
        # The route splits on "/" — "not-a-url" has no "/" so parts[-2]
        # will be empty → 400
        assert resp.status_code == 400
        assert "Invalid" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════
# 404 — repo not found
# ═══════════════════════════════════════════════════════════════

class TestAnalyze404:
    @patch("main.requests.get")
    def test_metadata_404(self, mock_get, client):
        mock_get.return_value = _make_mock_response(404, {})
        resp = client.post("/analyze",
                           json={"repo_url": "https://github.com/owner/missing"})
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════
# 429 — rate limited (GitHub returns 403)
# ═══════════════════════════════════════════════════════════════

class TestAnalyze429:
    @patch("main.requests.get")
    def test_metadata_403_becomes_429(self, mock_get, client):
        mock_get.return_value = _make_mock_response(403, {})
        resp = client.post("/analyze",
                           json={"repo_url": "https://github.com/owner/repo"})
        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════
# Cache hit — GitHub API never called
# ═══════════════════════════════════════════════════════════════

class TestCacheHit:
    @patch("main.requests.get")
    def test_cache_hit_skips_github(self, mock_get):
        cached_data = {
            "metadata": FAKE_METADATA,
            "commits": FAKE_COMMITS,
            "issues": FAKE_ISSUES,
            "releases": FAKE_RELEASES,
            "readme_status": 200,
        }
        with patch("main.init_db"), \
             patch("main.get_cached_repo", return_value=cached_data), \
             patch("main.save_to_cache"):
            from main import app
            with TestClient(app) as c:
                resp = c.post("/analyze",
                              json={"repo_url": "https://github.com/owner/repo"})

        assert resp.status_code == 200
        assert resp.json()["from_cache"] is True
        assert mock_get.call_count == 0
