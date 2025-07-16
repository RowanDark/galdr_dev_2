# interceptor/core/config.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
import os


@dataclass
class ProxyConfig:
    """Proxy configuration settings"""
    host: str = "127.0.0.1"
    port: int = 8080
    intercept_enabled: bool = True
    auto_forward: bool = True
    scope_patterns: List[str] = field(default_factory=lambda: ["*"])
    cert_dir: str = "./certs"
    database_url: str = "sqlite:///interceptor.db"
    log_level: str = "INFO"
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    timeout_seconds: int = 30
    enable_websocket: bool = True
    enable_http2: bool = True
    
    def save(self, config_file: str = "proxy_config.json"):
        """Save configuration to file"""
        with open(config_file, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
    
    @classmethod
    def load(cls, config_file: str = "proxy_config.json") -> 'ProxyConfig':
        """Load configuration from file"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()


class ConfigManager:
    """Configuration management for the proxy"""
    
    def __init__(self, config_file: str = "proxy_config.json"):
        self.config_file = config_file
        self.config = ProxyConfig.load(config_file)
    
    def update_config(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
    
    def save_config(self):
        """Save current configuration"""
        self.config.save(self.config_file)
    
    def get_config(self) -> ProxyConfig:
        """Get current configuration"""
        return self.config
