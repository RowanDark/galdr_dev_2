# galdr/interceptor/backend/modules/raider/api.py
# API endpoints for managing Raider attacks.

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any

from .engine import RaiderEngine, AttackType
from models.database import DatabaseManager

class AttackRequest(BaseModel):
    attack_type: AttackType
    base_request_template: Dict[str, Any]
    config: Dict[str, Any]

router = APIRouter(prefix="/api/raider", tags=["Raider"])

@router.post("/attacks", status_code=202)
async def launch_attack(attack_data: AttackRequest, request: Request):
    """
    Launches a new automated attack.
    It gets the WebSocket instance (sio) from the application's state to pass to the engine.
    """
    sio = request.app.state.sio
    engine = RaiderEngine(db_manager=DatabaseManager(), sio=sio)
    
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
        raise HTTPException(status_code=500, detail=f"Failed to start attack: {str(e)}")

@router.delete("/attacks/{attack_id}", status_code=200)
async def stop_attack(attack_id: str):
    """Stops a running attack."""
    # Since the engine is stateless for this action, we can instantiate it directly.
    engine = RaiderEngine(db_manager=DatabaseManager())
    if engine.stop_attack(attack_id):
        return {"message": "Attack stopping..."}
    else:
        raise HTTPException(status_code=404, detail="Attack ID not found or not currently running.")
