"""
AI Analyzer for Passive Crawler Module
Integrates AI for enhanced content and vulnerability analysis
galdr/interceptor/backend/modules/crawler/analyzers/ai_analyzer.py
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import openai
from datetime import datetime

class AIAnalyzer:
    """AI-powered content analysis for passive crawling"""
    
    def __init__(self, ai_config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.ai_config = ai_config
        self.client = None
        self._initialize_client()
        
        # Analysis prompts
        self.prompts = {
            'vulnerability_analysis': """
            Analyze the following web content for security vulnerabilities.
            Look for patterns that might indicate:
            1. SQL injection vulnerabilities
            2. Cross-site scripting (XSS) opportunities
            3. Information disclosure
            4. Authentication bypasses
            5. Authorization flaws
            
            Content: {content}
            
            Respond with JSON format:
            {{
                "vulnerabilities": [
                    {{
                        "type": "vulnerability_type",
                        "severity": "high|medium|low",
                        "description": "detailed_description",
                        "evidence": "code_snippet_or_pattern",
                        "recommendation": "how_to_fix"
                    }}
                ],
                "confidence": 0.85
            }}
            """,
            
            'secrets_detection': """
            Analyze the following content for exposed secrets, credentials, and sensitive information.
            Look for:
            1. API keys and tokens
            2. Database connection strings
            3. Passwords and credentials
            4. Private keys and certificates
            5. Configuration data
            6. Internal URLs and endpoints
            
            Content: {content}
            
            Respond with JSON format:
            {{
                "secrets": [
                    {{
                        "type": "secret_type",
                        "value": "redacted_value",
                        "severity": "high|medium|low",
                        "description": "what_was_found",
                        "location": "where_found"
                    }}
                ],
                "confidence": 0.90
            }}
            """,
            
            'technology_analysis': """
            Analyze the following web content to identify technologies, frameworks, and libraries being used.
            Look for:
            1. Frontend frameworks (React, Angular, Vue, etc.)
            2. Backend technologies (PHP, Python, Node.js, etc.)
            3. CMS platforms (WordPress, Drupal, etc.)
            4. JavaScript libraries
            5. CSS frameworks
            6. Server technologies
            
            Content: {content}
            Headers: {headers}
            
            Respond with JSON format:
            {{
                "technologies": [
                    {{
                        "name": "technology_name",
                        "version": "version_if_detected",
                        "category": "frontend|backend|cms|library|framework",
                        "confidence": 0.95,
                        "evidence": "detection_method_or_pattern"
                    }}
                ],
                "confidence": 0.88
            }}
            """,
            
            'content_classification': """
            Analyze and classify the following web content.
            Determine:
            1. Content type and purpose
            2. Intended audience
            3. Security posture
            4. Data sensitivity level
            5. Compliance considerations
            
            Content: {content}
            URL: {url}
            
            Respond with JSON format:
            {{
                "classification": {{
                    "content_type": "login_page|api_endpoint|admin_panel|public_content|etc",
                    "purpose": "description_of_purpose",
                    "audience": "public|internal|admin|api_consumer",
                    "sensitivity": "public|internal|confidential|restricted",
                    "security_concerns": ["concern1", "concern2"],
                    "compliance_notes": "any_compliance_considerations"
                }},
                "confidence": 0.80
            }}
            """
        }
    
    def _initialize_client(self):
        """Initialize AI client based on configuration"""
        try:
            provider = self.ai_config.get('provider', 'openai')
            
            if provider == 'openai':
                openai.api_key = self.ai_config.get('api_key')
                self.client = openai
                self.logger.info("OpenAI client initialized")
            
            # Add support for other providers as needed
            # elif provider == 'anthropic':
            #     # Initialize Anthropic client
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI client: {e}")
            self.client = None
    
    async def analyze_content(self, content: str, headers: Dict[str, str], 
                            url: str, analysis_types: List[str] = None) -> Dict:
        """
        Perform AI-powered content analysis
        
        Args:
            content: Web content to analyze
            headers: HTTP headers
            url: Content URL
            analysis_types: Types of analysis to perform
            
        Returns:
            AI analysis results
        """
        if not self.client:
            return {'error': 'AI client not initialized'}
        
        # Default analysis types
        if not analysis_types:
            analysis_types = ['vulnerability_analysis', 'secrets_detection', 'technology_analysis']
        
        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'analysis_types': analysis_types,
            'results': {},
            'errors': []
        }
        
        # Truncate content if too long (AI models have token limits)
        truncated_content = self._truncate_content(content, max_length=8000)
        
        # Perform each type of analysis
        for analysis_type in analysis_types:
            try:
                self.logger.info(f"Performing {analysis_type} for {url}")
                
                analysis_result = await self._perform_analysis(
                    analysis_type, truncated_content, headers, url
                )
                
                results['results'][analysis_type] = analysis_result
                
            except Exception as e:
                error_msg = f"Failed {analysis_type}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # Calculate overall confidence score
        results['overall_confidence'] = self._calculate_overall_confidence(results['results'])
        
        return results
    
    async def _perform_analysis(self, analysis_type: str, content: str, 
                              headers: Dict[str, str], url: str) -> Dict:
        """Perform specific type of AI analysis"""
        
        if analysis_type not in self.prompts:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        # Prepare prompt
        prompt_template = self.prompts[analysis_type]
        
        if analysis_type == 'technology_analysis':
            prompt = prompt_template.format(
                content=content,
                headers=json.dumps(headers, indent=2)
            )
        elif analysis_type == 'content_classification':
            prompt = prompt_template.format(
                content=content,
                url=url
            )
        else:
            prompt = prompt_template.format(content=content)
        
        # Make AI request
        try:
            response = await self._make_ai_request(prompt)
            
            # Parse JSON response
            parsed_response = self._parse_ai_response(response)
            
            return {
                'success': True,
                'data': parsed_response,
                'raw_response': response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type
            }
    
    async def _make_ai_request(self, prompt: str) -> str:
        """Make request to AI service"""
        try:
            # For OpenAI
            if self.ai_config.get('provider') == 'openai':
                response = await asyncio.to_thread(
                    self.client.ChatCompletion.create,
                    model=self.ai_config.get('model', 'gpt-3.5-turbo'),
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a cybersecurity expert analyzing web content for vulnerabilities and security issues."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=self.ai_config.get('max_tokens', 1500),
                    temperature=self.ai_config.get('temperature', 0.1)
                )
                
                return response.choices[0].message.content
            
            # Add support for other providers
            else:
                raise ValueError(f"Unsupported AI provider: {self.ai_config.get('provider')}")
                
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response, handling potential formatting issues"""
        try:
            # Try to parse as JSON
            return json.loads(response)
            
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = None
            
            # Look for JSON-like structure
            import re
            json_pattern = r'\{.*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                for match in matches:
                    try:
                        return json.loads(match)
                    except:
                        continue
            
            # If no valid JSON found, return structured error
            return {
                'error': 'Failed to parse AI response as JSON',
                'raw_response': response,
                'parsed': False
            }
    
    def _truncate_content(self, content: str, max_length: int = 8000) -> str:
        """Truncate content to fit within AI model limits"""
        if len(content) <= max_length:
            return content
        
        # Try to truncate at a reasonable boundary
        truncated = content[:max_length]
        
        # Find last complete line
        last_newline = truncated.rfind('\n')
        if last_newline > max_length * 0.8:  # If we can save at least 20%
            truncated = truncated[:last_newline]
        
        return truncated + '\n\n[CONTENT TRUNCATED]'
    
    def _calculate_overall_confidence(self, results: Dict) -> float:
        """Calculate overall confidence score from all analyses"""
        confidences = []
        
        for analysis_type, result in results.items():
            if result.get('success') and 'data' in result:
                data = result['data']
                if isinstance(data, dict) and 'confidence' in data:
                    confidences.append(data['confidence'])
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    async def analyze_for_privacy_concerns(self, content: str, url: str) -> Dict:
        """Specialized analysis for privacy and data protection concerns"""
        
        privacy_prompt = """
        Analyze the following web content for privacy and data protection concerns.
        Look for:
        1. Personal data collection (PII)
        2. Cookie usage and tracking
        3. Third-party integrations
        4. Data sharing practices
        5. GDPR/CCPA compliance indicators
        6. Privacy policy references
        
        Content: {content}
        URL: {url}
        
        Respond with JSON format:
        {{
            "privacy_concerns": [
                {{
                    "type": "concern_type",
                    "severity": "high|medium|low",
                    "description": "detailed_description",
                    "regulation": "GDPR|CCPA|other",
                    "recommendation": "compliance_suggestion"
                }}
            ],
            "data_collection": {{
                "personal_data_detected": true/false,
                "tracking_detected": true/false,
                "third_party_services": ["service1", "service2"],
                "privacy_policy_found": true/false
            }},
            "compliance_score": 0.75,
            "confidence": 0.85
        }}
        """
        
        formatted_prompt = privacy_prompt.format(content=content, url=url)
        
        try:
            response = await self._make_ai_request(formatted_prompt)
            parsed_response = self._parse_ai_response(response)
            
            return {
                'success': True,
                'privacy_analysis': parsed_response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis_type': 'privacy_analysis'
            }
    
    async def analyze_api_endpoint(self, content: str, headers: Dict[str, str], 
                                 url: str, method: str = 'GET') -> Dict:
        """Specialized analysis for API endpoints"""
        
        api_prompt = """
        Analyze the following API endpoint response for security and design issues.
        Look for:
        1. Authentication/authorization vulnerabilities
        2. Data exposure issues
        3. API design problems
        4. Rate limiting concerns
        5. Input validation gaps
        6. Error handling issues
        
        URL: {url}
        Method: {method}
        Headers: {headers}
        Response: {content}
        
        Respond with JSON format:
        {{
            "api_security": [
                {{
                    "issue_type": "vulnerability_type",
                    "severity": "high|medium|low",
                    "description": "detailed_description",
                    "endpoint": "{url}",
                    "recommendation": "how_to_fix"
                }}
            ],
            "api_design": {{
                "rest_compliance": 0.80,
                "documentation_quality": "good|fair|poor",
                "error_handling": "good|fair|poor",
                "versioning_detected": true/false
            }},
            "security_score": 0.70,
            "confidence": 0.88
        }}
        """
        
        formatted_prompt = api_prompt.format(
            url=url,
            method=method,
            headers=json.dumps(headers, indent=2),
            content=content
        )
        
        try:
            response = await self._make_ai_request(formatted_prompt)
            parsed_response = self._parse_ai_response(response)
            
            return {
                'success': True,
                'api_analysis': parsed_response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis_type': 'api_analysis'
            }
    
    def get_supported_analysis_types(self) -> List[str]:
        """Get list of supported analysis types"""
        return list(self.prompts.keys()) + ['privacy_analysis', 'api_analysis']
    
    def is_available(self) -> bool:
        """Check if AI analysis is available"""
        return self.client is not None
    
    async def batch_analyze(self, content_items: List[Dict], 
                          analysis_types: List[str] = None) -> List[Dict]:
        """
        Perform batch analysis on multiple content items
        
        Args:
            content_items: List of dicts with 'content', 'headers', 'url'
            analysis_types: Types of analysis to perform
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Process in batches to avoid overwhelming the AI service
        batch_size = self.ai_config.get('batch_size', 5)
        
        for i in range(0, len(content_items), batch_size):
            batch = content_items[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = []
            for item in batch:
                task = self.analyze_content(
                    item['content'],
                    item['headers'],
                    item['url'],
                    analysis_types
                )
                batch_tasks.append(task)
            
            try:
                # Wait for batch completion with timeout
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*batch_tasks, return_exceptions=True),
                    timeout=self.ai_config.get('batch_timeout', 300)
                )
                
                # Process results and handle exceptions
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Batch item {i+j} failed: {result}")
                        results.append({
                            'url': batch[j]['url'],
                            'error': str(result),
                            'batch_index': i + j
                        })
                    else:
                        results.append(result)
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(content_items):
                    await asyncio.sleep(self.ai_config.get('batch_delay', 2))
                    
            except asyncio.TimeoutError:
                self.logger.error(f"Batch {i//batch_size + 1} timed out")
                for j in range(len(batch)):
                    results.append({
                        'url': batch[j]['url'],
                        'error': 'Batch processing timeout',
                        'batch_index': i + j
                    })
            
            except Exception as e:
                self.logger.error(f"Batch {i//batch_size + 1} failed: {e}")
                for j in range(len(batch)):
                    results.append({
                        'url': batch[j]['url'],
                        'error': f'Batch processing error: {str(e)}',
                        'batch_index': i + j
                    })
        
        return results
    
    def get_usage_statistics(self) -> Dict:
        """Get AI usage statistics"""
        # This would track API usage, costs, etc.
        # Implementation depends on AI provider
        return {
            'provider': self.ai_config.get('provider'),
            'model': self.ai_config.get('model'),
            'requests_made': 0,  # Would be tracked
            'tokens_used': 0,    # Would be tracked
            'cost_estimate': 0.0 # Would be calculated
        }
