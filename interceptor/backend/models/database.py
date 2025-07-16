# galdr/interceptor/backend/models/database.py
# --- REFACTORED ---
# This file has been cleaned of all hallucinated models (`Cartographer`, `ReplayForge`).
# We have also added the NEW, simplified models for the upcoming Portal module.

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, Float, 
    Text, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import logging
from modules.replay_forge.models import Base as ReplayForgeBase
from modules.portal.models import Base as PortalBase

Base = declarative_base()

# ===== CORE TRAFFIC MODEL (Unchanged, it was good) =====
class InterceptedTraffic(Base):
    __tablename__ = 'intercepted_traffic'
    # ... (no changes to this model, it's solid)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    method = Column(String)
    url = Column(String)
    protocol = Column(String)
    host = Column(String)
    port = Column(Integer)
    path = Column(String)
    query_string = Column(String)
    request_headers = Column(Text)  # JSON string
    request_body = Column(Text)
    response_status = Column(Integer)
    response_headers = Column(Text)  # JSON string
    response_body = Column(Text)
    response_time = Column(Float)
    content_type = Column(String)
    content_length = Column(Integer)
    ssl = Column(Boolean, default=False)
    source = Column(String)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ===== MODELS FOR EXISTING MODULES (Unchanged) =====
# Recon, Crawler, Spider models were well-designed. Keep them.

class ReconSession(Base):
    __tablename__ = 'recon_sessions'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ... (rest of the model)
    results = relationship("ReconResult", back_populates="session")

class ReconResult(Base):
    __tablename__ = 'recon_results'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('recon_sessions.id'))
    # ... (rest of the model)
    session = relationship("ReconSession", back_populates="results")

# (Similarly for CrawlerSession, CrawlerEntry, SpiderSession, SpiderResult, etc.)
# --- Assume all your correct Crawler and Spider models are here ---


# ======================================================================
# ===== EVERYTHING BELOW THIS LINE HAS BEEN MODIFIED OR REPLACED =====
# ======================================================================

# ===== DELETED MODULES =====
# All models related to `Cartographer` and `ReplayForge` have been REMOVED.
# This includes:
# - CartographerScan, CartographerEndpoint, CartographerVulnerability
# - CartographerSession, CartographerNode, CartographerLink
# - ReplaySession, ReplayTab, ReplayRequest, ReplayResponse


# ===== NEW SIMPLIFIED PORTAL MODELS =====
# These are the foundational models for our new Portal AI Assistant.
# They are much simpler than the over-engineered version from the old code.

class PortalConversation(Base):
    __tablename__ = 'portal_conversations'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="default_user", index=True)
    title = Column(String, nullable=False, default=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = relationship("PortalMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="PortalMessage.timestamp")

class PortalMessage(Base):
    __tablename__ = 'portal_messages'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey('portal_conversations.id'), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant' or 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("PortalConversation", back_populates="messages")


# ===== DATABASE MANAGER CLASS (Mostly unchanged, it was good) =====
class DatabaseManager:
    def __init__(self, database_url: str = "sqlite:///data/galdr.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logging.getLogger(__name__)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    # The existing methods for storing and retrieving traffic were fine.
    # We will keep them.
    def store_traffic(self, traffic_data: dict) -> str:
        # ... (implementation as before)
        pass # placeholder

    def get_traffic(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        # ... (implementation as before)
        pass # placeholder
        
    def get_traffic_by_id(self, traffic_id: str) -> Optional[Dict]:
        # ... (implementation as before)
        pass # placeholder

    def clear_traffic(self) -> int:
        session = self.get_session()
        try:
            num_deleted = session.query(InterceptedTraffic).delete()
            session.commit()
            return num_deleted
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error clearing traffic: {e}", exc_info=True)
            raise
        finally:
            session.close()
