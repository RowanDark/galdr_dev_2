# galdr/interceptor/backend/modules/raider/api.py
# API endpoints for managing Raider attacks.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from .engine import RaiderEngine, AttackType
from models.database import DatabaseManager

class AttackRequest(BaseModel):
    attack_type: AttackType
    base_request_template: Dict[str, Any]
    config: Dict[str, Any]

router = APIRouter(prefix="/api/raider", tags=["Raider"])
engine = RaiderEngine(db_manager=DatabaseManager())

@router.post("/attacks", status_code=202) # 202 Accepted, since it's a background task
async def launch_attack(attack_data: AttackRequest):
    """Launches a new automated attack."""
    try:
        attack_id = await engine.start_attack(
            attack_type=attack_data.attack_type,
            base_request_template=attack_data.base_request_template,
            config=attack_data.config
        )
        return {"message": "Attack started successfully", "attack_id": attack_id}
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # It's good practice to log the actual exception on the server
        # self.logger.error(f"Failed to start attack: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start attack: {str(e)}")

@router.delete("/attacks/{attack_id}", status_code=200)
async def stop_attack(attack_id: str):
    """Stops a running attack."""
    if engine.stop_attack(attack_id):
        return {"message": "Attack stopping..."}
    else:
        raise HTTPException(status_code=404, detail="Attack ID not found or not currently running.")

# We will add endpoints here later to get the status and results of an attack.
# For example: GET /attacks/{attack_id}/status and GET /attacks/{attack_id}/results
