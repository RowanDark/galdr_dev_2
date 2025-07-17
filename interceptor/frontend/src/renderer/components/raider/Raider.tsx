// galdr/interceptor/frontend/src/renderer/components/raider/Raider.tsx
// --- FINALIZED & FUNCTIONAL ---

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Bug, Play, Target, List, Square, Loader, ChevronUp, ChevronDown } from 'lucide-react';
import { raiderManager, RaiderAttackRequest } from '../../services/RaiderManager';
import { proxyManager, RaiderResultEvent, RaiderStatusEvent } from '../../services/ProxyManager';
import { SendRequestData } from '../../services/ReplayForgeManager';

interface RaiderProps {
    initialRequest?: SendRequestData | null;
}

export const Raider: React.FC<RaiderProps> = ({ initialRequest }) => {
    // --- State Management ---
    const [baseRequest, setBaseRequest] = useState<SendRequestData | null>(initialRequest);
    const [payloads, setPayloads] = useState<string>("1\nadmin\ntest\nuser\nroot");
    const [activeAttackId, setActiveAttackId] = useState<string | null>(null);
    const [isAttacking, setIsAttacking] = useState(false);
    const [results, setResults] = useState<RaiderResultEvent[]>([]);
    
    // State for the results table sorting
    const [sortConfig, setSortConfig] = useState<{ key: keyof RaiderResultEvent; direction: 'asc' | 'desc' } | null>(null);

    // If a new request is passed via props, update the state
    useEffect(() => {
        if (initialRequest) {
            setBaseRequest(initialRequest);
        }
    }, [initialRequest]);
    
    // --- Real-time Event Listeners ---
    useEffect(() => {
        // Handler for a new result from the backend
        const handleNewResult = (newResult: RaiderResultEvent) => {
            if (newResult.attack_id === activeAttackId) {
                setResults(prev => [...prev, newResult]);
            }
        };

        // Handler for when an attack's status changes (e.g., 'completed')
        const handleStatusChange = (status: RaiderStatusEvent) => {
            if (status.attack_id === activeAttackId) {
                setIsAttacking(false);
                setActiveAttackId(null);
            }
        };

        // Subscribe to events
        proxyManager.onRaiderResult = handleNewResult;
        proxyManager.onRaiderStatus = handleStatusChange;

        // Cleanup function to unsubscribe when the component unmounts
        return () => {
            proxyManager.onRaiderResult = null;
            proxyManager.onRaiderStatus = null;
            if (activeAttackId) {
                proxyManager.socket.emit('leave_raider_room', { attack_id: activeAttackId });
            }
        };
    }, [activeAttackId]); // This effect re-subscribes if the attack ID changes

    // --- Action Handlers ---
    const handleLaunchAttack = useCallback(async () => {
        if (!baseRequest) return alert("Base request is not set.");
        const payloadList = payloads.split('\n').filter(p => p.trim() !== '');
        if (payloadList.length === 0) return alert("Payload list is empty.");

        const attackData: RaiderAttackRequest = {
            attack_type: 'sniper',
            base_request_template: baseRequest,
            config: { payloads: payloadList },
        };

        setIsAttacking(true);
        setResults([]);
        try {
            const { attack_id } = await raiderManager.launchAttack(attackData);
            setActiveAttackId(attack_id);
            // Tell the backend we want results for THIS attack
            proxyManager.socket.emit('join_raider_room', { attack_id });
        } catch (e) {
            console.error(e);
            alert(`Error launching attack: ${(e as Error).message}`);
            setIsAttacking(false);
        }
    }, [baseRequest, payloads]);

    const handleStopAttack = useCallback(async () => {
        if (!activeAttackId) return;
        try {
            await raiderManager.stopAttack(activeAttackId);
            setIsAttacking(false);
            proxyManager.socket.emit('leave_raider_room', { attack_id: activeAttackId });
            setActiveAttackId(null);
        } catch(e) { console.error("Failed to stop attack", e); }
    }, [activeAttackId]);

    // --- Memoized and Sorted Results ---
    const sortedResults = useMemo(() => {
        let sortableItems = [...results];
        if (sortConfig !== null) {
            sortableItems.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
                if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        return sortableItems;
    }, [results, sortConfig]);
    
    const requestSort = (key: keyof RaiderResultEvent) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const getSortIndicator = (key: keyof RaiderResultEvent) => {
        if (!sortConfig || sortConfig.key !== key) return null;
        return sortConfig.direction === 'asc' ? <ChevronUp size={14}/> : <ChevronDown size={14}/>;
    };


    return (
    <div className="h-full flex flex-col bg-gray-800 text-white p-4 gap-4">
      {/* Header & Controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3 text-2xl font-bold"><Bug size={28} className="text-red-400"/><h1>Raider Attacks</h1></div>
        {!isAttacking ? (
          <button onClick={handleLaunchAttack} disabled={!baseRequest} className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg font-bold hover:bg-red-500 disabled:bg-gray-600">
            <Play size={18}/> Launch Attack
          </button>
        ) : (
          <button onClick={handleStopAttack} className="flex items-center gap-2 px-6 py-2 bg-gray-600 text-white rounded-lg font-bold hover:bg-gray-500">
            <Square size={18}/> Stop Attack
          </button>
        )}
      </div>

      {/* Configuration Panes */}
      <div className="flex-1 grid grid-cols-2 gap-4 overflow-hidden min-h-[200px]">
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><Target size={18}/> Base Request</h2>
            <div className="flex-1 bg-gray-900 rounded-md p-2 font-mono text-xs border border-gray-700 overflow-auto">
                <pre>{baseRequest ? JSON.stringify(baseRequest, null, 2) : "Send a request from Replay Forge to begin..."}</pre>
            </div>
        </div>
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><List size={18}/> Payloads ({payloads.split('\n').filter(p=>p).length})</h2>
            <textarea value={payloads} onChange={e => setPayloads(e.target.value)} className="flex-1 bg-gray-900 rounded-md p-2 font-mono text-sm border border-gray-700 resize-none"/>
        </div>
      </div>
      
      {/* Results Table */}
      <div className="h-2/5 flex flex-col border border-gray-700 rounded-md bg-gray-900">
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm text-left table-fixed">
            <thead className="sticky top-0 bg-gray-800"><tr className="cursor-pointer">
              <th className="p-2 w-1/12" onClick={() => requestSort('request_number')}># {getSortIndicator('request_number')}</th>
              <th className="p-2 w-5/12" onClick={() => requestSort('payload')}>Payload {getSortIndicator('payload')}</th>
              <th className="p-2 w-2/12" onClick={() => requestSort('status')}>Status {getSortIndicator('status')}</th>
              <th className="p-2 w-2/12" onClick={() => requestSort('length')}>Length {getSortIndicator('length')}</th>
              <th className="p-2 w-2/12" onClick={() => requestSort('duration')}>Duration {getSortIndicator('duration')}</th>
            </tr></thead>
            <tbody>
              {sortedResults.map((r, i) => (
                <tr key={i} className="border-t border-gray-800 hover:bg-gray-700/50">
                    <td className="p-2 text-gray-400">{r.request_number}</td><td className="p-2 font-mono truncate">{r.payload}</td><td className="p-2">{r.status}</td><td className="p-2">{r.length} B</td><td className="p-2">{r.duration} ms</td>
                </tr>
              ))}
               {isAttacking && results.length === 0 && <tr><td colSpan={5} className="text-center p-4"><Loader className="animate-spin inline-block mr-2"/>Waiting for results...</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="p-1 text-xs border-t border-gray-700 text-gray-400 text-center">
            Status: {isAttacking ? `Attacking... (${results.length} requests sent)` : activeAttackId ? "Stopped" : "Idle"}
        </div>
      </div>
    </div>
  );
};
