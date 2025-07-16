// galdr/interceptor/frontend/src/renderer/components/raider/Raider.tsx
// The main UI for the Raider Automated Attack module.

import React, { useState } from 'react';
import { Bug, Play, Target, List } from 'lucide-react';

export const Raider: React.FC = () => {
  const [baseRequest, setBaseRequest] = useState('GET /api/users/§payload§ HTTP/1.1\nHost: example.com\nUser-Agent: Galdr/3.0');
  const [payloads, setPayloads] = useState('1\n2\nadmin\n...\n');

  // Placeholder for state and handlers
  const handleStartAttack = () => {
    alert("Starting attack... (functionality to be implemented)");
    console.log("Base Request:", baseRequest);
    console.log("Payloads:", payloads.split('\n').filter(p => p));
  };

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white p-4 gap-4">
      <div className="flex items-center gap-3 text-2xl font-bold">
        <Bug size={28} className="text-red-400"/>
        <h1>Raider - Automated Attacks</h1>
      </div>
      
      {/* Configuration Panes */}
      <div className="flex-1 grid grid-cols-2 gap-4 overflow-hidden">
        {/* Request Template Pane */}
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><Target size={18} /> Base Request Template</h2>
            <p className="text-xs text-gray-400">Mark payload positions with the §payload§ marker.</p>
            <textarea 
                value={baseRequest} 
                onChange={e => setBaseRequest(e.target.value)} 
                className="flex-1 bg-gray-900 rounded-md p-2 font-mono text-sm border border-gray-700"
            />
        </div>
        
        {/* Payloads Pane */}
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><List size={18} /> Payload List</h2>
            <p className="text-xs text-gray-400">Enter one payload per line.</p>
            <textarea 
                value={payloads} 
                onChange={e => setPayloads(e.target.value)}
                className="flex-1 bg-gray-900 rounded-md p-2 font-mono text-sm border border-gray-700"
            />
        </div>
      </div>
      
      {/* Controls */}
      <div className="flex justify-end">
          <button onClick={handleStartAttack} className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg font-bold hover:bg-red-500">
            <Play size={18} /> Launch Attack
          </button>
      </div>

      {/* Results Table (Placeholder) */}
      <div className="h-1/3 border border-gray-700 rounded-md bg-gray-900">
        <div className="p-2 font-bold text-center text-gray-400">Attack Results Will Appear Here</div>
      </div>
    </div>
  );
};
