# galdr/interceptor/backend/modules/crawler/analyzers/tech_stack.py
import re
import json
from typing import List, Dict, Set, Optional
import aiohttp
from bs4 import BeautifulSoup

from ..models.crawl_data import CrawlEntry


class TechStackAnalyzer:
    """Analyzes technology stack similar to Wappalyzer"""
    
    def __init__(self, config):
        self.config = config
        self.technologies_db = self._load_technologies_database()
        self.ai_analyzer = None
        
        if config.enable_ai_analysis and config.llm_api_key:
            from .ai_analyzer import AITechAnalyzer
            self.ai_analyzer = AITechAnalyzer(config)
    
    def _load_technologies_database(self) -> Dict:
        """Load technology detection patterns"""
        # This is a simplified version of Wappalyzer's technology database
        return {
            "WordPress": {
                "html": [r'<meta name="generator" content="WordPress'],
                "headers": {"X-Pingback": r"/xmlrpc\.php"},
                "script": [r'wp-content', r'wp-includes'],
                "cookies": {"wordpress_logged_in": ".*"}
            },
            "React": {
                "html": [r'<div[^>]+id="root"', r'react-dom'],
                "script": [r'react\.development\.js', r'react\.production\.min\.js'],
                "dom": ["data-reactroot"]
            },
            "Angular": {
                "html": [r'ng-app', r'ng-controller'],
                "script": [r'angular\.js', r'angular\.min\.js'],
                "meta": {"ng-version": ".*"}
            },
            "Vue.js": {
                "html": [r'<div[^>]+id="app"'],
                "script": [r'vue\.js', r'vue\.min\.js', r'vue\.runtime'],
                "dom": ["v-if", "v-for", "v-model"]
            },
            "jQuery": {
                "script": [r'jquery\.js', r'jquery\.min\.js', r'\$\(document\)\.ready']
            },
            "Bootstrap": {
                "html": [r'class="[^"]*\b(?:container|row|col-)', r'bootstrap'],
                "css": [r'bootstrap\.css', r'bootstrap\.min\.css']
            },
            "Apache": {
                "headers": {"Server": r"Apache"}
            },
            "Nginx": {
                "headers": {"Server": r"nginx"}
            },
            "Node.js": {
                "headers": {"X-Powered-By": r"Express"},
                "script": [r'node_modules']
            },
            "PHP": {
                "headers": {"X-Powered-By": r"PHP", "Set-Cookie": r"PHPSESSID"},
                "html": [r'\.php(?:\?|$)']
            },
            "Laravel": {
                "headers": {"Set-Cookie": r"laravel_session"},
                "html": [r'csrf-token']
            },
            "Django": {
                "headers": {"Set-Cookie": r"csrftoken", "Server": r"WSGIServer"},
                "html": [r'csrfmiddlewaretoken']
            },
            "Flask": {
                "headers": {"Server": r"Werkzeug"}
            },
            "ASP.NET": {
                "headers": {"X-AspNet-Version": ".*", "X-Powered-By": r"ASP\.NET"},
                "html": [r'__VIEWSTATE', r'aspnetForm']
            },
            "IIS": {
                "headers": {"Server": r"Microsoft-IIS"}
            },
            "Cloudflare": {
                "headers": {"CF-RAY": ".*", "Server": r"cloudflare"}
            },
            "Amazon Web Services": {
                "headers": {"Server": r"AmazonS3", "X-Amz-.*": ".*"}
            },
            "Google Analytics": {
                "script": [r'google-analytics\.com/analytics\.js', r'gtag\(']
            },
            "Font Awesome": {
                "html": [r'font-awesome', r'fa-'],
                "css": [r'font-awesome\.css']
            }
        }
    
    async def analyze(self, entry: CrawlEntry) -> List[str]:
        """Analyze technology stack for the given entry"""
        detected_technologies = set()
        
        try:
            # Rule-based detection
            rule_based_techs = self._analyze_with_rules(entry)
            detected_technologies.update(rule_based_techs)
            
            # AI-enhanced detection (if enabled)
            if self.ai_analyzer:
                ai_techs = await self.ai_analyzer.analyze(entry)
                detected_technologies.update(ai_techs)
            
        except Exception as e:
            self.logger.error(f"Error analyzing tech stack: {e}")
        
        return sorted(list(detected_technologies))
    
    def _analyze_with_rules(self, entry: CrawlEntry) -> Set[str]:
        """Analyze using rule-based detection"""
        detected = set()
        
        for tech_name, rules in self.technologies_db.items():
            if self._matches_technology(entry, rules):
                detected.add(tech_name)
        
        return detected
    
    def _matches_technology(self, entry: CrawlEntry, rules: Dict) -> bool:
        """Check if entry matches technology rules"""
        # Check HTML patterns
        if 'html' in rules:
            for pattern in rules['html']:
                if re.search(pattern, entry.response_body, re.IGNORECASE):
                    return True
        
        # Check headers
        if 'headers' in rules:
            for header_name, pattern in rules['headers'].items():
                header_value = entry.response_headers.get(header_name, '')
                if re.search(pattern, header_value, re.IGNORECASE):
                    return True
        
        # Check script content
        if 'script' in rules:
            for pattern in rules['script']:
                if re.search(pattern, entry.response_body, re.IGNORECASE):
                    return True
        
        # Check CSS content
        if 'css' in rules:
            for pattern in rules['css']:
                if re.search(pattern, entry.response_body, re.IGNORECASE):
                    return True
        
        # Check meta tags
        if 'meta' in rules:
            soup = BeautifulSoup(entry.response_body, 'html.parser')
            for meta_name, pattern in rules['meta'].items():
                meta_tag = soup.find('meta', {'name': meta_name})
                if meta_tag and re.search(pattern, meta_tag.get('content', ''), re.IGNORECASE):
                    return True
        
        # Check DOM attributes
        if 'dom' in rules:
            for attr in rules['dom']:
                if attr in entry.response_body:
                    return True
        
        # Check cookies
        if 'cookies' in rules:
            set_cookie = entry.response_headers.get('Set-Cookie', '')
            for cookie_name, pattern in rules['cookies'].items():
                if cookie_name in set_cookie and re.search(pattern, set_cookie, re.IGNORECASE):
                    return True
        
        return False


# AI-enhanced technology detection
class AITechAnalyzer:
    """AI-enhanced technology stack analyzer"""
    
    def __init__(self, config):
        self.config = config
        self.client = self._initialize_ai_client()
    
    def _initialize_ai_client(self):
        """Initialize AI client based on provider"""
        if self.config.llm_provider == "openai":
            import openai
            return openai.AsyncOpenAI(api_key=self.config.llm_api_key)
        elif self.config.llm_provider == "anthropic":
            import anthropic
            return anthropic.AsyncAnthropic(api_key=self.config.llm_api_key)
        else:
            return None
    
    async def analyze(self, entry: CrawlEntry) -> List[str]:
        """Use AI to detect additional technologies"""
        if not self.client:
            return []
        
        try:
            # Prepare content for analysis
            analysis_content = self._prepare_content(entry)
            
            # Generate AI prompt
            prompt = self._create_analysis_prompt(analysis_content)
            
            # Get AI response
            response = await self._get_ai_response(prompt)
            
            # Parse technologies from response
            technologies = self._parse_technologies(response)
            
            return technologies
            
        except Exception as e:
            self.logger.error(f"AI analysis error: {e}")
            return []
    
    def _prepare_content(self, entry: CrawlEntry) -> str:
        """Prepare content for AI analysis"""
        # Truncate content to manageable size
        max_content_length = 4000
        
        content_parts = []
        
        # Add headers
        content_parts.append("=== RESPONSE HEADERS ===")
        for key, value in entry.response_headers.items():
            content_parts.append(f"{key}: {value}")
        
        # Add HTML head section if present
        soup = BeautifulSoup(entry.response_body, 'html.parser')
        if soup.head:
            content_parts.append("\n=== HTML HEAD ===")
            content_parts.append(str(soup.head)[:1500])
        
        # Add script tags
        scripts = soup.find_all('script')
        if scripts:
            content_parts.append("\n=== SCRIPT TAGS ===")
            for script in scripts[:5]:  # Limit to first 5 scripts
                content_parts.append(str(script)[:500])
        
        # Add link tags
        links = soup.find_all('link')
        if links:
            content_parts.append("\n=== LINK TAGS ===")
            for link in links[:10]:  # Limit to first 10 links
                content_parts.append(str(link))
        
        full_content = "\n".join(content_parts)
        
        # Truncate if too long
        if len(full_content) > max_content_length:
            full_content = full_content[:max_content_length] + "... [TRUNCATED]"
        
        return full_content
    
    def _create_analysis_prompt(self, content: str) -> str:
        """Create prompt for AI analysis"""
        return f"""
Analyze the following web page content and identify the technologies used. Look for:

1. Web frameworks (React, Angular, Vue.js, etc.)
2. Backend technologies (PHP, Python, Node.js, etc.)
3. Web servers (Apache, Nginx, IIS, etc.)
4. Content Management Systems (WordPress, Drupal, etc.)
5. JavaScript libraries (jQuery, Bootstrap, etc.)
6. Cloud services (AWS, Cloudflare, etc.)
7. Analytics and tracking tools
8. Any other notable technologies

Content to analyze:
{content}

Please respond with a JSON array of technology names only, for example:
["React", "Node.js", "Webpack", "Bootstrap"]

Be conservative in your identification - only include technologies you're confident about based on clear evidence in the content.
"""
    
    async def _get_ai_response(self, prompt: str) -> str:
        """Get response from AI provider"""
        if self.config.llm_provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            return response.choices[0].message.content
        
        elif self.config.llm_provider == "anthropic":
            response = await self.client.messages.create(
                model=self.config.llm_model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        return ""
    
    def _parse_technologies(self, response: str) -> List[str]:
        """Parse technologies from AI response"""
        try:
            # Try to parse as JSON
            import json
            technologies = json.loads(response.strip())
            
            if isinstance(technologies, list):
                return [tech for tech in technologies if isinstance(tech, str)]
        
        except json.JSONDecodeError:
            # Fallback: extract from text
            lines = response.split('\n')
            technologies = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('#', '//', '/*')):
                    # Remove quotes and brackets
                    tech = re.sub(r'["\[\],]', '', line).strip()
                    if tech and len(tech) < 50:  # Sanity check
                        technologies.append(tech)
        
        return technologies[:20]  # Limit to reasonable number
