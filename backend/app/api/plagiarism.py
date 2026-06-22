from itertools import combinations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Team
from app.schemas import PlagiarismReport
from app.services.plagiarism_detector import compare_repos, compare_snapshots, fetch_repo_snapshot

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/plagiarism", tags=["plagiarism"])

MAX_TEAMS_PER_SCAN = 10


@router.post("/compare", response_model=PlagiarismReport)
def compare_teams(
    hackathon_id: int,
    team_a_id: int,
    team_b_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role not in ("organizer", "judge"):
        raise HTTPException(403, "Only organizers and judges can run plagiarism checks")

    team_a = db.get(Team, team_a_id)
    team_b = db.get(Team, team_b_id)
    if not team_a or team_a.hackathon_id != hackathon_id or not team_b or team_b.hackathon_id != hackathon_id:
        raise HTTPException(404, "Team not found")
    if not team_a.github_repo_url or not team_b.github_repo_url:
        raise HTTPException(400, "Both teams need a GitHub repo URL set before comparing")

    result = compare_repos(team_a.github_repo_url, team_b.github_repo_url)
    return PlagiarismReport(
        team_a_id=team_a_id, team_b_id=team_b_id,
        overall_similarity=result.overall_similarity, risk_level=result.risk_level,
        file_matches=[m.__dict__ for m in result.file_matches],
        commit_stats=result.commit_stats, notes=result.notes,
    )


@router.get("/scan", response_model=list[PlagiarismReport])
def scan_hackathon(
    hackathon_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role not in ("organizer", "judge"):
        raise HTTPException(403, "Only organizers and judges can run plagiarism scans")

    teams = (
        db.query(Team)
        .filter(Team.hackathon_id == hackathon_id, Team.github_repo_url.isnot(None))
        .limit(MAX_TEAMS_PER_SCAN)
        .all()
    )
    if len(teams) < 2:
        return []

    with httpx.Client(timeout=10.0) as client:
        snapshots = {team.id: fetch_repo_snapshot(team.github_repo_url, client=client) for team in teams}

    reports = []
    for team_a, team_b in combinations(teams, 2):
        result = compare_snapshots(snapshots[team_a.id], snapshots[team_b.id])
        if result.risk_level in ("medium", "high"):
            reports.append(PlagiarismReport(
                team_a_id=team_a.id, team_b_id=team_b.id,
                overall_similarity=result.overall_similarity, risk_level=result.risk_level,
                file_matches=[m.__dict__ for m in result.file_matches],
                commit_stats=result.commit_stats, notes=result.notes,
            ))
    reports.sort(key=lambda r: r.overall_similarity, reverse=True)
    return reports
