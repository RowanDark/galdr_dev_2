// galdr/interceptor/frontend/src/renderer/components/replay_forge/ResponseViewer.tsx
// A read-only component for displaying HTTP responses with syntax highlighting.

import React, { useState } from 'react';
import { Editor } from '@monaco-editor/react';
import { Loader, ServerCrash, CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { ReplayResult } from '../../services/ReplayForgeManager';

interface ResponseViewerProps {
  response: ReplayResult['response'] | null;
  isLoading: boolean;
}

const getBodyLanguage = (headers: Record<string, string> | undefined): string => {
    const contentType = headers?.['content-type']?.toLowerCase() || '';
    if (contentType.includes('json')) return 'json';
    if (contentType.includes('xml')) return 'xml';
    if (contentType.includes('html')) return 'html';
    if (contentType.includes('javascript')) return 'javascript';
    if (contentType.includes('css')) return 'css';
    return 'plaintext';
};

const formatHeaders = (headers: Record<string, string>): string => {
    return Object.entries(headers).map(([key, value]) => `${key}: ${value}`).join('\n');
}

export const ResponseViewer: React.FC<ResponseViewerProps> = ({ response, isLoading }) => {
  const [activeSubTab, setActiveSubTab] = useState<'body' | 'headers'>('body');
  
  if (isLoading) {
    return <div className="flex justify-center items-center h-full"><Loader className="animate-spin" size={48} /></div>;
  }
  
  if (!response) {
    return <div className="flex justify-center items-center h-full text-gray-500">No response received yet.</div>;
  }

  const isError = !response.status_code || response.status_code >= 400;
  const statusColor = isError ? 'text-red-400' : 'text-green-400';
  const statusIcon = isError ? <AlertTriangle size={18} /> : <CheckCircle size={18} />;

  return (
    <div className="h-full flex flex-col bg-gray-800">
        <div className="p-2 border-b border-gray-700 bg-gray-900">
            <div className="flex justify-between items-center">
                <span className={`flex items-center gap-2 font-bold ${statusColor}`}>
                    {statusIcon} Status: {response.status_code || 'Error'}
                </span>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span className="flex items-center gap-1"><Clock size={14}/> {response.response_time_ms.toFixed(0)} ms</span>
                    <span>Size: {(response.body?.length || 0) / 1024 > 1 ? `${((response.body?.length || 0)/1024).toFixed(2)} KB` : `${(response.body?.length || 0)} B` }</span>
                </div>
            </div>
            {response.error && <div className="mt-2 text-xs text-red-300 bg-red-900/50 p-2 rounded">{response.error}</div>}
        </div>
        
        <div className="flex items-center border-b border-gray-700">
            <button onClick={() => setActiveSubTab('body')} className={`px-4 py-2 text-sm ${activeSubTab === 'body' ? 'bg-gray-800 text-white font-semibold' : 'text-gray-400 hover:bg-gray-700/50'}`}>Body</button>
            <button onClick={() => setActiveSubTab('headers')} className={`px-4 py-2 text-sm ${activeSubTab === 'headers' ? 'bg-gray-800 text-white font-semibold' : 'text-gray-400 hover:bg-gray-700/50'}`}>Headers</button>
        </div>

        <div className="flex-1 overflow-hidden">
            <Editor
                height="100%"
                theme="vs-dark"
                language={activeSubTab === 'headers' ? 'ini' : getBodyLanguage(response.headers_json)}
                value={activeSubTab === 'headers' ? formatHeaders(response.headers_json) : response.body}
                options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    wordWrap: 'on',
                    fontSize: 13,
                    scrollBeyondLastLine: false,
                }}
            />
        </div>
    </div>
  );
};
