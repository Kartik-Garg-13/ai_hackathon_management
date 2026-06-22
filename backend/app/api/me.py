from fastapi import APIRouter, Depends

from app.auth import CurrentActor, require_hackathon_scope
from app.models import Organizer, Participant, Reviewer
from app.schemas import OrganizerOut, ParticipantOut, ReviewerOut

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/me", tags=["me"])


@router.get("")
def get_me(
    hackathon_id: int,
    actor: CurrentActor = Depends(require_hackathon_scope),
):
    if isinstance(actor.actor, Organizer):
        profile = OrganizerOut.model_validate(actor.actor).model_dump()
    elif isinstance(actor.actor, Reviewer):
        profile = ReviewerOut.model_validate(actor.actor).model_dump()
    elif isinstance(actor.actor, Participant):
        profile = ParticipantOut.model_validate(actor.actor).model_dump()
    else:
        profile = {}

    return {"role": actor.role, **profile}
