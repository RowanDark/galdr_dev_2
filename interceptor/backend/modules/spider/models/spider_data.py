# galdr/interceptor/backend/modules/spider/models/spider_data.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class DiscoveredEndpoint:
    """Represents a discovered API/AJAX endpoint"""
    url: str
    method: str
    headers: Dict[str, str] = field(default_factory=dict)
    post_data: Optional[str] = None
    resource_type: str = "xhr"
    discovery_method: str = "network_monitoring"
    response_status: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'post_data': self.post_data,
            'resource_type': self.resource_type,
            'discovery_method': self.discovery_method,
            'response_status': self.response_status,
            'response_headers': self.response_headers,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class APIEndpoint:
    """Represents a discovered API endpoint with metadata"""
    url: str
    method: str
    parameters: List[str] = field(default_factory=list)
    description: str = ""
    response_format: str = "json"
    authentication_required: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SpiderResult:
    """Result from spidering a single page"""
    url: str
    depth: int
    status_code: int
    content_type: str
    timestamp: datetime
    
    # Page content
    page_content: str = ""
    title: str = ""
    meta_description: str = ""
    
    # Discovered elements
    discovered_forms: List['FormData'] = field(default_factory=list)
    form_submissions: List['FormSubmissionResult'] = field(default_factory=list)
    ajax_endpoints: List[DiscoveredEndpoint] = field(default_factory=list)
    
    # Analysis results
    content_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Screenshots
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'depth': self.depth,
            'status_code': self.status_code,
            'content_type': self.content_type,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'meta_description': self.meta_description,
            'discovered_forms': [form.to_dict() for form in self.discovered_forms],
            'form_submissions': [sub.to_dict() for sub in self.form_submissions],
            'ajax_endpoints': [ep.to_dict() for ep in self.ajax_endpoints],
            'content_analysis': self.content_analysis,
            'screenshot_path': self.screenshot_path
        }


@dataclass
class SpiderSession:
    """Spider session containing all results"""
    session_id: str
    target_url: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, stopped, error
    config: Optional[Any] = None
    
    # Session results
    results: List[SpiderResult] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'target_url': self.target_url,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_pages': len(self.results),
            'statistics': self.statistics,
            'errors': self.errors,
            'results': [result.to_dict() for result in self.results[-50:]]  # Last 50 results
        }
