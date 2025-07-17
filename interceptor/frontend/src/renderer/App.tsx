// galdr/interceptor/frontend/src/renderer/App.tsx
// --- FINALIZED & CORRECTED ---
// This version has the correct component structure and handles state transfer
// for both Replay Forge and Raider.

import React, { useState, useEffect } from 'react';

// Core Components
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { TrafficViewer } from './components/TrafficViewer';
import { ReplayForge } from './components/replay_forge/ReplayForge';
import { Portal } from './components/portal/Portal';
import { Raider } from './components/raider/Raider';

// Services
import { proxyManager } from './services/ProxyManager';

// Types
import { InterceptedTraffic, ProxyStatus } from './types/traffic';
import { SendRequestData } from './services/ReplayForgeManager'; // Raider will use this type

// This type definition now includes all our planned modules for type safety.
type ViewType = 'dashboard' | 'traffic' | 'recon' | 'crawler' | 'spider' | 'replay_forge' | 'raider' | 'mirror' | 'entropy' | 'cipher' | 'accomplice' | 'portal' | 'config';

export const App: React.FC = () => {
  // --- STATE MANAGEMENT ---
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [traffic, setTraffic] = useState<InterceptedTraffic[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<InterceptedTraffic | null>(null);
  const [proxyStatus, setProxyStatus] = useState<ProxyStatus>('stopped');
  
  // State for passing data to other modules when switching views
  const [requestForReplay, setRequestForReplay] = useState<any | null>(null);
  const [requestForRaider, setRequestForRaider] = useState<any | null>(null);

  // --- LIFECYCLE HOOKS ---
  useEffect(() => {
    // Setup event listeners for the proxy service
    proxyManager.onStatusUpdate = (status) => setProxyStatus(status);
    proxyManager.onNewTraffic = (newTraffic) => {
        setTraffic(prev => [newTraffic, ...prev]);
    };
    proxyManager.onError = (error) => console.error("Backend Service Error:", error);

    // Load initial traffic when the app starts
    proxyManager.getInitialTraffic()
      .then(initialTraffic => setTraffic(initialTraffic.reverse())) // Show oldest first
      .catch(err => console.error("Could not load initial traffic:", err));

    return () => {
      proxyManager.disconnect();
    };
  }, []); // Empty dependency array ensures this effect runs only once.

  // Effects to 'consume' the request data once the view switches away
  useEffect(() => {
      if(currentView !== 'replay_forge' && requestForReplay !== null) {
          setRequestForReplay(null);
      }
      if(currentView !== 'raider' && requestForRaider !== null) {
          setRequestForRaider(null);
      }
  }, [currentView, requestForReplay, requestForRaider])


  // --- EVENT HANDLERS ---
  const handleStartProxy = () => proxyManager.startProxy().catch(console.error);
  const handleStopProxy = () => proxyManager.stopProxy().catch(console.error);
  const handleClearTraffic = async () => {
    await proxyManager.clearTraffic();
    setTraffic([]);
    setSelectedRequest(null);
  };
  
  const handleSendToReplayForge = (trafficItem: InterceptedTraffic) => {
    const replayRequestData = {
      method: trafficItem.method,
      url: trafficItem.url,
      headers: JSON.parse(trafficItem.request_headers || '{}'),
      body: trafficItem.request_body || '',
    };
    setRequestForReplay(replayRequestData);
    setCurrentView('replay_forge');
  };
  
  // Correctly defined handler for sending data to Raider
  const handleSendToRaider = (requestData: SendRequestData) => {
      setRequestForRaider(requestData);
      setCurrentView('raider');
  };

  // --- VIEW RENDERER ---
  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard proxyStatus={proxyStatus} onStartProxy={handleStartProxy} onStopProxy={handleStopProxy} trafficCount={traffic.length} />;
      case 'traffic':
        return (
          <TrafficViewer 
            traffic={traffic}
            selectedRequest={selectedRequest}
            onSelectRequest={setSelectedRequest}
            onClearTraffic={handleClearTraffic}
            onSendToReplayForge={handleSendToReplayForge}
          />
        );
      case 'replay_forge':
        return <ReplayForge initialRequest={requestForReplay} onSendToRaider={handleSendToRaider} />;
      case 'portal':
        return <Portal />;
      case 'raider':
        return <Raider initialRequest={requestForRaider} />;
      // Default case for any views not yet implemented.
      default:
        return <div className="p-4"><p>View not yet implemented: {currentView}</p></div>;
    }
  };

  // --- MAIN COMPONENT RENDER ---
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
