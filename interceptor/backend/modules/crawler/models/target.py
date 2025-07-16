"""
Target and Request Models for Passive Crawler Module
Provides data models for crawling targets and request management
galdr/interceptor/backend/modules/crawler/models/target.py
"""

import uuid
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import urlparse, urljoin
import logging

class TargetType(Enum):
    """Types of crawling targets"""
    DOMAIN = "domain"
    URL = "url"
    IP_RANGE = "ip_range"
    SUBDOMAIN = "subdomain"
    PATH = "path"

class TargetStatus(Enum):
    """Target processing status"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    EXCLUDED = "excluded"

class RequestStatus(Enum):
    """Request processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

class Priority(Enum):
    """Request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ScopeConfig:
    """Configuration for crawling scope"""
    allowed_domains: List[str] = field(default_factory=list)
    excluded_domains: List[str] = field(default_factory=list)
    allowed_schemes: List[str] = field(default_factory=lambda: ['http', 'https'])
    excluded_paths: List[str] = field(default_factory=list)
    included_paths: List[str] = field(default_factory=list)
    max_depth: int = 5
    max_pages: int = 1000
    follow_redirects: bool = True
    respect_robots_txt: bool = True
    user_agent: str = "Galdr-Crawler/3.0"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScopeConfig':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_second: float = 1.0
    requests_per_minute: int = 60
    concurrent_requests: int = 5
    delay_between_requests: float = 1.0
    burst_limit: int = 10
    backoff_factor: float = 2.0
    max_retries: int = 3
    retry_delay: float = 5.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RateLimitConfig':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class Target:
    """Represents a crawling target"""
    target_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    target_type: TargetType = TargetType.URL
    status: TargetStatus = TargetStatus.PENDING
    priority: Priority = Priority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Configuration
    scope_config: ScopeConfig = field(default_factory=ScopeConfig)
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Metadata
    name: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_bytes: int = 0
    average_response_time: float = 0.0
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = 0
    consecutive_errors: int = 0
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.name:
            self.name = self._generate_name()
        
        # Validate URL
        if self.url and not self._is_valid_url(self.url):
            raise ValueError(f"Invalid URL: {self.url}")
    
    def _generate_name(self) -> str:
        """Generate a name based on target type and URL"""
        if self.target_type == TargetType.DOMAIN:
            parsed = urlparse(self.url)
            return f"Domain: {parsed.netloc}"
        elif self.target_type == TargetType.URL:
            parsed = urlparse(self.url)
            return f"URL: {parsed.netloc}{parsed.path}"
        else:
            return f"{self.target_type.value}: {self.url}"
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def update_status(self, status: TargetStatus, error: Optional[str] = None):
        """Update target status"""
        self.status = status
        self.updated_at = datetime.now()
        
        if status == TargetStatus.COMPLETED:
            self.completed_at = datetime.now()
        elif status == TargetStatus.FAILED and error:
            self.last_error = error
            self.error_count += 1
            self.consecutive_errors += 1
        elif status == TargetStatus.ACTIVE:
            self.consecutive_errors = 0
    
    def add_statistics(self, requests: int = 0, successful: int = 0, 
                      failed: int = 0, bytes_transferred: int = 0, 
                      response_time: float = 0.0):
        """Add statistics to target"""
        self.total_requests += requests
        self.successful_requests += successful
        self.failed_requests += failed
        self.total_bytes += bytes_transferred
        
        # Update average response time
        if response_time > 0:
            total_time = self.average_response_time * (self.total_requests - requests)
            total_time += response_time * requests
            self.average_response_time = total_time / self.total_requests if self.total_requests > 0 else 0
        
        self.updated_at = datetime.now()
    
    def is_in_scope(self, url: str) -> bool:
        """Check if URL is within target scope"""
        parsed_url = urlparse(url)
        
        # Check scheme
        if parsed_url.scheme not in self.scope_config.allowed_schemes:
            return False
        
        # Check allowed domains
        if self.scope_config.allowed_domains:
            if not any(domain in parsed_url.netloc for domain in self.scope_config.allowed_domains):
                return False
        
        # Check excluded domains
        if any(domain in parsed_url.netloc for domain in self.scope_config.excluded_domains):
            return False
        
        # Check excluded paths
        if any(path in parsed_url.path for path in self.scope_config.excluded_paths):
            return False
        
        # Check included paths (if specified)
        if self.scope_config.included_paths:
            if not any(path in parsed_url.path for path in self.scope_config.included_paths):
                return False
        
        return True
    
    def get_base_domain(self) -> str:
        """Get base domain from target URL"""
        parsed = urlparse(self.url)
        return parsed.netloc
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['target_type'] = self.target_type.value
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        
        # Convert datetime objects
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        
        if self.scheduled_at:
            data['scheduled_at'] = self.scheduled_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Target':
        """Create Target from dictionary"""
        # Convert string values back to enums
        if 'target_type' in data:
            data['target_type'] = TargetType(data['target_type'])
        if 'status' in data:
            data['status'] = TargetStatus(data['status'])
        if 'priority' in data:
            data['priority'] = Priority(data['priority'])
        
        # Convert ISO strings back to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'scheduled_at' in data and isinstance(data['scheduled_at'], str):
            data['scheduled_at'] = datetime.fromisoformat(data['scheduled_at'])
        if 'completed_at' in data and isinstance(data['completed_at'], str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        # Convert nested configs
        if 'scope_config' in data and isinstance(data['scope_config'], dict):
            data['scope_config'] = ScopeConfig.from_dict(data['scope_config'])
        if 'rate_limit_config' in data and isinstance(data['rate_limit_config'], dict):
            data['rate_limit_config'] = RateLimitConfig.from_dict(data['rate_limit_config'])
        
        return cls(**data)

@dataclass
class CrawlRequest:
    """Represents a single crawl request"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str = ""
    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    
    # Request metadata
    depth: int = 0
    parent_request_id: Optional[str] = None
    referrer: Optional[str] = None
    discovered_by: str = "unknown"  # How this URL was discovered
    
    # Status and timing
    status: RequestStatus = RequestStatus.QUEUED
    priority: Priority = Priority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Response data
    response_status: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    response_time: float = 0.0
    content_type: Optional[str] = None
    content_length: int = 0
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    
    # Analysis flags
    analyzed: bool = False
    analysis_completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.url:
            raise ValueError("URL is required for CrawlRequest")
        
        if not self._is_valid_url(self.url):
            raise ValueError(f"Invalid URL: {self.url}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def start_processing(self):
        """Mark request as started"""
        self.status = RequestStatus.PROCESSING
        self.started_at = datetime.now()
    
    def complete_request(self, response_status: int, response_headers: Dict[str, str],
                        response_body: str, response_time: float):
        """Mark request as completed with response data"""
        self.status = RequestStatus.COMPLETED
        self.completed_at = datetime.now()
        
        self.response_status = response_status
        self.response_headers = response_headers
        self.response_body = response_body
        self.response_time = response_time
        
        # Extract content metadata
        self.content_type = response_headers.get('content-type', '')
        self.content_length = len(response_body) if response_body else 0
    
    def fail_request(self, error_message: str):
        """Mark request as failed"""
        self.status = RequestStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
    
    def schedule_retry(self, delay_seconds: int = 60):
        """Schedule request for retry"""
        if self.retry_count >= self.max_retries:
            self.status = RequestStatus.FAILED
            self.error_message = f"Max retries ({self.max_retries}) exceeded"
        else:
            self.status = RequestStatus.RETRYING
            self.retry_count += 1
            self.next_retry_at = datetime.now() + timedelta(seconds=delay_seconds)
    
    def mark_analyzed(self):
        """Mark request as analyzed"""
        self.analyzed = True
        self.analysis_completed_at = datetime.now()
    
    def is_ready_for_retry(self) -> bool:
        """Check if request is ready for retry"""
        return (self.status == RequestStatus.RETRYING and 
                self.next_retry_at and 
                datetime.now() >= self.next_retry_at)
    
    def get_processing_time(self) -> Optional[float]:
        """Get total processing time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        
        # Convert datetime objects
        data['created_at'] = self.created_at.isoformat()
        
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        if self.next_retry_at:
            data['next_retry_at'] = self.next_retry_at.isoformat()
        if self.analysis_completed_at:
            data['analysis_completed_at'] = self.analysis_completed_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CrawlRequest':
        """Create CrawlRequest from dictionary"""
        # Convert string values back to enums
        if 'status' in data:
            data['status'] = RequestStatus(data['status'])
        if 'priority' in data:
            data['priority'] = Priority(data['priority'])
        
        # Convert ISO strings back to datetime
        datetime_fields = ['created_at', 'started_at', 'completed_at', 'next_retry_at', 'analysis_completed_at']
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)

class TargetManager:
    """Manages crawling targets and requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.targets: Dict[str, Target] = {}
        self.requests: Dict[str, CrawlRequest] = {}
        self.request_queue: List[str] = []  # Request IDs in queue order
    
    def add_target(self, url: str, target_type: TargetType = TargetType.URL,
                  name: str = "", description: str = "", tags: List[str] = None,
                  scope_config: ScopeConfig = None, 
                  rate_limit_config: RateLimitConfig = None) -> Target:
        """Add a new crawling target"""
        
        target = Target(
            url=url,
            target_type=target_type,
            name=name,
            description=description,
            tags=tags or [],
            scope_config=scope_config or ScopeConfig(),
            rate_limit_config=rate_limit_config or RateLimitConfig()
        )
        
        self.targets[target.target_id] = target
        self.logger.info(f"Added target: {target.name} ({target.target_id})")
        
        # Create initial request for the target URL
        if target.url:
            initial_request = self.create_request(
                target_id=target.target_id,
                url=target.url,
                discovered_by="initial_target"
            )
            self.add_request(initial_request)
        
        return target
    
    def get_target(self, target_id: str) -> Optional[Target]:
        """Get target by ID"""
        return self.targets.get(target_id)
    
    def get_targets_by_status(self, status: TargetStatus) -> List[Target]:
        """Get targets by status"""
        return [target for target in self.targets.values() if target.status == status]
    
    def update_target_status(self, target_id: str, status: TargetStatus, error: str = None):
        """Update target status"""
        if target_id in self.targets:
            self.targets[target_id].update_status(status, error)
    
    def create_request(self, target_id: str, url: str, method: str = "GET",
                      headers: Dict[str, str] = None, body: str = None,
                      depth: int = 0, parent_request_id: str = None,
                      referrer: str = None, discovered_by: str = "unknown",
                      priority: Priority = Priority.NORMAL) -> CrawlRequest:
        """Create a new crawl request"""
        
        request = CrawlRequest(
            target_id=target_id,
            url=url,
            method=method,
            headers=headers or {},
            body=body,
            depth=depth,
            parent_request_id=parent_request_id,
            referrer=referrer,
            discovered_by=discovered_by,
            priority=priority
        )
        
        return request
    
    def add_request(self, request: CrawlRequest):
        """Add request to queue"""
        self.requests[request.request_id] = request
        
        # Insert based on priority
        insert_index = len(self.request_queue)
        for i, existing_id in enumerate(self.request_queue):
            existing_request = self.requests[existing_id]
            if request.priority.value > existing_request.priority.value:
                insert_index = i
                break
        
        self.request_queue.insert(insert_index, request.request_id)
        self.logger.debug(f"Added request to queue: {request.url} (priority: {request.priority.value})")
    
    def get_next_request(self) -> Optional[CrawlRequest]:
        """Get next request from queue"""
        while self.request_queue:
            request_id = self.request_queue.pop(0)
            request = self.requests.get(request_id)
            
            if request and request.status == RequestStatus.QUEUED:
                return request
            elif request and request.is_ready_for_retry():
                return request
        
        return None
    
    def get_request(self, request_id: str) -> Optional[CrawlRequest]:
        """Get request by ID"""
        return self.requests.get(request_id)
    
    def get_requests_by_target(self, target_id: str) -> List[CrawlRequest]:
        """Get all requests for a target"""
        return [req for req in self.requests.values() if req.target_id == target_id]
    
    def get_requests_by_status(self, status: RequestStatus) -> List[CrawlRequest]:
        """Get requests by status"""
        return [req for req in self.requests.values() if req.status == status]
    
    def discover_urls_from_request(self, request: CrawlRequest, discovered_urls: List[str]) -> List[CrawlRequest]:
        """Create new requests from discovered URLs"""
        new_requests = []
        target = self.get_target(request.target_id)
        
        if not target:
            return new_requests
        
        for url in discovered_urls:
            # Check if URL is in scope
            if not target.is_in_scope(url):
                continue
            
            # Check if we've already processed this URL
            existing = any(req.url == url for req in self.requests.values())
            if existing:
                continue
            
            # Check depth limit
            if request.depth >= target.scope_config.max_depth:
                continue
            
            # Create new request
            new_request = self.create_request(
                target_id=request.target_id,
                url=url,
                depth=request.depth + 1,
                parent_request_id=request.request_id,
                referrer=request.url,
                discovered_by="link_extraction"
            )
            
            new_requests.append(new_request)
            self.add_request(new_request)
        
        return new_requests
    
    def get_queue_status(self) -> Dict:
        """Get queue status information"""
        status_counts = {}
        for status in RequestStatus:
            status_counts[status.value] = len(self.get_requests_by_status(status))
        
        return {
            'queue_length': len(self.request_queue),
            'total_requests': len(self.requests),
            'status_distribution': status_counts,
            'next_request_url': self.request_queue[0] if self.request_queue else None
        }
    
    def cleanup_completed_requests(self, max_age_days: int = 7):
        """Clean up old completed requests"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        to_remove = []
        for request_id, request in self.requests.items():
            if (request.status in [RequestStatus.COMPLETED, RequestStatus.FAILED] and
                request.completed_at and request.completed_at < cutoff_date):
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.requests[request_id]
            # Remove from queue if present
            if request_id in self.request_queue:
                self.request_queue.remove(request_id)
        
        self.logger.info(f"Cleaned up {len(to_remove)} old requests")
    
    def export_targets(self) -> List[Dict]:
        """Export all targets as dictionaries"""
        return [target.to_dict() for target in self.targets.values()]
    
    def import_targets(self, target_data: List[Dict]) -> List[Target]:
        """Import targets from dictionaries"""
        imported = []
        
        for data in target_data:
            try:
                target = Target.from_dict(data)
                self.targets[target.target_id] = target
                imported.append(target)
            except Exception as e:
                self.logger.error(f"Failed to import target: {e}")
        
        return imported
