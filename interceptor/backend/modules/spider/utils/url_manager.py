# galdr/interceptor/backend/modules/spider/utils/url_manager.py
import re
from typing import Set, List
from urllib.parse import urlparse, urljoin


class URLManager:
    """Manages URL filtering, normalization, and scope control"""
    
    def __init__(self, config):
        self.config = config
        self.visited_urls: Set[str] = set()
        
        # Default excluded patterns
        self.excluded_patterns = [
            r'logout',
            r'signout',
            r'delete',
            r'remove',
            r'destroy',
            r'\.pdf$',
            r'\.zip$',
            r'\.exe$',
            r'\.dmg$',
            r'\.deb$',
            r'\.rpm$',
            r'javascript:',
            r'mailto:',
            r'tel:',
            r'ftp:',
        ]
        
        # Add configured exclusions
        if config.excluded_file_types:
            for ext in config.excluded_file_types:
                self.excluded_patterns.append(f'{re.escape(ext)}$')
        
        if config.excluded_paths:
            for path in config.excluded_paths:
                self.excluded_patterns.append(re.escape(path))
    
    def should_process_url(self, url: str, target_url: str) -> bool:
        """Determine if URL should be processed"""
        try:
            parsed_url = urlparse(url)
            parsed_target = urlparse(target_url)
            
            # Check if already visited
            if url in self.visited_urls:
                return False
            
            # Check domain scope
            if self.config.stay_in_domain:
                if parsed_url.netloc != parsed_target.netloc:
                    return False
            
            # Check allowed domains
            if self.config.allowed_domains:
                if parsed_url.netloc not in self.config.allowed_domains:
                    return False
            
            # Check excluded patterns
            for pattern in self.excluded_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            # Check scheme
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            return True
            
        except Exception:
            return False
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize URL"""
        try:
            # Handle relative URLs
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            # Remove fragment
            parsed = urlparse(url)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            return normalized
            
        except Exception:
            return url
    
    def add_visited_url(self, url: str):
        """Mark URL as visited"""
        self.visited_urls.add(url)
    
    def get_visited_count(self) -> int:
        """Get number of visited URLs"""
        return len(self.visited_urls)
    
    def clear_visited(self):
        """Clear visited URLs"""
        self.visited_urls.clear()
