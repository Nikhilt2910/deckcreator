from fastapi import APIRouter, HTTPException

from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant_service import answer_with_web_search


router = APIRouter(prefix="/api", tags=["api-assistant"])


@router.post("/assistant/respond", response_model=AssistantResponse)
async def assistant_respond(payload: AssistantRequest) -> AssistantResponse:
    try:
        return answer_with_web_search(payload.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Assistant request failed: {exc}") from exc

