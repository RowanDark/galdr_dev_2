// galdr/interceptor/frontend/src/renderer/services/ProxyManager.ts
// --- REFACTORED ---
// This class now uses `socket.io-client` for robust, event-based communication.
// API calls now point to the new FastAPI server on port 8000.

import { io, Socket } from 'socket.io-client';
import { InterceptedTraffic, ProxyStatus } from '../types/traffic'; // Assuming types are defined

const API_BASE_URL = 'http://localhost:8000';

class ProxyManager {
  private socket: Socket;

  // Define clear event handlers for better state management in components
  public onStatusUpdate: ((status: ProxyStatus) => void) | null = null;
  public onNewTraffic: ((traffic: InterceptedTraffic) => void) | null = null;
  public onError: ((error: string) => void) | null = null;

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
export const proxyManager = new ProxyManager();```

**File:** `galdr/interceptor/frontend/src/renderer/App.tsx`
```tsx
// galdr/interceptor/frontend/src/renderer/App.tsx
// --- REFACTORED ---
// Removed `Cartographer` and `ReplayForge` components.
// Simplified state management and now uses the singleton `proxyManager`.

import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { TrafficViewer } from './components/TrafficViewer';
// We will add the real ReplayForge component back here when we build it
// import { ReplayForge } from './components/ReplayForge'; 
import { Recon } from './components/Recon';
import { PassiveCrawler } from './components/PassiveCrawler';
import { ActiveSpider } from './components/ActiveSpider';
import { Configuration } from './components/Configuration';

// Service managers
import { proxyManager } from './services/ProxyManager';
// ... import other managers

import { InterceptedTraffic, ProxyStatus } from './types/traffic';

// Define the available views. Note the removal of the hallucinated modules.
type ViewType = 'dashboard' | 'traffic' | 'recon' | 'crawler' | 'spider' | 'replay_forge' | 'config';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [traffic, setTraffic] = useState<InterceptedTraffic[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<InterceptedTraffic | null>(null);
  const [proxyStatus, setProxyStatus] = useState<ProxyStatus>('stopped');

  useEffect(() => {
    // --- Setup Event Handlers for ProxyManager ---
    proxyManager.onStatusUpdate = (status) => setProxyStatus(status);
    proxyManager.onNewTraffic = (newTraffic) => {
        // We add new traffic to the top of the list for a real-time feel
        setTraffic(prev => [newTraffic, ...prev.slice(0, 999)]);
    };
    proxyManager.onError = (error) => console.error("Backend Error:", error);

    // Load initial traffic data when the component mounts
    proxyManager.getInitialTraffic()
        .then(initialTraffic => setTraffic(initialTraffic))
        .catch(err => console.error("Could not load initial traffic:", err));
    
    // Cleanup on unmount
    return () => {
      proxyManager.disconnect();
    };
  }, []); // Empty dependency array ensures this runs only once on mount

  const handleStartProxy = () => proxyManager.startProxy().catch(console.error);
  const handleStopProxy = () => proxyManager.stopProxy().catch(console.error);

  const handleClearTraffic = async () => {
    try {
        await proxyManager.clearTraffic();
        setTraffic([]);
        setSelectedRequest(null);
    } catch(err) {
        console.error("Failed to clear traffic:", err);
    }
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard proxyStatus={proxyStatus} onStartProxy={handleStartProxy} onStopProxy={handleStopProxy} trafficCount={traffic.length} />;
      case 'traffic':
        return <TrafficViewer traffic={traffic} selectedRequest={selectedRequest} onSelectRequest={setSelectedRequest} onClearTraffic={handleClearTraffic} />;
      // --- Add cases for Recon, Crawler, Spider as they are built out ---
      // case 'replay_forge':
      //   return <ReplayForge initialRequest={selectedRequest} />; // Example
      default:
        return <Dashboard proxyStatus={proxyStatus} onStartProxy={handleStartProxy} onStopProxy={handleStopProxy} trafficCount={traffic.length} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar
        currentView={currentView}
        onViewChange={setCurrentView}
        proxyStatus={proxyStatus}
        trafficCount={traffic.length}
      />
      <main className="flex-1 overflow-hidden bg-gray-800">
        {renderCurrentView()}
      </main>
    </div>
  );
};
