# galdr/interceptor/backend/modules/spider/forms/form_handler.py
import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import random
import string

from playwright.async_api import Page, ElementHandle
from bs4 import BeautifulSoup

from ..models.spider_data import FormData, FormField, FormSubmissionResult


@dataclass
class FormField:
    """Represents a form field"""
    name: str
    field_type: str
    value: str = ""
    required: bool = False
    placeholder: str = ""
    options: List[str] = None
    max_length: int = None
    pattern: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.field_type,
            'value': self.value,
            'required': self.required,
            'placeholder': self.placeholder,
            'options': self.options or [],
            'max_length': self.max_length,
            'pattern': self.pattern
        }


@dataclass
class FormData:
    """Represents a discovered form"""
    action: str
    method: str
    enctype: str
    fields: List[FormField]
    has_file_upload: bool = False
    is_login_form: bool = False
    is_search_form: bool = False
    form_id: str = ""
    form_class: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'method': self.method,
            'enctype': self.enctype,
            'fields': [field.to_dict() for field in self.fields],
            'has_file_upload': self.has_file_upload,
            'is_login_form': self.is_login_form,
            'is_search_form': self.is_search_form,
            'form_id': self.form_id,
            'form_class': self.form_class,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class FormSubmissionResult:
    """Result of form submission"""
    form_data: FormData
    submitted_values: Dict[str, str]
    response_status: int
    response_url: str
    redirect_url: Optional[str] = None
    response_content: str = ""
    errors: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.errors is None:
            self.errors = []


class FormHandler:
    """Handles form discovery, analysis, and submission"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Smart form filling data
        self.test_data = {
            'email': ['test@example.com', 'user@test.com', 'admin@example.org'],
            'username': ['testuser', 'admin', 'user123', 'demo'],
            'password': ['password123', 'admin123', 'test123'],
            'name': ['John Doe', 'Test User', 'Admin User'],
            'phone': ['+1234567890', '555-123-4567', '(555) 123-4567'],
            'address': ['123 Test St', '456 Demo Ave', '789 Example Blvd'],
            'city': ['Test City', 'Demo Town', 'Example City'],
            'zip': ['12345', '54321', '67890'],
            'company': ['Test Company', 'Demo Corp', 'Example Inc'],
            'website': ['http://example.com', 'https://test.com', 'http://demo.org']
        }
    
    async def discover_forms(self, page: Page) -> List[FormData]:
        """Discover all forms on the page"""
        forms = []
        
        try:
            # Get all form elements
            form_elements = await page.query_selector_all('form')
            
            for form_element in form_elements:
                form_data = await self._analyze_form(page, form_element)
                if form_data:
                    forms.append(form_data)
            
            self.logger.info(f"Discovered {len(forms)} forms on page")
            
        except Exception as e:
            self.logger.error(f"Error discovering forms: {e}")
        
        return forms
    
    async def _analyze_form(self, page: Page, form_element: ElementHandle) -> Optional[FormData]:
        """Analyze a single form element"""
        try:
            # Get form attributes
            action = await form_element.get_attribute('action') or ''
            method = (await form_element.get_attribute('method') or 'GET').upper()
            enctype = await form_element.get_attribute('enctype') or 'application/x-www-form-urlencoded'
            form_id = await form_element.get_attribute('id') or ''
            form_class = await form_element.get_attribute('class') or ''
            
            # Resolve relative action URLs
            if action:
                action = await page.evaluate(f'(action) => new URL(action, window.location.href).href', action)
            else:
                action = page.url
            
            # Find all form fields
            fields = await self._discover_form_fields(form_element)
            
            # Analyze form characteristics
            is_login_form = self._is_login_form(fields, form_id, form_class)
            is_search_form = self._is_search_form(fields, form_id, form_class)
            has_file_upload = any(field.field_type == 'file' for field in fields)
            
            form_data = FormData(
                action=action,
                method=method,
                enctype=enctype,
                fields=fields,
                has_file_upload=has_file_upload,
                is_login_form=is_login_form,
                is_search_form=is_search_form,
                form_id=form_id,
                form_class=form_class
            )
            
            return form_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing form: {e}")
            return None
    
    async def _discover_form_fields(self, form_element: ElementHandle) -> List[FormField]:
        """Discover all fields in a form"""
        fields = []
        
        try:
            # Query all input types
            input_selectors = [
                'input[type="text"]',
                'input[type="email"]', 
                'input[type="password"]',
                'input[type="number"]',
                'input[type="tel"]',
                'input[type="url"]',
                'input[type="search"]',
                'input[type="hidden"]',
                'input[type="file"]',
                'input[type="checkbox"]',
                'input[type="radio"]',
                'textarea',
                'select'
            ]
            
            for selector in input_selectors:
                elements = await form_element.query_selector_all(selector)
                
                for element in elements:
                    field = await self._analyze_form_field(element)
                    if field:
                        fields.append(field)
        
        except Exception as e:
            self.logger.error(f"Error discovering form fields: {e}")
        
        return fields
    
    async def _analyze_form_field(self, element: ElementHandle) -> Optional[FormField]:
        """Analyze a single form field"""
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            field_type = await element.get_attribute('type') or 'text'
            name = await element.get_attribute('name') or ''
            required = await element.get_attribute('required') is not None
            placeholder = await element.get_attribute('placeholder') or ''
            max_length = await element.get_attribute('maxlength')
            pattern = await element.get_attribute('pattern') or ''
            
            if not name:
                return None
            
            # Convert maxlength to int if present
            max_length = int(max_length) if max_length and max_length.isdigit() else None
            
            # Handle select options
            options = []
            if tag_name == 'select':
                option_elements = await element.query_selector_all('option')
                for option in option_elements:
                    option_value = await option.get_attribute('value')
                    option_text = await option.text_content()
                    if option_value:
                        options.append(option_value)
                    elif option_text:
                        options.append(option_text.strip())
            
            field = FormField(
                name=name,
                field_type=field_type if tag_name == 'input' else tag_name,
                required=required,
                placeholder=placeholder,
                options=options if options else None,
                max_length=max_length,
                pattern=pattern
            )
            
            return field
            
        except Exception as e:
            self.logger.error(f"Error analyzing form field: {e}")
            return None
    
    def _is_login_form(self, fields: List[FormField], form_id: str, form_class: str) -> bool:
        """Determine if form is a login form"""
        # Check for password field
        has_password = any(field.field_type == 'password' for field in fields)
        
        # Check for username/email field
        has_username = any(
            field.name.lower() in ['username', 'email', 'login', 'user'] 
            or field.field_type == 'email'
            for field in fields
        )
        
        # Check form attributes
        form_indicators = any(
            keyword in (form_id + ' ' + form_class).lower()
            for keyword in ['login', 'signin', 'auth', 'logon']
        )
        
        return has_password and (has_username or form_indicators)
    
    def _is_search_form(self, fields: List[FormField], form_id: str, form_class: str) -> bool:
        """Determine if form is a search form"""
        # Check for search-related field names
        has_search_field = any(
            keyword in field.name.lower()
            for field in fields
            for keyword in ['search', 'query', 'q', 'term']
        )
        
        # Check form attributes
        form_indicators = any(
            keyword in (form_id + ' ' + form_class).lower()
            for keyword in ['search', 'query', 'find']
        )
        
        return has_search_field or form_indicators
    
    async def submit_form(self, page: Page, form_data: FormData, current_url: str) -> Optional[FormSubmissionResult]:
        """Submit a form with appropriate test data"""
        try:
            # Skip login forms unless explicitly enabled
            if form_data.is_login_form and not self.config.enable_login_forms:
                self.logger.debug("Skipping login form (not enabled)")
                return None
            
            # Skip file upload forms for now
            if form_data.has_file_upload:
                self.logger.debug("Skipping file upload form")
                return None
            
            # Generate form values
            form_values = self._generate_form_values(form_data)
            
            # Fill the form
            await self._fill_form_fields(page, form_data, form_values)
            
            # Record current URL
            initial_url = page.url
            
            # Submit the form
            submit_button = await page.query_selector('input[type="submit"], button[type="submit"], button:not([type])')
            if submit_button:
                await submit_button.click()
            else:
                # Try to submit via Enter key on first text field
                first_text_field = next(
                    (field for field in form_data.fields if field.field_type in ['text', 'email']),
                    None
                )
                if first_text_field:
                    await page.press(f'input[name="{first_text_field.name}"]', 'Enter')
            
            # Wait for potential navigation or response
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass
            
            # Get response information
            final_url = page.url
            response_content = await page.content()
            
            # Check for redirect
            redirect_url = final_url if final_url != initial_url else None
            
            # Create submission result
            result = FormSubmissionResult(
                form_data=form_data,
                submitted_values=form_values,
                response_status=200,  # We'll enhance this with actual response tracking
                response_url=final_url,
                redirect_url=redirect_url,
                response_content=response_content[:1000]  # Truncate for storage
            )
            
            self.logger.info(f"Successfully submitted form to {form_data.action}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error submitting form: {e}")
            return None
    
    def _generate_form_values(self, form_data: FormData) -> Dict[str, str]:
        """Generate appropriate test values for form fields"""
        values = {}
        
        for field in form_data.fields:
            if field.field_type in ['hidden', 'submit', 'button']:
                continue
            
            value = self._generate_field_value(field)
            if value:
                values[field.name] = value
        
        return values
    
    def _generate_field_value(self, field: FormField) -> str:
        """Generate appropriate value for a single field"""
        field_name_lower = field.name.lower()
        
        # Handle different field types
        if field.field_type == 'email':
            return random.choice(self.test_data['email'])
        
        elif field.field_type == 'password':
            return random.choice(self.test_data['password'])
        
        elif field.field_type == 'select' and field.options:
            # Skip empty options
            valid_options = [opt for opt in field.options if opt.strip()]
            return random.choice(valid_options) if valid_options else ''
        
        elif field.field_type == 'checkbox':
            return 'on' if random.choice([True, False]) else ''
        
        elif field.field_type == 'radio':
            return field.options[0] if field.options else 'on'
        
        # Handle text fields based on name patterns
        elif field.field_type in ['text', 'search', 'tel', 'url']:
            if any(keyword in field_name_lower for keyword in ['email', 'mail']):
                return random.choice(self.test_data['email'])
            
            elif any(keyword in field_name_lower for keyword in ['user', 'login', 'account']):
                return random.choice(self.test_data['username'])
            
            elif any(keyword in field_name_lower for keyword in ['name', 'full']):
                return random.choice(self.test_data['name'])
            
            elif any(keyword in field_name_lower for keyword in ['phone', 'tel', 'mobile']):
                return random.choice(self.test_data['phone'])
            
            elif any(keyword in field_name_lower for keyword in ['address', 'street']):
                return random.choice(self.test_data['address'])
            
            elif any(keyword in field_name_lower for keyword in ['city', 'town']):
                return random.choice(self.test_data['city'])
            
            elif any(keyword in field_name_lower for keyword in ['zip', 'postal']):
                return random.choice(self.test_data['zip'])
            
            elif any(keyword in field_name_lower for keyword in ['company', 'organization']):
                return random.choice(self.test_data['company'])
            
            elif any(keyword in field_name_lower for keyword in ['website', 'url', 'site']):
                return random.choice(self.test_data['website'])
            
            elif any(keyword in field_name_lower for keyword in ['search', 'query', 'q']):
                return 'test query'
            
            # Generate based on field constraints
            elif field.max_length:
                if field.max_length <= 10:
                    return 'test'
                elif field.max_length <= 50:
                    return 'test input value'
                else:
                    return 'This is a longer test input value for testing purposes'
            
            # Default text value
            else:
                return 'test'
        
        elif field.field_type == 'number':
            return str(random.randint(1, 100))
        
        elif field.field_type == 'textarea':
            return 'This is a test message for the textarea field.'
        
        return ''
    
    async def _fill_form_fields(self, page: Page, form_data: FormData, form_values: Dict[str, str]):
        """Fill form fields with generated values"""
        for field in form_data.fields:
            if field.name not in form_values:
                continue
            
            value = form_values[field.name]
            if not value:
                continue
            
            try:
                selector = f'[name="{field.name}"]'
                
                if field.field_type == 'select':
                    await page.select_option(selector, value)
                
                elif field.field_type in ['checkbox', 'radio']:
                    if value and value != '':
                        await page.check(selector)
                
                elif field.field_type in ['text', 'email', 'password', 'search', 'tel', 'url', 'number']:
                    await page.fill(selector, value)
                
                elif field.field_type == 'textarea':
                    await page.fill(selector, value)
                
            except Exception as e:
                self.logger.debug(f"Error filling field {field.name}: {e}")
                continue
