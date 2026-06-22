from datetime import datetime, timedelta

from app.services.burnout_detection import assess_team_burnout

NOW = datetime(2026, 6, 21, 12, 0, 0)


def test_active_team_is_low_risk():
    timestamps = [NOW - timedelta(hours=h) for h in [2, 10, 20]]
    result = assess_team_burnout(1, timestamps, now=NOW)
    assert result.burnout_risk_level == "Low"


def test_long_inactive_team_is_high_risk():
    timestamps = [NOW - timedelta(hours=70)]
    result = assess_team_burnout(2, timestamps, now=NOW)
    assert result.burnout_risk_level == "High"


def test_no_activity_at_all_is_high_risk():
    result = assess_team_burnout(3, [], now=NOW)
    assert result.burnout_risk_level == "High"
    assert "no activity logged" in result.summary.lower()


def test_declining_activity_is_flagged_medium():
    timestamps = [NOW - timedelta(hours=h) for h in [90, 85, 80, 10]]
    result = assess_team_burnout(4, timestamps, now=NOW)
    assert result.burnout_risk_level == "Medium"
