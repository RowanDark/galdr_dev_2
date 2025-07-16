# galdr/interceptor/backend/modules/replay_forge/api.py
# All API endpoints for Replay Forge, keeping it decoupled from other modules.

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any

from .engine import ReplayForgeEngine
from models.database import DatabaseManager

# Pydantic models for request validation and serialization
class CreateTabRequest(BaseModel):
    name: str
    original_request: Dict[str, Any]

class SendRequestData(BaseModel):
    method: str
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body: str = ""

# Dependency for getting a DB session (example, can be more robust)
def get_db():
    db_manager = DatabaseManager()
    return db_manager

router = APIRouter(prefix="/api/replay", tags=["Replay Forge"])
engine = ReplayForgeEngine(db_manager=get_db()) # Initialize the engine once

@router.post("/tabs", status_code=201)
async def create_replay_tab(data: CreateTabRequest):
    """Creates a new tab in Replay Forge."""
    new_tab = await engine.create_new_tab(name=data.name, original_request=data.original_request)
    return new_tab

@router.post("/tabs/{tab_id}/send")
async def send_replay_request(tab_id: str, request_data: SendRequestData):
    """Sends a new request associated with a specific tab."""
    result = await engine.send_request_from_tab(tab_id=tab_id, request_data=request_data.model_dump())
    return result

# You would add more endpoints here: get all tabs, get history for a tab, etc.
