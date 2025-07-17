# galdr/interceptor/backend/modules/raider/engine.py
# --- MAJOR OVERHAUL ---
# The engine now supports all four attack types with different payload iteration logic.

import asyncio
import logging
import json
import itertools # Needed for Cluster Bomb attack
from typing import Dict, List, Any
from models.database import DatabaseManager
from modules.replay_forge.http_client import ReplayHttpClient
from .models import RaiderAttack, RaiderResult, AttackType

class RaiderEngine:
    def __init__(self, db_manager: DatabaseManager, sio=None):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.http_client = ReplayHttpClient()
        self.active_attacks: Dict[str, asyncio.Task] = {}
        self.sio = sio

    def _prepare_request(self, template_str: str, payload_map: Dict[str, str]) -> dict:
        """Injects multiple named payloads into the request template."""
        injected_str = template_str
        for key, value in payload_map.items():
            # The payload marker is now the key, e.g., §username§
            marker = f"§{key}§"
            # Use json.dumps to handle escaping of quotes and special chars in the payload value
            injected_str = injected_str.replace(marker, json.dumps(value)[1:-1])
        return json.loads(injected_str)

    async def _execute_and_store(self, session, attack_id, req_num, payload_map, base_request_str):
        """Helper function to send one request and store its result."""
        request_data = self._prepare_request(base_request_str, payload_map)
        response = await self.http_client.send_request(
            method=request_data['method'],
            url=request_data['url'],
            headers=request_data.get('headers', {}),
            body=request_data.get('body', '')
        )
        
        result = RaiderResult(
            attack_id=attack_id,
            request_number=req_num,
            payloads_used_json=payload_map,
            status_code=response.get('status_code'),
            response_length=len(response.get('body', '')),
            response_time_ms=int(response.get('response_time_ms', 0)),
            response_headers_json=response.get('headers_json', {})
        )
        session.add(result)

        if self.sio:
            result_data = { "attack_id": attack_id, "request_number": req_num, "payloads": payload_map, "status": result.status_code, "length": result.response_length, "duration": result.response_time_ms }
            await self.sio.emit('raider_result_update', result_data, room=attack_id)

    async def _run_attack_loop(self, attack_id: str, attack: RaiderAttack):
        """Dispatcher that chooses the correct loop based on attack type."""
        self.logger.info(f"Starting attack loop for {attack.id} (Type: {attack.attack_type.name})")
        session = self.db.get_session()
        base_request_str = json.dumps(attack.base_request_template)
        config = attack.config_json
        payload_sets = config.get("payload_sets", {})
        
        try:
            req_num = 0
            iterator = None

            if attack.attack_type == AttackType.SNIPER or attack.attack_type == AttackType.BATTERING_RAM:
                # Both use a single list of payloads
                payload_list = next(iter(payload_sets.values()), [])
                markers = config.get("markers", [])
                # Create an iterator that yields a map for each payload.
                iterator = ({marker: payload for marker in markers} for payload in payload_list)

            elif attack.attack_type == AttackType.PITCHFORK:
                # Parallel lists. The number of requests is len of the shortest list.
                lists = [payload_sets.get(marker, []) for marker in config.get("markers", [])]
                iterator = (dict(zip(config.get("markers", []), p_tuple)) for p_tuple in zip(*lists))
            
            elif attack.attack_type == AttackType.CLUSTER_BOMB:
                # Cartesian product of all payload lists. Warning: can be huge.
                lists = [payload_sets.get(marker, []) for marker in config.get("markers", [])]
                product = itertools.product(*lists)
                iterator = (dict(zip(config.get("markers", []), p_tuple)) for p_tuple in product)

            if not iterator:
                raise ValueError("Could not create a payload iterator for the attack.")
            
            for payload_map in iterator:
                if attack_id not in self.active_attacks: break
                await self._execute_and_store(session, attack_id, req_num, payload_map, base_request_str)
                req_num += 1
                if req_num % 100 == 0: session.commit()
            
            attack.status = "completed"
            
        except asyncio.CancelledError:
            attack.status = "stopped"
            self.logger.info(f"Attack {attack_id} loop was cancelled.")
        except Exception as e:
            attack.status = "error"
            self.logger.error(f"Error during attack {attack.id}: {e}", exc_info=True)
        finally:
            if self.sio: await self.sio.emit('raider_attack_status', {'status': attack.status, 'attack_id': attack_id}, room=attack_id)
            session.commit()
            session.close()
            if attack_id in self.active_attacks: del self.active_attacks[attack_id]

    async def start_attack(self, name: str, attack_type: AttackType, base_request_template: dict, config: dict) -> str:
        """Creates an attack record and starts the attack loop in the background."""
        session = self.db.get_session()
        try:
            attack = RaiderAttack(
                name=name, attack_type=attack_type, base_request_template=base_request_template, config_json=config, status="running"
            )
            session.add(attack)
            session.commit()
            attack_id = attack.id
            
            task = asyncio.create_task(self._run_attack_loop(attack_id, attack))
            self.active_attacks[attack_id] = task
            self.logger.info(f"Started Raider attack {attack_id}")
            return attack_id
        finally:
            session.close()
    
    def stop_attack(self, attack_id: str):
        if attack_id not in self.active_attacks: return False
        self.active_attacks[attack_id].cancel()
        return True
