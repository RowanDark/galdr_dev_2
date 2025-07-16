# galdr/interceptor/backend/main.py
# --- REFACTORED ---
# This file is now responsible for initializing all components and starting the Uvicorn server.
# The core logic is more modular, handing off responsibilities to the api_app and proxy_engine.

import asyncio
import logging
import sys
from pathlib import Path

import uvicorn
from core.proxy_server import EnhancedProxyEngine
from core.cert_manager import CertificateManager
from models.database import DatabaseManager
from utils.helpers import setup_logging
from api.routes import create_api_app

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

class GaldrApp:
    def __init__(self):
        setup_logging()
        self.logger = logging.getLogger(__name__)

        self.db_manager = DatabaseManager("sqlite:///galdr/interceptor/data/interceptor.db")
        self.cert_manager = CertificateManager("./galdr/interceptor/certs")
        
        # The proxy engine is now a component managed by the main app, not the core process.
        self.proxy_engine = EnhancedProxyEngine(
            "127.0.0.1", 
            8080, 
            cert_manager=self.cert_manager,
            db_manager=self.db_manager
        )

        # The FastAPI application is created here, injecting dependencies.
        # This keeps the web layer separate from the core business logic.
        self.api_app = create_api_app(
            proxy_engine=self.proxy_engine,
            db_manager=self.db_manager,
            # Pass module engines here as they are created
        )

    def start(self):
        """Starts the Galdr application by running the Uvicorn server."""
        self.logger.info("Starting Galdr Interceptor...")
        self.logger.info("=" * 60)
        self.logger.info(f"API & WebSocket Server running on http://127.0.0.1:8000")
        self.logger.info(f"Proxy will run on http://{self.proxy_engine.host}:{self.proxy_engine.port} when started.")
        self.logger.info(f"CA Certificate: {self.cert_manager.get_ca_cert_path()}")
        self.logger.info("=" * 60)
        self._print_cert_instructions()

        uvicorn.run(
            self.api_app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )

    def _print_cert_instructions(self):
        """Prints certificate installation instructions to the console."""
        # This helper function is good, we'll keep it as is.
        ca_cert_path = self.cert_manager.get_ca_cert_path()
        
        self.logger.info("\nCERTIFICATE INSTALLATION INSTRUCTIONS:")
        self.logger.info("-" * 40)
        self.logger.info("To intercept HTTPS traffic, install the CA certificate:")
        self.logger.info(f"Certificate location: {ca_cert_path}")
        self.logger.info("\nFor Chrome/Edge:")
        self.logger.info("1. Go to Settings > Privacy and Security > Security")
        self.logger.info("2. Click 'Manage certificates'")
        self.logger.info("3. Go to 'Trusted Root Certification Authorities'")
        self.logger.info("4. Click 'Import' and select the CA certificate")
        self.logger.info("\nFor Firefox:")
        self.logger.info("1. Go to Settings > Privacy & Security")
        self.logger.info("2. Scroll to 'Certificates' and click 'View Certificates'")
        self.logger.info("3. Go to 'Authorities' tab and click 'Import'")
        self.logger.info("4. Select the CA certificate and trust for websites")
        self.logger.info("-" * 40)


if __name__ == "__main__":
    app = GaldrApp()
    app.start()
