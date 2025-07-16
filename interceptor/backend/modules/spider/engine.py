# galdr/interceptor/backend/modules/spider/engine.py
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse
import hashlib
import re

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from .navigation.page_navigator import PageNavigator
from .discovery.endpoint_discoverer import EndpointDiscoverer
from .forms.form_handler import FormHandler
from .analysis.content_analyzer import SpiderContentAnalyzer
from .models.spider_data import SpiderSession, SpiderResult, DiscoveredEndpoint, FormData
from .utils.url_manager import URLManager
from .utils.request_generator import RequestGenerator


@dataclass
class SpiderConfig:
    """Configuration for active spider operations"""
    max_depth: int = 3
    max_pages_per_domain: int = 100
    max_concurrent_pages: int = 5
    request_delay: float = 1.0
    respect_robots_txt: bool = True
    follow_redirects: bool = True
    
    # Browser settings
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # Form handling
    enable_form_submission: bool = True
    enable_login_forms: bool = False  # Requires credentials
    max_forms_per_page: int = 10
    form_fill_strategy: str = "smart"  # smart, random, minimal
    
    # Discovery settings
    discover_ajax_endpoints: bool = True
    discover_api_endpoints: bool = True
    analyze_javascript: bool = True
    extract_hidden_inputs: bool = True
    
    # OSINT collection (same as passive crawler)
    collect_emails: bool = True
    collect_files: bool = True
    detect_technologies: bool = True
    detect_vulnerabilities: bool = False
    detect_secrets: bool = True
    
    # Performance and safety
    page_timeout: int = 30000  # 30 seconds
    navigation_timeout: int = 30000
    max_response_size: int = 10 * 1024 * 1024  # 10MB
    enable_screenshots: bool = False
    
    # Scope control
    stay_in_domain: bool = True
    allowed_domains: List[str] = field(default_factory=list)
    excluded_paths: List[str] = field(default_factory=lambda: ['/logout', '/delete'])
    excluded_file_types: List[str] = field(default_factory=lambda: ['.pdf', '.zip', '.exe', '.dmg'])


class ActiveSpiderEngine:
    """Main engine for active web spidering and discovery"""
    
    def __init__(self, config: Optional[SpiderConfig] = None):
        self.config = config or SpiderConfig()
        self.logger = logging.getLogger(__name__)
        
        # Browser management
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Core components
        self.url_manager = URLManager(self.config)
        self.page_navigator = PageNavigator(self.config)
        self.endpoint_discoverer = EndpointDiscoverer(self.config)
        self.form_handler = FormHandler(self.config)
        self.content_analyzer = SpiderContentAnalyzer(self.config)
        self.request_generator = RequestGenerator(self.config)
        
        # Session data
        self.active_sessions: Dict[str, SpiderSession] = {}
        self.session_history: List[SpiderSession] = []
        
        # Discovery results
        self.discovered_endpoints: Dict[str, DiscoveredEndpoint] = {}
        self.discovered_forms: Dict[str, FormData] = {}
        self.collected_data: Dict[str, Any] = {
            'links': set(),
            'emails': set(),
            'files': {},
            'technologies': {},
            'vulnerabilities': [],
            'secrets': []
        }
        
        # Progress tracking
        self.is_running = False
        self.current_session_id: Optional[str] = None
        self.progress_callbacks: List[callable] = []
        self.completion_callbacks: List[callable] = []
        
        # Rate limiting and queue management
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_pages)
        self.visited_urls: Set[str] = set()
        self.queued_urls: asyncio.Queue = asyncio.Queue()
    
    async def start_spider_session(self, target_url: str, session_name: str = None) -> str:
        """Start a new active spider session"""
        try:
            # Initialize browser if not already done
            await self._initialize_browser()
            
            # Create session
            session_id = session_name or f"spider_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session = SpiderSession(
                session_id=session_id,
                target_url=target_url,
                start_time=datetime.now(),
                config=self.config
            )
            
            self.active_sessions[session_id] = session
            self.current_session_id = session_id
            self.is_running = True
            
            self.logger.info(f"Starting active spider session: {session_id} for {target_url}")
            
            # Initialize URL queue
            await self.queued_urls.put({
                'url': target_url,
                'depth': 0,
                'referrer': None,
                'method': 'GET'
            })
            
            # Start spidering process
            await self._execute_spider_session(session)
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to start spider session: {e}")
            raise
    
    async def stop_spider_session(self, session_id: str):
        """Stop an active spider session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = datetime.now()
            session.status = "stopped"
            
            # Move to history
            self.session_history.append(session)
            del self.active_sessions[session_id]
            
            self.is_running = False
            self.current_session_id = None
            
            self.logger.info(f"Stopped spider session: {session_id}")
            await self._notify_session_complete(session)
    
    async def _initialize_browser(self):
        """Initialize Playwright browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            
            # Launch browser
            if self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.config.headless)
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.config.headless)
            else:
                self.browser = await self.playwright.chromium.launch(headless=self.config.headless)
            
            # Create context with configuration
            self.context = await self.browser.new_context(
                user_agent=self.config.user_agent,
                viewport={'width': self.config.viewport_width, 'height': self.config.viewport_height}
            )
            
            # Enable request/response logging
            self.context.on("request", self._on_request)
            self.context.on("response", self._on_response)
    
    async def _execute_spider_session(self, session: SpiderSession):
        """Execute the main spidering logic"""
        try:
            # Create worker tasks for concurrent processing
            workers = []
            for i in range(self.config.max_concurrent_pages):
                worker = asyncio.create_task(self._spider_worker(session))
                workers.append(worker)
            
            # Wait for all workers to complete or queue to be empty
            await asyncio.gather(*workers, return_exceptions=True)
            
            # Finalize session
            await self._finalize_session(session)
            
        except Exception as e:
            self.logger.error(f"Error in spider session: {e}")
            session.errors.append(str(e))
        finally:
            session.status = "completed"
            session.end_time = datetime.now()
    
    async def _spider_worker(self, session: SpiderSession):
        """Worker process for spidering URLs"""
        while self.is_running and not self.queued_urls.empty():
            try:
                # Get next URL from queue
                url_info = await asyncio.wait_for(self.queued_urls.get(), timeout=1.0)
                
                # Skip if already visited or exceeds depth
                if (url_info['url'] in self.visited_urls or 
                    url_info['depth'] > self.config.max_depth or
                    len(session.results) >= self.config.max_pages_per_domain):
                    continue
                
                # Process the URL
                async with self.request_semaphore:
                    await self._process_url(session, url_info)
                
                # Add delay between requests
                if self.config.request_delay > 0:
                    await asyncio.sleep(self.config.request_delay)
                    
            except asyncio.TimeoutError:
                # No more URLs in queue
                break
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
    
    async def _process_url(self, session: SpiderSession, url_info: Dict):
        """Process a single URL"""
        url = url_info['url']
        depth = url_info['depth']
        
        try:
            # Check if URL should be processed
            if not self.url_manager.should_process_url(url, session.target_url):
                return
            
            self.visited_urls.add(url)
            
            # Create new page
            page = await self.context.new_page()
            
            try:
                # Navigate to page
                result = await self._navigate_and_analyze_page(page, url, depth, session)
                
                if result:
                    session.results.append(result)
                    await self._notify_progress(f"Processed {url}", len(session.results))
                
            finally:
                await page.close()
                
        except Exception as e:
            self.logger.error(f"Error processing URL {url}: {e}")
            session.errors.append(f"Error processing {url}: {str(e)}")
    
    async def _navigate_and_analyze_page(self, page: Page, url: str, depth: int, session: SpiderSession) -> Optional[SpiderResult]:
        """Navigate to page and perform comprehensive analysis"""
        try:
            # Set up page monitoring
            await self._setup_page_monitoring(page)
            
            # Navigate to the page
            response = await page.goto(url, timeout=self.config.navigation_timeout)
            
            if not response or response.status >= 400:
                return None
            
            # Wait for page to load completely
            await page.wait_for_load_state('networkidle', timeout=self.config.page_timeout)
            
            # Create result object
            result = SpiderResult(
                url=url,
                depth=depth,
                status_code=response.status,
                content_type=response.headers.get('content-type', ''),
                timestamp=datetime.now()
            )
            
            # Get page content
            content = await page.content()
            result.page_content = content
            
            # Extract basic page information
            result.title = await page.title()
            result.meta_description = await page.get_attribute('meta[name="description"]', 'content') or ''
            
            # Discover links and queue new URLs
            await self._discover_links(page, url, depth, session)
            
            # Handle forms
            await self._handle_forms(page, url, result)
            
            # Discover AJAX/API endpoints
            await self._discover_ajax_endpoints(page, result)
            
            # Analyze page content for OSINT data
            await self._analyze_page_content(content, url, result)
            
            # Handle JavaScript interactions
            await self._handle_javascript_interactions(page, url, depth, session)
            
            # Take screenshot if enabled
            if self.config.enable_screenshots:
                result.screenshot_path = await self._take_screenshot(page, url)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing page {url}: {e}")
            return None
    
    async def _setup_page_monitoring(self, page: Page):
        """Setup monitoring for network requests and JavaScript errors"""
        # Monitor network requests
        page.on('request', lambda request: self._on_page_request(request))
        page.on('response', lambda response: self._on_page_response(response))
        
        # Monitor JavaScript errors
        page.on('pageerror', lambda error: self.logger.warning(f"JavaScript error: {error}"))
        
        # Monitor console messages for potential leaks
        page.on('console', lambda msg: self._analyze_console_message(msg))
    
    async def _discover_links(self, page: Page, current_url: str, depth: int, session: SpiderSession):
        """Discover and queue new links from the page"""
        try:
            # Extract all links
            links = await page.evaluate("""
                () => {
                    const links = [];
                    
                    // Regular links
                    document.querySelectorAll('a[href]').forEach(link => {
                        links.push({
                            type: 'link',
                            url: link.href,
                            text: link.textContent.trim(),
                            target: link.target
                        });
                    });
                    
                    // Form actions
                    document.querySelectorAll('form[action]').forEach(form => {
                        links.push({
                            type: 'form',
                            url: form.action,
                            method: form.method || 'GET'
                        });
                    });
                    
                    // Script sources
                    document.querySelectorAll('script[src]').forEach(script => {
                        links.push({
                            type: 'script',
                            url: script.src
                        });
                    });
                    
                    // CSS and other resources
                    document.querySelectorAll('link[href]').forEach(link => {
                        links.push({
                            type: 'resource',
                            url: link.href,
                            rel: link.rel
                        });
                    });
                    
                    return links;
                }
            """)
            
            # Process and queue discovered links
            for link_info in links:
                absolute_url = urljoin(current_url, link_info['url'])
                
                if (link_info['type'] == 'link' and
