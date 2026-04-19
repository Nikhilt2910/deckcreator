from pydantic import BaseModel, Field


class AssistantSource(BaseModel):
    title: str
    url: str


class AssistantRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=4000)


class AssistantResponse(BaseModel):
    answer: str
    sources: list[AssistantSource] = Field(default_factory=list)

