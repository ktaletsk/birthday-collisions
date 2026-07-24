from fastapi.testclient import TestClient

from main import create_app
from birthday_room.store import room_store


def make_client() -> TestClient:
    room_store.clear()
    return TestClient(create_app(include_deck=False))


def test_join_page_is_served() -> None:
    client = make_client()

    response = client.get("/join/Demo")

    assert response.status_code == 200
    assert "When is your birthday?" in response.text
    assert "Name or nickname" in response.text
    assert 'data-room="demo"' in response.text


def test_two_people_can_create_an_exact_match() -> None:
    client = make_client()

    first = client.post(
        "/api/rooms/demo/birthday",
        json={
            "visitor_id": "visitor-one",
            "month": 7,
            "day": 24,
            "display_name": "Maya",
        },
    )
    second = client.post(
        "/api/rooms/demo/birthday",
        json={
            "visitor_id": "visitor-two",
            "month": 7,
            "day": 24,
            "display_name": "Anton",
        },
    )

    assert first.status_code == 200
    assert first.json()["your_birthday_count"] == 1
    assert second.status_code == 200
    assert second.json()["your_birthday_count"] == 2

    state = client.get("/api/rooms/demo/state").json()
    assert state["participant_count"] == 2
    assert state["birthdays"] == [
        {
            "month": 7,
            "day": 24,
            "count": 2,
            "names": ["Anton", "Maya"],
        }
    ]


def test_a_visitor_updates_instead_of_voting_twice() -> None:
    client = make_client()

    client.post(
        "/api/rooms/demo/birthday",
        json={"visitor_id": "same-visitor", "month": 1, "day": 2},
    )
    response = client.post(
        "/api/rooms/demo/birthday",
        json={"visitor_id": "same-visitor", "month": 12, "day": 31},
    )

    snapshot = response.json()["snapshot"]
    assert snapshot["participant_count"] == 1
    assert snapshot["revision"] == 2
    assert snapshot["birthdays"] == [
        {"month": 12, "day": 31, "count": 1, "names": []}
    ]


def test_invalid_calendar_date_is_rejected() -> None:
    client = make_client()

    response = client.post(
        "/api/rooms/demo/birthday",
        json={"visitor_id": "visitor-bad-date", "month": 2, "day": 30},
    )

    assert response.status_code == 422
    assert "day is out of range" in response.json()["detail"]


def test_february_29_is_supported() -> None:
    client = make_client()

    response = client.post(
        "/api/rooms/demo/birthday",
        json={"visitor_id": "leap-visitor", "month": 2, "day": 29},
    )

    assert response.status_code == 200
    assert response.json()["snapshot"]["birthdays"] == [
        {"month": 2, "day": 29, "count": 1, "names": []}
    ]


def test_optional_name_is_normalized_and_can_be_updated() -> None:
    client = make_client()

    first = client.post(
        "/api/rooms/demo/birthday",
        json={
            "visitor_id": "named-visitor",
            "month": 4,
            "day": 8,
            "display_name": "  Ada   Lovelace  ",
        },
    )
    second = client.post(
        "/api/rooms/demo/birthday",
        json={
            "visitor_id": "named-visitor",
            "month": 4,
            "day": 8,
            "display_name": "",
        },
    )

    assert first.status_code == 200
    assert first.json()["snapshot"]["birthdays"][0]["names"] == ["Ada Lovelace"]
    assert second.status_code == 200
    assert second.json()["snapshot"]["birthdays"][0]["names"] == []
    assert second.json()["snapshot"]["revision"] == 2


def test_name_length_is_limited() -> None:
    client = make_client()

    response = client.post(
        "/api/rooms/demo/birthday",
        json={
            "visitor_id": "verbose-visitor",
            "month": 5,
            "day": 1,
            "display_name": "x" * 31,
        },
    )

    assert response.status_code == 422
