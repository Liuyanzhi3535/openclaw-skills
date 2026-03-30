from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

router = APIRouter(prefix="/skill/calendar-gcal")

TOKEN_PATH = "/credentials/google_token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service():
    if not os.path.exists(TOKEN_PATH):
        raise HTTPException(status_code=503, detail="Google token not found. Run OAuth flow first.")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


# ---------- list ----------

class ListRequest(BaseModel):
    time_min: str
    time_max: str
    calendar_id: str = "primary"
    max_results: int = 20


@router.post("/list")
async def list_events(req: ListRequest):
    service = get_service()
    result = service.events().list(
        calendarId=req.calendar_id,
        timeMin=req.time_min,
        timeMax=req.time_max,
        maxResults=req.max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for e in result.get("items", []):
        events.append({
            "id": e["id"],
            "summary": e.get("summary", "（無標題）"),
            "start": e["start"].get("dateTime", e["start"].get("date")),
            "end": e["end"].get("dateTime", e["end"].get("date")),
            "location": e.get("location"),
            "description": e.get("description"),
        })

    return {"events": events}


# ---------- create ----------

class CreateRequest(BaseModel):
    summary: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None
    calendar_id: str = "primary"


@router.post("/create")
async def create_event(req: CreateRequest):
    service = get_service()
    body = {
        "summary": req.summary,
        "start": {"dateTime": req.start},
        "end": {"dateTime": req.end},
    }
    if req.location:
        body["location"] = req.location
    if req.description:
        body["description"] = req.description

    event = service.events().insert(calendarId=req.calendar_id, body=body).execute()

    return {
        "id": event["id"],
        "summary": event.get("summary"),
        "start": event["start"].get("dateTime"),
        "end": event["end"].get("dateTime"),
        "html_link": event.get("htmlLink"),
    }
