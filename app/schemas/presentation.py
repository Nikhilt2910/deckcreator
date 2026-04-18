from pydantic import BaseModel, Field


class TableRow(BaseModel):
    label: str
    value_1: str
    value_2: str


class PresentationAnalysis(BaseModel):
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
