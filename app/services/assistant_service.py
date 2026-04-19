import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.assistant import AssistantResponse, AssistantSource


load_dotenv()

ASSISTANT_PROMPT = (
    "You are DeckCreator's research copilot. Answer like a strong ChatGPT web-search session: "
    "concise, direct, current, and grounded in live sources. Prefer practical guidance over theory. "
    "When the user asks for recommendations or current information, rely on web search."
)


def answer_with_web_search(prompt: str) -> AssistantResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4")
    response = client.responses.create(
        model=model,
        instructions=ASSISTANT_PROMPT,
        input=prompt,
        tools=[
            {
                "type": "web_search",
                "user_location": {
                    "type": "approximate",
                    "country": "US",
                },
            }
        ],
        include=["web_search_call.action.sources"],
    )

    answer = (getattr(response, "output_text", None) or "").strip()
    if not answer:
        raise ValueError("OpenAI returned no assistant answer.")

    payload = response.model_dump() if hasattr(response, "model_dump") else {}
    sources = _extract_sources(payload)
    return AssistantResponse(answer=answer, sources=sources)


def _extract_sources(payload: dict[str, Any]) -> list[AssistantSource]:
    if not payload:
        return []

    deduped: dict[str, AssistantSource] = {}
    for item in payload.get("output", []):
        if item.get("type") != "web_search_call":
            continue
        for source in item.get("action", {}).get("sources", []):
            url = source.get("url")
            title = source.get("title") or source.get("site_name") or url
            if not url or not title:
                continue
            deduped[url] = AssistantSource(title=title, url=url)

    return list(deduped.values())

