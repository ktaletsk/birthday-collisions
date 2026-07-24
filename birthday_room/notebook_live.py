"""The small bridge between the live room and the marimo notebook."""

from __future__ import annotations

import calendar
import os
from datetime import date
from typing import Any

import segno

from birthday_room.store import RoomSnapshot, room_store


ROOM_CODE = os.getenv("VOTING_ROOM", "demo")
REFRESH_INTERVAL = os.getenv("VOTE_REFRESH_INTERVAL", "1s")
PUBLIC_URL = os.getenv("PUBLIC_URL", "").rstrip("/")


def join_url(request: Any | None) -> str:
    if PUBLIC_URL:
        return f"{PUBLIC_URL}/join/{ROOM_CODE}"
    if request is None:
        return f"http://127.0.0.1:8010/join/{ROOM_CODE}"

    host = request.headers.get("x-forwarded-host")
    host = host or request.headers.get("host") or "127.0.0.1:8010"
    scheme = request.headers.get("x-forwarded-proto") or "http"
    return f"{scheme}://{host}/join/{ROOM_CODE}"


def qr_data_uri(url: str) -> str:
    return segno.make_qr(url, error="m").svg_data_uri(
        scale=5,
        border=4,
        dark="#111827",
        light="#ffffff",
    )


def snapshot() -> RoomSnapshot:
    return room_store.snapshot(ROOM_CODE)


def attendance(participants: int) -> str:
    noun = "person" if participants == 1 else "people"
    return f"{participants} {noun} checked in"


def corner_styles(qr_code: str, participants: int) -> str:
    safe_qr_code = qr_code.replace('"', '\\"')
    return (
        "<style>"
        ".reveal-viewport::after {"
        f'content: "{attendance(participants)}";'
        f'background-image: url("{safe_qr_code}");'
        "}"
        "</style>"
    )


def collision_summary(room: RoomSnapshot) -> str:
    matches = [birthday for birthday in room["birthdays"] if birthday["count"] > 1]
    if not matches:
        return "No exact collision yet."

    match = matches[0]
    date = f"{calendar.month_name[match['month']]} {match['day']}"
    people = ", ".join(match["names"]) or "mystery guests"
    return f"**Collision!** {date}: {people}."


def near_miss_summary(room: RoomSnapshot) -> str:
    birthdays_by_day = {
        date(2000, birthday["month"], birthday["day"]).timetuple().tm_yday: birthday
        for birthday in room["birthdays"]
    }
    for day, birthday in birthdays_by_day.items():
        neighbor = birthdays_by_day.get(day % 366 + 1)
        if neighbor is not None:
            first = f"{calendar.month_name[birthday['month']]} {birthday['day']}"
            second = f"{calendar.month_name[neighbor['month']]} {neighbor['day']}"
            return f"**Near miss!** {first} and {second} are both represented."
    return "No birthdays one day apart yet."
