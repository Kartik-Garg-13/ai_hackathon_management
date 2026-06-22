from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_hackathon_scope, require_organizer
from app.database import get_db
from app.models import Hackathon, Organizer
from app.schemas import HackathonCreate, HackathonOut

router = APIRouter(prefix="/api/hackathons", tags=["hackathons"])


@router.post("", response_model=HackathonOut)
def create_hackathon(
    payload: HackathonCreate,
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    hackathon = Hackathon(organizer_id=organizer.id, **payload.model_dump())
    db.add(hackathon)
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.get("", response_model=list[HackathonOut])
def list_my_hackathons(
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    return db.query(Hackathon).filter(Hackathon.organizer_id == organizer.id).all()


@router.get("/public", response_model=list[HackathonOut])
def list_open_hackathons(include_closed: bool = False, db: Session = Depends(get_db)):
    if include_closed:
        return db.query(Hackathon).order_by(Hackathon.created_at.desc()).all()
    now = datetime.utcnow()
    return (
        db.query(Hackathon)
        .filter((Hackathon.registration_deadline.is_(None)) | (Hackathon.registration_deadline > now))
        .order_by(Hackathon.created_at.desc())
        .all()
    )


@router.get("/{hackathon_id}", response_model=HackathonOut)
def get_hackathon(hackathon_id: int, db: Session = Depends(get_db), _=Depends(require_hackathon_scope)):
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon:
        raise HTTPException(404, "Hackathon not found")
    return hackathon


def _get_owned_hackathon(hackathon_id: int, organizer: Organizer, db: Session) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if not hackathon or hackathon.organizer_id != organizer.id:
        raise HTTPException(404, "Hackathon not found")
    return hackathon


@router.post("/{hackathon_id}/stop", response_model=HackathonOut)
def stop_hackathon(
    hackathon_id: int,
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    hackathon = _get_owned_hackathon(hackathon_id, organizer, db)
    if hackathon.status != "active":
        raise HTTPException(400, f"Hackathon is already {hackathon.status}, not active")
    hackathon.status = "stopped"
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.post("/{hackathon_id}/resume", response_model=HackathonOut)
def resume_hackathon(
    hackathon_id: int,
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    hackathon = _get_owned_hackathon(hackathon_id, organizer, db)
    if hackathon.status != "stopped":
        raise HTTPException(400, f"Hackathon is {hackathon.status}, not stopped — nothing to resume")
    hackathon.status = "active"
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.post("/{hackathon_id}/end", response_model=HackathonOut)
def end_hackathon(
    hackathon_id: int,
    organizer: Organizer = Depends(require_organizer),
    db: Session = Depends(get_db),
):
    hackathon = _get_owned_hackathon(hackathon_id, organizer, db)
    if hackathon.status == "ended":
        raise HTTPException(400, "Hackathon has already ended")
    hackathon.status = "ended"
    db.commit()
    db.refresh(hackathon)
    return hackathon
