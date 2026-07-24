"""Thread-safe in-memory storage for birthday rooms."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone
from threading import RLock
from typing import TypedDict


ROOM_CODE_PATTERN = re.compile(r"^[a-z0-9-]{1,40}$")


class BirthdayCount(TypedDict):
    month: int
    day: int
    count: int
    names: list[str]


class RoomSnapshot(TypedDict):
    room_code: str
    revision: int
    participant_count: int
    birthdays: list[BirthdayCount]
    updated_at: str | None


def normalize_room_code(room_code: str) -> str:
    """Normalize and validate a public room code."""
    normalized = room_code.strip().lower()
    if not ROOM_CODE_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Room codes may contain lowercase letters, numbers, and hyphens."
        )
    return normalized


def validate_birthday(month: int, day: int) -> None:
    """Validate a month/day pair, including February 29."""
    date(2000, month, day)


def normalize_display_name(display_name: str | None) -> str | None:
    """Normalize an optional public nickname and reject control characters."""
    if display_name is None:
        return None

    normalized = " ".join(display_name.split())
    if not normalized:
        return None
    if len(normalized) > 30:
        raise ValueError("Names and nicknames must be 30 characters or fewer.")
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        raise ValueError("Names and nicknames cannot contain control characters.")
    return normalized


class RoomStore:
    """Store one birthday per anonymous visitor in each room."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._birthdays: dict[
            str,
            dict[str, tuple[int, int, str | None]],
        ] = {}
        self._revisions: dict[str, int] = {}
        self._updated_at: dict[str, str] = {}

    def submit_birthday(
        self,
        room_code: str,
        visitor_id: str,
        month: int,
        day: int,
        display_name: str | None = None,
    ) -> RoomSnapshot:
        """Create or replace one visitor's birthday and return a snapshot."""
        room_code = normalize_room_code(room_code)
        validate_birthday(month, day)
        display_name = normalize_display_name(display_name)

        with self._lock:
            room = self._birthdays.setdefault(room_code, {})
            birthday = (month, day, display_name)
            if room.get(visitor_id) != birthday:
                room[visitor_id] = birthday
                self._revisions[room_code] = self._revisions.get(room_code, 0) + 1
                self._updated_at[room_code] = datetime.now(timezone.utc).isoformat()
            return self._snapshot_unlocked(room_code)

    def snapshot(self, room_code: str) -> RoomSnapshot:
        """Return an aggregate-only snapshot for a room."""
        room_code = normalize_room_code(room_code)
        with self._lock:
            return self._snapshot_unlocked(room_code)

    def clear(self) -> None:
        """Clear all rooms. Intended for tests and local rehearsals."""
        with self._lock:
            self._birthdays.clear()
            self._revisions.clear()
            self._updated_at.clear()

    def _snapshot_unlocked(self, room_code: str) -> RoomSnapshot:
        room = self._birthdays.get(room_code, {})
        counts = Counter((month, day) for month, day, _name in room.values())
        names_by_birthday: dict[tuple[int, int], list[str]] = {}
        for month, day, display_name in room.values():
            if display_name:
                names_by_birthday.setdefault((month, day), []).append(display_name)
        birthdays: list[BirthdayCount] = [
            {
                "month": month,
                "day": day,
                "count": count,
                "names": sorted(names_by_birthday.get((month, day), []), key=str.casefold),
            }
            for (month, day), count in sorted(counts.items())
        ]
        return {
            "room_code": room_code,
            "revision": self._revisions.get(room_code, 0),
            "participant_count": len(room),
            "birthdays": birthdays,
            "updated_at": self._updated_at.get(room_code),
        }


room_store = RoomStore()
