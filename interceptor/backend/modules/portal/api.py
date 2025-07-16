# galdr/interceptor/backend/modules/portal/api.py
# --- UPDATED ---
# We are upgrading the Pydantic model to optionally accept a context dictionary.

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from .engine import PortalEngine
from models.database import DatabaseManager

# UPDATED: This model now includes an optional 'context' field.
class UserMessage(BaseModel):
    content: str
    context: Optional[Dict[str, Any]] = None # The context from the originating Galdr module

# This router will be imported and included in the main FastAPI app.
router = APIRouter(prefix="/api/portal", tags=["Portal AI"])
engine = PortalEngine(db_manager=DatabaseManager())

# --- No changes to the GET endpoints ---
@router.get("/conversations", status_code=200)
async def get_conversations():
    return engine.get_all_conversations()

@router.post("/conversations", status_code=201)
async def create_new_conversation():
    return engine.start_conversation()

@router.get("/conversations/{conversation_id}/messages", status_code=200)
async def get_messages(conversation_id: str):
    return engine.get_conversation_messages(conversation_id)

# UPDATED: This endpoint now accepts the context object.
@router.post("/conversations/{conversation_id}/messages", status_code=201)
async def post_message_to_conversation(conversation_id: str, message: UserMessage):
    """Submits a user message and optional context to a conversation."""
    assistant_response = await engine.submit_message(
        conversation_id, 
        message.content, 
        message.context # Pass the context to the engine
    )
    return assistant_response
