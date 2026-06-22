import hashlib
import hmac
import secrets
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organizer, Participant, Reviewer

PBKDF2_ITERATIONS = 200_000


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate, password_hash)


@dataclass
class CurrentActor:
    role: str
    hackathon_id: int | None
    actor: Organizer | Reviewer | Participant


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    return authorization.removeprefix("Bearer ").strip()


def resolve_actor_by_token(token: str, db: Session) -> CurrentActor | None:
    organizer = db.query(Organizer).filter(Organizer.auth_token == token).first()
    if organizer:
        return CurrentActor(role="organizer", hackathon_id=None, actor=organizer)

    reviewer = db.query(Reviewer).filter(Reviewer.auth_token == token).first()
    if reviewer:
        return CurrentActor(role=reviewer.role, hackathon_id=reviewer.hackathon_id, actor=reviewer)

    participant = db.query(Participant).filter(Participant.auth_token == token).first()
    if participant:
        if participant.approval_status == "rejected":
            return None
        return CurrentActor(role="participant", hackathon_id=participant.hackathon_id, actor=participant)

    return None


def get_current_actor(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentActor:
    token = _extract_token(authorization)
    actor = resolve_actor_by_token(token, db)
    if not actor:
        raise HTTPException(401, "Invalid or expired token")
    return actor


def require_organizer(current: CurrentActor = Depends(get_current_actor)) -> Organizer:
    if current.role != "organizer":
        raise HTTPException(403, "Organizer access required")
    return current.actor


def require_hackathon_scope(
    hackathon_id: int,
    current: CurrentActor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> CurrentActor:
    if current.role == "organizer":
        from app.models import Hackathon

        hackathon = db.get(Hackathon, hackathon_id)
        if not hackathon or hackathon.organizer_id != current.actor.id:
            raise HTTPException(403, "Not authorized for this hackathon")
        return current
    if current.hackathon_id != hackathon_id:
        raise HTTPException(403, "Not authorized for this hackathon")
    return current
