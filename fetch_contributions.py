#!/usr/bin/env python3
"""공개 GitHub 기여도 데이터를 가져와 JSON으로 저장한다."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "codedbyminjae"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"


def count_for(cell, soup: BeautifulSoup) -> int:
    label = cell.get("aria-label", "")
    if cell_id := cell.get("id"):
        tooltip = soup.find("tool-tip", attrs={"for": cell_id})
        if tooltip:
            label = tooltip.get_text(" ", strip=True)
    match = re.search(r"(\d+) contribution", label, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def fetch_days() -> list[dict[str, str | int]]:
    response = requests.get(
        f"https://github.com/users/{USERNAME}/contributions",
        headers={"User-Agent": "codedbyminjae-profile-readme"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        raise RuntimeError("GitHub 기여도 달력을 찾지 못했어.")
    return sorted(
        [{"date": cell["data-date"], "count": count_for(cell, soup)} for cell in cells],
        key=lambda day: str(day["date"]),
    )


def calculate_streaks(days: list[dict[str, str | int]]) -> tuple[int, int]:
    counts = [int(day["count"]) for day in days]
    index = len(counts) - 1
    if counts and counts[-1] == 0:
        index -= 1
    current = 0
    while index >= 0 and counts[index] > 0:
        current += 1
        index -= 1

    longest = running = 0
    for count in counts:
        running = running + 1 if count > 0 else 0
        longest = max(longest, running)
    return current, longest


if __name__ == "__main__":
    days = fetch_days()
    current, longest = calculate_streaks(days)
    best = max(days, key=lambda day: int(day["count"]))
    data = {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total": sum(int(day["count"]) for day in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "days": days,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{data['total']:,}개 기여도를 저장했어.")
