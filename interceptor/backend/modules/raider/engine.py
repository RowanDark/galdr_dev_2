# galdr/interceptor/backend/modules/raider/engine.py
# The core engine that runs attack loops and manages results.

import asyncio
import logging
from typing import Dict, List, Any
from models.database import DatabaseManager
from modules.replay_forge.http_client import ReplayHttpClient
from .models import RaiderAttack, RaiderResult, AttackType

class RaiderEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        # We can reuse the HTTP client from Replay Forge for sending requests.
        self.http_client = ReplayHttpClient()
        self.active_attacks: Dict[str, asyncio.Task] = {}
        self.sio = sio

    def _prepare_request(self, template: dict, payload: str) -> dict:
        template_str = json.dumps(template)
        # We'll use a simple marker for payloads: §payload§
        injected_str = template_str.replace("§payload§", json.dumps(payload)[1:-1]) # Handle JSON string escaping
        return json.loads(injected_str)

    async def _run_attack_loop(self, attack_id: str, attack_config: dict, base_request: dict, payload_list: List[str]):
        """The main asynchronous loop that executes the attack and emits live results."""
        session = self.db.get_session()
        request_counter = 0

        for payload in payload_list:
            # Check if the task was cancelled
            if attack_id not in self.active_attacks:
                self.logger.info(f"Attack {attack_id} cancelled by user.")
                break

            request_data = self._prepare_request(base_request, payload)
            response = await self.http_client.send_request(
                method=request_data['method'],
                url=request_data['url'],
                headers=request_data.get('headers', {}),
                body=request_data.get('body', '')
            )
            
            result = RaiderResult(
                attack_id=attack_id,
                request_number=request_counter,
                payload_value=payload,
                status_code=response.get('status_code'),
                response_length=len(response.get('body', '')),
                response_time_ms=int(response.get('response_time_ms', 0))
            )
            session.add(result)
            request_counter += 1
             # NEW: Emit the live result over WebSocket.
            if self.sio:
                result_data = {
                    "attack_id": result.attack_id,
                    "request_number": result.request_number,
                    "payload": result.payload_value,
                    "status": result.status_code,
                    "length": result.response_length,
                    "duration": result.response_time_ms,
                    }
                    # The room will be the attack_id, so only interested clients get updates.
                await self.sio.emit('raider_result_update', result_data, room=attack_id)
                
            if request_counter % 100 == 0:
                session.commit()
            
            session.commit()
        except asyncio.CancelledError:
            self.logger.info(f"Attack {attack_id} loop was cancelled.")
            session.rollback() # Rollback partial commits if cancelled
        finally:
            attack_record = session.query(RaiderAttack).filter_by(id=attack_id).first()
            if attack_record and attack_id in self.active_attacks:
                attack_record.status = "completed"
                if self.sio: await self.sio.emit('raider_attack_status', {'status': 'completed', 'attack_id': attack_id}, room=attack_id)

            session.commit()
            session.close()
            self.logger.info(f"Attack {attack_id} loop finished with {request_counter} requests.")
            if attack_id in self.active_attacks:
                del self.active_attacks[attack_id]


        
        # Mark attack as completed
        attack_record = session.query(RaiderAttack).filter_by(id=attack_id).first()
        if attack_record:
            attack_record.status = "completed"
            session.commit()
            
        session.close()
        self.logger.info(f"Attack {attack_id} completed with {request_counter} requests.")
        del self.active_attacks[attack_id]

    async def start_attack(self, attack_type: AttackType, base_request_template: dict, config: dict) -> str:
        """Creates an attack record and starts the attack loop in the background."""
        if attack_type != AttackType.SNIPER:
            raise NotImplementedError("Only Sniper attack type is implemented in this phase.")

        session = self.db.get_session()
        try:
            attack = RaiderAttack(
                attack_type=attack_type,
                base_request_template=base_request_template,
                config_json=config,
                status="running"
            )
            session.add(attack)
            session.commit()
            attack_id = attack.id
            
            payload_list = config.get("payloads", [])
            
            # Start the attack loop as a background task
            task = asyncio.create_task(
                self._run_attack_loop(attack_id, config, base_request_template, payload_list)
            )
            self.active_attacks[attack_id] = task

            self.logger.info(f"Started Raider attack {attack_id} with {len(payload_list)} payloads.")
            return attack_id
        finally:
            session.close()

    def stop_attack(self, attack_id: str):
        """Stops an active attack."""
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id].cancel()
            del self.active_attacks[attack_id]
            
            # Update status in DB
            session = self.db.get_session()
            attack_record = session.query(RaiderAttack).filter_by(id=attack_id).first()
            if attack_record:
                attack_record.status = "stopped"
                session.commit()
            session.close()
            
            self.logger.info(f"Successfully stopped attack {attack_id}.")
            return True
        return False
