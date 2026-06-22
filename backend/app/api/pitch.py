import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import PitchReview, Team
from app.schemas import PitchReviewOut
from app.services.pitch_analyzer import analyze_pitch
from app.services.repo_inspector import inspect_repo_health

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/pitch", tags=["pitch"])


@router.post("/analyze", response_model=PitchReviewOut)
async def analyze_team_pitch(
    hackathon_id: int,
    team_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    team = db.get(Team, team_id)
    if not team or team.hackathon_id != hackathon_id:
        raise HTTPException(404, "Team not found")
    if not file.filename.lower().endswith(".pptx"):
        raise HTTPException(400, "Only .pptx files are supported")

    raw = await file.read()
    try:
        result = analyze_pitch(io.BytesIO(raw), project_novelty_score=team.project_novelty_score)
    except Exception as exc:
        raise HTTPException(400, f"Could not parse the .pptx file: {exc}") from exc

    if team.github_repo_url:
        repo_health = inspect_repo_health(team.github_repo_url)
        result["issues"] = result["issues"] + repo_health["issues"]

    review = PitchReview(hackathon_id=hackathon_id, team_id=team_id, **result)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{team_id}", response_model=PitchReviewOut)
def get_latest_pitch_review(
    hackathon_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    review = (
        db.query(PitchReview)
        .filter(PitchReview.team_id == team_id, PitchReview.hackathon_id == hackathon_id)
        .order_by(PitchReview.created_at.desc())
        .first()
    )
    if not review:
        raise HTTPException(404, "No pitch review found for this team")
    return review
