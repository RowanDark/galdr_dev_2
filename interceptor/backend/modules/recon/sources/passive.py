# galdr/interceptor/backend/modules/recon/sources/passive.py
import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse, urljoin
import logging
from bs4 import BeautifulSoup
import ssl
import socket

from ..models.target import ReconTarget


class PassiveReconSources:
    """Handler for passive reconnaissance sources (no API keys required)"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests,
            ssl=ssl.create_default_context()
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
        """Gather data from all passive sources"""
        async with self:
            tasks = {
                'wayback_machine': self.query_wayback_machine(target),
                'crt_sh': self.query_crt_sh(target),
                'dnsdumpster': self.query_dnsdumpster(target),
                'threatcrowd': self.query_threatcrowd(target),
                'hackertarget': self.query_hackertarget(target),
                'otx_alienvault': self.query_otx_alienvault(target),
                'urlscan_io': self.query_urlscan_io(target),
                'web_archive': self.query_web_archive(target)
            }
            
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
    
    async def query_wayback_machine(self, target: ReconTarget) -> Dict:
        """Query Wayback Machine for historical URLs"""
        self.logger.info(f"Querying Wayback Machine for {target.primary_target}")
        
        urls = set()
        subdomains = set()
        
        try:
            # Query Wayback Machine API
            wayback_url = f"http://web.archive.org/cdx/search/cdx"
            params = {
                'url': f"*.{target.primary_target}/*",
                'output': 'json',
                'fl': 'original',
                'collapse': 'urlkey',
                'limit': self.config.wayback_limit
            }
            
            async with self.session.get(wayback_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for entry in data[1:]:  # Skip header row
                        url = entry[0]
                        urls.add(url)
                        
                        # Extract subdomain
                        parsed = urlparse(url)
                        if parsed.hostname:
                            subdomains.add(parsed.hostname)
            
            return {
                'urls': list(urls),
                'subdomains': list(subdomains),
                'count': len(urls),
                'source': 'wayback_machine'
            }
            
        except Exception as e:
            self.logger.error(f"Wayback Machine query failed: {e}")
            return {'urls': [], 'subdomains': [], 'count': 0, 'error': str(e)}
    
    async def query_crt_sh(self, target: ReconTarget) -> Dict:
        """Query crt.sh for SSL certificate data"""
        self.logger.info(f"Querying crt.sh for {target.primary_target}")
        
        subdomains = set()
        certificates = []
        
        try:
            # Query crt.sh API
            crt_url = f"https://crt.sh/"
            params = {
                'q': f"%.{target.primary_target}",
                'output': 'json'
            }
            
            async with self.session.get(crt_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for cert in data:
                        # Extract certificate info
                        cert_info = {
                            'id': cert.get('id'),
                            'common_name': cert.get('common_name'),
                            'name_value': cert.get('name_value'),
                            'issuer_ca_id': cert.get('issuer_ca_id'),
                            'issuer_name': cert.get('issuer_name'),
                            'not_before': cert.get('not_before'),
                            'not_after': cert.get('not_after')
                        }
                        certificates.append(cert_info)
                        
                        # Extract subdomains from certificate
                        if cert.get('name_value'):
                            names = cert['name_value'].split('\n')
                            for name in names:
                                name = name.strip()
                                if name and not name.startswith('*'):
                                    subdomains.add(name)
            
            return {
                'subdomains': list(subdomains),
                'certificates': certificates,
                'count': len(subdomains),
                'source': 'crt_sh'
            }
            
        except Exception as e:
            self.logger.error(f"crt.sh query failed: {e}")
            return {'subdomains': [], 'certificates': [], 'count': 0, 'error': str(e)}
    
    async def query_dnsdumpster(self, target: ReconTarget) -> Dict:
        """Query DNSDumpster for DNS information"""
        self.logger.info(f"Querying DNSDumpster for {target.primary_target}")
        
        subdomains = set()
        dns_records = []
        
        try:
            # Get CSRF token first
            dnsdumpster_url = "https://dnsdumpster.com/"
            
            async with self.session.get(dnsdumpster_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
            
            # Submit search form
            data = {
                'csrfmiddlewaretoken': csrf_token,
                'targetip': target.primary_target,
                'user': 'free'
            }
            
            headers = {
                'Referer': dnsdumpster_url
            }
            
            async with self.session.post(dnsdumpster_url, data=data, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Parse DNS records table
                    tables = soup.find_all('table', class_='table')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows[1:]:  # Skip header
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                subdomain = cells[0].get_text().strip()
                                record_type = cells[1].get_text().strip()
                                
                                if subdomain and subdomain.endswith(target.primary_target):
                                    subdomains.add(subdomain)
                                    dns_records.append({
                                        'subdomain': subdomain,
                                        'type': record_type,
                                        'value': cells[2].get_text().strip() if len(cells) > 2 else ''
                                    })
            
            return {
                'subdomains': list(subdomains),
                'dns_records': dns_records,
                'count': len(subdomains),
                'source': 'dnsdumpster'
            }
            
        except Exception as e:
            self.logger.error(f"DNSDumpster query failed: {e}")
            return {'subdomains': [], 'dns_records': [], 'count': 0, 'error': str(e)}
    
    async def query_threatcrowd(self, target: ReconTarget) -> Dict:
        """Query ThreatCrowd API for threat intelligence data"""
        self.logger.info(f"Querying ThreatCrowd for {target.primary_target}")
        
        subdomains = set()
        ips = set()
        
        try:
            # Query ThreatCrowd API
            threatcrowd_url = "https://www.threatcrowd.org/searchApi/v2/domain/report/"
            params = {'domain': target.primary_target}
            
            async with self.session.get(threatcrowd_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract subdomains
                    if 'subdomains' in data:
                        for subdomain in data['subdomains']:
                            subdomains.add(subdomain)
                    
                    # Extract IPs
                    if 'resolutions' in data:
                        for resolution in data['resolutions']:
                            if 'ip_address' in resolution:
                                ips.add(resolution['ip_address'])
            
            return {
                'subdomains': list(subdomains),
                'ips': list(ips),
                'count': len(subdomains),
                'source': 'threatcrowd'
            }
            
        except Exception as e:
            self.logger.error(f"ThreatCrowd query failed: {e}")
            return {'subdomains': [], 'ips': [], 'count': 0, 'error': str(e)}
    
    async def query_hackertarget(self, target: ReconTarget) -> Dict:
        """Query HackerTarget for reconnaissance data"""
        self.logger.info(f"Querying HackerTarget for {target.primary_target}")
        
        subdomains = set()
        
        try:
            # Query HackerTarget API
            hackertarget_url = f"https://api.hackertarget.com/hostsearch/"
            params = {'q': target.primary_target}
            
            async with self.session.get(hackertarget_url, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Parse results
                    lines = text.strip().split('\n')
                    for line in lines:
                        if ',' in line:
                            subdomain = line.split(',')[0].strip()
                            if subdomain and subdomain.endswith(target.primary_target):
                                subdomains.add(subdomain)
            
            return {
                'subdomains': list(subdomains),
                'count': len(subdomains),
                'source': 'hackertarget'
            }
            
        except Exception as e:
            self.logger.error(f"HackerTarget query failed: {e}")
            return {'subdomains': [], 'count': 0, 'error': str(e)}
    
    async def query_otx_alienvault(self, target: ReconTarget) -> Dict:
        """Query AlienVault OTX for threat intelligence"""
        self.logger.info(f"Querying OTX AlienVault for {target.primary_target}")
        
        subdomains = set()
        urls = set()
        
        try:
            # Query OTX API (public, no auth required for basic data)
            otx_url = f"https://otx.alienvault.com/api/v1/indicators/domain/{target.primary_target}/passive_dns"
            
            async with self.session.get(otx_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract passive DNS data
                    if 'passive_dns' in data:
                        for record in data['passive_dns']:
                            if 'hostname' in record:
                                hostname = record['hostname']
                                if hostname.endswith(target.primary_target):
                                    subdomains.add(hostname)
            
            return {
                'subdomains': list(subdomains),
                'urls': list(urls),
                'count': len(subdomains),
                'source': 'otx_alienvault'
            }
            
        except Exception as e:
            self.logger.error(f"OTX AlienVault query failed: {e}")
            return {'subdomains': [], 'urls': [], 'count': 0, 'error': str(e)}
    
    async def query_urlscan_io(self, target: ReconTarget) -> Dict:
        """Query URLScan.io for URL analysis data"""
        self.logger.info(f"Querying URLScan.io for {target.primary_target}")
        
        urls = set()
        subdomains = set()
        
        try:
            # Query URLScan.io API
            urlscan_url = "https://urlscan.io/api/v1/search/"
            params = {
                'q': f"domain:{target.primary_target}",
                'size': 100
            }
            
            async with self.session.get(urlscan_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract URLs and subdomains
                    if 'results' in data:
                        for result in data['results']:
                            if 'page' in result and 'url' in result['page']:
                                url = result['page']['url']
                                urls.add(url)
                                
                                # Extract subdomain
                                parsed = urlparse(url)
                                if parsed.hostname and parsed.hostname.endswith(target.primary_target):
                                    subdomains.add(parsed.hostname)
            
            return {
                'urls': list(urls),
                'subdomains': list(subdomains),
                'count': len(urls),
                'source': 'urlscan_io'
            }
            
        except Exception as e:
            self.logger.error(f"URLScan.io query failed: {e}")
            return {'urls': [], 'subdomains': [], 'count': 0, 'error': str(e)}
    
    async def query_web_archive(self, target: ReconTarget) -> Dict:
        """Query additional web archives for historical data"""
        self.logger.info(f"Querying Web Archives for {target.primary_target}")
        
        urls = set()
        subdomains = set()
        
        try:
            # Query Common Crawl Index
            commoncrawl_url = "https://index.commoncrawl.org/CC-MAIN-2023-50-index"
            params = {
                'url': f"*.{target.primary_target}/*",
                'output': 'json'
            }
            
            async with self.session.get(commoncrawl_url, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Parse JSONL format
                    for line in text.strip().split('\n'):
                        if line:
                            try:
                                data = json.loads(line)
                                if 'url' in data:
                                    url = data['url']
                                    urls.add(url)
                                    
                                    parsed = urlparse(url)
                                    if parsed.hostname:
                                        subdomains.add(parsed.hostname)
                            except json.JSONDecodeError:
                                continue
            
            return {
                'urls': list(urls),
                'subdomains': list(subdomains),
                'count': len(urls),
                'source': 'web_archive'
            }
            
        except Exception as e:
            self.logger.error(f"Web Archive query failed: {e}")
            return {'urls': [], 'subdomains': [], 'count': 0, 'error': str(e)}
