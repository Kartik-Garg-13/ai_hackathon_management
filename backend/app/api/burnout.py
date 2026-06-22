from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Activity, Team
from app.schemas import ActivityCreate, ActivityOut, BurnoutReportEntry
from app.services.burnout_detection import assess_team_burnout

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/burnout", tags=["burnout"])
activity_router = APIRouter(prefix="/api/hackathons/{hackathon_id}/activity", tags=["activity"])


@activity_router.post("", response_model=ActivityOut)
def log_activity(
    hackathon_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    team = db.get(Team, payload.team_id)
    if not team or team.hackathon_id != hackathon_id:
        raise HTTPException(404, "Team not found")
    if actor.role == "participant" and getattr(actor.actor, "team_id", None) != payload.team_id:
        raise HTTPException(403, "You can only log activity for your own team")
    sender_name = actor.actor.name if actor.role == "participant" else None
    activity = Activity(
        hackathon_id=hackathon_id, team_id=payload.team_id, activity_type=payload.activity_type,
        note=payload.note, sender_name=sender_name,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def _build_report(hackathon_id: int, db: Session) -> list[BurnoutReportEntry]:
    teams = db.query(Team).filter(Team.hackathon_id == hackathon_id).all()
    report = []
    for team in teams:
        timestamps = [a.timestamp for a in db.query(Activity).filter(Activity.team_id == team.id).all()]
        result = assess_team_burnout(team.id, timestamps)
        report.append(BurnoutReportEntry(
            team_id=team.id,
            team_name=team.team_name,
            burnout_risk_level=result.burnout_risk_level,
            summary=result.summary,
            hours_since_last_activity=result.hours_since_last_activity,
            activity_count_recent=result.activity_count_recent,
        ))
    return report


@router.get("/teams", response_model=list[BurnoutReportEntry])
def burnout_report(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return _build_report(hackathon_id, db)


@router.get("/flagged", response_model=list[BurnoutReportEntry])
def flagged_teams(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return [r for r in _build_report(hackathon_id, db) if r.burnout_risk_level in ("Medium", "High")]
