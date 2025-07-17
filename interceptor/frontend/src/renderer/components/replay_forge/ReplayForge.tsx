// galdr/interceptor/frontend/src/renderer/components/replay_forge/ReplayForge.tsx
// --- UPDATED ---
// This version integrates a dedicated "Portal AI Analysis" panel.

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Send, Plus, Loader, Layers, BrainCircuit, ChevronUp, ChevronDown, Sparkles, Bug } from 'lucide-react';

// Services & Child Components
import { replayForgeManager, ReplayTab, ReplayResult, SendRequestData } from '../../services/ReplayForgeManager';
import { portalManager } from '../../services/PortalManager';
import { RequestTabs } from './RequestTabs';
import { RequestEditor } from './RequestEditor';
import { ResponseViewer } from './ResponseViewer';
// We will need a Markdown renderer for AI responses. Let's add one to package.json:
// npm install react-markdown
import ReactMarkdown from 'react-markdown';


interface ReplayForgeProps {
  initialRequest?: any;
  onSendToRaider: (request: SendRequestData) => void;
}

export const ReplayForge: React.FC<ReplayForgeProps> = ({ initialRequest }) => {
    // --- State Management ---
    const [tabs, setTabs] = useState<ReplayTab[]>([]); 
    const [activeTabId, setActiveTabId] = useState<string | null>(null);
    const [requests, setRequests] = useState<Record<string, SendRequestData>>({});
    const [responses, setResponses] = useState<Record<string, ReplayResult['response'] | null>>({});
    const [loadingTabs, setLoadingTabs] = useState<Record<string, boolean>>({});

    // NEW STATE: For the AI Analysis panel
    const [isAnalysisPanelOpen, setIsAnalysisPanelOpen] = useState(true);
    const [analysisContent, setAnalysisContent] = useState<string>("Click a suggestion to analyze this request.");
    const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
    
    // --- Memoized Selectors ---
    const activeRequest = useMemo(() => activeTabId ? requests[activeTabId] : null, [activeTabId, requests]);
    const activeResponse = useMemo(() => activeTabId ? responses[activeTabId] : null, [activeTabId, responses]);
    const isActivelyLoading = useMemo(() => activeTabId ? !!loadingTabs[activeTabId] : false, [activeTabId, loadingTabs]);
    
    // --- Logic & Handlers ---
    const createNewTab = useCallback(async (reqData?: Partial<SendRequestData>) => {
        const fullRequest: SendRequestData = {
            method: 'GET', url: 'https://example.com', headers: {}, body: '', ...reqData,
        };
        const tabName = `${fullRequest.method} ${fullRequest.url.split('?')[0].substring(0, 40)}`;
        try {
            const newTab = await replayForgeManager.createTab(tabName, fullRequest);
            setTabs(prev => [...prev, newTab]);
            setRequests(prev => ({...prev, [newTab.id]: fullRequest}));
            setActiveTabId(newTab.id);
            setResponses(prev => ({ ...prev, [newTab.id]: null}));
            setAnalysisContent("Click a suggestion to analyze this request."); // Reset analysis on new tab
        } catch(e) { console.error("Failed to create new tab:", e); }
    }, []);
    
    // This is the core of our new functionality.
    const handleAiAnalysis = async (prompt: string) => {
        if (!activeRequest) return;
        setIsAnalysisLoading(true);
        setAnalysisContent(""); // Clear previous content

        try {
            // A "real" implementation would have a dedicated conversation ID for each tab.
            // For now, we will create one on the fly for simplicity.
            const tempConversation = await portalManager.startNewConversation();
            const context = {
                module: "Replay Forge",
                request: activeRequest,
                response: activeResponse // Include response if it exists
            }
            const aiResponse = await portalManager.analyzeWithContext(tempConversation.id, prompt, context);
            setAnalysisContent(aiResponse.content);
        } catch(e) {
            console.error("AI Analysis failed:", e);
            setAnalysisContent(`**Error:** Failed to get analysis. Is the AI server running?\n\n${e}`);
        } finally {
            setIsAnalysisLoading(false);
        }
    };

    // Remaining handlers (handleSend, handleTabClose, handleRequestUpdate) are unchanged.
    const handleSend = async () => { if (!activeTabId || !activeRequest) return; setLoadingTabs(prev => ({ ...prev, [activeTabId]: true })); setResponses(prev => ({ ...prev, [activeTabId]: null } as any)); try { const result = await replayForgeManager.sendRequest(activeTabId, activeRequest); setResponses(prev => ({ ...prev, [activeTabId]: result.response })); } catch (error) { console.error(error); const errorResponse = { id: '', status_code: 0, headers_json: {}, body: String(error), response_time_ms: 0, error: String(error), }; setResponses(prev => ({...prev, [activeTabId]: errorResponse })); } finally { setLoadingTabs(prev => ({ ...prev, [activeTabId]: false })); } };
    const handleRequestUpdate = (updatedRequest: SendRequestData) => { if (!activeTabId) return; setRequests(prev => ({...prev, [activeTabId]: updatedRequest})); };
    const handleTabClose = (tabIdToClose: string) => { const remainingTabs = tabs.filter(tab => tab.id !== tabIdToClose); setTabs(remainingTabs); if (activeTabId === tabIdToClose) { setActiveTabId(remainingTabs.length > 0 ? remainingTabs[remainingTabs.length - 1].id : null); } setRequests(prev => { const n = {...prev}; delete n[tabIdToClose]; return n; }); setResponses(prev => { const n = {...prev}; delete n[tabIdToClose]; return n; }); };
    useEffect(() => { if (tabs.length === 0) { createNewTab(initialRequest); } }, [initialRequest, tabs.length, createNewTab]);

    return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <RequestTabs tabs={tabs} activeTabId={activeTabId} onTabChange={setActiveTabId} onTabClose={handleTabClose} onCreateTab={() => createNewTab()} />
      
      {activeRequest ? (
        <div className="flex-1 grid grid-cols-2 gap-px bg-gray-700 overflow-hidden">
          
            <div className="flex flex-col">
              <RequestEditor request={activeRequest} onUpdateRequest={handleRequestUpdate} />
              <button onClick={handleSend} disabled={isActivelyLoading} className="flex justify-center items-center gap-2 p-2 bg-blue-600 rounded-none font-bold hover:bg-blue-500 disabled:bg-gray-500">
                  {isActivelyLoading ? <Loader size={16} className="animate-spin" /> : <Send size={16} />}
                  <span>Send</span>
              </button>
            </div>
            {/* Request Pane */}
            <div className="flex flex-col">
                <div className="p-2 bg-gray-900 flex justify-between items-center">
                    <h2 className="text-base font-bold">Request</h2>
                    <div className="flex items-center gap-2">
                        {/* NEW BUTTON */}
                        <button 
                          onClick={() => activeRequest && onSendToRaider(activeRequest)} 
                          disabled={!activeRequest}
                          className="flex items-center gap-2 px-3 py-1 bg-red-600 rounded text-white font-semibold text-sm hover:bg-red-500 disabled:bg-gray-600"
                          title="Send request to Raider for automated attacks"
                        >
                            <Bug size={16} />
                            <span>Raider</span>
                        </button>
                        <button onClick={handleSend} disabled={isActivelyLoading} className="flex justify-center items-center gap-2 px-3 py-1 bg-blue-600 rounded font-bold text-sm hover:bg-blue-500 disabled:bg-gray-500">
                            {isActivelyLoading ? <Loader size={16} className="animate-spin" /> : <Send size={16} />}
                            <span>Send</span>
                        </button>
                    </div>
                </div>
            <div className={`flex flex-col transition-all duration-300 ${isAnalysisPanelOpen ? 'h-full' : 'h-auto'}`}>
                <ResponseViewer response={activeResponse} isLoading={isActivelyLoading} />
                
                {/* --- NEW AI ANALYSIS PANEL --- */}
                <div className="flex flex-col bg-gray-900 border-t-4 border-blue-800">
                    <button onClick={() => setIsAnalysisPanelOpen(!isAnalysisPanelOpen)} className="w-full flex justify-between items-center p-2 bg-gray-800 hover:bg-gray-700">
                        <div className="flex items-center gap-2 font-bold"><BrainCircuit size={16} /> Portal AI Analysis</div>
                        {isAnalysisPanelOpen ? <ChevronDown size={18}/> : <ChevronUp size={18}/>}
                    </button>
                    {isAnalysisPanelOpen && (
                    <div className="flex flex-col" style={{ minHeight: '200px', maxHeight: '40vh' }}>
                        <div className="p-2 border-b border-gray-700 flex gap-2">
                           <button onClick={() => handleAiAnalysis("Analyze this request for potential vulnerabilities. Look for missing security headers, weak parameters, or other potential issues.")} disabled={isAnalysisLoading} className="flex-1 text-xs p-1.5 rounded bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 flex items-center gap-1 justify-center"><Sparkles size={14}/>Analyze for Vulnerabilities</button>
                           <button onClick={() => handleAiAnalysis("Explain what this HTTP request does in simple terms.")} disabled={isAnalysisLoading} className="flex-1 text-xs p-1.5 rounded bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500">Explain Request</button>
                           <button onClick={() => handleAiAnalysis("Suggest three ways to fuzz this request for security testing.")} disabled={isAnalysisLoading} className="flex-1 text-xs p-1.5 rounded bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500">Suggest Fuzzing</button>
                        </div>
                        <div className="p-4 flex-1 overflow-y-auto prose prose-invert prose-sm max-w-none prose-pre:bg-gray-800 prose-pre:text-white">
                           {isAnalysisLoading ? <div className="flex justify-center items-center h-full"><Loader className="animate-spin text-gray-400"/></div> : <ReactMarkdown>{analysisContent}</ReactMarkdown>}
                        </div>
                    </div>
                    )}
                </div>
            </div>
        </div>
      ) : ( /* The "No Tabs Open" placeholder UI */
        <div className="flex-1 flex justify-center items-center flex-col text-gray-500">
            <Layers size={64} className="mb-4" />
            <h2 className="text-2xl">No Request Tabs Open</h2>
            <button onClick={() => createNewTab()} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500">Create First Request</button>
        </div>
      )}
    </div>
  );
};
