// galdr/interceptor/frontend/src/renderer/App.tsx
// --- FINALIZED & CORRECTED ---
// This version properly handles the state transfer to ReplayForge, completing the workflow.

import React, { useState, useEffect } from 'react';

// Core Components
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { TrafficViewer } from './components/TrafficViewer';
import { ReplayForge } from './components/replay_forge/ReplayForge';

// Services
import { proxyManager } from './services/ProxyManager';

// Types
import { InterceptedTraffic, ProxyStatus } from './types/traffic';


// This type definition now includes all our planned modules for type safety.
type ViewType = 'dashboard' | 'traffic' | 'recon' | 'crawler' | 'spider' | 'replay_forge' | 'raider' | 'mirror' | 'entropy' | 'cipher' | 'accomplice' | 'portal' | 'config';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [traffic, setTraffic] = useState<InterceptedTraffic[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<InterceptedTraffic | null>(null);
  const [proxyStatus, setProxyStatus] = useState<ProxyStatus>('stopped');
  
  // NEW: This state holds the request data while we switch views to Replay Forge.
  const [requestToSend, setRequestToSend] = useState<any | null>(null);

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

  // --- Handlers for App-level Actions ---
  const handleStartProxy = () => proxyManager.startProxy().catch(console.error);
  const handleStopProxy = () => proxyManager.stopProxy().catch(console.error);
  const handleClearTraffic = async () => {
    await proxyManager.clearTraffic();
    setTraffic([]);
    setSelectedRequest(null);
  };

  // NEW: This is the core logic for the workflow.
  // It receives the request from TrafficViewer, formats it, sets it in state, and switches the view.
  const handleSendToReplayForge = (trafficItem: InterceptedTraffic) => {
    const replayRequestData = {
      method: trafficItem.method,
      url: trafficItem.url,
      headers: JSON.parse(trafficItem.request_headers || '{}'),
      body: trafficItem.request_body || '',
    };
    setRequestToSend(replayRequestData);
    setCurrentView('replay_forge');
  };
  
  // This effect ensures that once a request is passed to Replay Forge, it's 'consumed'
  // so it isn't sent again if the user just switches back to the view.
  useEffect(() => {
      if(currentView !== 'replay_forge' && requestToSend !== null) {
          setRequestToSend(null);
      }
  }, [currentView, requestToSend])


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
            onSendToReplayForge={handleSendToReplayForge} // Pass the handler down
          />
        );
      case 'replay_forge':
        // The ReplayForge component receives the request data via props.
        return <ReplayForge initialRequest={requestToSend} />;
      
      // We will add other views here as we build them.
      
      default:
        return <p>View not yet implemented: {currentView}</p>;
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
