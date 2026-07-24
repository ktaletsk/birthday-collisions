"""Run the FastAPI application that serves the audience UI and marimo deck."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import marimo
from fastapi import FastAPI, HTTPException, Path as PathParameter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from birthday_room.store import (
    normalize_room_code,
    room_store,
)


PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = PROJECT_ROOT / "birthday_room"


class BirthdaySubmission(BaseModel):
    visitor_id: str = Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    display_name: str | None = Field(default=None, max_length=30)


RoomCode = Annotated[
    str,
    PathParameter(
        min_length=1,
        max_length=40,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
]


def _room_code_or_404(room_code: str) -> str:
    try:
        return normalize_room_code(room_code)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def create_app(*, include_deck: bool = True) -> FastAPI:
    """Build the combined audience and presentation application."""
    app = FastAPI(
        title="Marimo Live Voting",
        description="Audience input powering a reactive marimo presentation.",
    )
    templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")

    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_ROOT / "static"),
        name="static",
    )

    @app.get("/", include_in_schema=False)
    async def index() -> RedirectResponse:
        return RedirectResponse(url="/deck/")

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/join/{room_code}", response_class=HTMLResponse)
    async def join_room(request: Request, room_code: RoomCode) -> HTMLResponse:
        normalized = _room_code_or_404(room_code)
        return templates.TemplateResponse(
            request=request,
            name="join.html",
            context={"room_code": normalized},
        )

    @app.get("/api/rooms/{room_code}/state")
    async def room_state(room_code: RoomCode) -> dict[str, object]:
        normalized = _room_code_or_404(room_code)
        return room_store.snapshot(normalized)

    @app.post("/api/rooms/{room_code}/birthday")
    async def submit_birthday(
        room_code: RoomCode,
        submission: BirthdaySubmission,
    ) -> dict[str, object]:
        normalized = _room_code_or_404(room_code)
        try:
            snapshot = room_store.submit_birthday(
                normalized,
                submission.visitor_id,
                submission.month,
                submission.day,
                submission.display_name,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        birthday_count = next(
            item["count"]
            for item in snapshot["birthdays"]
            if item["month"] == submission.month and item["day"] == submission.day
        )
        return {
            "ok": True,
            "your_birthday_count": birthday_count,
            "snapshot": snapshot,
        }

    if include_deck:
        deck = (
            marimo.create_asgi_app()
            .with_app(path="", root=str(PROJECT_ROOT / "custom.py"))
            .build()
        )
        app.mount("/deck", deck)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8010")),
    )
