// galdr/interceptor/frontend/src/renderer/services/SpiderManager.ts
import { InterceptedTraffic } from '../types/traffic';

export interface SpiderTarget {
  url: string;
  domain: string;
  scheme: string;
}

export interface SpiderConfig {
  max_depth: number;
  max_pages_per_domain: number;
  max_concurrent_pages: number;
  request_delay: number;
  respect_robots_txt: boolean;
  follow_redirects: boolean;
  
  // Browser settings
  browser_type: 'chromium' | 'firefox' | 'webkit';
  headless: boolean;
  user_agent: string;
  viewport_width: number;
  viewport_height: number;
  
  // Form handling
  enable_form_submission: boolean;
  enable_login_forms: boolean;
  max_forms_per_page: number;
  form_fill_strategy: 'smart' | 'random' | 'minimal';
  
  // Discovery settings
  discover_ajax_endpoints: boolean;
  discover_api_endpoints: boolean;
  analyze_javascript: boolean;
  extract_hidden_inputs: boolean;
  
  // OSINT collection
  collect_emails: boolean;
  collect_files: boolean;
  detect_technologies: boolean;
  detect_vulnerabilities: boolean;
  detect_secrets: boolean;
  
  // Performance and safety
  page_timeout: number;
  navigation_timeout: number;
  max_response_size: number;
  enable_screenshots: boolean;
  
  // Scope control
  stay_in_domain: boolean;
  allowed_domains: string[];
  excluded_paths: string[];
  excluded_file_types: string[];
}

export interface FormField {
  name: string;
  type: string;
  value: string;
  required: boolean;
  placeholder: string;
  options: string[];
  max_length?: number;
  pattern: string;
}

export interface DiscoveredForm {
  action: string;
  method: string;
  enctype: string;
  fields: FormField[];
  has_file_upload: boolean;
  is_login_form: boolean;
  is_search_form: boolean;
  form_id: string;
  form_class: string;
  timestamp: string;
}

export interface FormSubmissionResult {
  form_data: DiscoveredForm;
  submitted_values: Record<string, string>;
  response_status: number;
  response_url: string;
  redirect_url?: string;
  response_content: string;
  errors: string[];
  timestamp: string;
}

export interface DiscoveredEndpoint {
  url: string;
  method: string;
  headers: Record<string, string>;
  post_data?: string;
  resource_type: string;
  discovery_method: string;
  response_status?: number;
  response_headers: Record<string, string>;
  timestamp: string;
}

export interface SpiderResult {
  url: string;
  depth: number;
  status_code: number;
  content_type: string;
  timestamp: string;
  title: string;
  meta_description: string;
  discovered_forms: DiscoveredForm[];
  form_submissions: FormSubmissionResult[];
  ajax_endpoints: DiscoveredEndpoint[];
  content_analysis: Record<string, any>;
  screenshot_path?: string;
}

export interface SpiderSession {
  session_id: string;
  target_url: string;
  start_time: string;
  end_time?: string;
  status: 'running' | 'completed' | 'stopped' | 'error';
  total_pages: number;
  statistics: Record<string, any>;
  errors: string[];
  results: SpiderResult[];
}

export interface SpiderProgress {
  session_id: string;
  message: string;
  pages_processed: number;
  total_pages_estimated: number;
  current_url: string;
  current_depth: number;
  forms_discovered: number;
  endpoints_discovered: number;
  errors_count: number;
}

export interface SpiderStatistics {
  active_sessions: number;
  total_pages_visited: number;
  total_endpoints_discovered: number;
  total_forms_discovered: number;
  collected_links: number;
  collected_emails: number;
  collected_files: number;
  detected_technologies: number;
  found_vulnerabilities: number;
  found_secrets: number;
}

export class SpiderManager {
  private proxyUrl = 'http://localhost:8080';
  private websocket: WebSocket | null = null;
  private isConnected = false;
  
  // Callback arrays
  private progressCallbacks: ((progress: SpiderProgress) => void)[] = [];
  private sessionCallbacks: ((session: SpiderSession) => void)[] = [];
  private resultCallbacks: ((result: SpiderResult) => void)[] = [];
  private statisticsCallbacks: ((stats: SpiderStatistics) => void)[] = [];
  private errorCallbacks: ((error: string) => void)[] = [];

  constructor() {
    this.connectWebSocket();
  }

  private connectWebSocket() {
    try {
      this.websocket = new WebSocket('ws://localhost:8081');
      
      this.websocket.onopen = () => {
        this.isConnected = true;
        console.log('Spider WebSocket connected');
      };
      
      this.websocket.onclose = () => {
        this.isConnected = false;
        console.log('Spider WebSocket disconnected');
        
        // Attempt reconnection
        setTimeout(() => {
          if (!this.isConnected) {
            this.connectWebSocket();
          }
        }, 3000);
      };
      
      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.websocket.onerror = (error) => {
        console.error('Spider WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'spider_progress':
        this.notifyProgress(data.data);
        break;
      case 'spider_result':
        this.notifyResult(data.data);
        break;
      case 'spider_session_complete':
        this.notifySession(data.data);
        break;
      case 'spider_statistics':
        this.notifyStatistics(data.data);
        break;
      case 'spider_error':
        this.notifyError(data.data.message);
        break;
    }
  }

  async startSpiderSession(targetUrl: string, config?: Partial<SpiderConfig>, sessionName?: string): Promise<string> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          target_url: targetUrl, 
          config: config,
          session_name: sessionName 
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to start spider session: ${response.statusText}`);
      }

      const result = await response.json();
      return result.session_id;

    } catch (error) {
      console.error('Error starting spider session:', error);
      throw error;
    }
  }

  async stopSpiderSession(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/stop/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Failed to stop spider session: ${response.statusText}`);
      }

    } catch (error) {
      console.error('Error stopping spider session:', error);
      throw error;
    }
  }

  async getSessionData(sessionId: string): Promise<SpiderSession> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/session/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get session data: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting session data:', error);
      throw error;
    }
  }

  async getDiscoveredEndpoints(): Promise<DiscoveredEndpoint[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/endpoints`);
      
      if (!response.ok) {
        throw new Error(`Failed to get discovered endpoints: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting discovered endpoints:', error);
      throw error;
    }
  }

  async getDiscoveredForms(): Promise<DiscoveredForm[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/forms`);
      
      if (!response.ok) {
        throw new Error(`Failed to get discovered forms: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting discovered forms:', error);
      throw error;
    }
  }

  async getCollectedData(): Promise<Record<string, any>> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/collected-data`);
      
      if (!response.ok) {
        throw new Error(`Failed to get collected data: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting collected data:', error);
      throw error;
    }
  }

  async getStatistics(): Promise<SpiderStatistics> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/statistics`);
      
      if (!response.ok) {
        throw new Error(`Failed to get statistics: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting statistics:', error);
      throw error;
    }
  }

  async updateConfig(config: Partial<SpiderConfig>): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/spider/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`Failed to update config: ${response.statusText}`);
      }

    } catch (error) {
      console.error('Error updating config:', error);
      throw error;
    }
  }

  async exportData(format: 'json' | 'csv' | 'xlsx', dataType: 'session' | 'endpoints' | 'forms' | 'collected', sessionId?: string): Promise<Blob> {
    try {
      const params = new URLSearchParams({ format, type: dataType });
      if (sessionId) params.append('session_id', sessionId);
      
      const response = await fetch(`${this.proxyUrl}/api/spider/export?${params}`);
      
      if (!response.ok) {
        throw new Error(`Failed to export data: ${response.statusText}`);
      }

      return await response.blob();

    } catch (error) {
      console.error('Error exporting data:', error);
      throw error;
    }
  }

  // Event subscription methods
  onProgress(callback: (progress: SpiderProgress) => void) {
    this.progressCallbacks.push(callback);
  }

  onResult(callback: (result: SpiderResult) => void) {
    this.resultCallbacks.push(callback);
  }

  onSession(callback: (session: SpiderSession) => void) {
    this.sessionCallbacks.push(callback);
  }

  onStatistics(callback: (stats: SpiderStatistics) => void) {
    this.statisticsCallbacks.push(callback);
  }

  onError(callback: (error: string) => void) {
    this.errorCallbacks.push(callback);
  }

  // Notification methods
  private notifyProgress(progress: SpiderProgress) {
    this.progressCallbacks.forEach(callback => callback(progress));
  }

  private notifyResult(result: SpiderResult) {
    this.resultCallbacks.forEach(callback => callback(result));
  }

  private notifySession(session: SpiderSession) {
    this.sessionCallbacks.forEach(callback => callback(session));
  }

  private notifyStatistics(stats: SpiderStatistics) {
    this.statisticsCallbacks.forEach(callback => callback(stats));
  }

  private notifyError(error: string) {
    this.errorCallbacks.forEach(callback => callback(error));
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  isWebSocketConnected(): boolean {
    return this.isConnected;
  }
}
