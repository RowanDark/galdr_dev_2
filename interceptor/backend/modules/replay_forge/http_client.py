# galdr/interceptor/backend/modules/replay_forge/http_client.py
# A dedicated, async HTTP client for sending crafted requests.

import aiohttp
import ssl
import time
import logging

class ReplayHttpClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Create a single, reusable session for performance
        # We create a custom SSL context to ignore certificate verification, which is standard for a proxy tool.
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            headers={"User-Agent": "Galdr/3.0 ReplayForge"} # Default User-Agent
        )

    async def send_request(self, method: str, url: str, headers: dict, body: str) -> dict:
        """Sends a request and returns a structured response dictionary."""
        start_time = time.perf_counter()
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                data=body.encode('utf-8') if body else None,
                timeout=30 # 30-second timeout
            ) as response:
                response_body = await response.read()
                end_time = time.perf_counter()
                
                return {
                    "status_code": response.status,
                    "headers_json": dict(response.headers),
                    "body": response_body.decode('utf-8', errors='replace'),
                    "response_time_ms": (end_time - start_time) * 1000,
                    "error": None
                }
        except Exception as e:
            end_time = time.perf_counter()
            self.logger.error(f"HTTP request to {url} failed: {e}", exc_info=True)
            return {
                "status_code": 0,
                "headers_json": {},
                "body": f"ReplayForge Error: {str(e)}",
                "response_time_ms": (end_time - start_time) * 1000,
                "error": str(e)
            }

    async def close(self):
        """Closes the client session. Called on application shutdown."""
        await self.session.close()
