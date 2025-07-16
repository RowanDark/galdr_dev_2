# galdr/interceptor/backend/modules/spider/discovery/endpoint_discoverer.py
import re
import json
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page

from ..models.spider_data import DiscoveredEndpoint, APIEndpoint


class EndpointDiscoverer:
    """Discovers AJAX, API, and hidden endpoints"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.discovered_endpoints: Set[str] = set()
        
        # Patterns for discovering API endpoints
        self.api_patterns = [
            r'/api/v?\d*/?',
            r'/rest/?',
            r'/graphql/?',
            r'/endpoints?/?',
            r'/services?/?',
            r'\.json',
            r'\.xml',
            r'/ajax/',
            r'/json/',
            r'/data/'
        ]
        
        # Common API endpoint words
        self.api_words = [
            'users', 'user', 'auth', 'login', 'logout', 'register',
            'products', 'items', 'posts', 'comments', 'search',
            'upload', 'download', 'files', 'images', 'data',
            'admin', 'config', 'settings', 'status', 'health'
        ]
    
    async def discover_ajax_endpoints(self, page: Page) -> List[DiscoveredEndpoint]:
        """Discover AJAX and API endpoints on the page"""
        endpoints = []
        
        try:
            # Monitor network requests during page interactions
            await self._monitor_network_requests(page, endpoints)
            
            # Analyze JavaScript for endpoint references
            await self._analyze_javascript_endpoints(page, endpoints)
            
            # Look for API documentation or endpoint lists
            await self._discover_documented_endpoints(page, endpoints)
            
            # Trigger AJAX behaviors
            await self._trigger_ajax_behaviors(page, endpoints)
            
        except Exception as e:
            self.logger.error(f"Error discovering AJAX endpoints: {e}")
        
        return endpoints
    
    async def _monitor_network_requests(self, page: Page, endpoints: List[DiscoveredEndpoint]):
        """Monitor network requests to discover AJAX endpoints"""
        def handle_request(request):
            if request.resource_type in ['xhr', 'fetch']:
                endpoint = DiscoveredEndpoint(
                    url=request.url,
                    method=request.method,
                    headers=dict(request.headers),
                    post_data=request.post_data,
                    resource_type=request.resource_type,
                    timestamp=datetime.now()
                )
                
                endpoint_key = f"{request.method}:{request.url}"
                if endpoint_key not in self.discovered_endpoints:
                    self.discovered_endpoints.add(endpoint_key)
                    endpoints.append(endpoint)
        
        def handle_response(response):
            if response.request.resource_type in ['xhr', 'fetch']:
                # Find corresponding endpoint and update with response info
                for endpoint in endpoints:
                    if (endpoint.url == response.url and 
                        endpoint.method == response.request.method):
                        endpoint.response_status = response.status
                        endpoint.response_headers = dict(response.headers)
                        break
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        # Wait a bit for any initial AJAX requests
        await page.wait_for_timeout(2000)
    
    async def _analyze_javascript_endpoints(self, page: Page, endpoints: List[DiscoveredEndpoint]):
        """Analyze JavaScript code for endpoint references"""
        try:
            # Get all script contents
            scripts = await page.evaluate("""
                () => {
                    const scripts = [];
                    document.querySelectorAll('script').forEach(script => {
                        if (script.src) {
                            scripts.push({type: 'external', src: script.src});
                        } else if (script.textContent) {
                            scripts.push({type: 'inline', content: script.textContent});
                        }
                    });
                    return scripts;
                }
            """)
            
            current_url = page.url
            
            for script in scripts:
                if script['type'] == 'inline':
                    content = script['content']
                    discovered_urls = self._extract_urls_from_js(content, current_url)
                    
                    for url in discovered_urls:
                        if self._is_api_endpoint(url):
                            endpoint = DiscoveredEndpoint(
                                url=url,
                                method='GET',  # Default, might be POST
                                headers={},
                                discovery_method='javascript_analysis',
                                timestamp=datetime.now()
                            )
                            
                            endpoint_key = f"GET:{url}"
                            if endpoint_key not in self.discovered_endpoints:
                                self.discovered_endpoints.add(endpoint_key)
                                endpoints.append(endpoint)
        
        except Exception as e:
            self.logger.error(f"Error analyzing JavaScript endpoints: {e}")
    
    def _extract_urls_from_js(self, js_content: str, base_url: str) -> List[str]:
        """Extract URLs from JavaScript content"""
        urls = []
        
        # Common patterns for URLs in JavaScript
        url_patterns = [
            r'["\']([^"\']*(?:/api/|/rest/|/graphql|\.json|\.xml)[^"\']*)["\']',
            r'url\s*:\s*["\']([^"\']+)["\']',
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'axios\.[get|post|put|delete]+\s*\(\s*["\']([^"\']+)["\']',
            r'\$\.ajax\s*\(\s*["\']([^"\']+)["\']',
            r'XMLHttpRequest.*open\s*\(\s*["\'][^"\']*["\']\s*,\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in url_patterns:
            matches = re.finditer(pattern, js_content, re.IGNORECASE)
            for match in matches:
                url = match.group(1)
                
                # Convert relative URLs to absolute
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                elif not url.startswith('http'):
                    continue
                
                urls.append(url)
        
        return urls
    
    def _is_api_endpoint(self, url: str) -> bool:
        """Determine if URL looks like an API endpoint"""
        url_lower = url.lower()
        
        # Check against API patterns
        for pattern in self.api_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # Check for API words in path
        parsed = urlparse(url_lower)
        path_parts = parsed.path.split('/')
        
        for part in path_parts:
            if part in self.api_words:
                return True
        
        return False
    
    async def _discover_documented_endpoints(self, page: Page, endpoints: List[DiscoveredEndpoint]):
        """Look for documented API endpoints"""
        try:
            # Common API documentation paths
            doc_paths = [
                '/api/docs',
                '/docs',
                '/swagger',
                '/api-docs',
                '/documentation',
                '/api/swagger.json',
                '/api/openapi.json'
            ]
            
            current_url = page.url
            base_url = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}"
            
            for doc_path in doc_paths:
                doc_url = urljoin(base_url, doc_path)
                
                try:
                    # Try to navigate to documentation
                    response = await page.goto(doc_url, timeout=5000)
                    
                    if response and response.status == 200:
                        content = await page.content()
                        
                        # Parse Swagger/OpenAPI documentation
                        if 'swagger' in content.lower() or 'openapi' in content.lower():
                            await self._parse_swagger_endpoints(page, endpoints)
                        
                        # Look for endpoint lists in HTML
                        await self._parse_html_endpoints(page, endpoints)
                
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.error(f"Error discovering documented endpoints: {e}")
    
    async def _parse_swagger_endpoints(self, page: Page, endpoints: List[DiscoveredEndpoint]):
        """Parse Swagger/OpenAPI documentation for endpoints"""
        try:
            # Look for JSON data in page
            swagger_data = await page.evaluate("""
                () => {
                    // Try to find Swagger JSON data
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        const content = script.textContent;
                        if (content && (content.includes('swagger') || content.includes('openapi'))) {
                            try {
                                const jsonMatch = content.match(/\{[^{}]*"paths"[^{}]*\{.*\}/s);
                                if (jsonMatch) {
                                    return JSON.parse(jsonMatch[0]);
                                }
                            } catch (e) {}
                        }
                    }
                    return null;
                }
            """)
            
            if swagger_data and 'paths' in swagger_data:
                base_url = f"{urlparse(page.url).scheme}://{urlparse(page.url).netloc}"
                
                for path, methods in swagger_data['paths'].items():
                    for method in methods.keys():
                        endpoint_url = urljoin(base_url, path)
                        
                        endpoint = DiscoveredEndpoint(
                            url=endpoint_url,
                            method=method.upper(),
                            headers={},
                            discovery_method='swagger_documentation',
                            timestamp=datetime.now()
                        )
                        
                        endpoint_key = f"{method.upper()}:{endpoint_url}"
                        if endpoint_key not in self.discovered_endpoints:
                            self.discovered_endpoints.add(endpoint_key)
                            endpoints.append(endpoint)
        
        except Exception as e:
            self.logger.error(f"Error parsing Swagger endpoints: {e}")
    
    async def _parse_html_endpoints(self, page: Page, endpoints: List[DiscoveredEndpoint]):
        """Parse HTML content for endpoint references"""
        try:
            # Look for endpoint lists in the page
            endpoint_links = await page.evaluate("""
                () => {
                    const links = [];
                    const linkElements = document.querySelectorAll('a[href*="/api/"], a[href*="/rest/"], a[href*=".json"]');
                    
                    linkElements.forEach(link => {
                        links.push({
                            href: link.href,
                            text: link.textContent.trim()
                        });
                    });
                    
                    return links;
                }
            """)
            
            for link in endpoint_links:
                endpoint = DiscoveredEndpoint(
                    url=link['href'],
                    method='GET',
                    headers={},
                    discovery_method='html_documentation',
                    timestamp=datetime.now()
                )
                
                endpoint_key = f"GET:{link['href']}"
                if endpoint_key not in self.discovered_endpoints:
                    self.discovered_endpoints.add(endpoint_key)
                    endpoints.append(endpoint)
        
        except Exception as e:
            self.logger.error(f"Error parsing HTML endpoints: {e}")
    
    async def _trigger_ajax_behaviors(self, page: Page, endpoints: List[DiscoveredEndpoint]):
        """Trigger behaviors that might cause AJAX requests"""
        try:
            # Look for elements that commonly trigger AJAX
            interactive_selectors = [
                'button[data-url]',
                '[data-ajax]',
                '[data-remote]',
                '.ajax-link',
                '.load-more',
                '.pagination a',
                'select[data-url]',
                'input[data-autocomplete]'
            ]
            
            for selector in interactive_selectors:
                elements = await page.query_selector_all(selector)
                
                for element in elements[:3]:  # Limit to prevent too many requests
                    try:
                        if await element.is_visible():
                            await element.click()
                            await page.wait_for_timeout(1000)  # Wait for potential AJAX
                    except Exception:
                        continue
        
        except Exception as e:
            self.logger.error(f"Error triggering AJAX behaviors: {e}")
