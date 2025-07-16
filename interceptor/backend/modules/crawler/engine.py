# galdr/interceptor/backend/modules/crawler/engine.py
import asyncio
import logging
import re
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse
import hashlib

from .analyzers.content import ContentAnalyzer
from .analyzers.tech_stack import TechStackAnalyzer
from .analyzers.vulnerability import VulnerabilityAnalyzer
from .analyzers.secrets import SecretsAnalyzer
from .models.crawl_data import CrawlSession, CrawlEntry, AnalysisResult
from .utils.extractors import LinkExtractor, EmailExtractor, FileExtractor
from ..recon.models.target import InterceptedRequest, InterceptedResponse


@dataclass
class CrawlerConfig:
    """Configuration for passive crawler"""
    auto_analyze: bool = True
    max_entries_per_session: int = 10000
    enable_tech_stack_detection: bool = True
    enable_vulnerability_detection: bool = False
    enable_ai_analysis: bool = False
    enable_secrets_detection: bool = True
    
    # File type detection
    track_js_files: bool = True
    track_css_files: bool = True
    track_image_files: bool = False
    track_document_files: bool = True
    custom_file_extensions: List[str] = field(default_factory=lambda: ['.txt', '.svg', '.json', '.xml'])
    
    # Analysis thresholds
    min_response_size: int = 100
    max_response_size: int = 10 * 1024 * 1024  # 10MB
    
    # AI/LLM settings
    llm_provider: str = "openai"  # openai, anthropic, local
    llm_model: str = "gpt-4"
    llm_api_key: Optional[str] = None
    
    # CVE database settings
    cve_database_path: str = "./data/cve_database.json"
    vulnerability_confidence_threshold: float = 0.7


class PassiveCrawlerEngine:
    """Main engine for passive web crawling and analysis"""
    
    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self.content_analyzer = ContentAnalyzer(self.config)
        self.tech_stack_analyzer = TechStackAnalyzer(self.config)
        self.vulnerability_analyzer = VulnerabilityAnalyzer(self.config)
        self.secrets_analyzer = SecretsAnalyzer(self.config)
        
        # Initialize extractors
        self.link_extractor = LinkExtractor()
        self.email_extractor = EmailExtractor()
        self.file_extractor = FileExtractor(self.config)
        
        # Active crawl sessions
        self.active_sessions: Dict[str, CrawlSession] = {}
        self.session_history: List[CrawlSession] = []
        
        # Real-time data
        self.extracted_links: Set[str] = set()
        self.extracted_emails: Set[str] = set()
        self.extracted_files: Dict[str, List[str]] = {}
        self.detected_technologies: Dict[str, Set[str]] = {}
        self.found_vulnerabilities: List[Dict] = []
        self.discovered_secrets: List[Dict] = []
        
        # Callbacks for real-time updates
        self.update_callbacks: List[callable] = []
        
        # Processing queue
        self.processing_queue = asyncio.Queue()
        self.is_processing = False
    
    async def start_session(self, session_name: str = None) -> str:
        """Start a new crawl session"""
        session_id = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = CrawlSession(
            session_id=session_id,
            start_time=datetime.now(),
            config=self.config
        )
        
        self.active_sessions[session_id] = session
        self.logger.info(f"Started passive crawl session: {session_id}")
        
        # Start processing queue if not already running
        if not self.is_processing:
            asyncio.create_task(self._process_queue())
        
        return session_id
    
    async def stop_session(self, session_id: str):
        """Stop and finalize a crawl session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = datetime.now()
            session.status = "completed"
            
            # Move to history
            self.session_history.append(session)
            del self.active_sessions[session_id]
            
            self.logger.info(f"Stopped crawl session: {session_id}")
            await self._notify_session_complete(session)
    
    async def process_traffic(self, request: InterceptedRequest, response: InterceptedResponse):
        """Process intercepted traffic through the crawler"""
        # Add to processing queue
        await self.processing_queue.put((request, response))
    
    async def _process_queue(self):
        """Process traffic analysis queue"""
        self.is_processing = True
        
        try:
            while True:
                try:
                    # Get next item with timeout
                    request, response = await asyncio.wait_for(
                        self.processing_queue.get(), timeout=1.0
                    )
                    
                    await self._analyze_traffic(request, response)
                    
                except asyncio.TimeoutError:
                    # No new items, continue loop
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing traffic: {e}")
                    
        except asyncio.CancelledError:
            self.logger.info("Traffic processing cancelled")
        finally:
            self.is_processing = False
    
    async def _analyze_traffic(self, request: InterceptedRequest, response: InterceptedResponse):
        """Analyze a single request/response pair"""
        try:
            # Create crawl entry
            entry = CrawlEntry(
                url=request.url,
                method=request.method,
                status_code=response.status_code,
                request_headers=request.headers,
                response_headers=response.headers,
                request_body=request.body.decode('utf-8', errors='ignore'),
                response_body=response.body.decode('utf-8', errors='ignore'),
                timestamp=datetime.now(),
                content_type=response.headers.get('content-type', ''),
                content_length=len(response.body)
            )
            
            # Skip if response is too small or too large
            if not self._should_analyze_response(entry):
                return
            
            # Add to active sessions
            for session in self.active_sessions.values():
                session.entries.append(entry)
                if len(session.entries) > self.config.max_entries_per_session:
                    session.entries = session.entries[-self.config.max_entries_per_session:]
            
            # Extract basic data
            await self._extract_basic_data(entry)
            
            # Perform detailed analysis if enabled
            if self.config.auto_analyze:
                analysis_result = await self._perform_detailed_analysis(entry)
                entry.analysis_result = analysis_result
                
                # Update aggregated data
                await self._update_aggregated_data(analysis_result)
            
            # Notify real-time updates
            await self._notify_traffic_analyzed(entry)
            
        except Exception as e:
            self.logger.error(f"Error analyzing traffic for {request.url}: {e}")
    
    def _should_analyze_response(self, entry: CrawlEntry) -> bool:
        """Determine if response should be analyzed"""
        if entry.content_length < self.config.min_response_size:
            return False
        
        if entry.content_length > self.config.max_response_size:
            return False
        
        # Skip binary content types
        content_type = entry.content_type.lower()
        if any(binary_type in content_type for binary_type in [
            'image/', 'video/', 'audio/', 'application/octet-stream',
            'application/pdf', 'application/zip'
        ]):
            return False
        
        return True
    
    async def _extract_basic_data(self, entry: CrawlEntry):
        """Extract basic data from the response"""
        try:
            # Extract links
            links = self.link_extractor.extract_links(entry.response_body, entry.url)
            for link in links:
                self.extracted_links.add(link)
            entry.extracted_links = links
            
            # Extract emails
            emails = self.email_extractor.extract_emails(entry.response_body)
            for email in emails:
                self.extracted_emails.add(email)
            entry.extracted_emails = emails
            
            # Extract files
            files = self.file_extractor.extract_files(entry.response_body, entry.url)
            for file_type, file_list in files.items():
                if file_type not in self.extracted_files:
                    self.extracted_files[file_type] = []
                self.extracted_files[file_type].extend(file_list)
            entry.extracted_files = files
            
        except Exception as e:
            self.logger.error(f"Error extracting basic data: {e}")
    
    async def _perform_detailed_analysis(self, entry: CrawlEntry) -> AnalysisResult:
        """Perform detailed analysis on the entry"""
        analysis_result = AnalysisResult()
        
        try:
            # Tech stack detection
            if self.config.enable_tech_stack_detection:
                tech_stack = await self.tech_stack_analyzer.analyze(entry)
                analysis_result.technologies = tech_stack
            
            # Vulnerability detection
            if self.config.enable_vulnerability_detection:
                vulnerabilities = await self.vulnerability_analyzer.analyze(entry)
                analysis_result.vulnerabilities = vulnerabilities
            
            # Secrets detection
            if self.config.enable_secrets_detection:
                secrets = await self.secrets_analyzer.analyze(entry)
                analysis_result.secrets = secrets
            
            # Content analysis
            content_analysis = await self.content_analyzer.analyze(entry)
            analysis_result.content_analysis = content_analysis
            
        except Exception as e:
            self.logger.error(f"Error performing detailed analysis: {e}")
        
        return analysis_result
    
    async def _update_aggregated_data(self, analysis_result: AnalysisResult):
        """Update aggregated data with new analysis results"""
        try:
            # Update technologies
            for tech in analysis_result.technologies:
                domain = urlparse(analysis_result.url).netloc if hasattr(analysis_result, 'url') else 'unknown'
                if domain not in self.detected_technologies:
                    self.detected_technologies[domain] = set()
                self.detected_technologies[domain].add(tech)
            
            # Update vulnerabilities
            self.found_vulnerabilities.extend(analysis_result.vulnerabilities)
            
            # Update secrets
            self.discovered_secrets.extend(analysis_result.secrets)
            
        except Exception as e:
            self.logger.error(f"Error updating aggregated data: {e}")
    
    # Public interface methods
    def get_session_data(self, session_id: str) -> Optional[CrawlSession]:
        """Get data for a specific session"""
        return self.active_sessions.get(session_id) or next(
            (s for s in self.session_history if s.session_id == session_id), None
        )
    
    def get_extracted_links(self) -> List[str]:
        """Get all extracted links"""
        return sorted(list(self.extracted_links))
    
    def get_extracted_emails(self) -> List[str]:
        """Get all extracted emails"""
        return sorted(list(self.extracted_emails))
    
    def get_extracted_files(self) -> Dict[str, List[str]]:
        """Get all extracted files by type"""
        return {k: sorted(list(set(v))) for k, v in self.extracted_files.items()}
    
    def get_detected_technologies(self) -> Dict[str, List[str]]:
        """Get detected technologies by domain"""
        return {k: sorted(list(v)) for k, v in self.detected_technologies.items()}
    
    def get_vulnerabilities(self) -> List[Dict]:
        """Get found vulnerabilities"""
        return self.found_vulnerabilities
    
    def get_secrets(self) -> List[Dict]:
        """Get discovered secrets"""
        return self.discovered_secrets
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get crawler statistics"""
        total_entries = sum(len(session.entries) for session in self.active_sessions.values())
        
        return {
            'active_sessions': len(self.active_sessions),
            'total_entries': total_entries,
            'extracted_links': len(self.extracted_links),
            'extracted_emails': len(self.extracted_emails),
            'extracted_files': sum(len(files) for files in self.extracted_files.values()),
            'detected_technologies': sum(len(techs) for techs in self.detected_technologies.values()),
            'found_vulnerabilities': len(self.found_vulnerabilities),
            'discovered_secrets': len(self.discovered_secrets)
        }
    
    # Callback management
    def add_update_callback(self, callback: callable):
        """Add callback for real-time updates"""
        self.update_callbacks.append(callback)
    
    async def _notify_traffic_analyzed(self, entry: CrawlEntry):
        """Notify callbacks of new analyzed traffic"""
        for callback in self.update_callbacks:
            try:
                await callback('traffic_analyzed', entry)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    async def _notify_session_complete(self, session: CrawlSession):
        """Notify callbacks of session completion"""
        for callback in self.update_callbacks:
            try:
                await callback('session_complete', session)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
