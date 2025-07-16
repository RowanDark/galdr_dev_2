"""
Page Navigator for Active Spider
Handles intelligent page navigation and interaction
galdr/interceptor/backend/modules/spider/navigation/page_navigator.py
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page, Browser, BrowserContext, ElementHandle

class PageNavigator:
    """Handles smart page navigation and element interaction"""
    
    def __init__(self, browser: Browser):
        self.browser = browser
        self.logger = logging.getLogger(__name__)
        self.visited_urls: Set[str] = set()
        self.interaction_rules = {
            'click_elements': ['a', 'button', '[onclick]', '[role="button"]'],
            'form_elements': ['form', 'input[type="submit"]'],
            'navigation_elements': ['nav a', '.menu a', '.navbar a', '[role="navigation"] a'],
            'avoid_elements': ['[href*="logout"]', '[href*="delete"]', '[onclick*="confirm"]']
        }
    
    async def navigate_and_discover(self, start_url: str, max_depth: int = 3, 
                                  scope_config: Optional[Dict] = None) -> Dict:
        """
        Navigate pages and discover content systematically
        
        Args:
            start_url: Starting URL for navigation
            max_depth: Maximum navigation depth
            scope_config: Navigation scope configuration
            
        Returns:
            Navigation discovery results
        """
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        try:
            results = {
                'start_url': start_url,
                'discovered_pages': [],
                'discovered_links': [],
                'interactions_performed': [],
                'navigation_tree': {},
                'errors': [],
                'statistics': {
                    'pages_visited': 0,
                    'links_discovered': 0,
                    'forms_found': 0,
                    'interactive_elements': 0
                }
            }
            
            # Start navigation from root
            await self._navigate_recursively(
                context, start_url, 0, max_depth, scope_config, results
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Navigation discovery failed: {e}")
            return {'error': str(e)}
        finally:
            await context.close()
    
    async def _navigate_recursively(self, context: BrowserContext, url: str, 
                                  current_depth: int, max_depth: int,
                                  scope_config: Optional[Dict], results: Dict) -> None:
        """Recursively navigate pages"""
        
        if current_depth >= max_depth or url in self.visited_urls:
            return
        
        if scope_config and not self._is_in_scope(url, scope_config):
            return
        
        self.visited_urls.add(url)
        page = await context.new_page()
        
        try:
            self.logger.info(f"Navigating to: {url} (depth: {current_depth})")
            
            # Navigate to page
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response or response.status >= 400:
                results['errors'].append({
                    'url': url,
                    'error': f'HTTP {response.status if response else "timeout"}',
                    'depth': current_depth
                })
                return
            
            # Wait for page to load completely
            await page.wait_for_load_state('networkidle')
            
            # Discover page content
            page_info = await self._analyze_page_content(page, url, current_depth)
            results['discovered_pages'].append(page_info)
            results['statistics']['pages_visited'] += 1
            
            # Discover and analyze links
            links = await self._discover_page_links(page, url)
            results['discovered_links'].extend(links)
            results['statistics']['links_discovered'] += len(links)
            
            # Perform intelligent interactions
            interactions = await self._perform_page_interactions(page, url)
            results['interactions_performed'].extend(interactions)
            results['statistics']['interactive_elements'] += len(interactions)
            
            # Find and analyze forms
            forms = await self._discover_page_forms(page, url)
            results['statistics']['forms_found'] += len(forms)
            
            # Navigate to discovered links
            for link in links:
                if current_depth < max_depth - 1:
                    link_url = link.get('absolute_url')
                    if link_url and link_url not in self.visited_urls:
                        await self._navigate_recursively(
                            context, link_url, current_depth + 1, 
                            max_depth, scope_config, results
                        )
            
        except Exception as e:
            self.logger.error(f"Error navigating {url}: {e}")
            results['errors'].append({
                'url': url,
                'error': str(e),
                'depth': current_depth
            })
        finally:
            await page.close()
    
    async def _analyze_page_content(self, page: Page, url: str, depth: int) -> Dict:
        """Analyze page content and structure"""
        try:
            # Get basic page information
            title = await page.title()
            content = await page.content()
            
            # Analyze page structure
            structure = await self._analyze_page_structure(page)
            
            # Check for JavaScript frameworks
            frameworks = await self._detect_js_frameworks(page)
            
            # Analyze meta information
            meta_info = await self._extract_meta_information(page)
            
            # Check for security headers
            headers = await self._get_response_headers(page)
            
            return {
                'url': url,
                'depth': depth,
                'title': title,
                'content_length': len(content),
                'structure': structure,
                'frameworks': frameworks,
                'meta_info': meta_info,
                'headers': headers,
                'timestamp': page.url,  # Current timestamp would go here
                'screenshot_path': await self._take_screenshot(page, url)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing page {url}: {e}")
            return {'url': url, 'depth': depth, 'error': str(e)}
    
    async def _discover_page_links(self, page: Page, base_url: str) -> List[Dict]:
        """Discover and analyze all links on the page"""
        try:
            # Get all link elements
            link_elements = await page.query_selector_all('a[href]')
            
            links = []
            for element in link_elements:
                try:
                    href = await element.get_attribute('href')
                    text = await element.inner_text()
                    
                    if href:
                        absolute_url = urljoin(base_url, href)
                        
                        # Analyze link properties
                        link_info = {
                            'href': href,
                            'absolute_url': absolute_url,
                            'text': text.strip(),
                            'is_external': self._is_external_link(absolute_url, base_url),
                            'link_type': self._classify_link_type(href, text),
                            'found_on_page': base_url
                        }
                        
                        # Check for additional attributes
                        target = await element.get_attribute('target')
                        if target:
                            link_info['target'] = target
                        
                        rel = await element.get_attribute('rel')
                        if rel:
                            link_info['rel'] = rel
                        
                        links.append(link_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing link element: {e}")
                    continue
            
            return links
            
        except Exception as e:
            self.logger.error(f"Error discovering links on {base_url}: {e}")
            return []
    
    async def _perform_page_interactions(self, page: Page, url: str) -> List[Dict]:
        """Perform intelligent page interactions to discover hidden content"""
        interactions = []
        
        try:
            # Find interactive elements
            interactive_selectors = [
                'button:not([disabled])',
                '[role="button"]:not([disabled])',
                '[onclick]:not(a)',
                '.dropdown-toggle',
                '.menu-toggle',
                '[data-toggle]',
                '.accordion-header',
                '.tab-header'
            ]
            
            for selector in interactive_selectors:
                elements = await page.query_selector_all(selector)
                
                for element in elements[:5]:  # Limit interactions per selector
                    try:
                        # Check if element is visible and clickable
                        if await element.is_visible() and await element.is_enabled():
                            
                            # Get element info before interaction
                            element_text = await element.inner_text()
                            element_tag = await element.evaluate('el => el.tagName')
                            
                            # Perform click interaction
                            await element.click(timeout=5000)
                            
                            # Wait for potential content changes
                            await page.wait_for_timeout(1000)
                            
                            # Check for new content or URL changes
                            new_url = page.url
                            
                            interaction = {
                                'type': 'click',
                                'element_selector': selector,
                                'element_text': element_text.strip(),
                                'element_tag': element_tag,
                                'original_url': url,
                                'result_url': new_url,
                                'url_changed': new_url != url,
                                'interaction_successful': True
                            }
                            
                            interactions.append(interaction)
                            
                            # If URL changed, we've navigated away
                            if new_url != url:
                                await page.go_back(wait_until='networkidle')
                                await page.wait_for_timeout(1000)
                        
                    except Exception as e:
                        interactions.append({
                            'type': 'click',
                            'element_selector': selector,
                            'error': str(e),
                            'interaction_successful': False
                        })
                        continue
            
            # Try to trigger AJAX requests
            ajax_interactions = await self._trigger_ajax_interactions(page)
            interactions.extend(ajax_interactions)
            
            return interactions
            
        except Exception as e:
            self.logger.error(f"Error performing interactions on {url}: {e}")
            return []
    
    async def _discover_page_forms(self, page: Page, url: str) -> List[Dict]:
        """Discover and analyze forms on the page"""
        try:
            form_elements = await page.query_selector_all('form')
            forms = []
            
            for form in form_elements:
                try:
                    form_info = await self._analyze_form_element(form, url)
                    forms.append(form_info)
                except Exception as e:
                    self.logger.warning(f"Error analyzing form: {e}")
                    continue
            
            return forms
            
        except Exception as e:
            self.logger.error(f"Error discovering forms on {url}: {e}")
            return []
    
    async def _analyze_form_element(self, form: ElementHandle, url: str) -> Dict:
        """Analyze a single form element"""
        action = await form.get_attribute('action') or url
        method = await form.get_attribute('method') or 'GET'
        encoding = await form.get_attribute('enctype') or 'application/x-www-form-urlencoded'
        
        # Get form fields
        fields = []
        input_elements = await form.query_selector_all('input, textarea, select')
        
        for input_elem in input_elements:
            field_type = await input_elem.get_attribute('type') or 'text'
            field_name = await input_elem.get_attribute('name')
            field_id = await input_elem.get_attribute('id')
            placeholder = await input_elem.get_attribute('placeholder')
            required = await input_elem.get_attribute('required') is not None
            
            fields.append({
                'type': field_type,
                'name': field_name,
                'id': field_id,
                'placeholder': placeholder,
                'required': required
            })
        
        return {
            'action': urljoin(url, action),
            'method': method.upper(),
            'encoding': encoding,
            'field_count': len(fields),
            'fields': fields,
            'found_on_page': url
        }
    
    async def _analyze_page_structure(self, page: Page) -> Dict:
        """Analyze page structure and organization"""
        try:
            structure = {}
            
            # Count different element types
            structure['headings'] = {
                'h1': len(await page.query_selector_all('h1')),
                'h2': len(await page.query_selector_all('h2')),
                'h3': len(await page.query_selector_all('h3')),
                'h4': len(await page.query_selector_all('h4')),
                'h5': len(await page.query_selector_all('h5')),
                'h6': len(await page.query_selector_all('h6'))
            }
            
            structure['content'] = {
                'paragraphs': len(await page.query_selector_all('p')),
                'lists': len(await page.query_selector_all('ul, ol')),
                'images': len(await page.query_selector_all('img')),
                'tables': len(await page.query_selector_all('table'))
            }
            
            structure['interactive'] = {
                'links': len(await page.query_selector_all('a[href]')),
                'buttons': len(await page.query_selector_all('button')),
                'forms': len(await page.query_selector_all('form')),
                'inputs': len(await page.query_selector_all('input'))
            }
            
            structure['media'] = {
                'videos': len(await page.query_selector_all('video')),
                'audio': len(await page.query_selector_all('audio')),
                'iframes': len(await page.query_selector_all('iframe'))
            }
            
            # Check for semantic HTML5 elements
            structure['semantic'] = {
                'nav': len(await page.query_selector_all('nav')),
                'header': len(await page.query_selector_all('header')),
                'footer': len(await page.query_selector_all('footer')),
                'main': len(await page.query_selector_all('main')),
                'article': len(await page.query_selector_all('article')),
                'section': len(await page.query_selector_all('section')),
                'aside': len(await page.query_selector_all('aside'))
            }
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Error analyzing page structure: {e}")
            return {}
    
    async def _detect_js_frameworks(self, page: Page) -> List[str]:
        """Detect JavaScript frameworks and libraries"""
        try:
            frameworks = []
            
            # Check for common frameworks
            framework_checks = {
                'React': 'window.React',
                'Vue': 'window.Vue',
                'Angular': 'window.angular || window.ng',
                'jQuery': 'window.jQuery || window.$',
                'Bootstrap': 'window.bootstrap',
                'D3': 'window.d3',
                'Lodash': 'window._',
                'Moment': 'window.moment',
                'Axios': 'window.axios',
                'Chart.js': 'window.Chart'
            }
            
            for framework, check in framework_checks.items():
                try:
                    result = await page.evaluate(f'!!({check})')
                    if result:
                        frameworks.append(framework)
                except:
                    continue
            
            # Check for framework-specific elements
            if await page.query_selector('[data-reactroot], [data-react-checksum]'):
                if 'React' not in frameworks:
                    frameworks.append('React')
            
            if await page.query_selector('[v-app], [data-v-]'):
                if 'Vue' not in frameworks:
                    frameworks.append('Vue')
            
            if await page.query_selector('[ng-app], [ng-controller], .ng-scope'):
                if 'Angular' not in frameworks:
                    frameworks.append('Angular')
            
            return frameworks
            
        except Exception as e:
            self.logger.error(f"Error detecting JS frameworks: {e}")
            return []
    
    async def _extract_meta_information(self, page: Page) -> Dict:
        """Extract meta information from page"""
        try:
            meta_info = {}
            
            # Basic meta tags
            meta_tags = await page.query_selector_all('meta')
            
            for meta in meta_tags:
                name = await meta.get_attribute('name')
                property_attr = await meta.get_attribute('property')
                content = await meta.get_attribute('content')
                
                if name and content:
                    meta_info[name] = content
                elif property_attr and content:
                    meta_info[property_attr] = content
            
            # Specific important meta tags
            description = await page.query_selector('meta[name="description"]')
            if description:
                meta_info['description'] = await description.get_attribute('content')
            
            keywords = await page.query_selector('meta[name="keywords"]')
            if keywords:
                meta_info['keywords'] = await keywords.get_attribute('content')
            
            # Open Graph tags
            og_tags = await page.query_selector_all('meta[property^="og:"]')
            for og in og_tags:
                property_attr = await og.get_attribute('property')
                content = await og.get_attribute('content')
                if property_attr and content:
                    meta_info[property_attr] = content
            
            return meta_info
            
        except Exception as e:
            self.logger.error(f"Error extracting meta information: {e}")
            return {}
    
    async def _get_response_headers(self, page: Page) -> Dict:
        """Get response headers for the page"""
        try:
            # This would require intercepting the response
            # For now, return basic information that can be extracted
            return {
                'url': page.url,
                'status': 200  # Placeholder - would need response interception
            }
        except Exception as e:
            self.logger.error(f"Error getting response headers: {e}")
            return {}
    
    async def _take_screenshot(self, page: Page, url: str) -> Optional[str]:
        """Take screenshot of the page"""
        try:
            # Generate filename from URL
            parsed = urlparse(url)
            filename = f"spider_{parsed.netloc}_{parsed.path.replace('/', '_')}.png"
            screenshot_path = f"screenshots/{filename}"
            
            await page.screenshot(path=screenshot_path, full_page=True)
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def _trigger_ajax_interactions(self, page: Page) -> List[Dict]:
        """Try to trigger AJAX requests through interactions"""
        interactions = []
        
        try:
            # Look for elements that might trigger AJAX
            ajax_selectors = [
                '[data-remote="true"]',
                '.ajax-link',
                '[data-url]',
                '.load-more',
                '.pagination a'
            ]
            
            for selector in ajax_selectors:
                elements = await page.query_selector_all(selector)
                
                for element in elements[:3]:  # Limit AJAX interactions
                    try:
                        if await element.is_visible():
                            # Listen for network requests
                            requests_made = []
                            
                            def track_request(request):
                                requests_made.append({
                                    'url': request.url,
                                    'method': request.method,
                                    'resource_type': request.resource_type
                                })
                            
                            page.on('request', track_request)
                            
                            # Perform interaction
                            await element.click()
                            await page.wait_for_timeout(2000)
                            
                            page.remove_listener('request', track_request)
                            
                            if requests_made:
                                interactions.append({
                                    'type': 'ajax_trigger',
                                    'element_selector': selector,
                                    'requests_triggered': requests_made,
                                    'successful': True
                                })
                    
                    except Exception as e:
                        interactions.append({
                            'type': 'ajax_trigger',
                            'element_selector': selector,
                            'error': str(e),
                            'successful': False
                        })
                        continue
            
            return interactions
            
        except Exception as e:
            self.logger.error(f"Error triggering AJAX interactions: {e}")
            return []
    
    def _is_in_scope(self, url: str, scope_config: Dict) -> bool:
        """Check if URL is within navigation scope"""
        if not scope_config:
            return True
        
        parsed = urlparse(url)
        
        # Check allowed domains
        allowed_domains = scope_config.get('allowed_domains', [])
        if allowed_domains and parsed.netloc not in allowed_domains:
            return False
        
        # Check excluded paths
        excluded_paths = scope_config.get('excluded_paths', [])
        for excluded in excluded_paths:
            if excluded in parsed.path:
                return False
        
        # Check URL patterns
        excluded_patterns = scope_config.get('excluded_patterns', [])
        for pattern in excluded_patterns:
            if pattern in url:
                return False
        
        return True
    
    def _is_external_link(self, url: str, base_url: str) -> bool:
        """Check if link is external"""
        try:
            url_domain = urlparse(url).netloc
            base_domain = urlparse(base_url).netloc
            return url_domain != base_domain and url_domain != ''
        except:
            return False
    
    def _classify_link_type(self, href: str, text: str) -> str:
        """Classify the type of link"""
        href_lower = href.lower()
        text_lower = text.lower()
        
        # File downloads
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        if any(ext in href_lower for ext in file_extensions):
            return 'file_download'
        
        # External links
        if href.startswith('http') and not href.startswith('#'):
            return 'external'
        
        # Anchors
        if href.startswith('#'):
            return 'anchor'
        
        # JavaScript
        if href.startswith('javascript:'):
            return 'javascript'
        
        # Email
        if href.startswith('mailto:'):
            return 'email'
        
        # Navigation
        if any(word in text_lower for word in ['menu', 'nav', 'home', 'about', 'contact']):
            return 'navigation'
        
        # Admin/sensitive
        if any(word in href_lower for word in ['admin', 'login', 'logout', 'dashboard']):
            return 'admin'
        
        return 'page'
