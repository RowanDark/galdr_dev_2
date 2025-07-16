# galdr/interceptor/backend/core/websocket_server.py
import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from .proxy_server import InterceptedRequest, InterceptedResponse


class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self, host: str = "localhost", port: int = 8081):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.logger = logging.getLogger(__name__)
        
    async def start_server(self):
        """Start the WebSocket server"""
        self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        
        self.logger.info("WebSocket server started successfully")
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        self.logger.info(f"New WebSocket client connected: {client_ip}")
        
        try:
            # Send initial status
            await self.send_to_client(websocket, {
                "type": "status",
                "data": {
                    "connected": True,
                    "timestamp": datetime.now().isoformat(),
                    "proxy_running": True
                }
            })
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
                    await self.send_error(websocket, str(e))
                    
        except ConnectionClosed:
            self.logger.info(f"WebSocket client disconnected: {client_ip}")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await self.send_to_client(websocket, {"type": "pong"})
        
        elif message_type == "get_traffic":
            # Request traffic history
            await self.send_to_client(websocket, {
                "type": "traffic_history",
                "data": []  # Will be populated by proxy engine
            })
        
        elif message_type == "modify_request":
            # Handle request modification
            request_id = data.get("request_id")
            modifications = data.get("modifications", {})
            # Process modifications...
            
        elif message_type == "forward_request":
            # Handle manual request forwarding
            request_id = data.get("request_id")
            # Process forwarding...
            
        else:
            await self.send_error(websocket, f"Unknown message type: {message_type}")
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Send data to specific client"""
        try:
            await websocket.send(json.dumps(data))
        except ConnectionClosed:
            self.clients.discard(websocket)
        except Exception as e:
            self.logger.error(f"Error sending to client: {e}")
    
    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send error message to client"""
        await self.send_to_client(websocket, {
            "type": "error",
            "data": {"message": error_message}
        })
    
    async def broadcast_traffic(self, request: InterceptedRequest, response: InterceptedResponse = None):
        """Broadcast new traffic to all connected clients"""
        if not self.clients:
            return
        
        traffic_data = {
            "type": "new_traffic",
            "data": {
                "request": request.to_dict(),
                "response": response.to_dict() if response else None
            }
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self.clients:
            try:
                await client.send(json.dumps(traffic_data))
            except ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
    
    async def broadcast_status(self, status: str, additional_data: Dict[str, Any] = None):
        """Broadcast status update to all clients"""
        if not self.clients:
            return
        
        status_data = {
            "type": "status_update",
            "data": {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                **(additional_data or {})
            }
        }
        
        disconnected_clients = []
        for client in self.clients:
            try:
                await client.send(json.dumps(status_data))
            except ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error broadcasting status: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
    
    def get_connected_clients_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)
