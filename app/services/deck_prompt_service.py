import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from app.schemas.presentation import PresentationTheme, TableRow


load_dotenv()


THEME_RESEARCH_PROMPT = (
    "You are a presentation design researcher. If the user mentions a company, brand, visual reference, "
    "or design style, use web search to infer practical slide-design guidance: palette direction, tone, "
    "typography feel, and composition cues. If the prompt is generic, produce a concise neutral theme brief "
    "for a modern executive deck. Keep the result under 180 words."
)

PROMPT_DECK_SYSTEM_PROMPT = (
    "You convert a user request into a polished executive presentation brief. "
    "When no workbook is provided, create plausible, clearly directional slide content suitable for a demo deck. "
    "Do not claim to have measured real business results unless data was supplied. "
    "Keep the narrative concise, board-ready, and internally consistent."
)


class PromptOnlyDeckPlan(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    executive_summary: str = Field(..., min_length=1)
    key_insights: list[str] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    kpis: dict[str, str] = Field(default_factory=dict)
    channel_rows: list[TableRow] = Field(default_factory=list)
    region_rows: list[TableRow] = Field(default_factory=list)
    top_campaign_rows: list[TableRow] = Field(default_factory=list)
    sample_rows: list[dict[str, str]] = Field(default_factory=list)
    theme: PresentationTheme


class ThemePlan(BaseModel):
    theme_name: str = Field(default="Professional Editorial")
    design_summary: str = Field(default="")
    colors: dict[str, str] = Field(default_factory=dict)
    fonts: dict[str, str] = Field(default_factory=dict)


def build_prompt_only_deck_plan(
    prompt: str,
    reference_context: dict[str, str] | None = None,
) -> PromptOnlyDeckPlan:
    if not prompt or not prompt.strip():
        raise ValueError("A prompt is required to generate a deck without an Excel workbook.")

    client = _build_client()
    model = os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.4")
    theme = research_theme_from_prompt(prompt)
    reference_summary = _build_reference_summary(reference_context)

    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": PROMPT_DECK_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "Build a concise executive presentation plan from this request.\n\n"
                    f"User prompt:\n{prompt.strip()}\n\n"
                    f"Theme direction:\n{theme.model_dump_json(indent=2)}\n\n"
                    f"Reference context:\n{reference_summary}\n\n"
                    "Return:\n"
                    "- a strong deck title\n"
                    "- one executive summary paragraph\n"
                    "- 3 to 5 key insights\n"
                    "- 3 to 5 trends\n"
                    "- 2 to 4 risks\n"
                    "- 4 KPI values as presentation-friendly strings\n"
                    "- 3 short tables for channels, regions, and top campaigns\n"
                    "- 3 to 5 sample data rows\n"
                    "- a presentation theme with usable hex colors and presentation-appropriate fonts\n\n"
                    "If numeric facts are missing, use plausible demo-level directional placeholders rather than "
                    "pretending they are measured source data."
                ),
            },
        ],
        text_format=PromptOnlyDeckPlan,
    )

    if response.output_parsed is None:
        raise ValueError("OpenAI returned no structured prompt-only deck plan.")
    return response.output_parsed


def research_theme_from_prompt(prompt: str) -> PresentationTheme:
    if not prompt or not prompt.strip():
        return PresentationTheme()

    client = _build_client()
    model = os.getenv("OPENAI_CHAT_MODEL", os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.4"))
    notes = client.responses.create(
        model=model,
        instructions=THEME_RESEARCH_PROMPT,
        input=prompt.strip(),
        tools=[
            {
                "type": "web_search",
                "user_location": {
                    "type": "approximate",
                    "country": "US",
                },
            }
        ],
    )

    research_notes = (getattr(notes, "output_text", None) or "").strip()
    if not research_notes:
        return PresentationTheme()

    parsed = client.responses.parse(
        model=os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.4"),
        input=[
            {
                "role": "system",
                "content": (
                    "Convert presentation design research notes into a concrete deck theme. "
                    "Use clean hex colors only. Favor modern, widely available presentation fonts."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User prompt:\n{prompt.strip()}\n\n"
                    f"Research notes:\n{research_notes}\n\n"
                    "Return a theme with these color keys when possible: canvas, ink, muted, accent, "
                    "accent_soft, line, card, stripe, danger."
                ),
            },
        ],
        text_format=ThemePlan,
    )

    if parsed.output_parsed is None:
        return PresentationTheme()
    return PresentationTheme(**parsed.output_parsed.model_dump())


def _build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def _build_reference_summary(reference_context: dict[str, str] | None) -> str:
    if not reference_context:
        return "No reference file was provided."

    reference_type = reference_context.get("reference_type", "unknown")
    reference_text = (reference_context.get("reference_text") or "").strip()
    if not reference_text:
        return f"Reference type: {reference_type}. No extractable text was available."
    return f"Reference type: {reference_type}\nReference text:\n{reference_text[:4000]}"
