// galdr/interceptor/frontend/src/renderer/services/CrawlerManager.ts
import { InterceptedTraffic } from '../types/traffic';

export interface CrawlEntry {
  url: string;
  method: string;
  status_code: number;
  request_headers: Record<string, string>;
  response_headers: Record<string, string>;
  request_body: string;
  response_body: string;
  timestamp: string;
  content_type: string;
  content_length: number;
  extracted_links: string[];
  extracted_emails: string[];
  extracted_files: Record<string, string[]>;
  analysis_result?: AnalysisResult;
}

export interface AnalysisResult {
  technologies: string[];
  vulnerabilities: VulnerabilityFinding[];
  secrets: SecretFinding[];
  content_analysis: Record<string, any>;
}

export interface VulnerabilityFinding {
  type: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  confidence: number;
  description: string;
  evidence: string;
  location: {
    url: string;
    type: string;
    position?: number;
  };
  timestamp: string;
  remediation: string;
}

export interface SecretFinding {
  type: string;
  value: string;
  masked_value: string;
  confidence: number;
  location: {
    url: string;
    type: string;
    header_name?: string;
    parameter_name?: string;
  };
  timestamp: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  entropy: number;
}

export interface CrawlSession {
  session_id: string;
  start_time: string;
  end_time?: string;
  status: 'running' | 'completed' | 'stopped';
  total_requests: number;
  unique_domains: number;
  entries: CrawlEntry[];
}

export interface CrawlerConfig {
  auto_analyze: boolean;
  max_entries_per_session: number;
  enable_tech_stack_detection: boolean;
  enable_vulnerability_detection: boolean;
  enable_ai_analysis: boolean;
  enable_secrets_detection: boolean;
  track_js_files: boolean;
  track_css_files: boolean;
  track_image_files: boolean;
  track_document_files: boolean;
  custom_file_extensions: string[];
  min_response_size: number;
  max_response_size: number;
  llm_provider: string;
  llm_model: string;
  vulnerability_confidence_threshold: number;
}

export interface CrawlerStatistics {
  active_sessions: number;
  total_entries: number;
  extracted_links: number;
  extracted_emails: number;
  extracted_files: number;
  detected_technologies: number;
  found_vulnerabilities: number;
  discovered_secrets: number;
}

export class CrawlerManager {
  private proxyUrl = 'http://localhost:8080';
  private websocket: WebSocket | null = null;
  private isConnected = false;
  
  // Callback arrays
  private entryCallbacks: ((entry: CrawlEntry) => void)[] = [];
  private sessionCallbacks: ((session: CrawlSession) => void)[] = [];
  private statisticsCallbacks: ((stats: CrawlerStatistics) => void)[] = [];
  private errorCallbacks: ((error: string) => void)[] = [];

  constructor() {
    this.connectWebSocket();
  }

  private connectWebSocket() {
    try {
      this.websocket = new WebSocket('ws://localhost:8081');
      
      this.websocket.onopen = () => {
        this.isConnected = true;
        console.log('Crawler WebSocket connected');
      };
      
      this.websocket.onclose = () => {
        this.isConnected = false;
        console.log('Crawler WebSocket disconnected');
        
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
        console.error('Crawler WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'traffic_analyzed':
        this.notifyEntry(data.data);
        break;
      case 'session_complete':
        this.notifySession(data.data);
        break;
      case 'statistics_update':
        this.notifyStatistics(data.data);
        break;
      case 'crawler_error':
        this.notifyError(data.data.message);
        break;
    }
  }

  async startSession(sessionName?: string): Promise<string> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name: sessionName })
      });

      if (!response.ok) {
        throw new Error(`Failed to start crawler session: ${response.statusText}`);
      }

      const result = await response.json();
      return result.session_id;

    } catch (error) {
      console.error('Error starting crawler session:', error);
      throw error;
    }
  }

  async stopSession(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/stop/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Failed to stop crawler session: ${response.statusText}`);
      }

    } catch (error) {
      console.error('Error stopping crawler session:', error);
      throw error;
    }
  }

  async getSessionData(sessionId: string): Promise<CrawlSession> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/session/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get session data: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting session data:', error);
      throw error;
    }
  }

  async getExtractedLinks(): Promise<string[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/links`);
      
      if (!response.ok) {
        throw new Error(`Failed to get extracted links: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting extracted links:', error);
      throw error;
    }
  }

  async getExtractedEmails(): Promise<string[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/emails`);
      
      if (!response.ok) {
        throw new Error(`Failed to get extracted emails: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting extracted emails:', error);
      throw error;
    }
  }

  async getExtractedFiles(): Promise<Record<string, string[]>> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/files`);
      
      if (!response.ok) {
        throw new Error(`Failed to get extracted files: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting extracted files:', error);
      throw error;
    }
  }

  async getDetectedTechnologies(): Promise<Record<string, string[]>> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/technologies`);
      
      if (!response.ok) {
        throw new Error(`Failed to get detected technologies: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting detected technologies:', error);
      throw error;
    }
  }

  async getVulnerabilities(): Promise<VulnerabilityFinding[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/vulnerabilities`);
      
      if (!response.ok) {
        throw new Error(`Failed to get vulnerabilities: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting vulnerabilities:', error);
      throw error;
    }
  }

  async getSecrets(): Promise<SecretFinding[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/secrets`);
      
      if (!response.ok) {
        throw new Error(`Failed to get secrets: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting secrets:', error);
      throw error;
    }
  }

  async getStatistics(): Promise<CrawlerStatistics> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/statistics`);
      
      if (!response.ok) {
        throw new Error(`Failed to get statistics: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting statistics:', error);
      throw error;
    }
  }

  async updateConfig(config: Partial<CrawlerConfig>): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/config`, {
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

  async exportData(format: 'json' | 'csv' | 'xlsx', dataType: 'all' | 'links' | 'emails' | 'files' | 'vulnerabilities' | 'secrets'): Promise<Blob> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/crawler/export?format=${format}&type=${dataType}`);
      
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
  onEntry(callback: (entry: CrawlEntry) => void) {
    this.entryCallbacks.push(callback);
  }

  onSession(callback: (session: CrawlSession) => void) {
    this.sessionCallbacks.push(callback);
  }

  onStatistics(callback: (stats: CrawlerStatistics) => void) {
    this.statisticsCallbacks.push(callback);
  }

  onError(callback: (error: string) => void) {
    this.errorCallbacks.push(callback);
  }

  // Notification methods
  private notifyEntry(entry: CrawlEntry) {
    this.entryCallbacks.forEach(callback => callback(entry));
  }

  private notifySession(session: CrawlSession) {
    this.sessionCallbacks.forEach(callback => callback(session));
  }

  private notifyStatistics(stats: CrawlerStatistics) {
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
