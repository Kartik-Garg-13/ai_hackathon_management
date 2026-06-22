from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Hackathon, Score, Team
from app.schemas import WinnerEntry, WinnersResponse
from app.services.bias_detection import compute_final_rankings

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/winners", tags=["winners"])


def _build_rankings(hackathon_id: int, db: Session) -> list[WinnerEntry]:
    raw_scores = db.query(Score.reviewer_id, Score.team_id, Score.score).filter(Score.hackathon_id == hackathon_id).all()
    rankings = compute_final_rankings([(r.reviewer_id, r.team_id, r.score) for r in raw_scores])
    team_names = {t.id: t.team_name for t in db.query(Team).filter(Team.hackathon_id == hackathon_id).all()}
    return [
        WinnerEntry(
            rank=i + 1,
            team_id=r.team_id,
            team_name=team_names.get(r.team_id, "Unknown team"),
            average_normalized_score=r.average_normalized_score,
            num_scores=r.num_scores,
        )
        for i, r in enumerate(rankings)
    ]


@router.get("", response_model=WinnersResponse)
def get_winners(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon:
        raise HTTPException(404, "Hackathon not found")
    if not hackathon.winners_revealed_at:
        return WinnersResponse(revealed=False)
    return WinnersResponse(
        revealed=True,
        revealed_at=hackathon.winners_revealed_at,
        rankings=_build_rankings(hackathon_id, db),
    )


@router.post("/reveal", response_model=WinnersResponse)
def reveal_winners(
    hackathon_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can reveal winners")
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon:
        raise HTTPException(404, "Hackathon not found")
    if not hackathon.winners_revealed_at:
        hackathon.winners_revealed_at = datetime.utcnow()
        db.commit()
    return WinnersResponse(
        revealed=True,
        revealed_at=hackathon.winners_revealed_at,
        rankings=_build_rankings(hackathon_id, db),
    )
