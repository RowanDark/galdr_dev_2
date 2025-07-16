# galdr/interceptor/backend/modules/raider/models.py
# Database models for the Raider automated attack module.

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
    
    # Stores the base HTTP request with placeholder markers (e.g., §payload§)
    base_request_template = Column(JSON, nullable=False)
    
    # Stores the configuration, like payload sets, throttling, etc.
    config_json = Column(JSON, nullable=False)
    
    status = Column(String, default="pending", index=True) # pending, running, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationship to all the results from this attack
    results = relationship("RaiderResult", back_populates="attack", cascade="all, delete-orphan")

class RaiderResult(Base):
    """Represents the result of a single request made during an attack."""
    __tablename__ = 'raider_results'

    id = Column(Integer, primary_key=True) # Use integer for high-frequency inserts
    attack_id = Column(String, ForeignKey('raider_attacks.id'), nullable=False)
    
    request_number = Column(Integer, nullable=False)
    payload_value = Column(Text) # The payload used for this specific request
    
    # Response details
    status_code = Column(Integer)
    response_length = Column(Integer)
    response_time_ms = Column(Integer)
    
    attack = relationship("RaiderAttack", back_populates="results")
