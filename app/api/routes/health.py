from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, object]:
    return {
        "name": "DeckCreator Full Stack API",
        "status": "ok",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_routes": {
            "upload": "/api/upload",
            "ticket": "/api/ticket",
            "approve": "/api/approve",
            "reject": "/api/reject",
            "assistant": "/api/assistant/respond",
        },
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
