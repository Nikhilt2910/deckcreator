from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


def load_excel_preview(excel_path: Path) -> dict[str, object]:
    workbook = pd.read_excel(excel_path, sheet_name=None)
    first_sheet_name = next(iter(workbook.keys()), "")
    first_frame = workbook[first_sheet_name] if first_sheet_name else pd.DataFrame()
    return {
        "sheet_names": list(workbook.keys()),
        "row_count": int(len(first_frame.index)),
        "column_count": int(len(first_frame.columns)),
    }


def parse_excel_to_json(file_bytes: bytes, file_name: str) -> dict[str, Any]:
    workbook = pd.read_excel(BytesIO(file_bytes), sheet_name=None)
    sheets: list[dict[str, Any]] = []

    for sheet_name, frame in workbook.items():
        normalized = frame.copy()
        normalized.columns = [str(column) for column in normalized.columns]

        numeric_summary = {}
        numeric_columns = normalized.select_dtypes(include="number").columns.tolist()
        for column in numeric_columns[:10]:
            series = normalized[column].dropna()
            if series.empty:
                continue
            numeric_summary[str(column)] = {
                "min": _to_native(series.min()),
                "max": _to_native(series.max()),
                "mean": _to_native(round(series.mean(), 2)),
                "sum": _to_native(round(series.sum(), 2)),
            }

        categorical_summary = {}
        for column in normalized.select_dtypes(exclude="number").columns.tolist()[:6]:
            top_values = normalized[column].astype(str).value_counts().head(5).to_dict()
            categorical_summary[str(column)] = top_values

        sheets.append(
            {
                "sheet_name": str(sheet_name),
                "row_count": int(len(normalized.index)),
                "column_count": int(len(normalized.columns)),
                "columns": [str(column) for column in normalized.columns],
                "sample_rows": normalized.head(12).fillna("").to_dict(orient="records"),
                "numeric_summary": numeric_summary,
                "categorical_summary": categorical_summary,
            }
        )

    return {
        "file_name": file_name,
        "sheet_count": len(sheets),
        "sheets": sheets,
    }


def build_presentation_dataset(file_bytes: bytes) -> dict[str, Any]:
    frame = pd.read_excel(BytesIO(file_bytes))
    frame.columns = [str(column) for column in frame.columns]

    working = frame.copy()
    for column in ("Budget ($)", "Investment ($)", "Revenue ($)", "ROI (%)"):
        if column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")

    total_revenue = float(working.get("Revenue ($)", pd.Series(dtype=float)).fillna(0).sum())
    total_investment = float(working.get("Investment ($)", pd.Series(dtype=float)).fillna(0).sum())
    average_roi = float(working.get("ROI (%)", pd.Series(dtype=float)).fillna(0).mean())

    return {
        "kpis": {
            "campaign_count": f"{len(working):,}",
            "total_revenue": _format_currency(total_revenue),
            "total_investment": _format_currency(total_investment),
            "average_roi": f"{average_roi:.1f}%",
        },
        "channel_rows": _build_group_table(working, "Channel"),
        "region_rows": _build_group_table(working, "Region"),
        "top_campaign_rows": _build_campaign_table(working),
        "sample_rows": [
            {str(key): str(value) for key, value in row.items()}
            for row in working.head(6).fillna("").to_dict(orient="records")
        ],
    }


def _build_group_table(frame: pd.DataFrame, group_column: str) -> list[dict[str, str]]:
    if group_column not in frame.columns:
        return []

    grouped = (
        frame.groupby(group_column, dropna=False)
        .agg(revenue=("Revenue ($)", "sum"), roi=("ROI (%)", "mean"))
        .sort_values("revenue", ascending=False)
        .head(6)
        .reset_index()
    )

    rows: list[dict[str, str]] = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "label": str(row[group_column]),
                "value_1": _format_currency(float(row["revenue"])),
                "value_2": f"{float(row['roi']):.1f}%",
            }
        )
    return rows


def _build_campaign_table(frame: pd.DataFrame) -> list[dict[str, str]]:
    if "Campaign" not in frame.columns or "Revenue ($)" not in frame.columns or "ROI (%)" not in frame.columns:
        return []

    ranked = frame.sort_values("Revenue ($)", ascending=False).head(5)
    return [
        {
            "label": str(row["Campaign"]),
            "value_1": _format_currency(float(row["Revenue ($)"])),
            "value_2": f"{float(row['ROI (%)']):.1f}%",
        }
        for _, row in ranked.iterrows()
    ]


def _format_currency(value: float) -> str:
    return f"${value:,.0f}"


def _to_native(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value
