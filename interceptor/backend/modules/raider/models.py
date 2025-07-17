# galdr/interceptor/backend/modules/raider/models.py
# --- UPDATED ---
# Now supports storing multi-payload results and more response data for analysis.

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from models.database import Base
import enum

class AttackType(enum.Enum):
    SNIPER = "sniper"
    BATTERING_RAM = "battering_ram"
    PITCHFORK = "pitchfork"
    CLUSTER_BOMB = "cluster_bomb"

class RaiderAttack(Base):
    """Represents a single configured attack session in Raider."""
    __tablename__ = 'raider_attacks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, default="New Attack")
    attack_type = Column(SQLAlchemyEnum(AttackType), nullable=False)
    base_request_template = Column(JSON, nullable=False)
    config_json = Column(JSON, nullable=False)
    status = Column(String, default="pending", index=True) # pending, running, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    results = relationship("RaiderResult", back_populates="attack", cascade="all, delete-orphan")

class RaiderResult(Base):
    """Represents the result of a single request made during an attack."""
    __tablename__ = 'raider_results'

    id = Column(Integer, primary_key=True)
    attack_id = Column(String, ForeignKey('raider_attacks.id'), nullable=False)
    request_number = Column(Integer, nullable=False)
    
    # NEW: Store the set of payloads used in this request as a JSON object.
    # For Sniper/Battering Ram, it will be e.g., {"payload1": "admin"}
    # For Pitchfork/Cluster Bomb, e.g., {"username": "user1", "password": "123"}
    payloads_used_json = Column(JSON, nullable=False)
    
    status_code = Column(Integer)
    response_length = Column(Integer)
    response_time_ms = Column(Integer)
    
    # NEW: Store response headers for more advanced filtering (e.g., Content-Type)
    response_headers_json = Column(JSON)
    
    attack = relationship("RaiderAttack", back_populates="results")
