# galdr/interceptor/backend/modules/replay_forge/models.py
# This file defines the database structure for Replay Forge.

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from models.database import Base

class ReplayTab(Base):
    __tablename__ = 'replay_tabs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stores the original request sent to Replay Forge
    original_request_json = Column(JSON, nullable=False)
    
    # Relationship to the history of requests sent from this tab
    sent_requests = relationship("ReplayRequest", back_populates="tab", cascade="all, delete-orphan", lazy="dynamic")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "original_request": self.original_request_json,
            "request_count": self.sent_requests.count()
        }

class ReplayRequest(Base):
    __tablename__ = 'replay_requests'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tab_id = Column(String, ForeignKey('replay_tabs.id'), nullable=False)
    
    # The actual request that was sent
    sent_at = Column(DateTime, default=datetime.utcnow)
    method = Column(String, nullable=False)
    url = Column(String, nullable=False)
    headers_json = Column(JSON)
    body = Column(Text)
    
    # Relationship back to the tab
    tab = relationship("ReplayTab", back_populates="sent_requests")
    
    # Relationship to the response
    response = relationship("ReplayResponse", back_populates="request", uselist=False, cascade="all, delete-orphan")

class ReplayResponse(Base):
    __tablename__ = 'replay_responses'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, ForeignKey('replay_requests.id'), nullable=False)

    # The received response
    received_at = Column(DateTime, default=datetime.utcnow)
    status_code = Column(Integer)
    headers_json = Column(JSON)
    body = Column(Text)
    response_time_ms = Column(Float)
    
    # Relationship back to the request
    request = relationship("ReplayRequest", back_populates="response")
