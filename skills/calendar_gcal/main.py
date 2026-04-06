import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pydantic import BaseModel

router = APIRouter(prefix="/skill/calendar_gcal")

SERVICE_ACCOUNT_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH", "/credentials/service_account.json")
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service():
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        raise HTTPException(status_code=503, detail="Service account key not found.")

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


# ---------- list ----------

class ListRequest(BaseModel):
    time_min: str
    time_max: str
    calendar_id: str = "zea00312@gmail.com"
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
    calendar_id: str = "zea00312@gmail.com"


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
