# galdr/interceptor/backend/modules/crawler/models/crawl_data.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class CrawlEntry:
    """Single crawled request/response entry"""
    url: str
    method: str
    status_code: int
    request_headers: Dict[str, str]
    response_headers: Dict[str, str]
    request_body: str
    response_body: str
    timestamp: datetime
    content_type: str
    content_length: int
    
    # Extracted data
    extracted_links: List[str] = field(default_factory=list)
    extracted_emails: List[str] = field(default_factory=list)
    extracted_files: Dict[str, List[str]] = field(default_factory=dict)
    
    # Analysis results
    analysis_result: Optional['AnalysisResult'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'url': self.url,
            'method': self.method,
            'status_code': self.status_code,
            'request_headers': self.request_headers,
            'response_headers': self.response_headers,
            'request_body': self.request_body,
            'response_body': self.response_body,
            'timestamp': self.timestamp.isoformat(),
            'content_type': self.content_type,
            'content_length': self.content_length,
            'extracted_links': self.extracted_links,
            'extracted_emails': self.extracted_emails,
            'extracted_files': self.extracted_files,
            'analysis_result': self.analysis_result.to_dict() if self.analysis_result else None
        }


@dataclass
class AnalysisResult:
    """Results from detailed analysis of a crawl entry"""
    technologies: List[str] = field(default_factory=list)
    vulnerabilities: List[Dict] = field(default_factory=list)
    secrets: List[Dict] = field(default_factory=list)
    content_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'technologies': self.technologies,
            'vulnerabilities': self.vulnerabilities,
            'secrets': self.secrets,
            'content_analysis': self.content_analysis
        }


@dataclass
class CrawlSession:
    """Crawling session containing multiple entries"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, stopped
    config: Optional[Any] = None
    
    # Session data
    entries: List[CrawlEntry] = field(default_factory=list)
    
    # Session statistics
    total_requests: int = 0
    unique_domains: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_requests': len(self.entries),
            'unique_domains': len(set(entry.url.split('/')[2] for entry in self.entries if '/' in entry.url)),
            'entries': [entry.to_dict() for entry in self.entries[-100:]]  # Last 100 entries
        }
