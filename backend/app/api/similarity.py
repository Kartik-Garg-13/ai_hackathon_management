from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Team
from app.schemas import ProjectCategoryOut, SimilarityReport, SimilarProjectPair
from app.services.similarity_detector import TeamProject, categorize_projects, find_similar_projects

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/similarity", tags=["similarity"])


@router.get("/report", response_model=SimilarityReport)
def similarity_report(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    teams = db.query(Team).filter(Team.hackathon_id == hackathon_id).all()
    projects = [
        TeamProject(team_id=t.id, team_name=t.team_name, text=t.project_idea or "")
        for t in teams
    ]

    pairs = find_similar_projects(projects)
    categories = categorize_projects(projects)

    return SimilarityReport(
        duplicate_pairs=[
            SimilarProjectPair(
                team_a_id=p.team_a_id, team_a_name=p.team_a_name,
                team_b_id=p.team_b_id, team_b_name=p.team_b_name,
                similarity=p.similarity,
            )
            for p in pairs[:200]
        ],
        categories=[
            ProjectCategoryOut(label=c.label, team_count=c.team_count, team_ids=c.team_ids)
            for c in categories
        ],
    )
