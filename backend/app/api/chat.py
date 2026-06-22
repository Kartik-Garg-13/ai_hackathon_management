from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.auth import CurrentActor, require_hackathon_scope, resolve_actor_by_token
from app.database import SessionLocal, get_db
from app.models import ChatMessage
from app.schemas import ChatMessageOut

router = APIRouter(prefix="/api/hackathons/{hackathon_id}/chat", tags=["chat"])
ws_router = APIRouter(tags=["chat"])


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, hackathon_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(hackathon_id, []).append(websocket)

    def disconnect(self, hackathon_id: int, websocket: WebSocket):
        if hackathon_id in self.connections and websocket in self.connections[hackathon_id]:
            self.connections[hackathon_id].remove(websocket)

    async def broadcast(self, hackathon_id: int, message: dict):
        for connection in self.connections.get(hackathon_id, []):
            await connection.send_json(message)


manager = ConnectionManager()


def _actor_display(actor: CurrentActor) -> tuple[str, int, str]:
    return actor.role, actor.actor.id, actor.actor.name


@router.get("/messages", response_model=list[ChatMessageOut])
def get_chat_history(
    hackathon_id: int,
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_hackathon_scope),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.hackathon_id == hackathon_id, ChatMessage.channel == "group")
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )


@ws_router.websocket("/ws/hackathons/{hackathon_id}/chat")
async def chat_websocket(websocket: WebSocket, hackathon_id: int, token: str):
    db = SessionLocal()
    actor = resolve_actor_by_token(token, db)
    if not actor or (actor.role != "organizer" and actor.hackathon_id != hackathon_id):
        db.close()
        await websocket.close(code=4401)
        return
    if actor.role == "organizer":
        db.close()
        await websocket.close(code=4403)
        return

    role, sender_id, sender_name = _actor_display(actor)
    await manager.connect(hackathon_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            body = (data.get("body") or "").strip()
            if not body:
                continue

            message = ChatMessage(
                hackathon_id=hackathon_id, channel="group",
                sender_role=role, sender_id=sender_id, sender_name=sender_name,
                body=body,
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            await manager.broadcast(hackathon_id, {
                "id": message.id,
                "sender_role": message.sender_role,
                "sender_name": message.sender_name,
                "body": message.body,
                "timestamp": message.timestamp.isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(hackathon_id, websocket)
    finally:
        db.close()
