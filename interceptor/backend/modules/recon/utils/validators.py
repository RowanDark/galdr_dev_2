# galdr/interceptor/backend/modules/recon/utils/validators.py
import re
import ipaddress
from urllib.parse import urlparse


class TargetValidator:
    """Utility for validating and normalizing reconnaissance targets"""
    
    def __init__(self):
        self.domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
    
    def is_ip_address(self, target: str) -> bool:
        """Check if target is a valid IP address"""
        try:
            ipaddress.ip_address(target)
            return True
        except ipaddress.AddressValueError:
            return False
    
    def is_domain(self, target: str) -> bool:
        """Check if target is a valid domain"""
        # Extract domain from URL if needed
        domain = self.extract_domain(target)
        return bool(self.domain_regex.match(domain))
    
    def extract_domain(self, target: str) -> str:
        """Extract domain from various input formats"""
        target = target.strip().lower()
        
        # Remove protocol if present
        if target.startswith(('http://', 'https://')):
            parsed = urlparse(target)
            target = parsed.netloc
        
        # Remove port if present
        target = target.split(':')[0]
        
        # Remove path if present
        target = target.split('/')[0]
        
        # Remove www prefix for normalization
        if target.startswith('www.'):
            target = target[4:]
        
        return target
    
    def normalize_target(self, target: str) -> str:
        """Normalize target to consistent format"""
        if self.is_ip_address(target):
            return str(ipaddress.ip_address(target))
        elif self.is_domain(target):
            return self.extract_domain(target)
        else:
            raise ValueError(f"Invalid target format: {target}")
