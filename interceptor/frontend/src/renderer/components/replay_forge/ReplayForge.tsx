// galdr/interceptor/frontend/src/renderer/components/replay_forge/ReplayForge.tsx
// --- FINALIZED & CORRECTED FORMATTING ---
// This component now orchestrates the new UI components for a professional experience.

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Send, Plus, Loader, Layers } from 'lucide-react';
import { replayForgeManager, ReplayTab, ReplayResult, SendRequestData } from '../../services/ReplayForgeManager';

// Import our new, real components
import { RequestTabs } from './RequestTabs';
import { RequestEditor } from './RequestEditor';
import { ResponseViewer } from './ResponseViewer';


interface ReplayForgeProps {
  initialRequest?: any;
}

export const ReplayForge: React.FC<ReplayForgeProps> = ({ initialRequest }) => {
    // --- STATE MANAGEMENT ---
    // List of all open tabs
    const [tabs, setTabs] = useState<ReplayTab[]>([]); 
    // ID of the currently focused tab
    const [activeTabId, setActiveTabId] = useState<string | null>(null);
    // Map of tab IDs to their current request data
    const [requests, setRequests] = useState<Record<string, SendRequestData>>({});
    // Map of tab IDs to their latest response
    const [responses, setResponses] = useState<Record<string, ReplayResult['response'] | null>>({});
    // Map of tab IDs to their loading state
    const [loadingTabs, setLoadingTabs] = useState<Record<string, boolean>>({});

    // Memoized selectors to get data for the active tab easily
    const activeRequest = useMemo(() => activeTabId ? requests[activeTabId] : null, [activeTabId, requests]);
    const activeResponse = useMemo(() => activeTabId ? responses[activeTabId] : null, [activeTabId, responses]);
    const isActivelyLoading = useMemo(() => activeTabId ? !!loadingTabs[activeTabId] : false, [activeTabId, loadingTabs]);
    
    // --- LOGIC AND HANDLERS ---
    const createNewTab = useCallback(async (reqData?: Partial<SendRequestData>) => {
        const fullRequest: SendRequestData = {
            method: 'GET',
            url: 'https://example.com',
            headers: {},
            body: '',
            ...reqData,
        };
        const tabName = `${fullRequest.method} ${fullRequest.url.split('?')[0].substring(0, 40)}`;
        try {
            const newTab = await replayForgeManager.createTab(tabName, fullRequest);
            setTabs(prev => [...prev, newTab]);
            setRequests(prev => ({...prev, [newTab.id]: fullRequest}));
            setActiveTabId(newTab.id);
            setResponses(prev => ({ ...prev, [newTab.id]: null})); // Clear any old response for this ID
        } catch(e) { console.error("Failed to create new tab:", e); }
    }, []);

    // Effect to create an initial tab if none exist
    useEffect(() => {
        if (tabs.length === 0) {
            createNewTab(initialRequest);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [initialRequest, createNewTab]);
    
    const handleTabClose = (tabIdToClose: string) => {
        const remainingTabs = tabs.filter(tab => tab.id !== tabIdToClose);
        setTabs(remainingTabs);

        // If we closed the active tab, switch to another one
        if (activeTabId === tabIdToClose) {
            setActiveTabId(remainingTabs.length > 0 ? remainingTabs[remainingTabs.length - 1].id : null);
        }

        // Clean up state
        setRequests(prev => { const n = {...prev}; delete n[tabIdToClose]; return n; });
        setResponses(prev => { const n = {...prev}; delete n[tabIdToClose]; return n; });
    };

    const handleRequestUpdate = (updatedRequest: SendRequestData) => {
        if (!activeTabId) return;
        setRequests(prev => ({...prev, [activeTabId]: updatedRequest}));
    };
    
    const handleSend = async () => {
        if (!activeTabId || !activeRequest) return;

        setLoadingTabs(prev => ({ ...prev, [activeTabId]: true }));
        setResponses(prev => ({ ...prev, [activeTabId]: null } as any)); // Clear previous response

        try {
            const result = await replayForgeManager.sendRequest(activeTabId, activeRequest);
            setResponses(prev => ({ ...prev, [activeTabId]: result.response }));
        } catch (error) {
            console.error(error);
            const errorResponse = {
                id: '', status_code: 0, headers_json: {}, body: String(error), response_time_ms: 0, error: String(error),
            }
            setResponses(prev => ({...prev, [activeTabId]: errorResponse }));
        } finally {
            setLoadingTabs(prev => ({ ...prev, [activeTabId]: false }));
        }
    };
    
  return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <RequestTabs
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={setActiveTabId}
        onTabClose={handleTabClose}
        onCreateTab={() => createNewTab()}
      />
      
      {activeTabId && activeRequest ? (
        <div className="flex-1 grid grid-cols-2 gap-px bg-gray-700 overflow-hidden">
            {/* Request Pane */}
            <div className="flex flex-col">
                <div className="p-2 bg-gray-900 flex justify-between items-center">
                    <h2 className="text-base font-bold">Request</h2>
                    <button onClick={handleSend} disabled={isActivelyLoading} className="flex justify-center items-center gap-2 px-3 py-1 bg-blue-600 rounded font-bold text-sm hover:bg-blue-500 disabled:bg-gray-500">
                        {isActivelyLoading ? <Loader size={16} className="animate-spin" /> : <Send size={16} />}
                        <span>Send</span>
                    </button>
                </div>
                <div className="flex-1 overflow-hidden">
                  <RequestEditor request={activeRequest} onUpdateRequest={handleRequestUpdate} />
                </div>
            </div>
            {/* Response Pane */}
            <div className="flex flex-col">
              <div className="p-2 bg-gray-900"><h2 className="text-base font-bold">Response</h2></div>
              <div className="flex-1 overflow-hidden">
                <ResponseViewer response={activeResponse} isLoading={isActivelyLoading} />
              </div>
            </div>
        </div>
      ) : (
        <div className="flex-1 flex justify-center items-center flex-col text-gray-500">
            <Layers size={64} className="mb-4" />
            <h2 className="text-2xl">No Request Tabs Open</h2>
            <button onClick={() => createNewTab()} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500">
                Create First Request
            </button>
        </div>
      )}
    </div>
  );
};
