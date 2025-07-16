# galdr/interceptor/backend/modules/recon/utils/deduplicator.py
import re
from typing import Dict, List, Set
from urllib.parse import urlparse
import ipaddress


class ResultDeduplicator:
    """Utility for deduplicating and normalizing reconnaissance results"""
    
    def __init__(self):
        self.url_patterns = {
            'remove_params': re.compile(r'\?.*$'),
            'remove_fragment': re.compile(r'#.*$'),
            'normalize_path': re.compile(r'/+')
        }
    
    async def process_results(self, aggregated_data: Dict[str, List]) -> Dict[str, List]:
        """Process and deduplicate all result types"""
        deduplicated = {}
        
        # Process subdomains
        if 'subdomains' in aggregated_data:
            deduplicated['subdomains'] = self._deduplicate_subdomains(
                aggregated_data['subdomains']
            )
        
        # Process URLs
        if 'urls' in aggregated_data:
            deduplicated['urls'] = self._deduplicate_urls(
                aggregated_data['urls']
            )
        
        # Process IPs
        if 'ips' in aggregated_data:
            deduplicated['ips'] = self._deduplicate_ips(
                aggregated_data['ips']
            )
        
        # Process technologies (simple dedup)
        if 'technologies' in aggregated_data:
            deduplicated['technologies'] = list(set(aggregated_data['technologies']))
        
        # Process certificates (complex dedup by fingerprint)
        if 'certificates' in aggregated_data:
            deduplicated['certificates'] = self._deduplicate_certificates(
                aggregated_data['certificates']
            )
        
        # Process DNS records
        if 'dns_records' in aggregated_data:
            deduplicated['dns_records'] = self._deduplicate_dns_records(
                aggregated_data['dns_records']
            )
        
        return deduplicated
    
    def _deduplicate_subdomains(self, subdomains: List[str]) -> List[str]:
        """Deduplicate and normalize subdomains"""
        normalized = set()
        
        for subdomain in subdomains:
            # Normalize subdomain
            subdomain = subdomain.lower().strip()
            
            # Remove protocol if present
            subdomain = re.sub(r'^https?://', '', subdomain)
            
            # Remove trailing slashes and paths
            subdomain = subdomain.split('/')[0]
            
            # Remove port numbers
            subdomain = subdomain.split(':')[0]
            
            # Validate format
            if self._is_valid_subdomain(subdomain):
                normalized.add(subdomain)
        
        return sorted(list(normalized))
    
    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Deduplicate and normalize URLs"""
        normalized = set()
        
        for url in urls:
            try:
                # Parse URL
                parsed = urlparse(url.strip())
                
                # Skip invalid URLs
                if not parsed.scheme or not parsed.netloc:
                    continue
                
                # Normalize scheme
                scheme = parsed.scheme.lower()
                if scheme not in ['http', 'https', 'ftp', 'ftps']:
                    continue
                
                # Normalize netloc
                netloc = parsed.netloc.lower()
                
                # Normalize path
                path = parsed.path
                if not path:
                    path = '/'
                
                # Remove trailing slashes except for root
                if len(path) > 1 and path.endswith('/'):
                    path = path[:-1]
                
                # Reconstruct normalized URL
                normalized_url = f"{scheme}://{netloc}{path}"
                
                # Add query string if present (optional - might want to remove for dedup)
                if parsed.query:
                    normalized_url += f"?{parsed.query}"
                
                normalized.add(normalized_url)
                
            except Exception:
                # Skip malformed URLs
                continue
        
        return sorted(list(normalized))
    
    def _deduplicate_ips(self, ips: List[str]) -> List[str]:
        """Deduplicate and validate IP addresses"""
        valid_ips = set()
        
        for ip in ips:
            try:
                # Validate IP address
                ip_obj = ipaddress.ip_address(ip.strip())
                
                # Skip loopback and link-local addresses for external recon
                if not ip_obj.is_loopback and not ip_obj.is_link_local:
                    valid_ips.add(str(ip_obj))
                    
            except ipaddress.AddressValueError:
                # Skip invalid IP addresses
                continue
        
        return sorted(list(valid_ips), key=ipaddress.ip_address)
    
    def _deduplicate_certificates(self, certificates: List[Dict]) -> List[Dict]:
        """Deduplicate certificates by fingerprint or common name"""
        seen_fingerprints = set()
        seen_names = set()
        deduplicated = []
        
        for cert in certificates:
            # Try to use fingerprint first
            fingerprint = cert.get('fingerprint') or cert.get('id')
            common_name = cert.get('common_name')
            
            if fingerprint and fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                deduplicated.append(cert)
            elif common_name and common_name not in seen_names and not fingerprint:
                seen_names.add(common_name)
                deduplicated.append(cert)
        
        return deduplicated
    
    def _deduplicate_dns_records(self, dns_records: List[Dict]) -> List[Dict]:
        """Deduplicate DNS records"""
        seen_records = set()
        deduplicated = []
        
        for record in dns_records:
            # Create unique identifier for record
            identifier = (
                record.get('subdomain', ''),
                record.get('type', ''),
                record.get('value', '')
            )
            
            if identifier not in seen_records:
                seen_records.add(identifier)
                deduplicated.append(record)
        
        return deduplicated
    
    def _is_valid_subdomain(self, subdomain: str) -> bool:
        """Validate subdomain format"""
        if not subdomain or len(subdomain) > 253:
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9.-]+$', subdomain):
            return False
        
        # Check for valid structure
        parts = subdomain.split('.')
        for part in parts:
            if not part or len(part) > 63:
                return False
            if part.startswith('-') or part.endswith('-'):
                return False
        
        return True
