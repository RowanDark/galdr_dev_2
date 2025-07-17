# galdr/interceptor/backend/api/websocket_handlers.py
# --- NEW FILE ---
# This file centralizes WebSocket logic using python-socketio for a more
# robust, event-based communication channel than raw websockets.

import socketio
import logging

class WebSocketManager:
"""Manages the Socket.IO server and client connections."""

@staticmethod
def create_socketio_app():
    """Creates the Socket.IO server instance and ASGI app."""
    logger = logging.getLogger(__name__)
    
    # We use an async server
    sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
    
    # Wrap in an ASGI app
    sio_app = socketio.ASGIApp(sio)

    @sio.event
    async def connect(sid, environ):
        logger.info(f"Frontend client connected: {sid}")
        # We can send a welcome message or initial state here if needed
        await sio.emit('status_update', {'status': 'connected'}, to=sid)

    @sio.event
    async def disconnect(sid):
        logger.info(f"Frontend client disconnected: {sid}")

    @sio.on('get_initial_data')
    async def handle_get_initial_data(sid, data):
        """Handler for when the frontend requests initial state."""
        logger.info(f"Received 'get_initial_data' from {sid}")
        # Here you could send back recent traffic, status, etc.
        # Example:
        # traffic = db_manager.get_traffic(limit=50)
        # await sio.emit('initial_traffic', traffic, to=sid)

    @sio.on('join_raider_room')
        async def handle_join_raider_room(sid, data):
            attack_id = data.get('attack_id')
            if attack_id:
                sio.enter_room(sid, attack_id)
                logger.info(f"Client {sid} joined Raider room for attack {attack_id}")
        
        # NEW: Handler to leave a room when the attack is done or view is closed.
        @sio.on('leave_raider_room')
        async def handle_leave_raider_room(sid, data):
            attack_id = data.get('attack_id')
            if attack_id:
                sio.leave_room(sid, attack_id)
                logger.info(f"Client {sid} left Raider room for attack {attack_id}")
        
    return sio, sio_app
