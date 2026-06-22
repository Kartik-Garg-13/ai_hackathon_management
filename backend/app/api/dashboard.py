from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Score, Team
from app.schemas import JudgeDashboard, TeamCategoryCount, TopTeamEntry
from app.services.bias_detection import compute_population_stats, normalize_score
from app.services.burnout_detection import assess_team_burnout
from app.services.skill_taxonomy import project_required_categories

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/judge-dashboard", tags=["dashboard"])


@router.get("", response_model=JudgeDashboard)
def judge_dashboard(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    teams = db.query(Team).filter(Team.hackathon_id == hackathon_id).all()
    team_count = len(teams)

    from app.models import Activity

    active_count = 0
    for team in teams:
        timestamps = [a.timestamp for a in db.query(Activity).filter(Activity.team_id == team.id).all()]
        result = assess_team_burnout(team.id, timestamps)
        if result.burnout_risk_level == "Low":
            active_count += 1

    category_counter = Counter()
    for team in teams:
        for category in project_required_categories(team.project_idea or ""):
            category_counter[category] += 1
    category_distribution = [
        TeamCategoryCount(category=cat, team_count=count)
        for cat, count in category_counter.most_common()
    ]

    all_scores_by_reviewer: dict[int, list[float]] = {}
    for row in db.query(Score.reviewer_id, Score.score).filter(Score.hackathon_id == hackathon_id).all():
        all_scores_by_reviewer.setdefault(row.reviewer_id, []).append(row.score)
    population_mean, population_std = compute_population_stats(
        [s for scores in all_scores_by_reviewer.values() for s in scores]
    )

    team_normalized_avgs = []
    for team in teams:
        team_scores = db.query(Score).filter(Score.team_id == team.id).all()
        if not team_scores:
            continue
        normalized_values = []
        for score in team_scores:
            reviewer_scores = all_scores_by_reviewer.get(score.reviewer_id, [score.score])
            reviewer_mean, reviewer_std = compute_population_stats(reviewer_scores)
            normalized_values.append(normalize_score(score.score, reviewer_mean, reviewer_std, population_mean, population_std))
        team_normalized_avgs.append((team, round(sum(normalized_values) / len(normalized_values), 2)))

    team_normalized_avgs.sort(key=lambda t: t[1], reverse=True)
    top_teams = [
        TopTeamEntry(team_id=team.id, team_name=team.team_name, average_normalized_score=avg)
        for team, avg in team_normalized_avgs[:5]
    ]

    return JudgeDashboard(
        team_count=team_count,
        active_team_count=active_count,
        inactive_team_count=team_count - active_count,
        category_distribution=category_distribution,
        top_teams=top_teams,
    )
