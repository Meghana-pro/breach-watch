from datetime import date
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse

from app import database
from app.risk import score_incident

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

app = FastAPI(
    title="BreachWatch",
    description="Educational breach-intelligence dashboard with transparent demo risk scoring.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class IncidentCreate(BaseModel):
    organization: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=5, max_length=3000)
    source_name: str = Field(min_length=2, max_length=120)
    source_url: str = Field(default="", max_length=500)
    incident_date: date
    data_types: List[str] = Field(default_factory=list, max_length=15)

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        value = value.strip()
        if value:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Source URL must begin with http:// or https://")
        return value


class ActionUpdate(BaseModel):
    completed: bool


database.init_db()


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "application": "BreachWatch"}


@app.get("/api/summary")
def get_summary():
    return database.summary()


@app.get("/api/incidents")
def get_incidents():
    return database.list_incidents()


@app.post("/api/incidents", status_code=201)
def add_incident(payload: IncidentCreate):
    item = payload.model_dump()
    item["incident_date"] = item["incident_date"].isoformat()
    risk = score_incident(item["data_types"], item["description"])
    return database.create_incident(item, risk)


@app.patch("/api/incidents/{incident_id}/action")
def update_action(incident_id: int, payload: ActionUpdate):
    incident = database.set_action_completed(incident_id, payload.completed)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
