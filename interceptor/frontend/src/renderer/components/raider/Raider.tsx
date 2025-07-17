// galdr/interceptor/frontend/src/renderer/components/raider/Raider.tsx
// --- FINALIZED & FUNCTIONAL ---
// This version is a fully functional UI for the Sniper attack.

import React, { useState, useEffect, useCallback } from 'react';
import { Bug, Play, Target, List, Square, Loader } from 'lucide-react';
import { raiderManager, RaiderAttackRequest } from '../../services/RaiderManager';
// We'll also need our main WebSocket connection to listen for results
import { proxyManager } from '../../services/ProxyManager'; // Assuming this has the main socket

// Define the type for a single result row
interface RaiderResult {
    request_number: number;
    payload: string;
    status: number;
    length: number;
    duration: number;
}

export const Raider: React.FC = ({ initialRequest }) => {
    // UI and Configuration State
    const [baseRequest, setBaseRequest] = useState<any | null>(initialRequest);
    const [payloads, setPayloads] = useState<string>("1\nadmin\ntest\nuser\nroot");
    
    // Attack State
    const [activeAttackId, setActiveAttackId] = useState<string | null>(null);
    const [isAttacking, setIsAttacking] = useState(false);
    const [results, setResults] = useState<RaiderResult[]>([]);
    
    const handleLaunchAttack = useCallback(async () => {
        if (!baseRequest) {
            alert("Base request is not set.");
            return;
        }

        const attackData: RaiderAttackRequest = {
            attack_type: 'sniper',
            base_request_template: baseRequest,
            config: {
                payloads: payloads.split('\n').filter(p => p.trim() !== ''),
            },
        };

        setIsAttacking(true);
        setResults([]); // Clear old results
        try {
            const { attack_id } = await raiderManager.launchAttack(attackData);
            setActiveAttackId(attack_id);
            // After launching, tell the WebSocket server we are interested in updates for this attack.
            proxyManager.socket.emit('join_raider_room', { attack_id });

        } catch (e) {
            console.error("Failed to launch attack", e);
            alert(`Error: ${e.message}`);
            setIsAttacking(false);
        }
    }, [baseRequest, payloads]);

    const handleStopAttack = useCallback(async () => {
        if (!activeAttackId) return;
        try {
            await raiderManager.stopAttack(activeAttackId);
            setIsAttacking(false);
            setActiveAttackId(null);
        } catch(e) { console.error("Failed to stop attack", e); }
    }, [activeAttackId]);
    
    // Effect to listen for real-time results
    useEffect(() => {
        const handleResult = (newResult: RaiderResult) => {
            // Only update if the result is for our active attack
            if (newResult.attack_id === activeAttackId) {
                setResults(prev => [...prev, newResult]);
            }
        };
        const handleStatus = ({ attack_id, status }) => {
            if (attack_id === activeAttackId && status === 'completed') {
                setIsAttacking(false);
                setActiveAttackId(null);
            }
        }

        proxyManager.socket.on('raider_result_update', handleResult);
        proxyManager.socket.on('raider_attack_status', handleStatus);
        
        return () => {
            // Clean up listeners when component unmounts
            proxyManager.socket.off('raider_result_update', handleResult);
            proxyManager.socket.off('raider_attack_status', handleStatus);
        }
    }, [activeAttackId]); // Re-run effect if the active attack ID changes

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white p-4 gap-4">
      {/* Header and Controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3 text-2xl font-bold">
          <Bug size={28} className="text-red-400"/>
          <h1>Raider - Automated Attacks</h1>
        </div>
        {isAttacking ? (
             <button onClick={handleStopAttack} className="flex items-center gap-2 px-6 py-2 bg-gray-600 text-white rounded-lg font-bold hover:bg-gray-500">
                <Square size={18} /> Stop Attack
             </button>
        ) : (
            <button onClick={handleLaunchAttack} className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg font-bold hover:bg-red-500">
              <Play size={18} /> Launch Attack
            </button>
        )}
      </div>
      
      {/* Configuration Panes */}
      <div className="flex-1 grid grid-cols-2 gap-4 overflow-hidden" style={{ minHeight: '200px' }}>
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><Target size={18} /> Base Request</h2>
            <textarea 
                value={baseRequest ? JSON.stringify(baseRequest, null, 2) : "Send a request from Replay Forge to Raider."}
                readOnly 
                className="flex-1 bg-gray-900 rounded-md p-2 font-mono text-sm border border-gray-700 text-gray-400"
            />
        </div>
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><List size={18} /> Payload List</h2>
            <textarea 
                value={payloads} 
                onChange={e => setPayloads(e.target.value)}
                className="flex-1 bg-gray-900 rounded-md p-2 font-mono text-sm border border-gray-700"
            />
        </div>
      </div>
      
      {/* Results Table */}
      <div className="h-2/5 flex flex-col border border-gray-700 rounded-md bg-gray-900">
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm text-left">
            <thead className="sticky top-0 bg-gray-800">
              <tr>
                <th className="p-2">#</th><th className="p-2">Payload</th><th className="p-2">Status</th><th className="p-2">Length</th><th className="p-2">Duration (ms)</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.request_number} className="border-b border-gray-800 hover:bg-gray-700/50">
                    <td className="p-2 text-gray-400">{r.request_number}</td><td className="p-2 font-mono">{r.payload}</td><td className="p-2">{r.status}</td><td className="p-2">{r.length}</td><td className="p-2">{r.duration}</td>
                </tr>
              ))}
               {isAttacking && !results.length && <tr><td colSpan={5} className="text-center p-4"><Loader className="animate-spin inline-block"/> Waiting for first result...</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="p-2 text-xs border-t border-gray-700 text-gray-400">
            Status: {isAttacking ? "Running" : (activeAttackId ? "Stopped" : "Idle")} | Displaying {results.length} results.
        </div>
      </div>
    </div>
  );
