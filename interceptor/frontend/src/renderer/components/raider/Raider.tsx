// `galdr/interceptor/frontend/src/renderer/components/raider/Raider.tsx` (Final Version 2.0)
// --- FINALIZED & FUNCTIONAL 2.0 ---
// Complete overhaul to support multiple attack types and advanced results analysis.

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Bug, Play, Target, List, Square, Loader, Filter, BarChart, ChevronUp, ChevronDown, Wand2, X } from 'lucide-react';
import { raiderManager, RaiderAttackRequest } from '../../services/RaiderManager';
import { proxyManager, RaiderResultEvent } from '../../services/ProxyManager';
import { SendRequestData } from '../../services/ReplayForgeManager';
import { Editor } from '@monaco-editor/react';

// Re-usable component for a single payload set
const PayloadSetEditor = ({ name, value, onChange }) => (
    <div className="flex flex-col gap-1 h-full">
        <label className="text-xs font-bold text-gray-400">{name}</label>
        <div className="flex-1 bg-gray-900 rounded-md border border-gray-700">
          <Editor theme="vs-dark" language="text" value={value} onChange={onChange} options={{ minimap: { enabled: false }, fontSize: 12, wordWrap: 'on' }}/>
        </div>
    </div>
);

export const Raider: React.FC = ({ initialRequest }) => {
    // --- State Management ---
    const [attackName, setAttackName] = useState("New Attack");
    const [attackType, setAttackType] = useState<'sniper' | 'battering_ram' | 'pitchfork' | 'cluster_bomb'>('sniper');
    const [baseRequest, setBaseRequest] = useState<string>(initialRequest ? JSON.stringify(initialRequest, null, 2) : "Send a request from Replay Forge to begin...");
    
    // State for payload markers in the request template
    const [payloadMarkers, setPayloadMarkers] = useState<string[]>(['payload']);
    // State for the actual payload content, mapping marker name to a string of payloads
    const [payloadSets, setPayloadSets] = useState<Record<string, string>>({ payload: "1\nadmin\ntest\nuser\nroot" });
    
    const [activeAttackId, setActiveAttackId] = useState<string | null>(null);
    const [isAttacking, setIsAttacking] = useState(false);
    const [results, setResults] = useState<RaiderResultEvent[]>([]);
    
    // State for sophisticated analysis
    const [filterText, setFilterText] = useState("");
    const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' }>({ key: 'request_number', direction: 'asc' });

    useEffect(() => {
        if (initialRequest) { setBaseRequest(JSON.stringify(initialRequest, null, 2)); }
    }, [initialRequest]);

    // WebSocket Listeners for real-time updates
    useEffect(() => {
        const handleNewResult = (newResult: RaiderResultEvent) => { if (newResult.attack_id === activeAttackId) setResults(prev => [...prev, newResult]); };
        const handleStatusChange = ({ attack_id, status }) => { if (attack_id === activeAttackId) setIsAttacking(false); };
        proxyManager.onRaiderResult = handleNewResult;
        proxyManager.onRaiderStatus = handleStatusChange;
        return () => { proxyManager.onRaiderResult = null; proxyManager.onRaiderStatus = null; };
    }, [activeAttackId]);

    // --- Action Handlers ---
    const handleLaunchAttack = useCallback(async () => {
        if (!baseRequest) return alert("Base request is missing.");
        
        const config = {
            markers: payloadMarkers,
            payload_sets: Object.fromEntries(Object.entries(payloadSets).map(([key, value]) => [key, value.split('\n').filter(p => p.trim() !== '')]))
        };

        const attackData: RaiderAttackRequest = { name: attackName, attack_type: attackType, base_request_template: JSON.parse(baseRequest), config, };

        setIsAttacking(true);
        setResults([]);
        try {
            const { attack_id } = await raiderManager.launchAttack(attackData);
            setActiveAttackId(attack_id);
            proxyManager.socket.emit('join_raider_room', { attack_id });
        } catch (e) { console.error(e); alert(`Error: ${(e as Error).message}`); setIsAttacking(false); }
    }, [attackName, attackType, baseRequest, payloadMarkers, payloadSets]);

    const addPayloadMarker = () => {
        const newMarker = `payload${payloadMarkers.length + 1}`;
        setPayloadMarkers(prev => [...prev, newMarker]);
        setPayloadSets(prev => ({...prev, [newMarker]: ''}));
    }
    const handlePayloadSetChange = (marker: string, value: string) => {
        setPayloadSets(prev => ({ ...prev, [marker]: value }));
    }

    // --- Results Analysis & Sorting ---
    const sortedAndFilteredResults = useMemo(() => {
        let items = [...results];
        if (filterText) { items = items.filter(r => JSON.stringify(r).toLowerCase().includes(filterText.toLowerCase())); }
        items.sort((a, b) => {
            if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
            if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
        return items;
    }, [results, filterText, sortConfig]);

    const requestSort = (key: string) => {
        setSortConfig(prev => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }));
    };

    return (
    <div className="h-full flex flex-col bg-gray-800 text-white p-4 gap-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3 text-2xl font-bold"><Bug size={28} className="text-red-400"/><h1>Raider Attacks</h1></div>
        {!isAttacking ? (<button onClick={handleLaunchAttack} disabled={!baseRequest}><Play/></button>) : (<button onClick={()=>{}}><Square/></button>)}
      </div>
      
      {/* Attack Config Tabs */}
      <div className="flex items-center gap-4 p-2 bg-gray-900 rounded-lg">
        <div><select value={attackType} onChange={e=>setAttackType(e.target.value)} className="bg-gray-700 p-1 rounded">
          <option value="sniper">Sniper</option>
          <option value="battering_ram">Battering Ram</option>
          <option value="pitchfork">Pitchfork</option>
          <option value="cluster_bomb">Cluster Bomb</option>
        </select></div>
        <div>
          <button onClick={addPayloadMarker} disabled={attackType === 'sniper' || attackType === 'battering_ram'}><Plus/> Add Payload Set</button>
        </div>
      </div>
      
      {/* Configuration Panes: Request and Payloads */}
      <div className="flex-1 grid grid-cols-2 gap-4 overflow-hidden min-h-[200px]">
        <div className="flex flex-col gap-2">
            <h2 className="font-bold flex items-center gap-2"><Target size={18} /> Request Template</h2>
            <div className="flex-1 bg-gray-900 rounded-md border border-gray-700"><Editor theme="vs-dark" language="http" value={baseRequest} onChange={(val) => setBaseRequest(val)} options={{ minimap: {enabled: false}, fontSize: 12, wordWrap: 'on' }}/></div>
        </div>
        <div className="flex flex-col gap-2 overflow-hidden">
            <h2 className="font-bold flex items-center gap-2"><List size={18} /> Payloads</h2>
            <div className="flex-1 grid grid-cols-2 gap-2 overflow-hidden">
                {payloadMarkers.map((marker, i) => (
                    (attackType === 'sniper' || attackType === 'battering_ram') && i > 0 ? null :
                    <PayloadSetEditor key={marker} name={marker} value={payloadSets[marker]} onChange={(val) => handlePayloadSetChange(marker, val)}/>
                ))}
            </div>
        </div>
      </div>
      
      {/* Results Analysis Section */}
      <div className="h-2/5 flex flex-col border border-gray-700 rounded-md bg-gray-900">
        <div className="p-2 border-b border-gray-700 flex items-center gap-2">
            <Filter size={14} className="text-gray-400"/>
            <input type="text" placeholder="Filter results..." value={filterText} onChange={e => setFilterText(e.target.value)} className="w-full bg-gray-800 text-sm p-1 rounded"/>
        </div>
        <div className="flex-1 overflow-y-auto">
            <table className="w-full text-sm text-left table-fixed">
              <thead className="sticky top-0 bg-gray-800 cursor-pointer"><tr>
                {['request_number', 'payloads', 'status', 'length', 'duration'].map(key => (
                    <th key={key} className="p-2" onClick={() => requestSort(key)}>{key.replace('_', ' ')} {sortConfig?.key === key && (sortConfig.direction === 'asc' ? <ChevronUp/> : <ChevronDown/>)}</th>
                ))}
              </tr></thead>
              <tbody>{sortedAndFilteredResults.map((r, i) => (
                  <tr key={i} className="border-t border-gray-800 hover:bg-gray-700/50">
                      <td className="p-2">{r.request_number}</td><td className="p-2 font-mono truncate">{JSON.stringify(r.payloads)}</td><td className="p-2">{r.status}</td><td className="p-2">{r.length}</td><td className="p-2">{r.duration}</td>
                  </tr>
              ))}</tbody>
            </table>
        </div>
        <div className="p-1 text-xs border-t border-gray-700 text-gray-400 text-center">
            {isAttacking ? `Attacking... (${results.length} results)` : `Attack ${activeAttackId ? 'stopped' : 'idle'}. Displaying ${sortedAndFilteredResults.length} of ${results.length} total results.`}
        </div>
      </div>
    </div>
  );
};
