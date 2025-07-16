# interceptor/plugins/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from ..core.proxy_server import InterceptedRequest, InterceptedResponse


class BasePlugin(ABC):
    """Base class for all proxy plugins"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.enabled = True
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    async def process_request(self, request: InterceptedRequest) -> InterceptedRequest:
        """Process intercepted request"""
        pass
    
    @abstractmethod
    async def process_response(self, response: InterceptedResponse) -> InterceptedResponse:
        """Process intercepted response"""
        pass
    
    def configure(self, config: Dict[str, Any]):
        """Configure plugin with settings"""
        self.config.update(config)
    
    def enable(self):
        """Enable the plugin"""
        self.enabled = True
    
    def disable(self):
        """Disable the plugin"""
        self.enabled = False


class PluginManager:
    """Manages proxy plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
    
    def register_plugin(self, plugin: BasePlugin):
        """Register a new plugin"""
        self.plugins[plugin.name] = plugin
    
    def unregister_plugin(self, plugin_name: str):
        """Unregister a plugin"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> BasePlugin:
        """Get a plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins"""
        return list(self.plugins.keys())
    
    async def process_request_plugins(self, request: InterceptedRequest) -> InterceptedRequest:
        """Process request through all enabled plugins"""
        for plugin in self.plugins.values():
            if plugin.enabled:
                request = await plugin.process_request(request)
        return request
    
    async def process_response_plugins(self, response: InterceptedResponse) -> InterceptedResponse:
        """Process response through all enabled plugins"""
        for plugin in self.plugins.values():
            if plugin.enabled:
                response = await plugin.process_response(response)
        return response
