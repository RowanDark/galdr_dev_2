"""
Basic Content Analyzer for Passive Crawler Module
Provides fundamental content analysis capabilities
galdr/interceptor/backend/modules/crawler/analyzers/content.py
"""

import re
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse
from collections import Counter

class ContentAnalyzer:
    """Basic content analysis for passive crawling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Basic content patterns
        self.content_patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone_numbers': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'ip_addresses': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'urls': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'credit_cards': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'social_security': r'\b\d{3}-\d{2}-\d{4}\b'
        }
        
        # File type patterns
        self.file_patterns = {
            'documents': r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt|rtf)(?:\?|$|#)',
            'images': r'\.(jpg|jpeg|png|gif|bmp|svg|webp|ico)(?:\?|$|#)',
            'archives': r'\.(zip|rar|7z|tar|gz|bz2)(?:\?|$|#)',
            'executables': r'\.(exe|msi|dmg|app|deb|rpm)(?:\?|$|#)',
            'scripts': r'\.(js|css|php|asp|aspx|jsp|py|rb|pl)(?:\?|$|#)',
            'media': r'\.(mp4|avi|mov|wmv|flv|mp3|wav|aac|flac)(?:\?|$|#)'
        }
        
        # Basic vulnerability indicators
        self.vuln_indicators = {
            'sql_error': [
                r'ORA-\d+',
                r'MySQL.*Error',
                r'SQLServer.*Error',
                r'PostgreSQL.*ERROR',
                r'sqlite3.OperationalError'
            ],
            'stack_trace': [
                r'at\s+[a-zA-Z0-9_$]+\.[a-zA-Z0-9_$]+\(',
                r'Traceback \(most recent call last\)',
                r'Fatal error:.*in.*on line',
                r'Warning:.*in.*on line'
            ],
            'debug_info': [
                r'DEBUG.*=.*true',
                r'ENVIRONMENT.*=.*development',
                r'print_r\(',
                r'var_dump\(',
                r'console\.log\('
            ]
        }
    
    def analyze(self, content: str, headers: Dict[str, str], url: str) -> Dict:
        """
        Analyze content for basic patterns and information
        
        Args:
            content: Response content
            headers: HTTP headers
            url: Request URL
            
        Returns:
            Analysis results
        """
        try:
            analysis = {
                'url': url,
                'content_type': headers.get('Content-Type', 'unknown'),
                'content_length': len(content),
                'encoding': self._detect_encoding(headers, content),
                'language': self._detect_language(content),
                'extracted_data': self._extract_data_patterns(content),
                'file_references': self._extract_file_references(content),
                'vulnerability_indicators': self._detect_vulnerability_indicators(content),
                'metadata': self._extract_metadata(content),
                'forms': self._analyze_forms(content),
                'technologies': self._detect_technologies(content, headers),
                'security_headers': self._analyze_security_headers(headers),
                'content_analysis': self._analyze_content_structure(content)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Content analysis failed for {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'content_type': headers.get('Content-Type', 'unknown')
            }
    
    def _extract_data_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract common data patterns from content"""
        extracted = {}
        
        for pattern_name, pattern in self.content_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Remove duplicates and limit results
                unique_matches = list(set(matches))[:50]  # Limit to 50 matches per pattern
                extracted[pattern_name] = unique_matches
        
        return extracted
    
    def _extract_file_references(self, content: str) -> Dict[str, List[str]]:
        """Extract file references by type"""
        file_refs = {}
        
        for file_type, pattern in self.file_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                unique_matches = list(set(matches))[:100]  # Limit results
                file_refs[file_type] = unique_matches
        
        return file_refs
    
    def _detect_vulnerability_indicators(self, content: str) -> Dict[str, List[str]]:
        """Detect basic vulnerability indicators"""
        indicators = {}
        
        for vuln_type, patterns in self.vuln_indicators.items():
            found_indicators = []
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    found_indicators.extend(matches)
            
            if found_indicators:
                indicators[vuln_type] = list(set(found_indicators))[:10]  # Limit results
        
        return indicators
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract basic metadata from content"""
        metadata = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', 
                              content, re.IGNORECASE)
        if desc_match:
            metadata['description'] = desc_match.group(1)
        
        # Extract meta keywords
        keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', 
                                  content, re.IGNORECASE)
        if keywords_match:
            metadata['keywords'] = keywords_match.group(1)
        
        # Extract robots meta
        robots_match = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', 
                                content, re.IGNORECASE)
        if robots_match:
            metadata['robots'] = robots_match.group(1)
        
        return metadata
    
    def _analyze_forms(self, content: str) -> List[Dict]:
        """Basic form analysis"""
        forms = []
        
        # Find all forms
        form_matches = re.finditer(r'<form[^>]*>(.*?)</form>', content, re.IGNORECASE | re.DOTALL)
        
        for form_match in form_matches:
            form_html = form_match.group(0)
            form_content = form_match.group(1)
            
            # Extract form attributes
            action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
            method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
            
            # Count input fields
            input_count = len(re.findall(r'<input[^>]*>', form_content, re.IGNORECASE))
            
            # Check for password fields
            has_password = bool(re.search(r'type=["\']password["\']', form_content, re.IGNORECASE))
            
            # Check for file uploads
            has_file_upload = bool(re.search(r'type=["\']file["\']', form_content, re.IGNORECASE))
            
            form_info = {
                'action': action_match.group(1) if action_match else '',
                'method': method_match.group(1) if method_match else 'GET',
                'input_count': input_count,
                'has_password': has_password,
                'has_file_upload': has_file_upload
            }
            
            forms.append(form_info)
        
        return forms
    
    def _detect_technologies(self, content: str, headers: Dict[str, str]) -> List[str]:
        """Basic technology detection"""
        technologies = []
        
        # Check headers for technology indicators
        server_header = headers.get('Server', '').lower()
        powered_by = headers.get('X-Powered-By', '').lower()
        
        if 'apache' in server_header:
            technologies.append('Apache')
        elif 'nginx' in server_header:
            technologies.append('Nginx')
        elif 'iis' in server_header:
            technologies.append('IIS')
        
        if 'php' in powered_by:
            technologies.append('PHP')
        elif 'asp.net' in powered_by:
            technologies.append('ASP.NET')
        
        # Check content for technology indicators
        content_lower = content.lower()
        
        if 'wordpress' in content_lower or 'wp-content' in content_lower:
            technologies.append('WordPress')
        elif 'drupal' in content_lower:
            technologies.append('Drupal')
        elif 'joomla' in content_lower:
            technologies.append('Joomla')
        
        if 'jquery' in content_lower:
            technologies.append('jQuery')
        if 'bootstrap' in content_lower:
            technologies.append('Bootstrap')
        if 'react' in content_lower:
            technologies.append('React')
        if 'angular' in content_lower:
            technologies.append('Angular')
        
        return list(set(technologies))  # Remove duplicates
    
    def _analyze_security_headers(self, headers: Dict[str, str]) -> Dict:
        """Analyze security headers"""
        security_headers = {
            'present': [],
            'missing': []
        }
        
        important_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy'
        ]
        
        for header in important_headers:
            if any(header.lower() == h.lower() for h in headers.keys()):
                security_headers['present'].append(header)
            else:
                security_headers['missing'].append(header)
        
        return security_headers
    
    def _analyze_content_structure(self, content: str) -> Dict:
        """Analyze basic content structure"""
        structure = {}
        
        # Count HTML elements
        structure['html_tags'] = len(re.findall(r'<[^/>][^>]*>', content))
        structure['links'] = len(re.findall(r'<a[^>]*href', content, re.IGNORECASE))
        structure['images'] = len(re.findall(r'<img[^>]*src', content, re.IGNORECASE))
        structure['scripts'] = len(re.findall(r'<script[^>]*>', content, re.IGNORECASE))
        structure['stylesheets'] = len(re.findall(r'<link[^>]*rel=["\']stylesheet["\']', content, re.IGNORECASE))
        
        # Count forms and inputs
        structure['forms'] = len(re.findall(r'<form[^>]*>', content, re.IGNORECASE))
        structure['inputs'] = len(re.findall(r'<input[^>]*>', content, re.IGNORECASE))
        
        # Check for common vulnerabilities
        structure['inline_javascript'] = len(re.findall(r'<script[^>]*>[^<]', content, re.IGNORECASE))
        structure['inline_styles'] = len(re.findall(r'style\s*=\s*["\']', content, re.IGNORECASE))
        
        return structure
    
    def _detect_encoding(self, headers: Dict[str, str], content: str) -> str:
        """Detect content encoding"""
        # Check Content-Type header
        content_type = headers.get('Content-Type', '')
        encoding_match = re.search(r'charset=([^;]+)', content_type, re.IGNORECASE)
        if encoding_match:
            return encoding_match.group(1).strip()
        
        # Check HTML meta tag
        meta_encoding = re.search(r'<meta[^>]*charset=["\']?([^"\'>\s]+)', content, re.IGNORECASE)
        if meta_encoding:
            return meta_encoding.group(1)
        
        return 'unknown'
    
    def _detect_language(self, content: str) -> str:
        """Detect content language"""
        # Check HTML lang attribute
        lang_match = re.search(r'<html[^>]*lang=["\']?([^"\'>\s]+)', content, re.IGNORECASE)
        if lang_match:
            return lang_match.group(1)
        
        # Check meta language
        meta_lang = re.search(r'<meta[^>]*name=["\']language["\'][^>]*content=["\']([^"\']*)["\']', 
                             content, re.IGNORECASE)
        if meta_lang:
            return meta_lang.group(1)
        
        return 'unknown'
