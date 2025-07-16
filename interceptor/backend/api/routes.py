# galdr/interceptor/backend/api/routes.py
# --- NEW FILE ---
# This is the new home for all API endpoints. It uses FastAPI for modern,
# async-native performance and automatic documentation.

import asyncio
from fastapi import FastAPI, APIRouter
import socketio

from .websocket_handlers import WebSocketManager
from core.proxy_server import EnhancedProxyEngine
from models.database import DatabaseManager
from modules.replay_forge.api import router as replay_forge_router
from modules.portal.api import router as portal_router
from modules.raider.api import router as raider_router

def create_api_app(proxy_engine: EnhancedProxyEngine, db_manager: DatabaseManager):
    """Factory function to create the main FastAPI app and attach routers."""
    
    # Create the main FastAPI app instance
    app = FastAPI(title="Galdr Interceptor API")
    
    # Create a WebSocket manager and attach it to the proxy engine
    # This allows the proxy to broadcast events without being coupled to FastAPI.
    sio, sio_app = WebSocketManager.create_socketio_app()
    proxy_engine.set_websocket_manager(sio)

    # Mount the Socket.IO app
    app.mount('/socket.io', sio_app)

    # --- API Router for Core Proxy Functions ---
    proxy_router = APIRouter(prefix="/api/proxy", tags=["Proxy"])

    @proxy_router.post("/start")
    async def start_proxy():
        if proxy_engine.is_running:
            return {"status": "already_running"}
        # Run the proxy start method as a background task
        asyncio.create_task(proxy_engine.start())
        return {"status": "starting"}

    @proxy_router.post("/stop")
    async def stop_proxy():
        if not proxy_engine.is_running:
            return {"status": "already_stopped"}
        await proxy_engine.stop()
        return {"status": "stopped"}

    @proxy_router.get("/status")
    async def get_proxy_status():
        return {
            "is_running": proxy_engine.is_running,
            "host": proxy_engine.host,
            "port": proxy_engine.port
        }
        
    @proxy_router.get("/traffic")
    async def get_traffic_history(limit: int = 100, offset: int = 0):
        traffic = db_manager.get_traffic(limit=limit, offset=offset)
        return traffic

    @proxy_router.delete("/traffic")
    async def clear_all_traffic():
        count = db_manager.clear_traffic()
        return {"status": "success", "cleared_items": count}


    # Include the router in the main app
    app.include_router(proxy_router)
    app.include_router(replay_forge_router)
    app.include_router(portal_router)
    app.include_router(raider_router)

    # --- Placeholder for future module routers ---
    # As we build Replay Forge, Portal, etc., we will create their API routers
    # and include them here. For example:
    # from modules.portal.api import router as portal_router
    # app.include_router(portal_router)

    return app
