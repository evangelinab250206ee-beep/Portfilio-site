"""PDF report export for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd


def create_pdf_report(comparison: pd.DataFrame, recommendation: dict, output_path: Union[str, Path]) -> Path:
    """Create a concise engineering report PDF; reportlab is imported only on export."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as error:
        raise RuntimeError("PDF export requires reportlab. Run pip install -r requirements.txt.") from error
    path = Path(output_path)
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(str(path), pagesize=A4)
    story = [Paragraph("Solar-Assisted EV Route Optimisation Report", styles["Title"]), Spacer(1, 12)]
    story.extend([
        Paragraph(f"Recommended Route: <b>{recommendation['best_route']}</b>", styles["Heading2"]),
        Paragraph(recommendation["reason"], styles["BodyText"]), Spacer(1, 12),
    ])
    columns = ["route", "total_distance_km", "estimated_travel_time_hours", "total_solar_energy_kwh", "total_energy_consumed_kwh", "final_battery_remaining_percent", "route_score"]
    table_data = [["Route", "Distance km", "Time h", "Solar kWh", "Used kWh", "Battery %", "Score"]]
    for row in comparison[columns].itertuples(index=False):
        table_data.append([str(value) if not isinstance(value, float) else f"{value:.2f}" for value in row])
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(table)
    document.build(story)
    return path
