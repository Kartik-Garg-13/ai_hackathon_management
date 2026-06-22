from dataclasses import dataclass
from datetime import datetime

INACTIVITY_HIGH_RISK_HOURS = 48
INACTIVITY_MEDIUM_RISK_HOURS = 24
DECLINE_RATIO_THRESHOLD = 0.4


@dataclass
class BurnoutResult:
    team_id: int
    burnout_risk_level: str
    summary: str
    hours_since_last_activity: float
    activity_count_recent: int


def _hours_between(earlier: datetime, later: datetime) -> float:
    return (later - earlier).total_seconds() / 3600


def assess_team_burnout(
    team_id: int,
    activity_timestamps: list[datetime],
    now: datetime | None = None,
) -> BurnoutResult:
    now = now or datetime.utcnow()

    if not activity_timestamps:
        return BurnoutResult(
            team_id=team_id,
            burnout_risk_level="High",
            summary="No activity logged yet for this team. Worth a check-in to make sure they're not stuck.",
            hours_since_last_activity=-1.0,
            activity_count_recent=0,
        )

    timestamps = sorted(activity_timestamps)
    last_activity = timestamps[-1]
    hours_since_last = round(_hours_between(last_activity, now), 1)

    recent_cutoff = now.timestamp() - 48 * 3600
    prior_cutoff = now.timestamp() - 96 * 3600
    recent_count = sum(1 for t in timestamps if t.timestamp() >= recent_cutoff)
    prior_count = sum(1 for t in timestamps if prior_cutoff <= t.timestamp() < recent_cutoff)

    if hours_since_last >= INACTIVITY_HIGH_RISK_HOURS:
        return BurnoutResult(
            team_id=team_id,
            burnout_risk_level="High",
            summary=f"No activity in {hours_since_last:.0f} hours. This team may need a check-in.",
            hours_since_last_activity=hours_since_last,
            activity_count_recent=recent_count,
        )

    if prior_count > 0 and recent_count / prior_count < DECLINE_RATIO_THRESHOLD:
        return BurnoutResult(
            team_id=team_id,
            burnout_risk_level="Medium",
            summary="Activity has dropped off sharply compared to earlier in the event. Worth checking how they're doing.",
            hours_since_last_activity=hours_since_last,
            activity_count_recent=recent_count,
        )

    if hours_since_last >= INACTIVITY_MEDIUM_RISK_HOURS:
        return BurnoutResult(
            team_id=team_id,
            burnout_risk_level="Medium",
            summary=f"No activity in {hours_since_last:.0f} hours. Not urgent, but keep an eye on this team.",
            hours_since_last_activity=hours_since_last,
            activity_count_recent=recent_count,
        )

    return BurnoutResult(
        team_id=team_id,
        burnout_risk_level="Low",
        summary="Team is actively working — no concerns.",
        hours_since_last_activity=hours_since_last,
        activity_count_recent=recent_count,
    )
