# galdr/interceptor/backend/utils/helpers.py
import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory
    log_dir = Path("./galdr/interceptor/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "interceptor.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def format_request_summary(request):
    """Format request for logging"""
    return f"{request.method} {request.url} - {request.source_ip}"


def format_response_summary(response):
    """Format response for logging"""
    return f"Status: {response.status_code} - {response.duration_ms:.0f}ms"
