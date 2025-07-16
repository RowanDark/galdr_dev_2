"""
Content Analyzer for Active Spider Module
Provides spider-specific content analysis and vulnerability detection
galdr/interceptor/backend/modules/spider/analysis/content_analyzer.py
"""

import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging

class SpiderContentAnalyzer:
    """Advanced content analysis for spider discovery"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Vulnerability patterns for spider analysis
        self.vuln_patterns = {
            'xss_reflected': [
                r'<script[^>]*>.*?alert\s*\([^)]*\).*?</script>',
                r'javascript:\s*alert\s*\(',
                r'on\w+\s*=\s*["\'].*?alert\s*\(',
            ],
            'sql_injection': [
                r'(\'|\").*?(or|and)\s+\d+\s*=\s*\d+',
                r'union\s+select.*?from',
                r'exec\s*\(\s*\'.*?\'\s*\)',
            ],
            'path_traversal': [
                r'\.\.\/.*?\.\.\/.*?\.\./',
                r'\.\.\\.*?\.\.\\.*?\.\.\\'
            ],
            'command_injection': [
                r';\s*(cat|ls|pwd|whoami|id)\s*;',
                r'\|\s*(cat|ls|pwd|whoami|id)\s*\|',
            ]
        }
        
        # Sensitive data patterns
        self.secret_patterns = {
            'api_keys': [
                r'api[_-]?key\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']',
                r'token\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']',
            ],
            'passwords': [
                r'password\s*[:=]\s*["\']([^"\']{8,})["\']',
                r'passwd\s*[:=]\s*["\']([^"\']{8,})["\']',
            ],
            'database_strings': [
                r'mysql://[^:]+:[^@]+@[^/]+/',
                r'postgresql://[^:]+:[^@]+@[^/]+/',
                r'mongodb://[^:]+:[^@]+@[^/]+/',
            ],
            'aws_keys': [
                r'AKIA[0-9A-Z]{16}',
                r'aws_secret_access_key\s*[:=]\s*["\']([^"\']{40})["\']',
            ]
        }
        
        # Technology detection patterns
        self.tech_patterns = {
            'frameworks': {
                'react': [r'react', r'_react', r'React\.', r'ReactDOM'],
                'angular': [r'angular', r'ng-', r'Angular'],
                'vue': [r'vue\.js', r'Vue\.', r'v-'],
                'jquery': [r'jquery', r'\$\(', r'jQuery'],
                'bootstrap': [r'bootstrap', r'btn-', r'col-'],
                'foundation': [r'foundation', r'zurb'],
            },
            'cms': {
                'wordpress': [r'wp-content', r'wp-admin', r'wp-includes'],
                'drupal': [r'sites/default', r'modules/', r'Drupal'],
                'joomla': [r'components/com_', r'Joomla'],
                'magento': [r'skin/frontend', r'Magento'],
            },
            'servers': {
                'apache': [r'Apache/', r'mod_'],
                'nginx': [r'nginx/', r'X-Nginx'],
                'iis': [r'Microsoft-IIS', r'X-Powered-By: ASP.NET'],
                'tomcat': [r'Tomcat/', r'catalina'],
            }
        }
    
    def analyze_page_content(self, content: str, url: str, headers: Dict) -> Dict:
        """
        Comprehensive analysis of page content
        
        Args:
            content: HTML content of the page
            url: URL of the page
            headers: HTTP response headers
            
        Returns:
            Analysis results with vulnerabilities, secrets, and technologies
        """
        try:
            analysis_result = {
                'url': url,
                'content_hash': hashlib.md5(content.encode()).hexdigest(),
                'content_length': len(content),
                'analysis_timestamp': None,  # Would be current timestamp
                'vulnerabilities': self._detect_vulnerabilities(content, url),
                'secrets': self._detect_secrets(content),
                'technologies': self._detect_technologies(content, headers),
                'forms': self._analyze_forms(content, url),
                'links': self._analyze_links(content, url),
                'inputs': self._analyze_inputs(content),
                'comments': self._extract_comments(content),
                'meta_data': self._extract_metadata(content),
                'security_headers': self._analyze_security_headers(headers),
                'content_security': self._analyze_content_security(content),
                'accessibility': self._analyze_accessibility(content),
                'seo_analysis': self._analyze_seo(content)
            }
            
            # Calculate risk score
            analysis_result['risk_score'] = self._calculate_risk_score(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Content analysis failed for {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    def _detect_vulnerabilities(self, content: str, url: str) -> List[Dict]:
        """Detect potential vulnerabilities in content"""
        vulnerabilities = []
        
        for vuln_type, patterns in self.vuln_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    vulnerabilities.append({
                        'type': vuln_type,
                        'pattern': pattern,
                        'match': match.group(0)[:200],  # Limit length
                        'position': match.start(),
                        'severity': self._assess_vulnerability_severity(vuln_type),
                        'confidence': self._assess_confidence(vuln_type, match.group(0)),
                        'recommendation': self._get_vulnerability_recommendation(vuln_type)
                    })
        
        # Check for additional context-specific vulnerabilities
        vulnerabilities.extend(self._detect_context_vulnerabilities(content, url))
        
        return vulnerabilities
    
    def _detect_secrets(self, content: str) -> List[Dict]:
        """Detect sensitive information in content"""
        secrets = []
        
        for secret_type, patterns in self.secret_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Extract the secret value (usually in group 1)
                    secret_value = match.group(1) if match.groups() else match.group(0)
                    
                    secrets.append({
                        'type': secret_type,
                        'value': secret_value[:50] + '...' if len(secret_value) > 50 else secret_value,
                        'full_match': match.group(0)[:100],
                        'position': match.start(),
                        'severity': self._assess_secret_severity(secret_type),
                        'entropy': self._calculate_entropy(secret_value),
                        'recommendation': f'Remove {secret_type} from client-side code'
                    })
        
        return secrets
    
    def _detect_technologies(self, content: str, headers: Dict) -> Dict:
        """Detect technologies used on the page"""
        detected_tech = {
            'frameworks': [],
            'cms': [],
            'servers': [],
            'languages': [],
            'libraries': []
        }
        
        # Analyze content for technology patterns
        for tech_category, technologies in self.tech_patterns.items():
            for tech_name, patterns in technologies.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        if tech_category not in detected_tech:
                            detected_tech[tech_category] = []
                        
                        if tech_name not in detected_tech[tech_category]:
                            detected_tech[tech_category].append({
                                'name': tech_name,
                                'confidence': 'high',
                                'detection_method': 'content_pattern'
                            })
        
        # Analyze headers for technology indicators
        detected_tech.update(self._detect_tech_from_headers(headers))
        
        # Analyze script sources and imports
        detected_tech['libraries'].extend(self._detect_libraries(content))
        
        return detected_tech
    
    def _analyze_forms(self, content: str, url: str) -> List[Dict]:
        """Analyze forms for security implications"""
        forms = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            form_elements = soup.find_all('form')
            
            for form in form_elements:
                form_analysis = {
                    'action': form.get('action', ''),
                    'method': form.get('method', 'GET').upper(),
                    'absolute_action': urljoin(url, form.get('action', '')),
                    'enctype': form.get('enctype', 'application/x-www-form-urlencoded'),
                    'inputs': [],
                    'security_issues': []
                }
                
                # Analyze form inputs
                inputs = form.find_all(['input', 'textarea', 'select'])
                for input_elem in inputs:
                    input_analysis = {
                        'type': input_elem.get('type', 'text'),
                        'name': input_elem.get('name', ''),
                        'id': input_elem.get('id', ''),
                        'required': input_elem.has_attr('required'),
                        'autocomplete': input_elem.get('autocomplete', ''),
                        'placeholder': input_elem.get('placeholder', ''),
                        'value': input_elem.get('value', '')
                    }
                    form_analysis['inputs'].append(input_analysis)
                
                # Check for security issues
                if form_analysis['method'] == 'GET' and any(inp['type'] == 'password' for inp in form_analysis['inputs']):
                    form_analysis['security_issues'].append('Password sent via GET method')
                
                if not form.find('input', {'type': 'hidden', 'name': re.compile(r'csrf|token', re.I)}):
                    form_analysis['security_issues'].append('No CSRF protection detected')
                
                forms.append(form_analysis)
        
        except Exception as e:
            self.logger.warning(f"Form analysis error: {e}")
        
        return forms
    
    def _analyze_links(self, content: str, url: str) -> Dict:
        """Analyze links and their characteristics"""
        link_analysis = {
            'total_links': 0,
            'internal_links': 0,
            'external_links': 0,
            'suspicious_links': [],
            'broken_links': [],
            'redirects': []
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            parsed_base = urlparse(url)
            
            for link in links:
                href = link.get('href')
                absolute_url = urljoin(url, href)
                parsed_link = urlparse(absolute_url)
                
                link_analysis['total_links'] += 1
                
                # Categorize link
                if parsed_link.netloc == parsed_base.netloc:
                    link_analysis['internal_links'] += 1
                else:
                    link_analysis['external_links'] += 1
                
                # Check for suspicious patterns
                if self._is_suspicious_link(href, link.get_text().strip()):
                    link_analysis['suspicious_links'].append({
                        'url': absolute_url,
                        'text': link.get_text().strip(),
                        'reason': self._get_suspicion_reason(href)
                    })
        
        except Exception as e:
            self.logger.warning(f"Link analysis error: {e}")
        
        return link_analysis
    
    def _analyze_inputs(self, content: str) -> Dict:
        """Analyze input fields for security implications"""
        input_analysis = {
            'total_inputs': 0,
            'password_inputs': 0,
            'file_inputs': 0,
            'hidden_inputs': 0,
            'autocomplete_off': 0,
            'security_issues': []
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            inputs = soup.find_all(['input', 'textarea'])
            
            for input_elem in inputs:
                input_type = input_elem.get('type', 'text').lower()
                input_analysis['total_inputs'] += 1
                
                if input_type == 'password':
                    input_analysis['password_inputs'] += 1
                elif input_type == 'file':
                    input_analysis['file_inputs'] += 1
                elif input_type == 'hidden':
                    input_analysis['hidden_inputs'] += 1
                
                if input_elem.get('autocomplete', '').lower() == 'off':
                    input_analysis['autocomplete_off'] += 1
                
                # Check for security issues
                if input_type == 'password' and not input_elem.get('autocomplete'):
                    input_analysis['security_issues'].append('Password field without autocomplete attribute')
        
        except Exception as e:
            self.logger.warning(f"Input analysis error: {e}")
        
        return input_analysis
    
    def _extract_comments(self, content: str) -> List[Dict]:
        """Extract and analyze HTML comments"""
        comments = []
        
        # Find HTML comments
        comment_pattern = r'<!--(.*?)-->'
        comment_matches = re.finditer(comment_pattern, content, re.DOTALL)
        
        for match in comment_matches:
            comment_text = match.group(1).strip()
            
            # Check for sensitive information in comments
            sensitivity_score = self._assess_comment_sensitivity(comment_text)
            
            comments.append({
                'text': comment_text[:200],  # Limit length
                'position': match.start(),
                'length': len(comment_text),
                'sensitivity_score': sensitivity_score,
                'contains_secrets': self._check_comment_secrets(comment_text)
            })
        
        return comments
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from page"""
        metadata = {}
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Title
            title = soup.find('title')
            if title:
                metadata['title'] = title.get_text().strip()
            
            # Meta tags
            meta_tags = soup.find_all('meta')
            metadata['meta_tags'] = {}
            
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property')
                content_val = meta.get('content')
                
                if name and content_val:
                    metadata['meta_tags'][name] = content_val
            
            # Generator information
            generator = soup.find('meta', {'name': 'generator'})
            if generator:
                metadata['generator'] = generator.get('content')
        
        except Exception as e:
            self.logger.warning(f"Metadata extraction error: {e}")
        
        return metadata
    
    def _analyze_security_headers(self, headers: Dict) -> Dict:
        """Analyze security-related HTTP headers"""
        security_headers = {
            'present': [],
            'missing': [],
            'analysis': {}
        }
        
        expected_headers = {
            'x-frame-options': 'Prevents clickjacking attacks',
            'x-content-type-options': 'Prevents MIME type sniffing',
            'x-xss-protection': 'Enables XSS filtering',
            'strict-transport-security': 'Enforces HTTPS connections',
            'content-security-policy': 'Prevents various injection attacks',
            'referrer-policy': 'Controls referrer information',
            'feature-policy': 'Controls browser features'
        }
        
        for header, description in expected_headers.items():
            header_value = headers.get(header) or headers.get(header.title())
            
            if header_value:
                security_headers['present'].append(header)
                security_headers['analysis'][header] = {
                    'value': header_value,
                    'description': description,
                    'strength': self._assess_header_strength(header, header_value)
                }
            else:
                security_headers['missing'].append({
                    'header': header,
                    'description': description,
                    'risk_level': self._assess_missing_header_risk(header)
                })
        
        return security_headers
    
    def _analyze_content_security(self, content: str) -> Dict:
        """Analyze content for security implications"""
        security_analysis = {
            'inline_scripts': 0,
            'inline_styles': 0,
            'external_scripts': 0,
            'external_styles': 0,
            'mixed_content': [],
            'security_score': 0
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Count inline scripts
            inline_scripts = soup.find_all('script', src=False)
            security_analysis['inline_scripts'] = len(inline_scripts)
            
            # Count external scripts
            external_scripts = soup.find_all('script', src=True)
            security_analysis['external_scripts'] = len(external_scripts)
            
            # Count inline styles
            inline_styles = soup.find_all('style')
            security_analysis['inline_styles'] = len(inline_styles)
            
            # Count external styles
            external_styles = soup.find_all('link', {'rel': 'stylesheet'})
            security_analysis['external_styles'] = len(external_styles)
            
            # Check for mixed content (HTTP resources on HTTPS page)
            security_analysis['mixed_content'] = self._detect_mixed_content(content)
            
            # Calculate security score
            security_analysis['security_score'] = self._calculate_content_security_score(security_analysis)
        
        except Exception as e:
            self.logger.warning(f"Content security analysis error: {e}")
        
        return security_analysis
    
    def _analyze_accessibility(self, content: str) -> Dict:
        """Basic accessibility analysis"""
        accessibility = {
            'images_without_alt': 0,
            'missing_lang_attribute': False,
            'heading_structure': {},
            'form_labels': 0,
            'accessibility_score': 0
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check images without alt text
            images = soup.find_all('img')
            accessibility['images_without_alt'] = len([img for img in images if not img.get('alt')])
            
            # Check for lang attribute
            html_tag = soup.find('html')
            accessibility['missing_lang_attribute'] = not (html_tag and html_tag.get('lang'))
            
            # Analyze heading structure
            for level in range(1, 7):
                headings = soup.find_all(f'h{level}')
                accessibility['heading_structure'][f'h{level}'] = len(headings)
            
            # Check form labels
            labels = soup.find_all('label')
            accessibility['form_labels'] = len(labels)
            
            # Calculate accessibility score
            accessibility['accessibility_score'] = self._calculate_accessibility_score(accessibility)
        
        except Exception as e:
            self.logger.warning(f"Accessibility analysis error: {e}")
        
        return accessibility
    
    def _analyze_seo(self, content: str) -> Dict:
        """Basic SEO analysis"""
        seo_analysis = {
            'title_length': 0,
            'meta_description': False,
            'h1_count': 0,
            'meta_keywords': False,
            'canonical_url': None,
            'seo_score': 0
        }
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Title analysis
            title = soup.find('title')
            if title:
                seo_analysis['title_length'] = len(title.get_text().strip())
            
            # Meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            seo_analysis['meta_description'] = bool(meta_desc and meta_desc.get('content'))
            
            # H1 tags
            h1_tags = soup.find_all('h1')
            seo_analysis['h1_count'] = len(h1_tags)
            
            # Meta keywords
            meta_keywords = soup.find('meta', {'name': 'keywords'})
            seo_analysis['meta_keywords'] = bool(meta_keywords and meta_keywords.get('content'))
            
            # Canonical URL
            canonical = soup.find('link', {'rel': 'canonical'})
            if canonical:
                seo_analysis['canonical_url'] = canonical.get('href')
            
            # Calculate SEO score
            seo_analysis['seo_score'] = self._calculate_seo_score(seo_analysis)
        
        except Exception as e:
            self.logger.warning(f"SEO analysis error: {e}")
        
        return seo_analysis
    
    # Helper methods for assessment and calculation
    def _assess_vulnerability_severity(self, vuln_type: str) -> str:
        """Assess vulnerability severity"""
        severity_map = {
            'xss_reflected': 'high',
            'sql_injection': 'critical',
            'path_traversal': 'high',
            'command_injection': 'critical'
        }
        return severity_map.get(vuln_type, 'medium')
    
    def _assess_confidence(self, vuln_type: str, match: str) -> float:
        """Assess confidence level of vulnerability detection"""
        # Simple confidence assessment based on pattern specificity
        base_confidence = 0.7
        
        if 'alert(' in match.lower():
            base_confidence += 0.2
        if 'union select' in match.lower():
            base_confidence += 0.3
        
        return min(1.0, base_confidence)
    
    def _get_vulnerability_recommendation(self, vuln_type: str) -> str:
        """Get recommendation for vulnerability type"""
        recommendations = {
            'xss_reflected': 'Implement input validation and output encoding',
            'sql_injection': 'Use parameterized queries and input validation',
            'path_traversal': 'Validate and sanitize file paths',
            'command_injection': 'Avoid system calls with user input'
        }
        return recommendations.get(vuln_type, 'Review and sanitize user input')
    
    def _assess_secret_severity(self, secret_type: str) -> str:
        """Assess severity of exposed secret"""
        severity_map = {
            'api_keys': 'high',
            'passwords': 'critical',
            'database_strings': 'critical',
            'aws_keys': 'critical'
        }
        return severity_map.get(secret_type, 'medium')
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        from collections import Counter
        import math
        
        counts = Counter(text)
        length = len(text)
        
        entropy = 0
        for count in counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _detect_tech_from_headers(self, headers: Dict) -> Dict:
        """Detect technologies from HTTP headers"""
        tech_from_headers = {
            'servers': [],
            'languages': [],
            'frameworks': []
        }
        
        server_header = headers.get('server', '').lower()
        if 'apache' in server_header:
            tech_from_headers['servers'].append({'name': 'apache', 'confidence': 'high', 'detection_method': 'header'})
        elif 'nginx' in server_header:
            tech_from_headers['servers'].append({'name': 'nginx', 'confidence': 'high', 'detection_method': 'header'})
        
        powered_by = headers.get('x-powered-by', '').lower()
        if 'php' in powered_by:
            tech_from_headers['languages'].append({'name': 'php', 'confidence': 'high', 'detection_method': 'header'})
        elif 'asp.net' in powered_by:
            tech_from_headers['languages'].append({'name': 'asp.net', 'confidence': 'high', 'detection_method': 'header'})
        
        return tech_from_headers
    
    def _detect_libraries(self, content: str) -> List[Dict]:
        """Detect JavaScript libraries from script sources"""
        libraries = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            scripts = soup.find_all('script', src=True)
            
            library_patterns = {
                'jquery': r'jquery[.-](\d+\.?\d*\.?\d*)',
                'bootstrap': r'bootstrap[.-](\d+\.?\d*\.?\d*)',
                'react': r'react[.-](\d+\.?\d*\.?\d*)',
                'vue': r'vue[.-](\d+\.?\d*\.?\d*)',
                'angular': r'angular[.-](\d+\.?\d*\.?\d*)'
            }
            
            for script in scripts:
                src = script.get('src', '').lower()
                for lib_name, pattern in library_patterns.items():
                    match = re.search(pattern, src)
                    if match:
                        version = match.group(1) if match.groups() else 'unknown'
                        libraries.append({
                            'name': lib_name,
                            'version': version,
                            'confidence': 'high',
                            'detection_method': 'script_src'
                        })
        
        except Exception as e:
            self.logger.warning(f"Library detection error: {e}")
        
        return libraries
    
    def _is_suspicious_link(self, href: str, text: str) -> bool:
        """Check if link appears suspicious"""
        suspicious_patterns = [
            r'javascript:',
            r'data:',
            r'\.php\?.*eval',
            r'admin.*delete',
            r'logout'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, href, re.IGNORECASE) or re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _get_suspicion_reason(self, href: str) -> str:
        """Get reason for link suspicion"""
        if 'javascript:' in href.lower():
            return 'JavaScript protocol'
        elif 'data:' in href.lower():
            return 'Data URI'
        elif 'admin' in href.lower() and 'delete' in href.lower():
            return 'Admin deletion link'
        else:
            return 'Suspicious pattern detected'
    
    def _assess_comment_sensitivity(self, comment_text: str) -> float:
        """Assess sensitivity of comment content"""
        sensitive_keywords = [
            'password', 'key', 'secret', 'token', 'api', 'database',
            'admin', 'debug', 'test', 'todo', 'fixme', 'hack'
        ]
        
        score = 0
        for keyword in sensitive_keywords:
            if keyword.lower() in comment_text.lower():
                score += 1
        
        return min(1.0, score / len(sensitive_keywords))
    
    def _check_comment_secrets(self, comment_text: str) -> bool:
        """Check if comment contains potential secrets"""
        for secret_type, patterns in self.secret_patterns.items():
            for pattern in patterns:
                if re.search(pattern, comment_text, re.IGNORECASE):
                    return True
        return False
    
    def _assess_header_strength(self, header: str, value: str) -> str:
        """Assess strength of security header"""
        if header == 'x-frame-options':
            return 'strong' if value.upper() in ['DENY', 'SAMEORIGIN'] else 'weak'
        elif header == 'strict-transport-security':
            return 'strong' if 'max-age' in value and int(re.search(r'max-age=(\d+)', value).group(1)) > 86400 else 'weak'
        else:
            return 'medium'
    
    def _assess_missing_header_risk(self, header: str) -> str:
        """Assess risk of missing security header"""
        high_risk_headers = ['strict-transport-security', 'content-security-policy']
        return 'high' if header in high_risk_headers else 'medium'
    
    def _detect_mixed_content(self, content: str) -> List[str]:
        """Detect mixed content issues"""
        mixed_content = []
        
        # Find HTTP resources in content
        http_resources = re.findall(r'src=["\']http://[^"\']+["\']', content, re.IGNORECASE)
        mixed_content.extend(http_resources)
        
        return mixed_content
    
    def _calculate_content_security_score(self, security_analysis: Dict) -> int:
        """Calculate content security score (0-100)"""
        score = 100
        
        # Deduct points for security issues
        score -= security_analysis['inline_scripts'] * 5  # 5 points per inline script
        score -= len(security_analysis['mixed_content']) * 10  # 10 points per mixed content
        
        return max(0, score)
    
    def _calculate_accessibility_score(self, accessibility: Dict) -> int:
        """Calculate accessibility score (0-100)"""
        score = 100
        
        # Deduct points for accessibility issues
        score -= accessibility['images_without_alt'] * 5
        if accessibility['missing_lang_attribute']:
            score -= 20
        if accessibility['heading_structure'].get('h1', 0) != 1:
            score -= 15
        
        return max(0, score)
    
    def _calculate_seo_score(self, seo_analysis: Dict) -> int:
        """Calculate SEO score (0-100)"""
        score = 0
        
        # Add points for SEO elements
        if 30 <= seo_analysis['title_length'] <= 60:
            score += 25
        if seo_analysis['meta_description']:
            score += 25
        if seo_analysis['h1_count'] == 1:
            score += 20
        if seo_analysis['canonical_url']:
            score += 15
        
        return min(100, score)
    
    def _detect_context_vulnerabilities(self, content: str, url: str) -> List[Dict]:
        """Detect context-specific vulnerabilities"""
        context_vulns = []
        
        # Check for admin pages without authentication
        if re.search(r'admin|dashboard|control', url, re.IGNORECASE):
            if not re.search(r'login|auth|session', content, re.IGNORECASE):
                context_vulns.append({
                    'type': 'admin_no_auth',
                    'severity': 'high',
                    'description': 'Admin interface without visible authentication',
                    'recommendation': 'Implement proper authentication for admin areas'
                })
        
        return context_vulns
    
    def _calculate_risk_score(self, analysis_result: Dict) -> Dict:
        """Calculate overall risk score for the page"""
        risk_score = {
            'overall_score': 0,
            'vulnerability_score': 0,
            'secret_score': 0,
            'security_score': 0,
            'risk_level': 'low'
        }
        
        # Calculate vulnerability score
        vulns = analysis_result.get('vulnerabilities', [])
        critical_vulns = len([v for v in vulns if v.get('severity') == 'critical'])
        high_vulns = len([v for v in vulns if v.get('severity') == 'high'])
        
        risk_score['vulnerability_score'] = critical_vulns * 40 + high_vulns * 20
        
        # Calculate secret score
        secrets = analysis_result.get('secrets', [])
        critical_secrets = len([s for s in secrets if s.get('severity') == 'critical'])
        
        risk_score['secret_score'] = critical_secrets * 30
        
        # Calculate security score (inverse of content security score)
        content_security = analysis_result.get('content_security', {})
        risk_score['security_score'] = 100 - content_security.get('security_score', 100)
        
        # Calculate overall score
        risk_score['overall_score'] = min(100, (
            risk_score['vulnerability_score'] + 
            risk_score['secret_score'] + 
            risk_score['security_score']
        ) / 3)
        
        # Determine risk level
        if risk_score['overall_score'] >= 70:
            risk_score['risk_level'] = 'critical'
        elif risk_score['overall_score'] >= 50:
            risk_score['risk_level'] = 'high'
        elif risk_score['overall_score'] >= 30:
            risk_score['risk_level'] = 'medium'
        else:
            risk_score['risk_level'] = 'low'
        
        return risk_score
