# galdr/interceptor/backend/modules/portal/api.py
# --- UPDATED ---
# This version adds a new endpoint specifically for contextual analysis requests.

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from .engine import PortalEngine
from models.database import DatabaseManager

# --- Pydantic Models for type validation ---
class UserMessage(BaseModel):
    content: str

# NEW: A model to handle requests that include contextual data.
class ContextualUserMessage(BaseModel):
    content: str
    context: Dict[str, Any]

# --- Router Setup ---
router = APIRouter(prefix="/api/portal", tags=["Portal AI"])
engine = PortalEngine(db_manager=DatabaseManager())

# --- API Endpoints ---

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
    """
    Submits a user message to a conversation and gets an AI response.
    This is for general, non-contextual chat.
    """
    assistant_response = await engine.submit_message(
        conversation_id=conversation_id, 
        user_message_content=message.content,
        context=None # No context for this endpoint
    )
    return assistant_response

# NEW ENDPOINT: This is the core of our new integration.
@router.post("/conversations/{conversation_id}/analyze", status_code=201)
async def analyze_with_context(conversation_id: str, message: ContextualUserMessage):
    """
    Submits a user message along with contextual data for a more intelligent analysis.
    This will be used by modules like Replay Forge.
    """
    assistant_response = await engine.submit_message(
        conversation_id=conversation_id,
        user_message_content=message.content,
        context=message.context # We pass the context to the engine
    )
    return assistant_response
