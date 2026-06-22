from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import MentorQuery, Reviewer
from app.schemas import MentorLeaderboardEntry, MentorQueryCreate, MentorQueryOut, MentorQueryRate, MentorQueryRespond
from app.services.mentor_leaderboard import build_leaderboard
from app.services.mentor_matcher import MentorProfile, rank_mentors_by_relevance

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/queries", tags=["queries"])
leaderboard_router = APIRouter(prefix="/api/hackathons/{hackathon_id}/mentors", tags=["queries"])


def _pick_mentor(hackathon_id: int, category: str, body: str, db: Session) -> Reviewer | None:
    mentors = db.query(Reviewer).filter(Reviewer.hackathon_id == hackathon_id, Reviewer.role == "mentor").all()
    if not mentors:
        return None

    query_text = f"{category} {body}"
    profiles = [
        MentorProfile(mentor_id=m.id, text=f"{' '.join(m.expertise)} {m.bio or ''}")
        for m in mentors
    ]
    ranked = rank_mentors_by_relevance(query_text, profiles)
    if ranked:
        top_score = ranked[0][1]
        pool_ids = {mid for mid, score in ranked if score >= top_score - 0.05}
        pool = [m for m in mentors if m.id in pool_ids]
    else:
        matching = [m for m in mentors if category in m.expertise]
        pool = matching or mentors

    load_counts = {
        m.id: db.query(MentorQuery).filter(MentorQuery.assigned_mentor_id == m.id, MentorQuery.status == "open").count()
        for m in pool
    }
    return min(pool, key=lambda m: load_counts[m.id])


@router.post("", response_model=MentorQueryOut)
def submit_query(
    hackathon_id: int,
    payload: MentorQueryCreate,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "participant":
        raise HTTPException(403, "Only participants can submit mentor queries")

    mentor = _pick_mentor(hackathon_id, payload.category, payload.body, db)
    query = MentorQuery(
        hackathon_id=hackathon_id,
        participant_id=actor.actor.id,
        category=payload.category,
        body=payload.body,
        assigned_mentor_id=mentor.id if mentor else None,
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


@router.get("", response_model=list[MentorQueryOut])
def list_queries(
    hackathon_id: int,
    mentor_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    q = db.query(MentorQuery).filter(MentorQuery.hackathon_id == hackathon_id)
    if actor.role == "mentor":
        q = q.filter(MentorQuery.assigned_mentor_id == actor.actor.id)
    elif actor.role == "participant":
        q = q.filter(MentorQuery.participant_id == actor.actor.id)
    elif mentor_id is not None:
        q = q.filter(MentorQuery.assigned_mentor_id == mentor_id)
    return q.order_by(MentorQuery.created_at.desc()).all()


@router.post("/{query_id}/respond", response_model=MentorQueryOut)
def respond_to_query(
    hackathon_id: int,
    query_id: int,
    payload: MentorQueryRespond,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    query = db.get(MentorQuery, query_id)
    if not query or query.hackathon_id != hackathon_id:
        raise HTTPException(404, "Query not found")
    if actor.role != "mentor" or query.assigned_mentor_id != actor.actor.id:
        raise HTTPException(403, "Only the assigned mentor can respond to this query")

    query.response = payload.response
    query.status = "answered"
    query.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(query)
    return query


@router.post("/{query_id}/rate", response_model=MentorQueryOut)
def rate_query(
    hackathon_id: int,
    query_id: int,
    payload: MentorQueryRate,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if not (1 <= payload.rating <= 5):
        raise HTTPException(400, "Rating must be between 1 and 5")

    query = db.get(MentorQuery, query_id)
    if not query or query.hackathon_id != hackathon_id:
        raise HTTPException(404, "Query not found")
    if actor.role != "participant" or query.participant_id != actor.actor.id:
        raise HTTPException(403, "Only the participant who asked can rate this response")
    if query.status != "answered":
        raise HTTPException(400, "Can't rate a query that hasn't been answered yet")

    query.rating = payload.rating
    db.commit()
    db.refresh(query)
    return query


@leaderboard_router.get("/leaderboard", response_model=list[MentorLeaderboardEntry])
def mentor_leaderboard(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    mentors = db.query(Reviewer).filter(Reviewer.hackathon_id == hackathon_id, Reviewer.role == "mentor").all()
    queries_by_mentor: dict[int, list[dict]] = {m.id: [] for m in mentors}
    for query in db.query(MentorQuery).filter(MentorQuery.hackathon_id == hackathon_id).all():
        if query.assigned_mentor_id in queries_by_mentor:
            queries_by_mentor[query.assigned_mentor_id].append({"status": query.status, "rating": query.rating})

    results = build_leaderboard(queries_by_mentor)
    names = {m.id: m.name for m in mentors}
    return [
        MentorLeaderboardEntry(
            mentor_id=r.mentor_id,
            mentor_name=names.get(r.mentor_id, "Unknown"),
            response_count=r.response_count,
            average_rating=r.average_rating,
            summary=r.summary,
        )
        for r in results
    ]
