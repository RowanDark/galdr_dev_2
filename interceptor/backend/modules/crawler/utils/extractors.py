# galdr/interceptor/backend/modules/crawler/utils/extractors.py
import re
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class LinkExtractor:
    """Extracts links from HTML content"""
    
    def __init__(self):
        self.link_patterns = [
            r'href=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+)["\']',
            r'action=["\']([^"\']+)["\']',
            r'url\(["\']?([^"\')\s]+)["\']?\)',  # CSS urls
            r'["\']https?://[^"\']+["\']',  # Quoted URLs
        ]
        
        self.excluded_schemes = ['javascript:', 'mailto:', 'tel:', 'data:']
        self.excluded_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg', '.pdf']
    
    def extract_links(self, content: str, base_url: str) -> List[str]:
        """Extract all useful links from content"""
        links = set()
        
        try:
            # Parse HTML with BeautifulSoup for better accuracy
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract from common HTML elements
            for tag in soup.find_all(['a', 'link', 'script', 'img', 'iframe', 'form']):
                for attr in ['href', 'src', 'action']:
                    if tag.get(attr):
                        url = self._normalize_url(tag[attr], base_url)
                        if url and self._is_useful_link(url):
                            links.add(url)
            
            # Extract from CSS and JavaScript
            for script in soup.find_all('script'):
                if script.string:
                    script_links = self._extract_from_text(script.string, base_url)
                    links.update(script_links)
            
            for style in soup.find_all('style'):
                if style.string:
                    style_links = self._extract_from_text(style.string, base_url)
                    links.update(style_links)
            
            # Extract from text content using regex patterns
            text_links = self._extract_from_text(content, base_url)
            links.update(text_links)
            
        except Exception as e:
            # Fallback to regex extraction
            links.update(self._extract_from_text(content, base_url))
        
        return sorted(list(links))
    
    def _extract_from_text(self, text: str, base_url: str) -> Set[str]:
        """Extract links from text using regex patterns"""
        links = set()
        
        for pattern in self.link_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                url = self._normalize_url(match, base_url)
                if url and self._is_useful_link(url):
                    links.add(url)
        
        return links
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize and resolve relative URLs"""
        try:
            url = url.strip().strip('\'"')
            
            # Skip empty URLs
            if not url or url in ['#', '/', '.']:
                return None
            
            # Skip excluded schemes
            if any(url.lower().startswith(scheme) for scheme in self.excluded_schemes):
                return None
            
            # Resolve relative URLs
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            # Remove fragments and normalize
            parsed = urlparse(url)
            if parsed.scheme in ['http', 'https']:
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    normalized += f"?{parsed.query}"
                return normalized
            
        except Exception:
            pass
        
        return None
    
    def _is_useful_link(self, url: str) -> bool:
        """Determine if link is useful for analysis"""
        try:
            parsed = urlparse(url)
            
            # Skip certain file extensions
            if any(parsed.path.lower().endswith(ext) for ext in self.excluded_extensions):
                return False
            
            # Skip very long URLs (likely data URLs)
            if len(url) > 2000:
                return False
            
            return True
            
        except Exception:
            return False


class EmailExtractor:
    """Extracts email addresses from content"""
    
    def __init__(self):
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Common false positives to filter out
        self.excluded_domains = [
            'example.com', 'test.com', 'localhost', 'sentry.io',
            'w3.org', 'schema.org', 'google-analytics.com'
        ]
    
    def extract_emails(self, content: str) -> List[str]:
        """Extract email addresses from content"""
        emails = set()
        
        try:
            # Find all email patterns
            matches = self.email_pattern.findall(content)
            
            for email in matches:
                email = email.lower().strip()
                
                # Skip excluded domains
                domain = email.split('@')[1] if '@' in email else ''
                if domain not in self.excluded_domains:
                    emails.add(email)
        
        except Exception as e:
            pass
        
        return sorted(list(emails))


class FileExtractor:
    """Extracts file references from content"""
    
    def __init__(self, config):
        self.config = config
        
        # Define file type patterns
        self.file_patterns = {
            'javascript': [r'\.js(?:\?[^"\s]*)?', r'text/javascript'],
            'stylesheets': [r'\.css(?:\?[^"\s]*)?', r'text/css'],
            'images': [r'\.(jpg|jpeg|png|gif|svg|webp)(?:\?[^"\s]*)?'],
            'documents': [r'\.(pdf|doc|docx|xls|xlsx|txt|rtf)(?:\?[^"\s]*)?'],
            'data': [r'\.(json|xml|csv|yaml|yml)(?:\?[^"\s]*)?'],
            'archives': [r'\.(zip|rar|tar|gz|7z)(?:\?[^"\s]*)?']
        }
        
        # Add custom extensions from config
        if self.config.custom_file_extensions:
            custom_pattern = '|'.join(ext.replace('.', r'\.') for ext in self.config.custom_file_extensions)
            self.file_patterns['custom'] = [f'({custom_pattern})(?:\?[^"\\s]*)?']
    
    def extract_files(self, content: str, base_url: str) -> Dict[str, List[str]]:
        """Extract file references by type"""
        extracted_files = {}
        
        try:
            # Parse HTML for structured extraction
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract JavaScript files
            if self.config.track_js_files:
                js_files = self._extract_js_files(soup, content, base_url)
                if js_files:
                    extracted_files['javascript'] = js_files
            
            # Extract CSS files
            if self.config.track_css_files:
                css_files = self._extract_css_files(soup, content, base_url)
                if css_files:
                    extracted_files['stylesheets'] = css_files
            
            # Extract other file types based on config
            for file_type, patterns in self.file_patterns.items():
                if self._should_track_file_type(file_type):
                    files = self._extract_by_patterns(content, patterns, base_url)
                    if files:
                        extracted_files[file_type] = files
        
        except Exception as e:
            # Fallback to regex extraction
            for file_type, patterns in self.file_patterns.items():
                if self._should_track_file_type(file_type):
                    files = self._extract_by_patterns(content, patterns, base_url)
                    if files:
                        extracted_files[file_type] = files
        
        return extracted_files
    
    def _extract_js_files(self, soup: BeautifulSoup, content: str, base_url: str) -> List[str]:
        """Extract JavaScript files from HTML"""
        js_files = set()
        
        # Extract from script tags
        for script in soup.find_all('script'):
            if script.get('src'):
                url = urljoin(base_url, script['src'])
                js_files.add(url)
        
        # Extract from text using regex
        js_pattern = r'(?:src=|import\s+.*?from\s*)["\']([^"\']+\.js(?:\?[^"\']*)?)["\']'
        matches = re.findall(js_pattern, content, re.IGNORECASE)
        for match in matches:
            url = urljoin(base_url, match)
            js_files.add(url)
        
        return sorted(list(js_files))
    
    def _extract_css_files(self, soup: BeautifulSoup, content: str, base_url: str) -> List[str]:
        """Extract CSS files from HTML"""
        css_files = set()
        
        # Extract from link tags
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                url = urljoin(base_url, link['href'])
                css_files.add(url)
        
        # Extract from @import in style tags
        for style in soup.find_all('style'):
            if style.string:
                import_matches = re.findall(r'@import\s+url\(["\']?([^"\']+)["\']?\)', style.string)
                for match in import_matches:
                    url = urljoin(base_url, match)
                    css_files.add(url)
        
        return sorted(list(css_files))
    
    def _extract_by_patterns(self, content: str, patterns: List[str], base_url: str) -> List[str]:
        """Extract files using regex patterns"""
        files = set()
        
        for pattern in patterns:
            # Look for URLs containing the pattern
            url_pattern = f'(?:src=|href=|url\\()?["\']?([^"\'\\s]+{pattern}[^"\'\\s]*)["\']?'
            matches = re.findall(url_pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Clean up the match
                if isinstance(match, tuple):
                    match = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                
                if match:
                    url = urljoin(base_url, match.strip('\'"'))
                    if self._is_valid_file_url(url):
                        files.add(url)
        
        return sorted(list(files))
    
    def _should_track_file_type(self, file_type: str) -> bool:
        """Check if file type should be tracked based on config"""
        tracking_map = {
            'javascript': self.config.track_js_files,
            'stylesheets': self.config.track_css_files,
            'images': self.config.track_image_files,
            'documents': self.config.track_document_files,
            'custom': bool(self.config.custom_file_extensions)
        }
        
        return tracking_map.get(file_type, True)
    
    def _is_valid_file_url(self, url: str) -> bool:
        """Validate if URL is a valid file reference"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme in ['http', 'https'] and parsed.netloc and parsed.path)
        except:
            return False
