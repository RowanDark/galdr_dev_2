// galdr/interceptor/frontend/src/renderer/components/replay_forge/RequestEditor.tsx
// The core editor for manipulating all parts of an HTTP request.

import React, { useState, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';
import { SendRequestData } from '../../services/ReplayForgeManager';

interface RequestEditorProps {
  request: SendRequestData;
  onUpdateRequest: (updatedRequest: SendRequestData) => void;
}

export const RequestEditor: React.FC<RequestEditorProps> = ({ request, onUpdateRequest }) => {
  const [activeSubTab, setActiveSubTab] = useState<'body' | 'headers'>('body');

  // We use useEffect to handle changes to headers from the editor, since it's a string.
  const handleHeaderChange = (value: string | undefined) => {
    const newHeaders: Record<string, string> = {};
    if (value) {
      value.split('\n').forEach(line => {
        const parts = line.split(':');
        if (parts.length >= 2) {
          const key = parts[0].trim();
          const val = parts.slice(1).join(':').trim();
          if (key) {
            newHeaders[key] = val;
          }
        }
      });
    }
    onUpdateRequest({ ...request, headers: newHeaders });
  };
  
  return (
    <div className="h-full flex flex-col bg-gray-800">
        <div className="p-2 border-b border-gray-700 flex gap-2">
            <select
                value={request.method}
                onChange={e => onUpdateRequest({ ...request, method: e.target.value })}
                className="bg-gray-700 border border-gray-600 rounded-md px-2 py-1 font-bold"
            >
                <option>GET</option>
                <option>POST</option>
                <option>PUT</option>
                <option>DELETE</option>
                <option>PATCH</option>
                <option>OPTIONS</option>
                <option>HEAD</option>
            </select>
            <input
                type="text"
                value={request.url}
                onChange={e => onUpdateRequest({ ...request, url: e.target.value })}
                className="flex-grow bg-gray-700 border border-gray-600 rounded-md px-3 py-1 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://example.com/api/v1/users"
            />
        </div>

        <div className="flex items-center border-b border-gray-700">
            <button onClick={() => setActiveSubTab('body')} className={`px-4 py-2 text-sm ${activeSubTab === 'body' ? 'bg-gray-800 text-white font-semibold' : 'text-gray-400 hover:bg-gray-700/50'}`}>Body</button>
            <button onClick={() => setActiveSubTab('headers')} className={`px-4 py-2 text-sm ${activeSubTab === 'headers' ? 'bg-gray-800 text-white font-semibold' : 'text-gray-400 hover:bg-gray-700/50'}`}>Headers</button>
        </div>

        <div className="flex-1 overflow-hidden">
            <Editor
                height="100%"
                theme="vs-dark"
                language={activeSubTab === 'headers' ? 'ini' : 'json'}
                value={activeSubTab === 'headers' ? Object.entries(request.headers).map(([k, v]) => `${k}: ${v}`).join('\n') : request.body}
                onChange={(value) => {
                    if (activeSubTab === 'body') {
                        onUpdateRequest({ ...request, body: value || '' });
                    } else {
                        handleHeaderChange(value);
                    }
                }}
                options={{
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
