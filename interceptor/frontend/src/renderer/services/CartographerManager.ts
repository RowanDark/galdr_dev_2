// galdr/interceptor/frontend/src/renderer/services/CartographerManager.ts
import { InterceptedTraffic } from '../types/traffic';

export interface SiteMapNode {
  id: string;
  url: string;
  title: string;
  depth: number;
  node_type: 'page' | 'endpoint' | 'form' | 'file' | 'external';
  status_code?: number;
  content_type: string;
  size: number;
  discovery_method: 'passive' | 'active' | 'manual';
  timestamp: string;
  parent_id?: string;
  children: string[];
  
  // Additional metadata
  meta_description?: string;
  technologies: string[];
  forms_count: number;
  links_count: number;
  vulnerabilities_count: number;
  secrets_count: number;
  
  // Visual properties
  x?: number;
  y?: number;
  category: string;
  importance_score: number;
}

export interface SiteMapConnection {
  id: string;
  source_id: string;
  target_id: string;
  connection_type: 'link' | 'form_action' | 'ajax' | 'redirect' | 'iframe';
  method: string;
  parameters?: Record<string, string>;
  strength: number; // 1-10 indicating connection strength
  bidirectional: boolean;
}

export interface SiteMapCluster {
  id: string;
  name: string;
  nodes: string[];
  cluster_type: 'subdirectory' | 'functionality' | 'technology' | 'security_level';
  center_x: number;
  center_y: number;
  radius: number;
  color: string;
}

export interface SiteMapData {
  session_id: string;
  target_domain: string;
  creation_time: string;
  last_updated: string;
  
  nodes: SiteMapNode[];
  connections: SiteMapConnection[];
  clusters: SiteMapCluster[];
  
  statistics: {
    total_nodes: number;
    total_connections: number;
    max_depth: number;
    coverage_percentage: number;
    unique_technologies: number;
    security_issues: number;
  };
  
  layout_settings: {
    layout_type: 'hierarchical' | 'force' | 'circular' | 'tree';
    spacing: number;
    cluster_separation: number;
    edge_bundling: boolean;
  };
}

export interface CartographerConfig {
  auto_update: boolean;
  max_nodes: number;
  node_grouping: 'none' | 'subdirectory' | 'functionality' | 'depth';
  show_external_links: boolean;
  show_forms: boolean;
  show_endpoints: boolean;
  show_files: boolean;
  
  // Visual settings
  layout_algorithm: 'force' | 'hierarchical' | 'circular' | 'tree';
  animation_enabled: boolean;
  node_size_by: 'static' | 'importance' | 'connections' | 'content_size';
  color_scheme: 'default' | 'security' | 'technology' | 'depth';
  
  // Filtering
  min_depth: number;
  max_depth: number;
  include_status_codes: number[];
  exclude_file_types: string[];
  security_focus: boolean;
}

export interface MapAnalysis {
  orphaned_pages: SiteMapNode[];
  entry_points: SiteMapNode[];
  highly_connected: SiteMapNode[];
  security_hotspots: SiteMapNode[];
  technology_clusters: Record<string, SiteMapNode[]>;
  navigation_paths: {
    shortest_paths: Array<{from: string, to: string, path: string[], distance: number}>;
    critical_paths: Array<{path: string[], risk_score: number}>;
  };
}

export class CartographerManager {
  private proxyUrl = 'http://localhost:8080';
  private websocket: WebSocket | null = null;
  private isConnected = false;
  
  // Callback arrays
  private mapUpdateCallbacks: ((mapData: SiteMapData) => void)[] = [];
  private nodeUpdateCallbacks: ((node: SiteMapNode) => void)[] = [];
  private analysisCallbacks: ((analysis: MapAnalysis) => void)[] = [];
  private errorCallbacks: ((error: string) => void)[] = [];

  constructor() {
    this.connectWebSocket();
  }

  private connectWebSocket() {
    try {
      this.websocket = new WebSocket('ws://localhost:8081');
      
      this.websocket.onopen = () => {
        this.isConnected = true;
        console.log('Cartographer WebSocket connected');
      };
      
      this.websocket.onclose = () => {
        this.isConnected = false;
        console.log('Cartographer WebSocket disconnected');
        
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
        console.error('Cartographer WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'map_updated':
        this.notifyMapUpdate(data.data);
        break;
      case 'node_discovered':
        this.notifyNodeUpdate(data.data);
        break;
      case 'analysis_complete':
        this.notifyAnalysis(data.data);
        break;
      case 'cartographer_error':
        this.notifyError(data.data.message);
        break;
    }
  }

  async createSiteMap(targetUrl: string, config?: Partial<CartographerConfig>): Promise<string> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_url: targetUrl, config })
      });

      if (!response.ok) {
        throw new Error(`Failed to create site map: ${response.statusText}`);
      }

      const result = await response.json();
      return result.session_id;

    } catch (error) {
      console.error('Error creating site map:', error);
      throw error;
    }
  }

  async getSiteMapData(sessionId: string): Promise<SiteMapData> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/map/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get site map: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting site map data:', error);
      throw error;
    }
  }

  async updateMapLayout(sessionId: string, layoutSettings: Partial<SiteMapData['layout_settings']>): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/layout/${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(layoutSettings)
      });

      if (!response.ok) {
        throw new Error(`Failed to update layout: ${response.statusText}`);
      }

    } catch (error) {
      console.error('Error updating map layout:', error);
      throw error;
    }
  }

  async analyzeMap(sessionId: string): Promise<MapAnalysis> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/analyze/${sessionId}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to analyze map: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error analyzing map:', error);
      throw error;
    }
  }

  async exportMap(sessionId: string, format: 'png' | 'svg' | 'json' | 'cytoscape'): Promise<Blob> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/export/${sessionId}?format=${format}`);
      
      if (!response.ok) {
        throw new Error(`Failed to export map: ${response.statusText}`);
      }

      return await response.blob();

    } catch (error) {
      console.error('Error exporting map:', error);
      throw error;
    }
  }

  async searchNodes(sessionId: string, query: string, filters?: Record<string, any>): Promise<SiteMapNode[]> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/search/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, filters })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to search nodes: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error searching nodes:', error);
      throw error;
    }
  }

  async getNodeDetails(sessionId: string, nodeId: string): Promise<SiteMapNode> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/node/${sessionId}/${nodeId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get node details: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Error getting node details:', error);
      throw error;
    }
  }

  async updateConfig(config: Partial<CartographerConfig>): Promise<void> {
    try {
      const response = await fetch(`${this.proxyUrl}/api/cartographer/config`, {
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
  onMapUpdate(callback: (mapData: SiteMapData) => void) {
    this.mapUpdateCallbacks.push(callback);
  }

  onNodeUpdate(callback: (node: SiteMapNode) => void) {
    this.nodeUpdateCallbacks.push(callback);
  }

  onAnalysis(callback: (analysis: MapAnalysis) => void) {
    this.analysisCallbacks.push(callback);
  }

  onError(callback: (error: string) => void) {
    this.errorCallbacks.push(callback);
  }

  // Notification methods
  private notifyMapUpdate(mapData: SiteMapData) {
    this.mapUpdateCallbacks.forEach(callback => callback(mapData));
  }

  private notifyNodeUpdate(node: SiteMapNode) {
    this.nodeUpdateCallbacks.forEach(callback => callback(node));
  }

  private notifyAnalysis(analysis: MapAnalysis) {
    this.analysisCallbacks.forEach(callback => callback(analysis));
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
