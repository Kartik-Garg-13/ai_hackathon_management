from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import generate_token, require_organizer
from app.database import get_db
from app.models import Hackathon, InviteLink, Organizer, Participant, Reviewer, Team
from app.schemas import (
    AuthSession,
    EmailLogin,
    InviteInfo,
    InviteLinkOut,
    ParticipantRegisterViaInvite,
    ReviewerRegisterViaInvite,
)
from app.services.registration_intelligence import email_intelligence, phone_validity

router = APIRouter(prefix="/api/hackathons", tags=["invites"])
invite_router = APIRouter(prefix="/api/invite", tags=["invites"])

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_or_create_self_team(db: Session, hackathon_id: int, team_name: str | None, participant_name: str) -> Team:
    name = (team_name or "").strip() or f"{participant_name}'s Team"
    existing = (
        db.query(Team)
        .filter(Team.hackathon_id == hackathon_id, Team.team_name.ilike(name))
        .first()
    )
    if existing:
        existing.team_size = (existing.team_size or 0) + 1
        return existing
    team = Team(
        hackathon_id=hackathon_id,
        team_id_str=f"self-{generate_token()[:12]}",
        team_name=name,
        team_size=1,
    )
    db.add(team)
    db.flush()
    return team


@router.post("/{hackathon_id}/invite-links/generate", response_model=list[InviteLinkOut])
def generate_invite_links(
    hackathon_id: int,
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon or hackathon.organizer_id != organizer.id:
        raise HTTPException(404, "Hackathon not found")

    roles = ["judge"] if hackathon.allow_judges else []

    existing = {l.role: l for l in db.query(InviteLink).filter(InviteLink.hackathon_id == hackathon_id).all()}
    created = []
    for role in roles:
        if role in existing:
            created.append(existing[role])
            continue
        link = InviteLink(hackathon_id=hackathon_id, role=role, token=generate_token())
        db.add(link)
        created.append(link)
    db.commit()
    for link in created:
        db.refresh(link)
    return created


@router.get("/{hackathon_id}/invite-links", response_model=list[InviteLinkOut])
def list_invite_links(
    hackathon_id: int,
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon or hackathon.organizer_id != organizer.id:
        raise HTTPException(404, "Hackathon not found")
    return db.query(InviteLink).filter(InviteLink.hackathon_id == hackathon_id).all()


@invite_router.get("/{token}", response_model=InviteInfo)
def resolve_invite(token: str, db: Session = Depends(get_db)):
    link = db.query(InviteLink).filter(InviteLink.token == token).first()
    if not link:
        raise HTTPException(404, "Invite link not found or expired")
    hackathon = db.get(Hackathon, link.hackathon_id)
    return InviteInfo(hackathon_id=hackathon.id, hackathon_name=hackathon.name, role=link.role)


def _register_reviewer(db: Session, hackathon_id: int, role: str, payload: ReviewerRegisterViaInvite) -> Reviewer:
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon:
        raise HTTPException(404, "Hackathon not found")
    if role == "mentor" and not hackathon.allow_mentors:
        raise HTTPException(400, "This hackathon isn't accepting mentor registrations")
    if hackathon.registration_deadline and datetime.utcnow() > hackathon.registration_deadline:
        raise HTTPException(400, "Registration for this hackathon has closed")

    duplicate = (
        db.query(Reviewer)
        .filter(Reviewer.hackathon_id == hackathon_id, Reviewer.email == payload.email)
        .first()
    )
    if duplicate:
        raise HTTPException(400, "This email is already registered for this hackathon")

    reviewer = Reviewer(
        hackathon_id=hackathon_id,
        role=role,
        auth_token=generate_token(),
        **payload.model_dump(),
    )
    db.add(reviewer)
    db.commit()
    db.refresh(reviewer)
    return reviewer


def _register_participant(db: Session, hackathon_id: int, payload: ParticipantRegisterViaInvite, server_ip: str) -> Participant:
    if not payload.consent_accepted:
        raise HTTPException(400, "You must accept the code of conduct to register")

    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon:
        raise HTTPException(404, "Hackathon not found")
    if hackathon.registration_deadline and datetime.utcnow() > hackathon.registration_deadline:
        raise HTTPException(400, "Registration for this hackathon has closed")

    duplicate = (
        db.query(Participant)
        .filter(Participant.hackathon_id == hackathon_id, Participant.email == payload.email)
        .first()
    )
    if duplicate:
        raise HTTPException(400, "This email is already registered for this hackathon")

    reasons = []
    email_check = email_intelligence(payload.email)
    reasons.extend(email_check["flags"])
    if payload.phone_number:
        valid, _ = phone_validity(payload.phone_number)
        if not valid:
            reasons.append("Invalid Phone Format")
    if payload.claimed_ip_address and payload.claimed_ip_address != server_ip:
        reasons.append("Claimed IP Does Not Match Observed IP")

    team = get_or_create_self_team(db, hackathon_id, payload.team_name, payload.name)

    participant = Participant(
        hackathon_id=hackathon_id,
        registration_id=generate_token()[:16],
        auth_token=generate_token(),
        team_id=team.id,
        ip_address=server_ip,
        approval_status="pending",
        reasons=reasons,
        explanation=(
            "Awaiting full risk analysis — instant checks only: " + (", ".join(reasons) if reasons else "no red flags")
        ),
        **payload.model_dump(),
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@invite_router.post("/{token}/register/reviewer", response_model=AuthSession)
def register_reviewer_via_invite(token: str, payload: ReviewerRegisterViaInvite, db: Session = Depends(get_db)):
    link = db.query(InviteLink).filter(InviteLink.token == token).first()
    if not link or link.role not in ("judge", "mentor"):
        raise HTTPException(404, "Invite link not found or not valid for judges/mentors")

    reviewer = _register_reviewer(db, link.hackathon_id, link.role, payload)
    return AuthSession(auth_token=reviewer.auth_token, role=reviewer.role, name=reviewer.name, hackathon_id=reviewer.hackathon_id)


@invite_router.post("/{token}/register/participant", response_model=AuthSession)
def register_participant_via_invite(
    token: str,
    payload: ParticipantRegisterViaInvite,
    request: Request,
    db: Session = Depends(get_db),
):
    link = db.query(InviteLink).filter(InviteLink.token == token).first()
    if not link or link.role != "participant":
        raise HTTPException(404, "Invite link not found or not valid for participants")

    participant = _register_participant(db, link.hackathon_id, payload, get_client_ip(request))
    return AuthSession(auth_token=participant.auth_token, role="participant", name=participant.name, hackathon_id=participant.hackathon_id)


@router.post("/{hackathon_id}/register/participant", response_model=AuthSession)
def register_participant_open(
    hackathon_id: int,
    payload: ParticipantRegisterViaInvite,
    request: Request,
    db: Session = Depends(get_db),
):
    participant = _register_participant(db, hackathon_id, payload, get_client_ip(request))
    return AuthSession(auth_token=participant.auth_token, role="participant", name=participant.name, hackathon_id=participant.hackathon_id)


@router.post("/{hackathon_id}/login/participant", response_model=AuthSession)
def login_participant(hackathon_id: int, payload: EmailLogin, db: Session = Depends(get_db)):
    participant = (
        db.query(Participant)
        .filter(Participant.hackathon_id == hackathon_id, Participant.email == payload.email)
        .first()
    )
    if not participant:
        raise HTTPException(404, "No participant registered with that email for this hackathon")
    if participant.approval_status == "rejected":
        raise HTTPException(403, "This registration was rejected by the organizer — contact them for help")
    return AuthSession(auth_token=participant.auth_token, role="participant", name=participant.name, hackathon_id=participant.hackathon_id)


@router.post("/{hackathon_id}/login/reviewer", response_model=AuthSession)
def login_reviewer(hackathon_id: int, payload: EmailLogin, db: Session = Depends(get_db)):
    reviewer = (
        db.query(Reviewer)
        .filter(Reviewer.hackathon_id == hackathon_id, Reviewer.email == payload.email)
        .first()
    )
    if not reviewer:
        raise HTTPException(404, "No mentor or judge registered with that email for this hackathon")
    return AuthSession(auth_token=reviewer.auth_token, role=reviewer.role, name=reviewer.name, hackathon_id=reviewer.hackathon_id)


@router.post("/{hackathon_id}/register/mentor", response_model=AuthSession)
def register_mentor_open(hackathon_id: int, payload: ReviewerRegisterViaInvite, db: Session = Depends(get_db)):
    reviewer = _register_reviewer(db, hackathon_id, "mentor", payload)
    return AuthSession(auth_token=reviewer.auth_token, role=reviewer.role, name=reviewer.name, hackathon_id=reviewer.hackathon_id)
