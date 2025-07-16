# galdr/interceptor/backend/modules/recon/sources/api.py
import asyncio
import aiohttp
import base64
from typing import Dict, List, Set, Optional
import logging

from ..models.target import ReconTarget


class APIReconSources:
    """Handler for API-based reconnaissance sources (requires API keys)"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.config.custom_user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def gather_all(self, target: ReconTarget) -> Dict[str, Dict]:
        """Gather data from all API sources with available keys"""
        async with self:
            tasks = {}
            
            # Only include sources with available API keys
            if 'shodan' in self.config.api_keys:
                tasks['shodan'] = self.query_shodan(target)
            
            if 'censys' in self.config.api_keys:
                tasks['censys'] = self.query_censys(target)
            
            if 'securitytrails' in self.config.api_keys:
                tasks['securitytrails'] = self.query_securitytrails(target)
            
            if 'virustotal' in self.config.api_keys:
                tasks['virustotal'] = self.query_virustotal(target)
            
            if 'passivetotal' in self.config.api_keys:
                tasks['passivetotal'] = self.query_passivetotal(target)
            
            if not tasks:
                return {}
            
            results = {}
            completed_tasks = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            for source_name, result in zip(tasks.keys(), completed_tasks):
                if isinstance(result, Exception):
                    self.logger.error(f"Error in {source_name}: {result}")
                    results[source_name] = {'success': False, 'error': str(result)}
                else:
                    results[source_name] = result
                    results[source_name]['success'] = True
            
            return results
    
    async def query_shodan(self, target: ReconTarget) -> Dict:
        """Query Shodan API for network reconnaissance"""
        self.logger.info(f"Querying Shodan for {target.primary_target}")
        
        ips = set()
        ports = set()
        services = []
        
        try:
            api_key = self.config.api_keys['shodan']
            headers = {'Authorization': f'Bearer {api_key}'}
            
            # Search for domain
            shodan_url = "https://api.shodan.io/shodan/host/search"
            params = {
                'query': f'hostname:{target.primary_target}',
                'key': api_key
            }
            
            async with self.session.get(shodan_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'matches' in data:
                        for match in data['matches']:
                            if 'ip_str' in match:
                                ips.add(match['ip_str'])
                            
                            if 'port' in match:
                                ports.add(match['port'])
                            
                            service_info = {
                                'ip': match.get('ip_str'),
                                'port': match.get('port'),
                                'protocol': match.get('transport'),
                                'service': match.get('product'),
                                'version': match.get('version'),
                                'os': match.get('os'),
                                'location': {
                                    'country': match.get('location', {}).get('country_name'),
                                    'city': match.get('location', {}).get('city'),
                                    'org': match.get('org')
                                }
                            }
                            services.append(service_info)
            
            return {
                'ips': list(ips),
                'ports': list(ports),
                'services': services,
                'count': len(services),
                'source': 'shodan'
            }
            
        except Exception as e:
            self.logger.error(f"Shodan query failed: {e}")
            return {'ips': [], 'ports': [], 'services': [], 'count': 0, 'error': str(e)}
    
    async def query_censys(self, target: ReconTarget) -> Dict:
        """Query Censys API for internet-wide scanning data"""
        self.logger.info(f"Querying Censys for {target.primary_target}")
        
        ips = set()
        certificates = []
        services = []
        
        try:
            api_id = self.config.api_keys['censys'].split(':')[0]
            api_secret = self.config.api_keys['censys'].split(':')[1]
            
            # Create basic auth header
            credentials = base64.b64encode(f"{api_id}:{api_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {credentials}'}
            
            # Search certificates
            censys_url = "https://search.censys.io/api/v2/certificates/search"
            params = {
                'q': f'names: {target.primary_target}',
                'per_page': 100
            }
            
            async with self.session.get(censys_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'result' in data and 'hits' in data['result']:
                        for hit in data['result']['hits']:
                            cert_info = {
                                'fingerprint': hit.get('fingerprint_sha256'),
                                'names': hit.get('names', []),
                                'issuer': hit.get('parsed', {}).get('issuer_dn'),
                                'validity': hit.get('parsed', {}).get('validity')
                            }
                            certificates.append(cert_info)
                            
                            # Extract IPs from certificate
                            if 'names' in hit:
                                for name in hit['names']:
                                    if name.endswith(target.primary_target):
                                        # This would need additional IP resolution
                                        pass
            
            return {
                'ips': list(ips),
                'certificates': certificates,
                'services': services,
                'count': len(certificates),
                'source': 'censys'
            }
            
        except Exception as e:
            self.logger.error(f"Censys query failed: {e}")
            return {'ips': [], 'certificates': [], 'services': [], 'count': 0, 'error': str(e)}
    
    async def query_securitytrails(self, target: ReconTarget) -> Dict:
        """Query SecurityTrails API for DNS history"""
        self.logger.info(f"Querying SecurityTrails for {target.primary_target}")
        
        subdomains = set()
        dns_history = []
        
        try:
            api_key = self.config.api_keys['securitytrails']
            headers = {'APIKEY': api_key}
            
            # Get subdomains
            st_url = f"https://api.securitytrails.com/v1/domain/{target.primary_target}/subdomains"
            
            async with self.session.get(st_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'subdomains' in data:
                        for subdomain in data['subdomains']:
                            full_subdomain = f"{subdomain}.{target.primary_target}"
                            subdomains.add(full_subdomain)
            
            # Get DNS history
            history_url = f"https://api.securitytrails.com/v1/history/{target.primary_target}/dns/a"
            
            async with self.session.get(history_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'records' in data:
                        for record in data['records']:
                            dns_history.append({
                                'type': 'A',
                                'values': record.get('values', []),
                                'first_seen': record.get('first_seen'),
                                'last_seen': record.get('last_seen')
                            })
            
            return {
                'subdomains': list(subdomains),
                'dns_history': dns_history,
                'count': len(subdomains),
                'source': 'securitytrails'
            }
            
        except Exception as e:
            self.logger.error(f"SecurityTrails query failed: {e}")
            return {'subdomains': [], 'dns_history': [], 'count': 0, 'error': str(e)}
    
    async def query_virustotal(self, target: ReconTarget) -> Dict:
        """Query VirusTotal API for domain analysis"""
        self.logger.info(f"Querying VirusTotal for {target.primary_target}")
        
        subdomains = set()
        urls = set()
        malware_info = []
        
        try:
            api_key = self.config.api_keys['virustotal']
            headers = {'x-apikey': api_key}
            
            # Get domain report
            vt_url = f"https://www.virustotal.com/api/v3/domains/{target.primary_target}"
            
            async with self.session.get(vt_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract subdomains
                    subdomains_url = f"https://www.virustotal.com/api/v3/domains/{target.primary_target}/subdomains"
                    
                    async with self.session.get(subdomains_url, headers=headers) as response:
                        if response.status == 200:
                            subdomain_data = await response.json()
                            
                            if 'data' in subdomain_data:
                                for item in subdomain_data['data']:
                                    if 'id' in item:
                                        subdomains.add(item['id'])
            
            return {
                'subdomains': list(subdomains),
                'urls': list(urls),
                'malware_info': malware_info,
                'count': len(subdomains),
                'source': 'virustotal'
            }
            
        except Exception as e:
            self.logger.error(f"VirusTotal query failed: {e}")
            return {'subdomains': [], 'urls': [], 'malware_info': [], 'count': 0, 'error': str(e)}
    
    async def query_passivetotal(self, target: ReconTarget) -> Dict:
        """Query RiskIQ PassiveTotal API for passive DNS data"""
        self.logger.info(f"Querying PassiveTotal for {target.primary_target}")
        
        subdomains = set()
        passive_dns = []
        
        try:
            # PassiveTotal requires username:api_key format
            username, api_key = self.config.api_keys['passivetotal'].split(':')
            credentials = base64.b64encode(f"{username}:{api_key}".encode()).decode()
            headers = {'Authorization': f'Basic {credentials}'}
            
            # Get passive DNS data
            pt_url = "https://api.passivetotal.org/v2/dns/passive"
            params = {'query': target.primary_target}
            
            async with self.session.get(pt_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'results' in data:
                        for result in data['results']:
                            if 'resolve' in result:
                                subdomains.add(result['resolve'])
                            
                            passive_dns.append({
                                'resolve': result.get('resolve'),
                                'value': result.get('value'),
                                'collected': result.get('collected'),
                                'source': result.get('source')
                            })
            
            return {
                'subdomains': list(subdomains),
                'passive_dns': passive_dns,
                'count': len(subdomains),
                'source': 'passivetotal'
            }
            
        except Exception as e:
            self.logger.error(f"PassiveTotal query failed: {e}")
            return {'subdomains': [], 'passive_dns': [], 'count': 0, 'error': str(e)}
