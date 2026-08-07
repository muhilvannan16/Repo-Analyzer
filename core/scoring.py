from datetime import datetime, timezone
import statistics

def score_recency(pushed_at_str):
    pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    days_ago = (now - pushed_at).days
    if days_ago <= 7:
        return 13
    elif days_ago <= 30:
        return 10
    elif days_ago <= 90:
        return 7
    elif days_ago > 90:
        return 0

def score_frequency(commits, created_at_str):
    commit_count = len(commits)

    if commit_count < 5:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        repo_age_days = (now - created_at).days
        if repo_age_days <= 30:
            return 5
        else:
            return 3

    # Extract and sort commit dates (oldest to newest)
    dates = []
    for commit in commits:
        date_str = commit["commit"]["author"]["date"]
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dates.append(date)
    dates.sort()

    # Compute gaps between consecutive commits, in days
    gaps = []
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i - 1]).days
        gaps.append(gap)

    stdev = statistics.pstdev(gaps)

    if stdev <= 3:
        return 12
    elif stdev <= 7:
        return 9
    elif stdev <= 15:
        return 6
    elif stdev <= 30:
        return 3
    else:
        return 0

def score_momentum(commits, created_at_str):
    commit_count = len(commits)

    if commit_count < 8:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        repo_age_days = (now - created_at).days
        if repo_age_days <= 30:
            return 3
        else:
            return 2

    # Extract and sort commit dates (oldest to newest) — same as frequency
    dates = []
    for commit in commits:
        date_str = commit["commit"]["author"]["date"]
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dates.append(date)
    dates.sort()

    # Compute gaps between consecutive commits — same as frequency
    gaps = []
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i - 1]).days
        gaps.append(gap)

    # Split into recent (last 3 gaps) and earlier (everything before that)
    recent_gaps = gaps[-3:]
    earlier_gaps = gaps[:-3]

    recent_avg = statistics.mean(recent_gaps)
    earlier_avg = statistics.mean(earlier_gaps)

    earlier_avg = max(earlier_avg, 1)

    ratio = recent_avg / earlier_avg

    if ratio <= 0.7:
        return 8
    elif ratio <= 1.2:
        return 6
    elif ratio <= 2.0:
        return 3
    else:
        return 0

def score_fork_ratio(stargazers_count, forks_count):
    if stargazers_count < 10:
        return 5  # not enough data yet

    ratio = forks_count / stargazers_count

    if ratio >= 0.30:
        return 11
    elif ratio >= 0.15:
        return 8
    elif ratio >= 0.05:
        return 5
    elif ratio > 0:
        return 2
    else:
        return 0

def score_issue_engagement(issues):
    # Filter out pull requests, keep only real issues
    real_issues = []
    for item in issues:
        if "pull_request" not in item:
            real_issues.append(item)

    if len(real_issues) == 0:
        return 5  # neutral — nothing to measure

    comment_counts = []
    for issue in real_issues:
        comment_counts.append(issue["comments"])

    avg_comments = statistics.mean(comment_counts)

    if avg_comments >= 4.0:
        return 10
    elif avg_comments >= 2.0:
        return 7
    elif avg_comments >= 0.5:
        return 4
    elif avg_comments > 0:
        return 2
    else:
        return 0

def score_license(metadata):
    if metadata.get("license") is not None:
        return 6
    else:
        return 0

def score_resolution_rate(issues):
    # Filter out pull requests, keep only real issues
    real_issues = []
    for item in issues:
        if "pull_request" not in item:
            real_issues.append(item)

    if len(real_issues) == 0:
        return 6  # neutral — nothing to measure

    total_count = len(real_issues)

    completed_count = 0
    for issue in real_issues:
        if issue.get("state_reason") == "completed":
            completed_count += 1

    rate = completed_count / total_count

    if rate >= 0.70:
        return 13
    elif rate >= 0.50:
        return 10
    elif rate >= 0.30:
        return 7
    elif rate > 0:
        return 3
    else:
        return 0

def score_time_to_close(issues):
    # Filter out pull requests, keep only real issues
    real_issues = []
    for item in issues:
        if "pull_request" not in item:
            real_issues.append(item)

    if len(real_issues) == 0:
        return 5  # neutral — nothing to measure

    # Filter down to only genuinely completed issues
    completed_issues = []
    for issue in real_issues:
        if issue.get("state_reason") == "completed":
            completed_issues.append(issue)

    if len(completed_issues) == 0:
        return 0  # issues exist, but none were ever properly resolved

    # Compute days-to-close for each completed issue
    close_times = []
    for issue in completed_issues:
        created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        closed = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
        days_to_close = (closed - created).days
        close_times.append(days_to_close)

    avg_days = statistics.mean(close_times)

    if avg_days <= 7:
        return 10
    elif avg_days <= 21:
        return 7
    elif avg_days <= 60:
        return 4
    elif avg_days <= 120:
        return 2
    else:
        return 0

def score_recent_releases(releases):
    # Filter out drafts and prereleases, keep only real published releases
    real_releases = []
    for release in releases:
        if not release["draft"] and not release["prerelease"]:
            real_releases.append(release)

    if len(real_releases) == 0:
        return 5  # neutral — no qualifying releases

    # Find the most recent release date
    dates = []
    for release in real_releases:
        date_str = release["published_at"]
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dates.append(date)

    latest_release = max(dates)

    now = datetime.now(timezone.utc)
    days_ago = (now - latest_release).days

    if days_ago <= 90:
        return 11
    elif days_ago <= 180:
        return 8
    elif days_ago <= 365:
        return 5
    elif days_ago <= 730:
        return 2
    else:
        return 0

def score_readme(status_code):
    if status_code == 200:
        return 6
    else:
        return 0