# galdr/interceptor/backend/modules/portal/models.py
# Database models specifically for the Portal AI Assistant.
# This keeps the module's data structure self-contained.

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base # We import the shared declarative Base

class PortalConversation(Base):
    """Represents a single chat session with the AI."""
    __tablename__ = 'portal_conversations'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # In a multi-user system, this would link to a user ID.
    # user_id = Column(String, default="default_user", index=True)
    
    # This relationship ensures that when a conversation is deleted,
    # all its associated messages are also deleted.
    messages = relationship(
        "PortalMessage", 
        back_populates="conversation", 
        cascade="all, delete-orphan",
        order_by="PortalMessage.timestamp" # Ensure messages are always ordered correctly
    )

class PortalMessage(Base):
    """Represents a single message within a conversation."""
    __tablename__ = 'portal_messages'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey('portal_conversations.id'), nullable=False)
    
    # 'role' will be 'user', 'assistant', or 'system' to match LLM API formats.
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("PortalConversation", back_populates="messages")
