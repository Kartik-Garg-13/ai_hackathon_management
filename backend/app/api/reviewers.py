from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Assignment, Reviewer, Team
from app.schemas import AssignmentOut, ReviewerCreate, ReviewerOut
from app.services.reviewer_assignment import assign_reviewers

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/reviewers", tags=["reviewers"])


@router.post("", response_model=ReviewerOut)
def create_reviewer(
    hackathon_id: int,
    payload: ReviewerCreate,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can add reviewers directly")
    reviewer = Reviewer(hackathon_id=hackathon_id, **payload.model_dump())
    db.add(reviewer)
    db.commit()
    db.refresh(reviewer)
    return reviewer


@router.get("", response_model=list[ReviewerOut])
def list_reviewers(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return db.query(Reviewer).filter(Reviewer.hackathon_id == hackathon_id).all()


@router.post("/assign", response_model=list[AssignmentOut])
def run_assignment(
    hackathon_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can run reviewer assignment")

    already_assigned_team_ids = {
        a.team_id for a in db.query(Assignment.team_id).filter(Assignment.hackathon_id == hackathon_id).distinct()
    }
    teams_q = db.query(Team).filter(Team.hackathon_id == hackathon_id)
    if already_assigned_team_ids:
        teams_q = teams_q.filter(~Team.id.in_(already_assigned_team_ids))
    teams = teams_q.all()
    judges = db.query(Reviewer).filter(Reviewer.hackathon_id == hackathon_id, Reviewer.role == "judge").all()

    if not teams:
        raise HTTPException(400, "No unassigned teams found. Upload registrations first.")
    if not judges:
        raise HTTPException(400, "No judges registered. Create or invite judges first.")

    results = assign_reviewers(teams, judges)

    created = []
    for r in results:
        if r["reviewer_id"] is None:
            continue
        assignment = Assignment(
            hackathon_id=hackathon_id,
            team_id=r["team_id"],
            reviewer_id=r["reviewer_id"],
            match_score=r["match_score"],
            explanation=r["explanation"],
        )
        db.add(assignment)
        reviewer = db.get(Reviewer, r["reviewer_id"])
        reviewer.current_load += 1
        created.append(assignment)
    db.commit()
    for a in created:
        db.refresh(a)
    return created


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return db.query(Assignment).filter(Assignment.hackathon_id == hackathon_id).all()
