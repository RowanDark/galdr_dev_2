# galdr/interceptor/backend/modules/mirror_mirror/api.py
# API endpoint for submitting two responses to be compared.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from .engine import MirrorEngine
from models.database import DatabaseManager

class ComparisonRequest(BaseModel):
    response_a: Dict[str, Any]
    response_b: Dict[str, Any]

router = APIRouter(prefix="/api/mirror", tags=["Mirror Mirror"])
engine = MirrorEngine()
db_manager = DatabaseManager()

@router.post("/compare", status_code=200)
async def compare_http_responses(request_data: ComparisonRequest):
    """Compares two provided HTTP responses and returns a detailed diff."""
    try:
        comparison_result = engine.compare_responses(
            request_data.response_a,
            request_data.response_b
        )
        return comparison_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare responses: {e}")

# We can add an endpoint later to save a comparison:
# @router.post("/comparisons", status_code=201)
# async def save_comparison(...)
