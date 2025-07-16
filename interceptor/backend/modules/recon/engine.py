# galdr/interceptor/backend/modules/recon/engine.py
import asyncio
import logging
from typing import Dict, List, Set, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import re
import ipaddress
from urllib.parse import urlparse

from .sources.passive import PassiveReconSources
from .sources.api import APIReconSources
from .models.target import ReconTarget, ReconResult
from .utils.deduplicator import ResultDeduplicator
from .utils.validators import TargetValidator


@dataclass
class ReconConfig:
    """Configuration for reconnaissance operations"""
    timeout_seconds: int = 30
    max_concurrent_requests: int = 10
    enable_passive_sources: bool = True
    enable_api_sources: bool = False
    api_keys: Dict[str, str] = field(default_factory=dict)
    custom_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    delay_between_requests: float = 1.0
    max_results_per_source: int = 1000
    
    # Source-specific configurations
    wayback_limit: int = 1000
    crt_sh_timeout: int = 15
    dnsdumpster_solve_captcha: bool = False
    include_subdomains: bool = True
    include_historical: bool = True


class MimirsReconEngine:
    """Main reconnaissance engine for OSINT data gathering"""
    
    def __init__(self, config: Optional[ReconConfig] = None):
        self.config = config or ReconConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize source handlers
        self.passive_sources = PassiveReconSources(self.config)
        self.api_sources = APIReconSources(self.config)
        
        # Utilities
        self.validator = TargetValidator()
        self.deduplicator = ResultDeduplicator()
        
        # Results storage
        self.current_results: Dict[str, ReconResult] = {}
        self.scan_history: List[ReconResult] = []
        
        # Status tracking
        self.is_running = False
        self.current_target: Optional[ReconTarget] = None
        self.progress_callbacks: List[callable] = []
        self.completion_callbacks: List[callable] = []
    
    async def start_reconnaissance(self, target: str, scan_id: Optional[str] = None) -> ReconResult:
        """Start comprehensive reconnaissance on target"""
        try:
            # Validate and normalize target
            recon_target = await self._prepare_target(target)
            if not recon_target:
                raise ValueError(f"Invalid target: {target}")
            
            # Initialize scan
            scan_id = scan_id or f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = ReconResult(
                scan_id=scan_id,
                target=recon_target,
                start_time=datetime.now()
            )
            
            self.current_target = recon_target
            self.current_results[scan_id] = result
            self.is_running = True
            
            self.logger.info(f"Starting reconnaissance for {target} (ID: {scan_id})")
            
            # Execute reconnaissance phases
            await self._execute_recon_phases(result)
            
            # Finalize results
            await self._finalize_results(result)
            
            self.logger.info(f"Reconnaissance completed for {target}")
            return result
            
        except Exception as e:
            self.logger.error(f"Reconnaissance failed for {target}: {e}")
            if scan_id and scan_id in self.current_results:
                self.current_results[scan_id].error = str(e)
            raise
        finally:
            self.is_running = False
            self.current_target = None
    
    async def _prepare_target(self, target: str) -> Optional[ReconTarget]:
        """Validate and prepare target for reconnaissance"""
        target = target.strip().lower()
        
        # Determine target type
        if self.validator.is_ip_address(target):
            return ReconTarget(
                original_input=target,
                target_type="ip",
                primary_target=target
            )
        elif self.validator.is_domain(target):
            # Clean domain (remove protocol, path, etc.)
            domain = self.validator.extract_domain(target)
            return ReconTarget(
                original_input=target,
                target_type="domain",
                primary_target=domain
            )
        else:
            self.logger.error(f"Invalid target format: {target}")
            return None
    
    async def _execute_recon_phases(self, result: ReconResult):
        """Execute all reconnaissance phases"""
        phases = []
        
        # Phase 1: Passive Sources (Free)
        if self.config.enable_passive_sources:
            phases.append(self._run_passive_recon(result))
        
        # Phase 2: API Sources (Premium)
        if self.config.enable_api_sources and self.config.api_keys:
            phases.append(self._run_api_recon(result))
        
        # Execute phases concurrently
        if phases:
            await asyncio.gather(*phases, return_exceptions=True)
    
    async def _run_passive_recon(self, result: ReconResult):
        """Execute passive reconnaissance using free sources"""
        self.logger.info("Starting passive reconnaissance phase")
        
        try:
            # Get all passive source results
            passive_results = await self.passive_sources.gather_all(result.target)
            
            # Merge results
            for source_name, source_results in passive_results.items():
                result.sources[source_name] = source_results
                result.raw_data[source_name] = source_results.get('raw_data', {})
                
                # Update progress
                await self._notify_progress(f"Completed {source_name}", 
                                          len(result.sources) / 8 * 100)  # Assuming 8 total sources
            
        except Exception as e:
            self.logger.error(f"Passive reconnaissance failed: {e}")
            result.errors.append(f"Passive recon error: {e}")
    
    async def _run_api_recon(self, result: ReconResult):
        """Execute API reconnaissance using premium sources"""
        self.logger.info("Starting API reconnaissance phase")
        
        try:
            # Get all API source results
            api_results = await self.api_sources.gather_all(result.target)
            
            # Merge results
            for source_name, source_results in api_results.items():
                result.sources[source_name] = source_results
                result.raw_data[source_name] = source_results.get('raw_data', {})
                
                # Update progress
                await self._notify_progress(f"Completed {source_name}", 
                                          50 + (len(result.sources) / 12 * 50))  # API sources add to 100%
            
        except Exception as e:
            self.logger.error(f"API reconnaissance failed: {e}")
            result.errors.append(f"API recon error: {e}")
    
    async def _finalize_results(self, result: ReconResult):
        """Process, deduplicate and finalize results"""
        self.logger.info("Finalizing reconnaissance results")
        
        # Aggregate all discovered data
        await self._aggregate_results(result)
        
        # Deduplicate findings
        await self._deduplicate_results(result)
        
        # Enrich with additional data
        await self._enrich_results(result)
        
        # Set completion time
        result.end_time = datetime.now()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()
        
        # Store in history
        self.scan_history.append(result)
        
        # Notify completion
        await self._notify_completion(result)
    
    async def _aggregate_results(self, result: ReconResult):
        """Aggregate all discovered data from sources"""
        all_subdomains = set()
        all_urls = set()
        all_ips = set()
        all_technologies = set()
        all_certificates = []
        all_dns_records = []
        
        for source_name, source_data in result.sources.items():
            if 'subdomains' in source_data:
                all_subdomains.update(source_data['subdomains'])
            if 'urls' in source_data:
                all_urls.update(source_data['urls'])
            if 'ips' in source_data:
                all_ips.update(source_data['ips'])
            if 'technologies' in source_data:
                all_technologies.update(source_data['technologies'])
            if 'certificates' in source_data:
                all_certificates.extend(source_data['certificates'])
            if 'dns_records' in source_data:
                all_dns_records.extend(source_data['dns_records'])
        
        # Store aggregated results
        result.aggregated_data = {
            'subdomains': list(all_subdomains),
            'urls': list(all_urls),
            'ips': list(all_ips),
            'technologies': list(all_technologies),
            'certificates': all_certificates,
            'dns_records': all_dns_records,
            'total_subdomains': len(all_subdomains),
            'total_urls': len(all_urls),
            'total_ips': len(all_ips)
        }
    
    async def _deduplicate_results(self, result: ReconResult):
        """Remove duplicates and normalize data"""
        deduplicated = await self.deduplicator.process_results(result.aggregated_data)
        result.deduplicated_data = deduplicated
        
        # Update statistics
        result.statistics = {
            'sources_queried': len(result.sources),
            'successful_sources': len([s for s in result.sources.values() if s.get('success', False)]),
            'total_subdomains_found': len(deduplicated.get('subdomains', [])),
            'total_urls_found': len(deduplicated.get('urls', [])),
            'total_ips_found': len(deduplicated.get('ips', [])),
            'unique_technologies': len(deduplicated.get('technologies', [])),
            'certificates_found': len(deduplicated.get('certificates', [])),
            'dns_records_found': len(deduplicated.get('dns_records', []))
        }
    
    async def _enrich_results(self, result: ReconResult):
        """Enrich results with additional analysis"""
        # Analyze subdomain patterns
        subdomains = result.deduplicated_data.get('subdomains', [])
        result.analysis = {
            'subdomain_patterns': self._analyze_subdomain_patterns(subdomains),
            'interesting_subdomains': self._find_interesting_subdomains(subdomains),
            'ip_ranges': self._analyze_ip_ranges(result.deduplicated_data.get('ips', [])),
            'technology_stack': self._analyze_technologies(result.deduplicated_data.get('technologies', []))
        }
    
    def _analyze_subdomain_patterns(self, subdomains: List[str]) -> Dict[str, int]:
        """Analyze common subdomain patterns"""
        patterns = {}
        for subdomain in subdomains:
            parts = subdomain.split('.')
            if len(parts) > 2:
                pattern = parts[0]
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Return top 10 patterns
        return dict(sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _find_interesting_subdomains(self, subdomains: List[str]) -> List[str]:
        """Find potentially interesting subdomains"""
        interesting_keywords = [
            'admin', 'api', 'dev', 'test', 'staging', 'beta', 'internal',
            'jenkins', 'gitlab', 'jira', 'confluence', 'vpn', 'mail',
            'ftp', 'ssh', 'rdp', 'citrix', 'owa', 'webmail'
        ]
        
        interesting = []
        for subdomain in subdomains:
            for keyword in interesting_keywords:
                if keyword in subdomain.lower():
                    interesting.append(subdomain)
                    break
        
        return interesting
    
    def _analyze_ip_ranges(self, ips: List[str]) -> Dict[str, List[str]]:
        """Analyze IP addresses and group by ranges"""
        ranges = {}
        for ip in ips:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private:
                    network = str(ipaddress.ip_network(f"{ip}/24", strict=False))
                    if network not in ranges:
                        ranges[network] = []
                    ranges[network].append(ip)
            except:
                continue
        
        return ranges
    
    def _analyze_technologies(self, technologies: List[str]) -> Dict[str, List[str]]:
        """Categorize discovered technologies"""
        categories = {
            'web_servers': [],
            'cms': [],
            'databases': [],
            'frameworks': [],
            'cdn': [],
            'security': [],
            'analytics': [],
            'other': []
        }
        
        # Technology categorization logic
        for tech in technologies:
            tech_lower = tech.lower()
            if any(x in tech_lower for x in ['apache', 'nginx', 'iis', 'lighttpd']):
                categories['web_servers'].append(tech)
            elif any(x in tech_lower for x in ['wordpress', 'drupal', 'joomla', 'magento']):
                categories['cms'].append(tech)
            elif any(x in tech_lower for x in ['mysql', 'postgresql', 'mongodb', 'redis']):
                categories['databases'].append(tech)
            elif any(x in tech_lower for x in ['react', 'angular', 'vue', 'django', 'rails']):
                categories['frameworks'].append(tech)
            elif any(x in tech_lower for x in ['cloudflare', 'akamai', 'fastly', 'amazon']):
                categories['cdn'].append(tech)
            else:
                categories['other'].append(tech)
        
        return {k: v for k, v in categories.items() if v}
    
    # Callback management
    async def _notify_progress(self, message: str, percentage: float):
        """Notify progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                await callback(message, percentage)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")
    
    async def _notify_completion(self, result: ReconResult):
        """Notify completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                await callback(result)
            except Exception as e:
                self.logger.error(f"Completion callback error: {e}")
    
    # Public interface methods
    def add_progress_callback(self, callback: callable):
        """Add progress update callback"""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: callable):
        """Add completion callback"""
        self.completion_callbacks.append(callback)
    
    def get_scan_results(self, scan_id: str) -> Optional[ReconResult]:
        """Get results for specific scan"""
        return self.current_results.get(scan_id)
    
    def get_scan_history(self) -> List[ReconResult]:
        """Get all scan history"""
        return self.scan_history.copy()
    
    def stop_current_scan(self):
        """Stop current reconnaissance scan"""
        self.is_running = False
        self.logger.info("Reconnaissance scan stopped by user")
