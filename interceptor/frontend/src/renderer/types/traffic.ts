// galdr/interceptor/frontend/src/renderer/types/traffic.ts
export interface InterceptedTraffic {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  headers: Record<string, string>;
  request_body?: string;
  response?: {
    status_code: number;
    headers: Record<string, string>;
    body: string;
    duration_ms: number;
  };
  source_ip: string;
  target_host: string;
  target_port: number;
  is_https: boolean;
  duration_ms?: number;
}

export interface SSLConnectionInfo {
  connection_id: string;
  hostname: string;
  port: number;
  start_time: string;
  duration_seconds: number;
  bytes_sent: number;
  bytes_received: number;
}

export interface ProxyStats {
  total_requests: number;
  unique_hosts: number;
  ssl_connections: number;
  websocket_clients: number;
  average_response_time: number;
  error_rate: number;
  uptime_seconds: number;
}

export type ProxyStatus = 'stopped' | 'starting' | 'running' | 'error';

export interface RequestModification {
  headers?: Record<string, string>;
  body?: string;
  method?: string;
  url?: string;
}
