from fastapi import APIRouter

from app.schemas import CopilotAnswer, CopilotQuestion
from app.services import copilot

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("/ask", response_model=CopilotAnswer)
def ask_copilot(payload: CopilotQuestion):
    result = copilot.ask(payload.question)
    return CopilotAnswer(
        answer=result.answer,
        matched_question=result.matched_question,
        confidence=result.confidence,
    )
