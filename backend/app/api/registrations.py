import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope
from app.database import get_db
from app.models import Participant, Team
from app.schemas import ApprovalAction, ParticipantOut, ReanalyzeResult, RegistrationAnalytics
from app.services import registration_intelligence as ri

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/registrations", tags=["registrations"])

REQUIRED_COLUMNS = {
    "id", "name", "email", "college", "skills", "project_idea", "team_name", "phone_number",
}


@router.post("/upload")
async def upload_registrations(
    hackathon_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can upload registrations")

    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw), dtype={"phone_number": str})
    except Exception as exc:
        raise HTTPException(400, f"Could not parse CSV: {exc}") from exc

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(400, f"CSV missing required columns: {sorted(missing)}")

    analyzed = ri.analyze(df)
    metrics = ri.evaluate(analyzed)

    teams_by_id_str: dict[str, Team] = {}
    for team_id_str, group in analyzed.groupby("team_id"):
        first = group.iloc[0]
        team = Team(
            hackathon_id=hackathon_id,
            team_id_str=team_id_str,
            team_name=str(first["team_name"]),
            college=str(first["college"]),
            project_idea=str(first["project_idea"]),
            skill_categories=ri.team_skill_categories(group),
            team_size=int(first["team_size"]),
            team_health_score=float(first["team_health_score"]),
            project_novelty_score=float(first["project_novelty_score"]),
        )
        db.add(team)
        teams_by_id_str[team_id_str] = team
    db.flush()

    for _, row in analyzed.iterrows():
        participant = Participant(
            hackathon_id=hackathon_id,
            registration_id=str(row["id"]),
            team_id=teams_by_id_str[row["team_id"]].id,
            name=str(row["name"]),
            email=str(row["email"]),
            phone_number=str(row.get("phone_number", "")),
            college=str(row["college"]),
            skills=str(row["skills"]),
            project_idea=str(row["project_idea"]),
            team_name=str(row["team_name"]),
            final_trust_score=float(row["final_trust_score"]),
            final_risk_level=str(row["final_risk_level"]),
            confidence_score=float(row["confidence_score"]),
            anomaly_score=float(row["anomaly_score"]),
            fraud_ring_id=int(row["fraud_ring_id"]),
            reasons=list(row["reasons"]),
            explanation=str(row["explanation"]),
            ground_truth_label=str(row["ground_truth_label"]) if "ground_truth_label" in row and pd.notna(row["ground_truth_label"]) else None,
            predicted_label=str(row["predicted_label"]),
            ip_address=str(row["ip_address"]) if "ip_address" in row and pd.notna(row["ip_address"]) else None,
            github_username=str(row["github_username"]) if "github_username" in row and pd.notna(row["github_username"]) else None,
            academic_year=str(row["academic_year"]) if "academic_year" in row and pd.notna(row["academic_year"]) else None,
            consent_accepted=True,
        )
        db.add(participant)
    db.commit()

    return {
        "rows_ingested": len(analyzed),
        "teams_created": len(teams_by_id_str),
        "ground_truth_metrics": metrics,
    }


@router.get("", response_model=list[ParticipantOut])
def list_registrations(
    hackathon_id: int,
    risk_level: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    name: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    q = db.query(Participant).filter(Participant.hackathon_id == hackathon_id)
    if risk_level:
        q = q.filter(Participant.final_risk_level == risk_level)
    if approval_status:
        q = q.filter(Participant.approval_status == approval_status)
    if name:
        needle = f"%{name.strip().lower()}%"
        q = q.filter(
            func.lower(Participant.name).like(needle)
            | func.lower(Participant.team_name).like(needle)
        )
    return q.order_by(Participant.final_trust_score.asc()).offset(offset).limit(limit).all()


def reanalyze_all_participants(hackathon_id: int, db: Session) -> tuple[int, dict | None]:
    """Re-scores every participant in a hackathon against the full current
    population (duplicate/fraud-ring/anomaly detection are population-relative,
    so a single new registration is re-run against everyone, not in isolation).
    Used both by the organizer-triggered /reanalyze endpoint and automatically
    right after a new self-registration, so risk data is never stale."""
    participants = db.query(Participant).filter(Participant.hackathon_id == hackathon_id).all()
    if not participants:
        return 0, None

    team_members: dict[str, list[Participant]] = {}
    for p in participants:
        team_prefix = p.team_name.strip().replace(" ", "") if p.team_name else f"SOLO{p.id}"
        team_members.setdefault(team_prefix, []).append(p)

    rows = []
    for team_prefix, members in team_members.items():
        for member_num, p in enumerate(members, start=1):
            rows.append({
                "id": f"{team_prefix}_{member_num:03d}",
                "name": p.name,
                "email": p.email,
                "college": p.college or "",
                "skills": p.skills or "",
                "project_idea": p.project_idea or "",
                "team_name": p.team_name or f"Solo-{p.id}",
                "phone_number": p.phone_number or "",
                "ip_address": p.ip_address or "",
                "github_username": p.github_username or "",
                "ground_truth_label": p.ground_truth_label,
                "created_at": p.created_at,
                "_participant_id": p.id,
            })
    df = pd.DataFrame(rows)
    analyzed = ri.analyze(df.drop(columns=["_participant_id"]))
    analyzed["_participant_id"] = df["_participant_id"]
    metrics = ri.evaluate(analyzed)

    for _, row in analyzed.iterrows():
        participant = db.get(Participant, int(row["_participant_id"]))
        participant.final_trust_score = float(row["final_trust_score"])
        participant.final_risk_level = str(row["final_risk_level"])
        participant.confidence_score = float(row["confidence_score"])
        participant.anomaly_score = float(row["anomaly_score"])
        participant.fraud_ring_id = int(row["fraud_ring_id"])
        participant.reasons = list(row["reasons"])
        participant.explanation = str(row["explanation"])
        participant.predicted_label = str(row["predicted_label"])
    db.commit()

    return len(participants), metrics


@router.post("/reanalyze", response_model=ReanalyzeResult)
def reanalyze_registrations(
    hackathon_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can trigger a re-analysis")

    count, metrics = reanalyze_all_participants(hackathon_id, db)
    if count == 0:
        raise HTTPException(400, "No registrations to analyze yet")

    return ReanalyzeResult(participants_analyzed=count, ground_truth_metrics=metrics)


@router.post("/{participant_id}/approve", response_model=ApprovalAction)
def approve_registration(
    hackathon_id: int,
    participant_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can approve registrations")
    participant = db.get(Participant, participant_id)
    if not participant or participant.hackathon_id != hackathon_id:
        raise HTTPException(404, "Registration not found")
    participant.approval_status = "approved"
    db.commit()
    return ApprovalAction(participant_id=participant.id, approval_status="approved")


@router.post("/{participant_id}/reject", response_model=ApprovalAction)
def reject_registration(
    hackathon_id: int,
    participant_id: int,
    db: Session = Depends(get_db),
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if actor.role != "organizer":
        raise HTTPException(403, "Only the organizer can reject registrations")
    participant = db.get(Participant, participant_id)
    if not participant or participant.hackathon_id != hackathon_id:
        raise HTTPException(404, "Registration not found")
    participant.approval_status = "rejected"
    db.commit()
    return ApprovalAction(participant_id=participant.id, approval_status="rejected")


@router.get("/analytics", response_model=RegistrationAnalytics)
def registration_analytics(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    base = db.query(Participant).filter(Participant.hackathon_id == hackathon_id)
    total = base.count()
    if total == 0:
        return RegistrationAnalytics(
            total_registrations=0, total_teams=0, high_risk_count=0,
            medium_risk_count=0, low_risk_count=0, average_trust_score=0.0,
            fraud_rings_detected=0, statistical_anomalies=0,
        )

    total_teams = db.query(func.count(Team.id)).filter(Team.hackathon_id == hackathon_id).scalar() or 0
    high = base.filter(Participant.final_risk_level == "High Risk").count()
    medium = base.filter(Participant.final_risk_level == "Medium Risk").count()
    low = base.filter(Participant.final_risk_level == "Low Risk").count()
    avg_trust = db.query(func.avg(Participant.final_trust_score)).filter(Participant.hackathon_id == hackathon_id).scalar() or 0.0
    fraud_rings = (
        db.query(func.count(func.distinct(Participant.fraud_ring_id)))
        .filter(Participant.hackathon_id == hackathon_id, Participant.fraud_ring_id != -1)
        .scalar() or 0
    )
    anomalies = base.filter(Participant.anomaly_score >= 50).count()

    gt_rows = base.filter(Participant.ground_truth_label.isnot(None)).all()
    gt_metrics = None
    if gt_rows:
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        y_true = [r.ground_truth_label for r in gt_rows]
        y_pred = [r.predicted_label for r in gt_rows]
        acc = accuracy_score(y_true, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
        gt_metrics = {"accuracy": round(acc, 4), "macro_precision": round(prec, 4), "macro_recall": round(rec, 4), "macro_f1": round(f1, 4)}

    return RegistrationAnalytics(
        total_registrations=total,
        total_teams=total_teams,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        average_trust_score=round(float(avg_trust), 2),
        fraud_rings_detected=fraud_rings,
        statistical_anomalies=anomalies,
        ground_truth_metrics=gt_metrics,
    )


@router.get("/{participant_id}", response_model=ParticipantOut)
def get_registration(
    hackathon_id: int,
    participant_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    participant = db.get(Participant, participant_id)
    if not participant or participant.hackathon_id != hackathon_id:
        raise HTTPException(404, "Registration not found")
    return participant
