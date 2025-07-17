# galdr/interceptor/backend/modules/mirror_mirror/models.py
# Database model for saving interesting comparisons for later analysis or reporting.

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from models.database import Base

class MirrorComparison(Base):
    """Represents a single saved comparison session."""
    __tablename__ = 'mirror_comparisons'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, default="New Comparison")
    
    # Store the complete original responses being compared
    response_a_json = Column(JSON, nullable=False)
    response_b_json = Column(JSON, nullable=False)
    
    # Store the JSON result from the comparison engine
    comparison_result_json = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
