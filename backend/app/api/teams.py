from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Activity, Participant, Team
from app.schemas import ActivityOut, TeamLinksUpdate, TeamOut, TeammateOut

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/teams", tags=["teams"])


def _require_team_access(actor: CurrentActor, team_id: int) -> None:
    if actor.role == "organizer":
        return
    if actor.role == "participant" and getattr(actor.actor, "team_id", None) == team_id:
        return
    raise HTTPException(403, "You can only view your own team's details")


@router.get("", response_model=list[TeamOut])
def list_teams(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return db.query(Team).filter(Team.hackathon_id == hackathon_id).all()


@router.patch("/{team_id}/links", response_model=TeamOut)
def update_team_links(
    hackathon_id: int,
    team_id: int,
    payload: TeamLinksUpdate,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    team = db.get(Team, team_id)
    if not team or team.hackathon_id != hackathon_id:
        raise HTTPException(404, "Team not found")
    if actor.role not in ("organizer", "participant"):
        raise HTTPException(403, "Only the organizer or a team member can update project links")
    if actor.role == "participant" and getattr(actor.actor, "team_id", None) != team_id:
        raise HTTPException(403, "You can only update your own team's links")

    if payload.github_repo_url is not None:
        team.github_repo_url = payload.github_repo_url or None
    if payload.demo_video_url is not None:
        team.demo_video_url = payload.demo_video_url or None
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}/members", response_model=list[TeammateOut])
def list_team_members(
    hackathon_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    team = db.get(Team, team_id)
    if not team or team.hackathon_id != hackathon_id:
        raise HTTPException(404, "Team not found")
    _require_team_access(actor, team_id)
    return db.query(Participant).filter(Participant.team_id == team_id).all()


@router.get("/{team_id}/activity", response_model=list[ActivityOut])
def list_team_activity(
    hackathon_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    team = db.get(Team, team_id)
    if not team or team.hackathon_id != hackathon_id:
        raise HTTPException(404, "Team not found")
    _require_team_access(actor, team_id)
    return (
        db.query(Activity)
        .filter(Activity.team_id == team_id)
        .order_by(Activity.timestamp.desc())
        .all()
    )
