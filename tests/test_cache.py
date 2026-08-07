import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta

import pytest

from core.cache import init_db, get_cached_repo, save_to_cache

TEST_DB = "test_cache.db"


@pytest.fixture(autouse=True)
def clean_db():
    """Remove the test database before and after every test."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# ── init_db ──────────────────────────────────────────────────────

class TestInitDb:
    def test_creates_table(self):
        init_db(db_path=TEST_DB)
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='repo_cache'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_idempotent(self):
        init_db(db_path=TEST_DB)
        init_db(db_path=TEST_DB)  # should not raise


# ── save + get round-trip ────────────────────────────────────────

class TestSaveAndGet:
    def test_round_trip(self):
        init_db(db_path=TEST_DB)

        metadata = {"stargazers_count": 42, "license": {"key": "mit"}}
        commits = [{"sha": "abc123"}]
        issues = [{"number": 1, "comments": 3}]
        releases = [{"tag_name": "v1.0", "draft": False, "prerelease": False}]
        readme_status = 200

        save_to_cache("owner/repo", metadata, commits, issues, releases,
                       readme_status, db_path=TEST_DB)

        result = get_cached_repo("owner/repo", db_path=TEST_DB)
        assert result is not None
        assert result["metadata"] == metadata
        assert result["commits"] == commits
        assert result["issues"] == issues
        assert result["releases"] == releases
        assert result["readme_status"] == readme_status

    def test_json_fields_round_trip(self):
        init_db(db_path=TEST_DB)

        nested = {"a": [1, {"b": True, "c": None}]}
        save_to_cache("owner/nested", nested, [], [], [], 404,
                       db_path=TEST_DB)
        result = get_cached_repo("owner/nested", db_path=TEST_DB)
        assert result["metadata"] == nested


# ── get returns None for missing repo ────────────────────────────

class TestGetMissing:
    def test_returns_none(self):
        init_db(db_path=TEST_DB)
        assert get_cached_repo("nonexistent/repo", db_path=TEST_DB) is None


# ── get returns None for expired entry ───────────────────────────

class TestGetExpired:
    def test_expired_after_one_hour(self):
        init_db(db_path=TEST_DB)

        # Insert a row, then manually backdate cached_at to >1 hour ago
        save_to_cache("owner/old", {"x": 1}, [], [], [], 200,
                       db_path=TEST_DB)

        two_hours_ago = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat()

        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            "UPDATE repo_cache SET cached_at = ? WHERE repo_full_name = ?",
            (two_hours_ago, "owner/old"),
        )
        conn.commit()
        conn.close()

        assert get_cached_repo("owner/old", db_path=TEST_DB) is None
