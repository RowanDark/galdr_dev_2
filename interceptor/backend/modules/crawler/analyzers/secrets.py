# galdr/interceptor/backend/modules/crawler/analyzers/secrets.py
import re
import base64
import hashlib
from typing import List, Dict, Set
from datetime import datetime

from ..models.crawl_data import CrawlEntry


class SecretsAnalyzer:
    """Analyzes content for hardcoded secrets, keys, and credentials"""
    
    def __init__(self, config):
        self.config = config
        self.secret_patterns = self._initialize_secret_patterns()
        self.false_positives = self._initialize_false_positives()
    
    def _initialize_secret_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting different types of secrets"""
        return {
            # API Keys
            "api_keys": [
                r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
                r"(?i)apikey['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
                r"(?i)key['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
            ],
            
            # AWS Keys
            "aws_keys": [
                r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
                r"(?i)aws[_-]?access[_-]?key[_-]?id['\"]?\s*[:=]\s*['\"]([A-Z0-9]{20})['\"]",
                r"(?i)aws[_-]?secret[_-]?access[_-]?key['\"]?\s*[:=]\s*['\"]([A-Za-z0-9/+=]{40})['\"]",
            ],
            
            # Google API Keys
            "google_keys": [
                r"AIza[0-9A-Za-z_\-]{35}",  # Google API Key
                r"(?i)google[_-]?api[_-]?key['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-]{35,})['\"]",
            ],
            
            # JWT Tokens
            "jwt_tokens": [
                r"eyJ[A-Za-z0-9_\-]*\.eyJ[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]*",  # JWT pattern
                r"(?i)jwt['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{100,})['\"]",
                r"(?i)token['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{100,})['\"]",
            ],
            
            # Database Credentials
            "database_credentials": [
                r"(?i)password['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
                r"(?i)passwd['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
                r"(?i)pwd['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
                r"(?i)db[_-]?password['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
                r"(?i)database[_-]?password['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
            ],
            
            # Private Keys
            "private_keys": [
                r"-----BEGIN (?:RSA )?PRIVATE KEY-----[A-Za-z0-9+/=\s]+-----END (?:RSA )?PRIVATE KEY-----",
                r"-----BEGIN OPENSSH PRIVATE KEY-----[A-Za-z0-9+/=\s]+-----END OPENSSH PRIVATE KEY-----",
                r"-----BEGIN EC PRIVATE KEY-----[A-Za-z0-9+/=\s]+-----END EC PRIVATE KEY-----",
            ],
            
            # OAuth Tokens
            "oauth_tokens": [
                r"(?i)oauth[_-]?token['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{20,})['\"]",
                r"(?i)access[_-]?token['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{20,})['\"]",
                r"(?i)refresh[_-]?token['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{20,})['\"]",
            ],
            
            # GitHub Tokens
            "github_tokens": [
                r"ghp_[A-Za-z0-9]{36}",  # GitHub Personal Access Token
                r"gho_[A-Za-z0-9]{36}",  # GitHub OAuth Token
                r"ghu_[A-Za-z0-9]{36}",  # GitHub User Token
                r"ghs_[A-Za-z0-9]{36}",  # GitHub Server Token
            ],
            
            # Slack Tokens
            "slack_tokens": [
                r"xox[baprs]-[A-Za-z0-9\-]+",  # Slack tokens
                r"https://hooks\.slack\.com/services/[A-Z0-9]+/[A-Z0-9]+/[A-Za-z0-9]+",  # Slack webhooks
            ],
            
            # Discord Tokens
            "discord_tokens": [
                r"[MN][A-Za-z\d]{23}\.[A-Za-z\d]{6}\.[A-Za-z\d]{27}",  # Discord bot token
                r"mfa\.[A-Za-z\d]{84}",  # Discord MFA token
            ],
            
            # Credit Card Numbers
            "credit_cards": [
                r"\b4[0-9]{12}(?:[0-9]{3})?\b",  # Visa
                r"\b5[1-5][0-9]{14}\b",  # MasterCard
                r"\b3[47][0-9]{13}\b",  # American Express
                r"\b6(?:011|5[0-9]{2})[0-9]{12}\b",  # Discover
            ],
            
            # SSH Keys
            "ssh_keys": [
                r"ssh-rsa [A-Za-z0-9+/]+=*",
                r"ssh-ed25519 [A-Za-z0-9+/]+=*",
                r"ecdsa-sha2-nistp256 [A-Za-z0-9+/]+=*",
            ],
            
            # Generic Secrets
            "generic_secrets": [
                r"(?i)secret['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{16,})['\"]",
                r"(?i)private[_-]?key['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{20,})['\"]",
                r"(?i)client[_-]?secret['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{16,})['\"]",
            ],
            
            # Configuration Files
            "config_secrets": [
                r"(?i)encryption[_-]?key['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{16,})['\"]",
                r"(?i)hash[_-]?salt['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{8,})['\"]",
                r"(?i)csrf[_-]?token['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{16,})['\"]",
            ]
        }
    
    def _initialize_false_positives(self) -> Set[str]:
        """Initialize common false positive patterns"""
        return {
            # Common placeholder values
            "password", "secret", "key", "token", "your_key_here",
            "example", "test", "demo", "placeholder", "changeme",
            "123456", "admin", "root", "user", "guest",
            
            # Common development values
            "localhost", "127.0.0.1", "development", "staging",
            "null", "undefined", "none", "empty", "default",
            
            # Base64 encoded common strings
            "dGVzdA==",  # "test"
            "YWRtaW4=",  # "admin"
            "cGFzc3dvcmQ=",  # "password"
            
            # Common fake keys
            "sk_test_", "pk_test_", "test_", "fake_", "mock_",
            
            # Documentation examples
            "your-api-key", "your-secret-key", "insert-key-here"
        }
    
    async def analyze(self, entry: CrawlEntry) -> List[Dict]:
        """Analyze entry for hardcoded secrets"""
        secrets = []
        
        try:
            # Analyze response body
            body_secrets = self._analyze_content(entry.response_body, entry.url, "response_body")
            secrets.extend(body_secrets)
            
            # Analyze request body if available
            if entry.request_body:
                request_secrets = self._analyze_content(entry.request_body, entry.url, "request_body")
                secrets.extend(request_secrets)
            
            # Analyze headers
            header_secrets = self._analyze_headers(entry)
            secrets.extend(header_secrets)
            
            # Analyze URLs and query parameters
            url_secrets = self._analyze_url(entry.url)
            secrets.extend(url_secrets)
            
            # Filter false positives
            secrets = self._filter_false_positives(secrets)
            
            # Calculate entropy scores
            secrets = self._calculate_entropy_scores(secrets)
            
        except Exception as e:
            self.logger.error(f"Error analyzing secrets: {e}")
        
        return secrets
    
    def _analyze_content(self, content: str, url: str, location_type: str) -> List[Dict]:
        """Analyze content for secrets using patterns"""
        secrets = []
        
        for secret_type, patterns in self.secret_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    secret_value = match.group(1) if match.groups() else match.group(0)
                    
                    # Skip if too short or too long
                    if len(secret_value) < 8 or len(secret_value) > 500:
                        continue
                    
                    secret = {
                        'type': secret_type.replace('_', ' ').title(),
                        'value': secret_value,
                        'masked_value': self._mask_secret(secret_value),
                        'confidence': self._calculate_confidence(secret_type, secret_value),
                        'location': {
                            'url': url,
                            'type': location_type,
                            'position': match.start(),
                            'context': content[max(0, match.start()-50):match.end()+50]
                        },
                        'timestamp': datetime.now().isoformat(),
                        'severity': self._determine_severity(secret_type),
                        'pattern_matched': pattern
                    }
                    
                    secrets.append(secret)
        
        return secrets
    
    def _analyze_headers(self, entry: CrawlEntry) -> List[Dict]:
        """Analyze headers for exposed secrets"""
        secrets = []
        
        # Check both request and response headers
        all_headers = {}
        all_headers.update(entry.request_headers or {})
        all_headers.update(entry.response_headers or {})
        
        for header_name, header_value in all_headers.items():
            # Check for authorization headers
            if header_name.lower() in ['authorization', 'x-api-key', 'x-auth-token']:
                # Extract token from Authorization header
                if header_name.lower() == 'authorization':
                    auth_parts = header_value.split(' ')
                    if len(auth_parts) == 2:
                        token = auth_parts[1]
                    else:
                        token = header_value
                else:
                    token = header_value
                
                if len(token) > 10 and not self._is_false_positive(token):
                    secret = {
                        'type': 'Authorization Token',
                        'value': token,
                        'masked_value': self._mask_secret(token),
                        'confidence': 0.9,
                        'location': {
                            'url': entry.url,
                            'type': 'header',
                            'header_name': header_name
                        },
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'High',
                        'pattern_matched': 'header_analysis'
                    }
                    secrets.append(secret)
            
            # Check for cookies with sensitive names
            if header_name.lower() == 'set-cookie':
                cookie_secrets = self._analyze_cookies(header_value, entry.url)
                secrets.extend(cookie_secrets)
        
        return secrets
    
    def _analyze_cookies(self, cookie_header: str, url: str) -> List[Dict]:
        """Analyze cookies for sensitive values"""
        secrets = []
        
        # Parse cookies
        cookies = []
        for cookie_part in cookie_header.split(';'):
            if '=' in cookie_part:
                name, value = cookie_part.split('=', 1)
                cookies.append((name.strip(), value.strip()))
        
        sensitive_cookie_names = [
            'session', 'auth', 'token', 'jwt', 'api_key',
            'secret', 'csrf', 'xsrf', 'remember'
        ]
        
        for name, value in cookies:
            if any(sensitive_name in name.lower() for sensitive_name in sensitive_cookie_names):
                if len(value) > 10 and not self._is_false_positive(value):
                    secret = {
                        'type': 'Sensitive Cookie',
                        'value': value,
                        'masked_value': self._mask_secret(value),
                        'confidence': 0.7,
                        'location': {
                            'url': url,
                            'type': 'cookie',
                            'cookie_name': name
                        },
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'Medium',
                        'pattern_matched': 'cookie_analysis'
                    }
                    secrets.append(secret)
        
        return secrets
    
    def _analyze_url(self, url: str) -> List[Dict]:
        """Analyze URL for exposed secrets in query parameters"""
        secrets = []
        
        from urllib.parse import urlparse, parse_qs
        
        try:
            parsed = urlparse(url)
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=True)
                
                sensitive_param_names = [
                    'api_key', 'apikey', 'key', 'token', 'access_token',
                    'secret', 'password', 'pwd', 'auth', 'session'
                ]
                
                for param_name, param_values in params.items():
                    if any(sensitive_name in param_name.lower() for sensitive_name in sensitive_param_names):
                        for value in param_values:
                            if len(value) > 8 and not self._is_false_positive(value):
                                secret = {
                                    'type': 'URL Parameter Secret',
                                    'value': value,
                                    'masked_value': self._mask_secret(value),
                                    'confidence': 0.8,
                                    'location': {
                                        'url': url,
                                        'type': 'url_parameter',
                                        'parameter_name': param_name
                                    },
                                    'timestamp': datetime.now().isoformat(),
                                    'severity': 'High',
                                    'pattern_matched': 'url_analysis'
                                }
                                secrets.append(secret)
        
        except Exception:
            pass
        
        return secrets
    
    def _mask_secret(self, secret: str) -> str:
        """Mask secret value for display"""
        if len(secret) <= 8:
            return "*" * len(secret)
        
        visible_chars = 4
        return secret[:visible_chars] + "*" * (len(secret) - visible_chars * 2) + secret[-visible_chars:]
    
    def _calculate_confidence(self, secret_type: str, value: str) -> float:
        """Calculate confidence score for detected secret"""
        base_confidence = {
            'api_keys': 0.8,
            'aws_keys': 0.95,
            'google_keys': 0.9,
            'jwt_tokens': 0.85,
            'private_keys': 0.95,
            'github_tokens': 0.9,
            'slack_tokens': 0.9,
            'discord_tokens': 0.9,
            'ssh_keys': 0.95,
            'credit_cards': 0.7,
            'database_credentials': 0.6,
            'oauth_tokens': 0.8,
            'generic_secrets': 0.5,
            'config_secrets': 0.6
        }.get(secret_type, 0.5)
        
        # Adjust based on entropy
        entropy = self._calculate_entropy(value)
        if entropy > 4.0:
            base_confidence += 0.1
        elif entropy < 2.0:
            base_confidence -= 0.2
        
        # Adjust based on length
        if len(value) > 50:
            base_confidence += 0.1
        elif len(value) < 16:
            base_confidence -= 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not data:
            return 0
        
        entropy = 0
        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                entropy += - p_x * self._log2(p_x)
        
        return entropy
    
    def _log2(self, x: float) -> float:
        """Calculate log base 2"""
        import math
        return math.log(x) / math.log(2)
    
    def _filter_false_positives(self, secrets: List[Dict]) -> List[Dict]:
        """Filter out known false positives"""
        filtered_secrets = []
        
        for secret in secrets:
            value = secret['value'].lower()
            
            # Check against false positive patterns
            if not self._is_false_positive(value):
                filtered_secrets.append(secret)
        
        return filtered_secrets
    
    def _is_false_positive(self, value: str) -> bool:
        """Check if value is a known false positive"""
        value_lower = value.lower()
        
        # Check exact matches
        if value_lower in self.false_positives:
            return True
        
        # Check for common patterns
        if any(fp in value_lower for fp in ['example', 'test', 'demo', 'fake', 'mock']):
            return True
        
        # Check for repeated characters (likely placeholder)
        if len(set(value)) < 3:
            return True
        
        # Check for common development patterns
        if value_lower.startswith(('test_', 'dev_', 'local_', 'demo_')):
            return True
        
        return False
    
    def _calculate_entropy_scores(self, secrets: List[Dict]) -> List[Dict]:
        """Add entropy scores to secrets"""
        for secret in secrets:
            entropy = self._calculate_entropy(secret['value'])
            secret['entropy'] = entropy
            
            # Adjust confidence based on entropy
            if entropy < 2.0:
                secret['confidence'] *= 0.7
            elif entropy > 4.5:
                secret['confidence'] = min(1.0, secret['confidence'] * 1.1)
        
        return secrets
    
    def _determine_severity(self, secret_type: str) -> str:
        """Determine severity level for secret type"""
        severity_map = {
            'api_keys': 'High',
            'aws_keys': 'Critical',
            'google_keys': 'High',
            'jwt_tokens': 'High',
            'private_keys': 'Critical',
            'github_tokens': 'High',
            'slack_tokens': 'Medium',
            'discord_tokens': 'Medium',
            'ssh_keys': 'Critical',
            'credit_cards': 'Critical',
            'database_credentials': 'Critical',
            'oauth_tokens': 'High',
            'generic_secrets': 'Medium',
            'config_secrets': 'Medium'
        }
        return severity_map.get(secret_type, 'Medium')
