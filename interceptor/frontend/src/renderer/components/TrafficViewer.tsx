// galdr/interceptor/frontend/src/renderer/components/TrafficViewer.tsx
// --- FINALIZED ---
// This version is enhanced with the "Send to Replay Forge" functionality.

import React, { useState, useMemo, useEffect } from 'react';
import { Search, Trash2, Send, Pause, Play, CheckCircle, AlertTriangle, Clock, Shield } from 'lucide-react';
import { InterceptedTraffic } from '../types/traffic';
import { RequestResponseViewer } from './RequestResponseViewer';

interface TrafficViewerProps {
  traffic: InterceptedTraffic[];
  selectedRequest: InterceptedTraffic | null;
  onSelectRequest: (request: InterceptedTraffic | null) => void;
  onClearTraffic: () => void;
  // NEW PROP: Callback to send the selected request to the parent component (App.tsx).
  onSendToReplayForge: (request: InterceptedTraffic) => void;
}

// Helper to determine text color based on HTTP status
const getStatusColor = (status?: number) => {
    if (!status) return 'text-gray-400';
    if (status >= 500) return 'text-red-400';
    if (status >= 400) return 'text-yellow-400';
    if (status >= 300) return 'text-blue-400';
    return 'text-green-400';
};

export const TrafficViewer: React.FC<TrafficViewerProps> = ({
  traffic,
  selectedRequest,
  onSelectRequest,
  onClearTraffic,
  onSendToReplayForge,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isLive, setIsLive] = useState(true);

  // When a user selects a request, we pause the live feed to prevent the list from shifting.
  const handleSelectRequest = (request: InterceptedTraffic) => {
    onSelectRequest(request);
    setIsLive(false); 
  };
  
  // Memoize the filtered list for performance.
  const filteredTraffic = useMemo(() => {
    // If not live, we use the traffic list as-is. If live, we reverse it to show newest first.
    const sourceTraffic = isLive ? [...traffic].reverse() : traffic;
    if (!searchTerm) return sourceTraffic;
    return sourceTraffic.filter(item =>
      item.url.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [traffic, searchTerm, isLive]);
  

  return (
    <div className="h-full grid grid-cols-2 bg-gray-800 text-gray-200">
      {/* Left Pane: Traffic List */}
      <div className="flex flex-col border-r border-gray-700">
        <div className="p-2 border-b border-gray-700 bg-gray-900 flex items-center gap-2">
            <div className="relative flex-grow">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search URL..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 bg-gray-700 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
            </div>
            <button onClick={() => setIsLive(!isLive)} title={isLive ? 'Pause Live Traffic' : 'Resume Live Traffic'} className={`p-2 hover:bg-gray-700 rounded-md ${isLive ? 'text-green-400' : 'text-gray-400'}`}>
                {isLive ? <Play size={16}/> : <Pause size={16}/>}
            </button>
            <button onClick={onClearTraffic} title="Clear Traffic" className="p-2 text-red-400 hover:bg-gray-700 rounded-md">
                <Trash2 size={16}/>
            </button>
        </div>
        <div className="flex-1 overflow-y-auto">
            {filteredTraffic.map(item => (
                <div key={item.id} onClick={() => handleSelectRequest(item)}
                    className={`p-3 cursor-pointer border-l-4 ${selectedRequest?.id === item.id ? 'border-blue-500 bg-gray-700' : 'border-transparent hover:bg-gray-700/50'}`}>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="font-bold">{item.method}</span>
                        <span className={getStatusColor(item.response_status)}>{item.response_status || '...'}</span>
                    </div>
                    <div className="text-sm truncate text-gray-300" title={item.url}>
                        {item.host}{item.path}
                    </div>
                </div>
            ))}
        </div>
      </div>
      
      {/* Right Pane: Request/Response Details */}
      <div className="flex flex-col">
        {selectedRequest ? (
            <>
                <div className="p-2 border-b border-gray-700 bg-gray-900 flex justify-end">
                    {/* THIS IS THE NEW BUTTON */}
                    {/* It's only visible when a request is selected and triggers the callback. */}
                    <button 
                      onClick={() => onSendToReplayForge(selectedRequest)} 
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm font-semibold hover:bg-blue-500"
                    >
                        <Send size={14} />
                        Send to Replay Forge
                    </button>
                </div>
                {/* We use a simple placeholder viewer here. This can be expanded. */}
                <div className="p-4 flex-1 overflow-auto font-mono text-xs">
                    <h3 className="font-bold text-base text-white mb-2">{selectedRequest.method} {selectedRequest.url}</h3>
                    <div className="text-gray-400">HEADERS</div>
                    <pre className="p-2 bg-gray-900/50 rounded mt-1 mb-4">{JSON.stringify(JSON.parse(selectedRequest.request_headers || '{}'), null, 2)}</pre>
                    <div className="text-gray-400">BODY</div>
                    <pre className="p-2 bg-gray-900/50 rounded mt-1">{selectedRequest.request_body || '(No Body)'}</pre>
                </div>
            </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">Select a request to view details.</div>
        )}
      </div>
    </div>
  );
};
