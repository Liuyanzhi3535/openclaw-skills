import pytest


async def test_list_events_returns_events(client, mock_google_service):
    mock_google_service.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "abc123",
                "summary": "牙醫預約",
                "start": {"dateTime": "2026-03-30T10:00:00+08:00"},
                "end": {"dateTime": "2026-03-30T11:00:00+08:00"},
            }
        ]
    }

    response = await client.post(
        "/skill/calendar-gcal/list",
        json={
            "time_min": "2026-03-30T00:00:00+08:00",
            "time_max": "2026-03-30T23:59:59+08:00",
        },
    )

    assert response.status_code == 200
    events = response.json()["events"]
    assert len(events) == 1
    assert events[0]["id"] == "abc123"
    assert events[0]["summary"] == "牙醫預約"


async def test_list_events_empty(client, mock_google_service):
    mock_google_service.events.return_value.list.return_value.execute.return_value = {"items": []}

    response = await client.post(
        "/skill/calendar-gcal/list",
        json={
            "time_min": "2026-03-30T00:00:00+08:00",
            "time_max": "2026-03-30T23:59:59+08:00",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"events": []}


async def test_create_event(client, mock_google_service):
    mock_google_service.events.return_value.insert.return_value.execute.return_value = {
        "id": "new123",
        "summary": "健身",
        "start": {"dateTime": "2026-04-01T08:00:00+08:00"},
        "end": {"dateTime": "2026-04-01T09:00:00+08:00"},
        "htmlLink": "https://calendar.google.com/event?eid=new123",
    }

    response = await client.post(
        "/skill/calendar-gcal/create",
        json={
            "summary": "健身",
            "start": "2026-04-01T08:00:00+08:00",
            "end": "2026-04-01T09:00:00+08:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "new123"
    assert body["summary"] == "健身"
    assert "html_link" in body


async def test_list_events_missing_token(client):
    """Token 不存在時應回傳 503。"""
    response = await client.post(
        "/skill/calendar-gcal/list",
        json={
            "time_min": "2026-03-30T00:00:00+08:00",
            "time_max": "2026-03-30T23:59:59+08:00",
        },
    )
    assert response.status_code == 503
