from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import AuditLog, Reviewer, Score
from app.schemas import AuditLogOut, BiasReportEntry, NormalizedScoreEntry, ScoreCreate, ScoreOut
from app.services.bias_detection import compute_population_stats, explain_normalization, fairness_report, normalize_score

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/bias", tags=["bias"])
scores_router = APIRouter(prefix="/api/hackathons/{hackathon_id}/scores", tags=["scores"])
audit_router = APIRouter(prefix="/api/hackathons/{hackathon_id}/audit-log", tags=["audit"])
teams_router = APIRouter(prefix="/api/hackathons/{hackathon_id}/teams", tags=["teams"])


@scores_router.post("", response_model=ScoreOut)
def submit_score(
    hackathon_id: int,
    payload: ScoreCreate,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    reviewer = db.get(Reviewer, payload.reviewer_id)
    if not reviewer or reviewer.hackathon_id != hackathon_id:
        raise HTTPException(404, "Reviewer not found")

    score = Score(
        hackathon_id=hackathon_id,
        reviewer_id=payload.reviewer_id,
        team_id=payload.team_id,
        assignment_id=payload.assignment_id,
        score=payload.score,
        criteria=payload.criteria,
        comments=payload.comments,
    )
    db.add(score)
    db.flush()

    audit = AuditLog(
        hackathon_id=hackathon_id,
        entity_type="score",
        entity_id=score.id,
        action="submit_score",
        actor=payload.actor or reviewer.name,
        before=None,
        after={"score": payload.score, "criteria": payload.criteria, "team_id": payload.team_id},
        reasoning=payload.comments,
    )
    db.add(audit)
    db.commit()
    db.refresh(score)
    return score


def _bias_report(hackathon_id: int, db: Session) -> list[BiasReportEntry]:
    reviewers = db.query(Reviewer).filter(Reviewer.hackathon_id == hackathon_id).all()
    scores_by_reviewer: dict[int, list[float]] = {}
    for reviewer in reviewers:
        rows = db.query(Score.score).filter(Score.reviewer_id == reviewer.id).all()
        scores_by_reviewer[reviewer.id] = [s[0] for s in rows]

    results = fairness_report(scores_by_reviewer)
    reviewer_names = {r.id: r.name for r in reviewers}

    return [
        BiasReportEntry(
            reviewer_id=r.reviewer_id,
            reviewer_name=reviewer_names.get(r.reviewer_id, "Unknown"),
            bias_risk_level=r.bias_risk_level,
            confidence_label=r.confidence_label,
            summary=r.summary,
            num_scores=r.num_scores,
            mean_score=r.mean_score,
            z_score=r.z_score,
            bias_confidence=r.bias_confidence,
            flags=r.flags,
        )
        for r in results
    ]


@router.get("/reviewers", response_model=list[BiasReportEntry])
def bias_report(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return _bias_report(hackathon_id, db)


@router.get("/flagged", response_model=list[BiasReportEntry])
def flagged_reviewers(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return [r for r in _bias_report(hackathon_id, db) if r.bias_risk_level in ("Medium", "High")]


@audit_router.get("", response_model=list[AuditLogOut])
def list_audit_log(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return (
        db.query(AuditLog)
        .filter(AuditLog.hackathon_id == hackathon_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )


@teams_router.get("/{team_id}/normalized-scores", response_model=list[NormalizedScoreEntry])
def normalized_scores_for_team(
    hackathon_id: int,
    team_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    team_scores = db.query(Score).filter(Score.team_id == team_id, Score.hackathon_id == hackathon_id).all()
    if not team_scores:
        return []

    all_scores_by_reviewer: dict[int, list[float]] = {}
    for row in db.query(Score.reviewer_id, Score.score).filter(Score.hackathon_id == hackathon_id).all():
        all_scores_by_reviewer.setdefault(row.reviewer_id, []).append(row.score)

    population_mean, population_std = compute_population_stats(
        [s for scores in all_scores_by_reviewer.values() for s in scores]
    )

    results = []
    for score in team_scores:
        reviewer_scores = all_scores_by_reviewer.get(score.reviewer_id, [score.score])
        reviewer_mean, reviewer_std = compute_population_stats(reviewer_scores)
        normalized = normalize_score(score.score, reviewer_mean, reviewer_std, population_mean, population_std)
        reviewer = db.get(Reviewer, score.reviewer_id)
        results.append(NormalizedScoreEntry(
            score_id=score.id,
            reviewer_id=score.reviewer_id,
            reviewer_name=reviewer.name if reviewer else "Unknown",
            raw_score=score.score,
            normalized_score=normalized,
            explanation=explain_normalization(reviewer_mean, population_mean),
        ))
    return results
