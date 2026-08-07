import sqlite3
import json
from datetime import datetime, timezone


def init_db(db_path="cache.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repo_cache (
            repo_full_name TEXT PRIMARY KEY,
            metadata TEXT,
            commits TEXT,
            issues TEXT,
            releases TEXT,
            readme_status INTEGER,
            cached_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_cached_repo(repo_full_name, db_path="cache.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT metadata, commits, issues, releases, readme_status, cached_at FROM repo_cache WHERE repo_full_name = ?",
        (repo_full_name,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None  # nothing cached at all

    metadata_str, commits_str, issues_str, releases_str, readme_status, cached_at_str = row

    cached_at = datetime.fromisoformat(cached_at_str)
    now = datetime.now(timezone.utc)
    seconds_elapsed = (now - cached_at).total_seconds()

    if seconds_elapsed < 3600:  # 1 hour threshold
        return {
            "metadata": json.loads(metadata_str),
            "commits": json.loads(commits_str),
            "issues": json.loads(issues_str),
            "releases": json.loads(releases_str),
            "readme_status": readme_status
        }
    else:
        return None

def save_to_cache(repo_full_name, metadata, commits, issues, releases, readme_status, db_path="cache.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = datetime.now(timezone.utc)
    cached_at_str = now.isoformat()

    cursor.execute(
        "INSERT OR REPLACE INTO repo_cache (repo_full_name, metadata, commits, issues, releases, readme_status, cached_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (repo_full_name, json.dumps(metadata), json.dumps(commits), json.dumps(issues), json.dumps(releases), readme_status, cached_at_str)
    )

    conn.commit()
    conn.close()
    