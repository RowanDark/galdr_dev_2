// galdr/interceptor/frontend/src/renderer/services/ProxyManager.ts
// --- REFACTORED ---
// This class now uses `socket.io-client` for robust, event-based communication.
// API calls now point to the new FastAPI server on port 8000.

import { io, Socket } from 'socket.io-client';
import { InterceptedTraffic, ProxyStatus } from '../types/traffic'; // Assuming types are defined

const API_BASE_URL = 'http://localhost:8000';

// NEW: Define the structure for a Raider result event
export interface RaiderResultEvent {
    attack_id: string;
    request_number: number;
    payload: string;
    status: number;
    length: number;
    duration: number;
}
export interface RaiderStatusEvent {
    attack_id: string;
    status: 'completed' | 'stopped' | 'error';
}

class ProxyManager {
  private socket: Socket;

  // Define clear event handlers for better state management in components
  public onStatusUpdate: ((status: ProxyStatus) => void) | null = null;
  public onNewTraffic: ((traffic: InterceptedTraffic) => void) | null = null;
  public onError: ((error: string) => void) | null = null;
  public onRaiderResult: ((result: RaiderResultEvent) => void) | null = null;
  public onRaiderStatus: ((status: RaiderStatusEvent) => void) | null = null;

  constructor() {
    this.socket = io(API_BASE_URL, {
      transports: ['websocket'],
      reconnectionAttempts: 5,
      reconnectionDelay: 3000,
    });
    this.setupSocketEvents();
  }

  private setupSocketEvents(): void {
    this.socket.on('connect', () => {
      console.log('Successfully connected to Galdr backend via WebSocket.');
      // After connecting, request the current proxy status
      this.socket.emit('get_proxy_status'); 
    });

    this.socket.on('disconnect', () => {
      console.warn('Disconnected from Galdr backend.');
      if (this.onStatusUpdate) this.onStatusUpdate('stopped'); // Assume stopped on disconnect
    });

    this.socket.on('connect_error', (err) => {
      console.error('Connection Error:', err.message);
      if (this.onError) this.onError(err.message);
    });

    // Custom events from our backend
    this.socket.on('status_update', (data: { status: ProxyStatus }) => {
      if (this.onStatusUpdate) this.onStatusUpdate(data.status);
    });

    this.socket.on('new_traffic', (data: InterceptedTraffic) => {
      if (this.onNewTraffic) this.onNewTraffic(data);
    });
     // NEW: Listen for events from the Raider module and pass to the handler
    this.socket.on('raider_result_update', (data: RaiderResultEvent) => {
        if (this.onRaiderResult) this.onRaiderResult(data);
    });
    
    this.socket.on('raider_attack_status', (data: RaiderStatusEvent) => {
        if (this.onRaiderStatus) this.onRaiderStatus(data);
    });
  }
  

  // --- API Methods ---

  async startProxy(): Promise<void> {
    await fetch(`${API_BASE_URL}/api/proxy/start`, { method: 'POST' });
    // Status updates will be received via WebSocket
  }

  async stopProxy(): Promise<void> {
    await fetch(`${API_BASE_URL}/api/proxy/stop`, { method: 'POST' });
    // Status updates will be received via WebSocket
  }

  async getInitialTraffic(): Promise<InterceptedTraffic[]> {
    const response = await fetch(`${API_BASE_URL}/api/proxy/traffic?limit=200`);
    if (!response.ok) {
      throw new Error('Failed to fetch initial traffic');
    }
    return response.json();
  }
  
  async clearTraffic(): Promise<{ cleared_items: number }> {
    const response = await fetch(`${API_BASE_URL}/api/proxy/traffic`, { method: 'DELETE' });
    if (!response.ok) {
        throw new Error('Failed to clear traffic');
    }
    return response.json();
  }
  
  // Disconnect socket for cleanup
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
    }
  }
}

// Export a singleton instance
export const proxyManager = new ProxyManager();
