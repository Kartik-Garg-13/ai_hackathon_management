from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import generate_token, hash_password, verify_password
from app.database import get_db
from app.models import Organizer, Reviewer
from app.schemas import AuthSession, EmailLogin, OrganizerLogin, OrganizerSignup

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/organizer/signup", response_model=AuthSession)
def organizer_signup(payload: OrganizerSignup, db: Session = Depends(get_db)):
    existing = db.query(Organizer).filter(Organizer.email == payload.email).first()
    if existing:
        raise HTTPException(400, "An organizer with this email already exists")

    password_hash, salt = hash_password(payload.password)
    organizer = Organizer(
        name=payload.name,
        email=payload.email,
        password_hash=password_hash,
        password_salt=salt,
        auth_token=generate_token(),
        organization_name=payload.organization_name,
        contact_phone=payload.contact_phone,
        logo_url=payload.logo_url,
    )
    db.add(organizer)
    db.commit()
    db.refresh(organizer)
    return AuthSession(auth_token=organizer.auth_token, role="organizer", name=organizer.name)


@router.post("/organizer/login", response_model=AuthSession)
def organizer_login(payload: OrganizerLogin, db: Session = Depends(get_db)):
    organizer = db.query(Organizer).filter(Organizer.email == payload.email).first()
    if not organizer or not verify_password(payload.password, organizer.password_hash, organizer.password_salt):
        raise HTTPException(401, "Invalid email or password")

    organizer.auth_token = generate_token()
    db.commit()
    return AuthSession(auth_token=organizer.auth_token, role="organizer", name=organizer.name)


@router.post("/judge/login", response_model=AuthSession)
def judge_login(payload: EmailLogin, db: Session = Depends(get_db)):
    # Judges are invite-only and don't browse a public hackathon list, so this
    # looks them up by email alone across every hackathon rather than requiring
    # a hackathon_id up front like the participant/mentor login does.
    judge = db.query(Reviewer).filter(Reviewer.role == "judge", Reviewer.email == payload.email).first()
    if not judge:
        raise HTTPException(404, "No judge account found with that email — you'll need an invite link from the organizer")
    return AuthSession(auth_token=judge.auth_token, role="judge", name=judge.name, hackathon_id=judge.hackathon_id)
