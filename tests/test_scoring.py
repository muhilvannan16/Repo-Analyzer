import statistics
from datetime import datetime, timezone, timedelta
from core.scoring import (
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
)


# ── helpers ──────────────────────────────────────────────────────

def _iso(dt):
    """Convert a datetime to the ISO string format GitHub uses."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _days_ago(n):
    """Return an ISO timestamp for n days before now."""
    return _iso(datetime.now(timezone.utc) - timedelta(days=n))


def _commits_from_gaps(gaps):
    """Build a minimal list of commit dicts whose author-dates are
    separated by the given day-gaps (oldest → newest)."""
    base = datetime.now(timezone.utc) - timedelta(days=sum(gaps) + 1)
    dates = [base]
    for g in gaps:
        dates.append(dates[-1] + timedelta(days=g))
    return [{"commit": {"author": {"date": _iso(d)}}} for d in dates]


def _issue(comments=0, is_pr=False, state_reason=None,
           created_days_ago=30, closed_days_ago=None):
    """Build a minimal issue dict."""
    now = datetime.now(timezone.utc)
    item = {
        "comments": comments,
        "created_at": _iso(now - timedelta(days=created_days_ago)),
    }
    if is_pr:
        item["pull_request"] = {}
    if state_reason:
        item["state_reason"] = state_reason
    if closed_days_ago is not None:
        item["closed_at"] = _iso(now - timedelta(days=closed_days_ago))
    return item


def _release(days_ago, draft=False, prerelease=False):
    """Build a minimal release dict."""
    return {
        "published_at": _days_ago(days_ago),
        "draft": draft,
        "prerelease": prerelease,
    }


# ═══════════════════════════════════════════════════════════════
# score_recency  (max 13)
# ═══════════════════════════════════════════════════════════════

class TestScoreRecency:
    def test_within_7_days(self):
        assert score_recency(_days_ago(0)) == 13
        assert score_recency(_days_ago(7)) == 13

    def test_just_outside_7(self):
        assert score_recency(_days_ago(8)) == 10

    def test_within_30_days(self):
        assert score_recency(_days_ago(30)) == 10

    def test_just_outside_30(self):
        assert score_recency(_days_ago(31)) == 7

    def test_within_90_days(self):
        assert score_recency(_days_ago(90)) == 7

    def test_beyond_90_days(self):
        assert score_recency(_days_ago(91)) == 0
        assert score_recency(_days_ago(365)) == 0


# ═══════════════════════════════════════════════════════════════
# score_frequency  (max 12)
# ═══════════════════════════════════════════════════════════════

class TestScoreFrequency:
    # -- fewer than 5 commits branch --
    def test_few_commits_young_repo(self):
        commits = _commits_from_gaps([1, 1, 1])  # 4 commits
        created = _days_ago(10)  # repo 10 days old
        assert score_frequency(commits, created) == 5

    def test_few_commits_old_repo(self):
        commits = _commits_from_gaps([1, 1, 1])
        created = _days_ago(60)
        assert score_frequency(commits, created) == 3

    def test_few_commits_boundary_30_days(self):
        commits = _commits_from_gaps([1, 1, 1])
        created = _days_ago(30)
        assert score_frequency(commits, created) == 5

    def test_few_commits_boundary_31_days(self):
        commits = _commits_from_gaps([1, 1, 1])
        created = _days_ago(31)
        assert score_frequency(commits, created) == 3

    # -- 5+ commits: stdev boundaries --
    def test_stdev_zero(self):
        # all gaps identical → pstdev = 0 → ≤3 → 12
        commits = _commits_from_gaps([5, 5, 5, 5])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 12

    def test_stdev_at_3(self):
        # gaps [2, 8, 2, 8] → mean=5, pstdev=3.0 → ≤3 → 12
        commits = _commits_from_gaps([2, 8, 2, 8])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 12

    def test_stdev_just_above_3(self):
        # gaps [1, 9, 1, 9] → mean=5, pstdev=4.0 → ≤7 → 9
        commits = _commits_from_gaps([1, 9, 1, 9])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 9

    def test_stdev_at_7(self):
        # gaps [3, 17, 3, 17] → mean=10, pstdev=7.0 → ≤7 → 9
        commits = _commits_from_gaps([3, 17, 3, 17])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 9

    def test_stdev_just_above_7(self):
        # gaps [2, 18, 2, 18] → mean=10, pstdev=8.0 → ≤15 → 6
        commits = _commits_from_gaps([2, 18, 2, 18])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 6

    def test_stdev_at_15(self):
        # gaps [5, 35, 5, 35] → mean=20, pstdev=15.0 → ≤15 → 6
        commits = _commits_from_gaps([5, 35, 5, 35])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 6

    def test_stdev_just_above_15(self):
        # gaps [4, 36, 4, 36] → mean=20, pstdev=16.0 → ≤30 → 3
        commits = _commits_from_gaps([4, 36, 4, 36])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 3

    def test_stdev_at_30(self):
        # gaps [10, 70, 10, 70] → mean=40, pstdev=30.0 → ≤30 → 3
        commits = _commits_from_gaps([10, 70, 10, 70])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 3

    def test_stdev_above_30(self):
        # gaps [1, 99, 1, 99] → mean=50, pstdev=49.0 → 0
        commits = _commits_from_gaps([1, 99, 1, 99])
        created = _days_ago(365)
        assert score_frequency(commits, created) == 0


# ═══════════════════════════════════════════════════════════════
# score_momentum  (max 8)
# ═══════════════════════════════════════════════════════════════

class TestScoreMomentum:
    # -- fewer than 8 commits --
    def test_few_commits_young_repo(self):
        commits = _commits_from_gaps([1, 1, 1, 1, 1, 1])  # 7 commits
        created = _days_ago(10)
        assert score_momentum(commits, created) == 3

    def test_few_commits_old_repo(self):
        commits = _commits_from_gaps([1, 1, 1, 1, 1, 1])
        created = _days_ago(60)
        assert score_momentum(commits, created) == 2

    def test_few_commits_boundary_30(self):
        commits = _commits_from_gaps([1, 1, 1, 1, 1, 1])
        created = _days_ago(30)
        assert score_momentum(commits, created) == 3

    def test_few_commits_boundary_31(self):
        commits = _commits_from_gaps([1, 1, 1, 1, 1, 1])
        created = _days_ago(31)
        assert score_momentum(commits, created) == 2

    # -- 8+ commits: ratio boundaries --
    # gaps list: first N-3 are "earlier", last 3 are "recent"
    def test_ratio_well_below_0_7(self):
        # earlier=[10,10,10,10], recent=[5,5,5] → ratio=0.5 → ≤0.7 → 8
        commits = _commits_from_gaps([10, 10, 10, 10, 5, 5, 5])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 8

    def test_ratio_at_0_7(self):
        # earlier=[10,10,10,10], recent=[7,7,7] → ratio=0.7 → ≤0.7 → 8
        commits = _commits_from_gaps([10, 10, 10, 10, 7, 7, 7])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 8

    def test_ratio_just_above_0_7(self):
        # earlier=[10,10,10,10], recent=[8,8,8] → ratio=0.8 → ≤1.2 → 6
        commits = _commits_from_gaps([10, 10, 10, 10, 8, 8, 8])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 6

    def test_ratio_at_1_0(self):
        # earlier=[10,10,10,10], recent=[10,10,10] → ratio=1.0 → ≤1.2 → 6
        commits = _commits_from_gaps([10, 10, 10, 10, 10, 10, 10])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 6

    def test_ratio_at_1_2(self):
        # earlier=[10,10,10,10], recent=[12,12,12] → ratio=1.2 → ≤1.2 → 6
        commits = _commits_from_gaps([10, 10, 10, 10, 12, 12, 12])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 6

    def test_ratio_just_above_1_2(self):
        # earlier=[10,10,10,10], recent=[13,13,13] → ratio=1.3 → ≤2.0 → 3
        commits = _commits_from_gaps([10, 10, 10, 10, 13, 13, 13])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 3

    def test_ratio_at_2_0(self):
        # earlier=[10,10,10,10], recent=[20,20,20] → ratio=2.0 → ≤2.0 → 3
        commits = _commits_from_gaps([10, 10, 10, 10, 20, 20, 20])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 3

    def test_ratio_above_2_0(self):
        # earlier=[5,5,5,5], recent=[15,15,15] → ratio=3.0 → 0
        commits = _commits_from_gaps([5, 5, 5, 5, 15, 15, 15])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 0

    def test_earlier_avg_clamped_to_1(self):
        # earlier gaps all 0 → earlier_avg clamped to 1
        # recent=[2,2,2] → ratio=2.0 → ≤2.0 → 3
        commits = _commits_from_gaps([0, 0, 0, 0, 2, 2, 2])
        created = _days_ago(365)
        assert score_momentum(commits, created) == 3


# ═══════════════════════════════════════════════════════════════
# score_fork_ratio  (max 11)
# ═══════════════════════════════════════════════════════════════

class TestScoreForkRatio:
    def test_fewer_than_10_stars(self):
        assert score_fork_ratio(9, 5) == 5
        assert score_fork_ratio(0, 0) == 5

    def test_ratio_gte_0_30(self):
        assert score_fork_ratio(100, 30) == 11
        assert score_fork_ratio(100, 50) == 11

    def test_ratio_gte_0_15(self):
        assert score_fork_ratio(100, 15) == 8
        assert score_fork_ratio(100, 29) == 8

    def test_ratio_gte_0_05(self):
        assert score_fork_ratio(100, 5) == 5
        assert score_fork_ratio(100, 14) == 5

    def test_ratio_gt_0(self):
        assert score_fork_ratio(100, 1) == 2
        assert score_fork_ratio(100, 4) == 2

    def test_ratio_eq_0(self):
        assert score_fork_ratio(100, 0) == 0


# ═══════════════════════════════════════════════════════════════
# score_issue_engagement  (max 10)
# ═══════════════════════════════════════════════════════════════

class TestScoreIssueEngagement:
    def test_no_real_issues(self):
        assert score_issue_engagement([]) == 5
        # only PRs → still no real issues
        assert score_issue_engagement([_issue(is_pr=True)]) == 5

    def test_avg_comments_gte_4(self):
        issues = [_issue(comments=4), _issue(comments=4)]
        assert score_issue_engagement(issues) == 10

    def test_avg_comments_gte_2(self):
        issues = [_issue(comments=2), _issue(comments=2)]
        assert score_issue_engagement(issues) == 7

    def test_avg_comments_gte_0_5(self):
        issues = [_issue(comments=1), _issue(comments=0)]  # avg=0.5
        assert score_issue_engagement(issues) == 4

    def test_avg_comments_gt_0(self):
        issues = [_issue(comments=1), _issue(comments=0), _issue(comments=0)]  # avg≈0.33
        assert score_issue_engagement(issues) == 2

    def test_avg_comments_eq_0(self):
        issues = [_issue(comments=0), _issue(comments=0)]
        assert score_issue_engagement(issues) == 0

    def test_prs_filtered_out(self):
        issues = [_issue(comments=10), _issue(comments=0, is_pr=True)]
        assert score_issue_engagement(issues) == 10


# ═══════════════════════════════════════════════════════════════
# score_license  (max 6)
# ═══════════════════════════════════════════════════════════════

class TestScoreLicense:
    def test_has_license(self):
        assert score_license({"license": {"key": "mit"}}) == 6

    def test_no_license(self):
        assert score_license({"license": None}) == 0

    def test_missing_key(self):
        assert score_license({}) == 0


# ═══════════════════════════════════════════════════════════════
# score_resolution_rate  (max 13)
# ═══════════════════════════════════════════════════════════════

class TestScoreResolutionRate:
    def test_no_real_issues(self):
        assert score_resolution_rate([]) == 6
        assert score_resolution_rate([_issue(is_pr=True)]) == 6

    def test_rate_gte_0_70(self):
        # 7 of 10 completed
        issues = [_issue(state_reason="completed") for _ in range(7)]
        issues += [_issue() for _ in range(3)]
        assert score_resolution_rate(issues) == 13

    def test_rate_gte_0_50(self):
        # 5 of 10
        issues = [_issue(state_reason="completed") for _ in range(5)]
        issues += [_issue() for _ in range(5)]
        assert score_resolution_rate(issues) == 10

    def test_rate_gte_0_30(self):
        # 3 of 10
        issues = [_issue(state_reason="completed") for _ in range(3)]
        issues += [_issue() for _ in range(7)]
        assert score_resolution_rate(issues) == 7

    def test_rate_gt_0(self):
        # 1 of 10
        issues = [_issue(state_reason="completed")]
        issues += [_issue() for _ in range(9)]
        assert score_resolution_rate(issues) == 3

    def test_rate_eq_0(self):
        issues = [_issue() for _ in range(5)]
        assert score_resolution_rate(issues) == 0


# ═══════════════════════════════════════════════════════════════
# score_time_to_close  (max 10)
# ═══════════════════════════════════════════════════════════════

class TestScoreTimeToClose:
    def test_no_real_issues(self):
        assert score_time_to_close([]) == 5
        assert score_time_to_close([_issue(is_pr=True)]) == 5

    def test_issues_but_none_completed(self):
        issues = [_issue(), _issue()]
        assert score_time_to_close(issues) == 0

    def test_avg_days_lte_7(self):
        issues = [_issue(state_reason="completed", created_days_ago=10, closed_days_ago=3)]
        assert score_time_to_close(issues) == 10

    def test_avg_days_lte_21(self):
        issues = [_issue(state_reason="completed", created_days_ago=35, closed_days_ago=21)]
        assert score_time_to_close(issues) == 7

    def test_avg_days_lte_60(self):
        issues = [_issue(state_reason="completed", created_days_ago=90, closed_days_ago=45)]
        assert score_time_to_close(issues) == 4

    def test_avg_days_lte_120(self):
        issues = [_issue(state_reason="completed", created_days_ago=150, closed_days_ago=50)]
        assert score_time_to_close(issues) == 2

    def test_avg_days_above_120(self):
        issues = [_issue(state_reason="completed", created_days_ago=200, closed_days_ago=50)]
        assert score_time_to_close(issues) == 0


# ═══════════════════════════════════════════════════════════════
# score_recent_releases  (max 11)
# ═══════════════════════════════════════════════════════════════

class TestScoreRecentReleases:
    def test_no_qualifying_releases(self):
        assert score_recent_releases([]) == 5
        # only drafts / prereleases
        assert score_recent_releases([_release(10, draft=True)]) == 5
        assert score_recent_releases([_release(10, prerelease=True)]) == 5

    def test_within_90_days(self):
        assert score_recent_releases([_release(1)]) == 11
        assert score_recent_releases([_release(90)]) == 11

    def test_within_180_days(self):
        assert score_recent_releases([_release(91)]) == 8
        assert score_recent_releases([_release(180)]) == 8

    def test_within_365_days(self):
        assert score_recent_releases([_release(181)]) == 5
        assert score_recent_releases([_release(365)]) == 5

    def test_within_730_days(self):
        assert score_recent_releases([_release(366)]) == 2
        assert score_recent_releases([_release(730)]) == 2

    def test_beyond_730_days(self):
        assert score_recent_releases([_release(731)]) == 0

    def test_picks_most_recent(self):
        # oldest is 400 days ago but newest is 50 → 11
        assert score_recent_releases([_release(400), _release(50)]) == 11


# ═══════════════════════════════════════════════════════════════
# score_readme  (max 6)
# ═══════════════════════════════════════════════════════════════

class TestScoreReadme:
    def test_200(self):
        assert score_readme(200) == 6

    def test_404(self):
        assert score_readme(404) == 0

    def test_other_status(self):
        assert score_readme(500) == 0
