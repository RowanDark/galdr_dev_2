// galdr/interceptor/frontend/src/renderer/services/ReconManager.ts
import { InterceptedTraffic, ProxyStatus } from '../types/traffic';

export interface ReconTarget {
  original_input: string;
  target_type: 'domain' | 'ip';
  primary_target: string;
}

export interface ReconProgress {
  scan_id: string;
  message: string;
  percentage: number;
  current_source?: string;
  sources_completed: number;
  total_sources: number;
}

export interface ReconResult {
  scan_id: string;
  target: ReconTarget;
  start_time: string;
  end_time?: string;
  duration_seconds: number;
  status: 'running' | 'completed' | 'error' | 'cancelled';
  
  // Aggregated results
  deduplicated_data: {
    subdomains: string[];
    urls: string[];
    ips: string[];
    technologies: string[];
    certificates: any[];
    dns_records: any[];
  };
  
  // Analysis
  analysis: {
    subdomain_patterns: Record<string, number>;
    interesting_subdomains: string[];
    ip_ranges: Record<string, string[]>;
    technology_stack: Record<string, string[]>;
  };
  
  // Statistics
  statistics: {
    sources_queried: number;
    successful_sources: number;
    total_subdomains_found: number;
    total_urls_found: number;
    total_ips_found: number;
    unique_technologies: number;
    certificates_found: number;
    dns_records_found: number;
  };
  
  // Source details
  sources: Record<string, {
    success: boolean;
    count: number;
    error?: string;
  }>;
  
  errors: string[];
}

export interface ReconConfig {
  timeout_seconds: number;
  max_concurrent_requests: number;
  enable_passive_sources: boolean;
  enable_api_sources: boolean;
  api_keys: Record<string, string>;
  delay_between_requests: number;
  max_results_per_source: number;
  include_subdomains: boolean;
  include_historical: boolean;
}

export class ReconManager {
  private proxyUrl = 'http://localhost:8080';
  private websocket: WebSocket | null = null;
  private isConnected = false;
  
  // Callback arrays
  private progressCallbacks: ((progress: ReconProgress) => void)[] = [];
  private completionCallbacks: ((result: ReconResult) => void)[] = [];
  private errorCallbacks: ((error: string) => void)[] = [];

  constructor() {
    this.connectWebSocket();
  }

  private connectWebSocket() {
    try {
      this.websocket = new WebSocket('ws://localhost:8081');
      
      this.websocket.onopen = () => {
        this.isConnected = true;
        console.log('Recon WebSocket connected');
      };
      
      this.websocket.onclose = () => {
        this.isConnected = false;
        console.log('Recon WebSocket disconnected');
        
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
        console.error('Recon WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'recon_progress':
        this.notifyProgress(data.data);
        break;
      case 'recon_complete':
        this.notifyCompletion(data.data);
        break;
      case 'recon_error':
        this.notifyError(data.data.message);
        break;
    }
  }

  async startReconnaissance(target: string, config?: Partial<ReconConfig>): Promise<string> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/recon/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, config })
      });

      if (!response.ok) {
        throw new Error(`Failed to start reconnaissance: ${response.statusText}`);
      }

      const result = await response.json();
      return result.scan_id;

    } catch (error) {
      console.error('Error starting reconnaissance:', error);
      throw error;
    }
  }

  async stopReconnaissance(scanId: string): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/recon/stop/${scanId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Failed to stop reconnaissance: ${response.statusText}`);
      }

    } catch (error) {
      console.error('Error stopping reconnaissance:', error);
      throw error;
    }
  }

  async getReconResults(scanId: string): Promise<ReconResult> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/recon/results/${scanId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get results: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting recon results:', error);
      throw error;
    }
  }

  async getReconHistory(): Promise<ReconResult[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/recon/history`);
      
      if (!response.ok) {
        throw new Error(`Failed to get history: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting recon history:', error);
      throw error;
    }
  }

  async exportResults(scanId: string, format: 'json' | 'csv' | 'txt'): Promise<Blob> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/recon/export/${scanId}?format=${format}`);
      
      if (!response.ok) {
        throw new Error(`Failed to export results: ${response.statusText}`);
      }

      return await response.blob();

    } catch (error) {
      console.error('Error exporting results:', error);
      throw error;
    }
  }

  async updateConfig(config: Partial<ReconConfig>): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/recon/config`, {
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

  // Event subscription methods
  onProgress(callback: (progress: ReconProgress) => void) {
    this.progressCallbacks.push(callback);
  }

  onCompletion(callback: (result: ReconResult) => void) {
    this.completionCallbacks.push(callback);
  }

  onError(callback: (error: string) => void) {
    this.errorCallbacks.push(callback);
  }

  // Notification methods
  private notifyProgress(progress: ReconProgress) {
    this.progressCallbacks.forEach(callback => callback(progress));
  }

  private notifyCompletion(result: ReconResult) {
    this.completionCallbacks.forEach(callback => callback(result));
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
