import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


ANALYSIS_PROMPT = "You are a McKinsey consultant analyzing business data"
load_dotenv()


class AnalysisResult(BaseModel):
    key_insights: list[str] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    executive_summary: str


def analyze_data(
    data_json: dict[str, Any] | list[Any] | str,
    deck_prompt: str | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.4")
    payload = _normalize_data_json(data_json)

    additional_instructions = ""
    if deck_prompt and deck_prompt.strip():
        additional_instructions = (
            "\n\nAdditional user direction for this deck:\n"
            f"{deck_prompt.strip()}"
        )

    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": (
                    "Analyze the following business data for an executive marketing performance deck. "
                    "Return concise, board-ready insights grounded in the data. Focus on channel, region, "
                    "revenue, investment, and ROI patterns. Avoid generic recommendations and repeated ideas.\n\n"
                    f"Business data:\n{payload}"
                    f"{additional_instructions}"
                ),
            },
        ],
        text_format=AnalysisResult,
    )

    if response.output_parsed is None:
        raise ValueError("OpenAI returned no structured analysis.")
    return response.output_parsed.model_dump()


def build_analysis_job_hint(excel_path: Path) -> dict[str, str]:
    return {
        "status": "ready",
        "next_step": "parse_excel_and_analyze",
        "excel_path": str(excel_path),
    }


def _normalize_data_json(data_json: dict[str, Any] | list[Any] | str) -> str:
    if isinstance(data_json, str):
        return data_json
    import json

    return json.dumps(data_json, indent=2, ensure_ascii=True, default=str)
