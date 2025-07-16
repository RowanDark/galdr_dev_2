# galdr/interceptor/backend/modules/portal/api.py
# All API endpoints related to the Portal module.

from fastapi import APIRouter
from pydantic import BaseModel
from .engine import PortalEngine
from models.database import DatabaseManager
class UserMessage(BaseModel):
content: str

# This router will be imported and included in the main FastAPI app.
router = APIRouter(prefix="/api/portal", tags=["Portal AI"])
engine = PortalEngine(db_manager=DatabaseManager())
@router.get("/conversations", status_code=200)
async def get_conversations():
"""Get a list of all past conversations."""
return engine.get_all_conversations()
@router.post("/conversations", status_code=201)
async def create_new_conversation():
"""Starts a new, empty conversation."""
return engine.start_conversation()
@router.get("/conversations/{conversation_id}/messages", status_code=200)
async def get_messages(conversation_id: str):
"""Get all messages for a specific conversation."""
return engine.get_conversation_messages(conversation_id)
@router.post("/conversations/{conversation_id}/messages", status_code=201)
async def post_message_to_conversation(conversation_id: str, message: UserMessage):
"""Submits a user message to a conversation and gets an AI response."""
assistant_response = await engine.submit_message(conversation_id, message.content)
return assistant_response
