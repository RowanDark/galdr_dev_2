# galdr/interceptor/backend/modules/replay_forge/engine.py
# The engine orchestrates Replay Forge logic. It uses the HTTP client and the database models.

import logging
from .http_client import ReplayHttpClient
from .models import ReplayTab, ReplayRequest, ReplayResponse
from models.database import DatabaseManager

class ReplayForgeEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.http_client = ReplayHttpClient()

    async def create_new_tab(self, name: str, original_request: dict) -> dict:
        """Creates and persists a new Replay Tab."""
        session = self.db.get_session()
        try:
            new_tab = ReplayTab(
                name=name,
                original_request_json=original_request
            )
            session.add(new_tab)
            session.commit()
            self.logger.info(f"Created Replay Forge tab: {new_tab.id} ({name})")
            return new_tab.to_dict()
        finally:
            session.close()

    async def send_request_from_tab(self, tab_id: str, request_data: dict) -> dict:
        """Sends a request for a given tab and records the full exchange."""
        session = self.db.get_session()
        try:
            # Create and save the request record first
            req_record = ReplayRequest(
                tab_id=tab_id,
                method=request_data['method'],
                url=request_data['url'],
                headers_json=request_data.get('headers', {}),
                body=request_data.get('body', '')
            )
            session.add(req_record)
            session.commit()

            # Now, send the request using our dedicated client
            response_dict = await self.http_client.send_request(
                method=req_record.method,
                url=req_record.url,
                headers=req_record.headers_json,
                body=req_record.body
            )

            # Create and save the response record
            resp_record = ReplayResponse(
                request_id=req_record.id,
                status_code=response_dict['status_code'],
                headers_json=response_dict['headers_json'],
                body=response_dict['body'],
                response_time_ms=response_dict['response_time_ms']
            )
            session.add(resp_record)
            session.commit()
            
            self.logger.info(f"Sent request {req_record.id} for tab {tab_id}, received {resp_record.status_code}")
            
            return {
                "request_id": req_record.id,
                "response": {
                    "id": resp_record.id,
                    **response_dict
                }
            }
            
        except Exception as e:
            self.logger.error(f"Engine error sending request for tab {tab_id}: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
