#!/usr/bin/env python3
"""기여도 JSON을 터미널 스타일 애니메이션 SVG로 렌더링한다."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"

PALETTE = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0")
CELL, GAP, STEP, PAD, LABEL_WIDTH = 12, 3, 15, 22, 30


def color_level(count: int) -> int:
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def make_grid(days: list[dict]) -> list[list[dict | None]]:
    first = dt.date.fromisoformat(days[0]["date"])
    column: list[dict | None] = [None] * ((first.weekday() + 1) % 7)
    columns: list[list[dict | None]] = []
    for day in days:
        weekday = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7
        column.extend([None] * (weekday - len(column)))
        column.append(day)
        if len(column) == 7:
            columns.append(column)
            column = []
    if column:
        columns.append(column + [None] * (7 - len(column)))
    return columns


def render(data: dict) -> str:
    columns = make_grid(data["days"])
    art_width, art_height = len(columns) * STEP, 7 * STEP
    width = PAD + LABEL_WIDTH + art_width + PAD
    title_height, month_height, legend_height = 30, 20, 32
    height = title_height + month_height + art_height + legend_height + PAD
    left, top = PAD + LABEL_WIDTH, title_height + month_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>@keyframes reveal{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}.cell{opacity:0;animation:reveal .42s cubic-bezier(.2,.8,.2,1) both}</style>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0d1420"/><stop offset="1" stop-color="#0a0e14"/></linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/><rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="none" stroke="#1f6feb" stroke-opacity=".55"/>',
        f'<line x2="{width}" y1="{title_height}" y2="{title_height}" stroke="#1f6feb" stroke-opacity=".35"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(f'<text x="{width / 2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">codedbyminjae@github: ~/contributions --graph</text>')

    seen_months: set[tuple[int, int]] = set()
    for column_index, column in enumerate(columns):
        for day in column:
            if day is None:
                continue
            date = dt.date.fromisoformat(day["date"])
            month = (date.year, date.month)
            if month not in seen_months and date.day <= 7:
                seen_months.add(month)
                parts.append(f'<text x="{left + column_index * STEP}" y="44" fill="#7d8590" font-size="10">{date.strftime("%b")}</text>')
            break
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="{PAD}" y="{top + row * STEP + 9}" fill="#7d8590" font-size="9">{label}</text>')

    for column_index, column in enumerate(columns):
        for row_index, day in enumerate(column):
            if day is None:
                continue
            count = int(day["count"])
            delay = column_index * .018 + row_index * .045
            x, y = left + column_index * STEP, top + row_index * STEP
            parts.append(f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[color_level(count)]}" style="animation-delay:{delay:.3f}s"><title>{day["date"]}: {count} contribution{"s" if count != 1 else ""}</title></rect>')

    legend_y, legend_x = top + art_height + 6, width - PAD - 140
    parts.append(f'<text x="{legend_x}" y="{legend_y + 9}" fill="#7d8590" font-size="10" text-anchor="end">Less</text>')
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{legend_x + 8 + index * 12}" y="{legend_y}" width="11" height="11" rx="2.2" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 84}" y="{legend_y + 9}" fill="#7d8590" font-size="10">More</text>')

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    OUTPUT.write_text(render(json.loads(INPUT.read_text(encoding="utf-8"))), encoding="utf-8")
    print(f"{OUTPUT.name} 생성 완료")
