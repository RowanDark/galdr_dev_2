// galdr/interceptor/frontend/src/renderer/components/RequestResponseViewer.tsx
import React, { useState, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';
import { Copy, Send, Edit, Save, X, AlertCircle, CheckCircle, Shield, Clock } from 'lucide-react';
import { InterceptedTraffic, RequestModification } from '../types/traffic';

interface RequestResponseViewerProps {
  request: InterceptedTraffic;
  onModifyRequest?: (modifications: RequestModification) => void;
  onResendRequest?: () => void;
}

export const RequestResponseViewer: React.FC<RequestResponseViewerProps> = ({ 
  request, 
  onModifyRequest,
  onResendRequest 
}) => {
  const [activeTab, setActiveTab] = useState<'request' | 'response'>('request');
  const [subTab, setSubTab] = useState<'headers' | 'body'>('headers');
  const [isEditing, setIsEditing] = useState(false);
  const [editedRequest, setEditedRequest] = useState<Partial<InterceptedTraffic>>(request);
  const [isModified, setIsModified] = useState(false);

  useEffect(() => {
    setEditedRequest(request);
    setIsModified(false);
    setIsEditing(false);
  }, [request]);

  const formatHeaders = (headers: Record<string, string>) => {
    return Object.entries(headers)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');
  };

  const formatBody = (body: string) => {
    if (!body) return '';
    
    try {
      const parsed = JSON.parse(body);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return body;
    }
  };

  const getContentType = (headers: Record<string, string>) => {
    const contentType = headers['content-type'] || headers['Content-Type'] || '';
    if (contentType.includes('json')) return 'json';
    if (contentType.includes('xml')) return 'xml';
    if (contentType.includes('html')) return 'html';
    if (contentType.includes('javascript')) return 'javascript';
    if (contentType.includes('css')) return 'css';
    return 'text';
  };

  const handleSaveModifications = () => {
    if (onModifyRequest) {
      const modifications: RequestModification = {};
      
      if (editedRequest.headers !== request.headers) {
        modifications.headers = editedRequest.headers;
      }
      if (editedRequest.request_body !== request.request_body) {
        modifications.body = editedRequest.request_body;
      }
      if (editedRequest.method !== request.method) {
        modifications.method = editedRequest.method;
      }
      if (editedRequest.url !== request.url) {
        modifications.url = editedRequest.url;
      }
      
      onModifyRequest(modifications);
    }
    
    setIsEditing(false);
    setIsModified(false);
  };

  const handleCancelEdit = () => {
    setEditedRequest(request);
    setIsEditing(false);
    setIsModified(false);
  };

  const handleCopyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // Show success notification
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const getStatusIndicator = () => {
    if (!request.response) {
      return (
        <div className="flex items-center space-x-2 text-gray-500">
          <Clock className="w-4 h-4" />
          <span>Pending</span>
        </div>
      );
    }
    
    const status = request.response.status_code;
    const isError = status >= 400;
    
    return (
      <div className={`flex items-center space-x-2 ${isError ? 'text-red-600' : 'text-green-600'}`}>
        {isError ? <AlertCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
        <span>{status}</span>
        {request.response.duration_ms && (
          <span className="text-gray-500">({request.response.duration_ms.toFixed(0)}ms)</span>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Enhanced Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold">Request Details</h3>
            {request.is_https && <Shield className="w-5 h-5 text-purple-500" />}
            {getStatusIndicator()}
          </div>
          
          <div className="flex space-x-2">
            {isEditing ? (
              <>
                <button
                  onClick={handleSaveModifications}
                  className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                >
                  <Save className="w-4 h-4" />
                  <span>Save</span>
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="flex items-center space-x-1 px-3 py-1 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm"
                >
                  <X className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleCopyToClipboard(request.url)}
                  className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                  title="Copy URL"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                  title="Edit request"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={onResendRequest}
                  className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                  title="Resend request"
                >
                  <Send className="w-4 h-4" />
                  <span>Resend</span>
                </button>
              </>
            )}
          </div>
        </div>
        
        {/* Request Summary */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-sm">
            <span className="font-medium text-gray-700">Method:</span>
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
              {request.method}
            </span>
          </div>
          <div className="text-sm">
            <span className="font-medium text-gray-700">URL:</span>
            <span className="ml-2 text-gray-600 break-all">{request.url}</span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>Host: {request.target_host}:{request.target_port}</span>
            <span>Protocol: {request.is_https ? 'HTTPS' : 'HTTP'}</span>
            <span>Time: {new Date(request.timestamp).toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('request')}
          className={`px-4 py-2 font-medium text-sm ${
            activeTab === 'request' 
              ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Request
        </button>
        <button
          onClick={() => setActiveTab('response')}
          className={`px-4 py-2 font-medium text-sm ${
            activeTab === 'response' 
              ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Response
          {request.response && (
            <span className="ml-2 text-xs text-gray-500">
              ({request.response.status_code})
            </span>
          )}
        </button>
      </div>

      {/* Sub-tab Navigation */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        <button
          onClick={() => setSubTab('headers')}
          className={`px-4 py-2 text-sm ${
            subTab === 'headers' 
              ? 'bg-white border-b-2 border-blue-500 text-blue-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Headers
        </button>
        <button
          onClick={() => setSubTab('body')}
          className={`px-4 py-2 text-sm ${
            subTab === 'body' 
              ? 'bg-white border-b-2 border-blue-500 text-blue-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Body
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'request' && (
          <div className="h-full">
            {subTab === 'headers' && (
              <Editor
                height="100%"
                language="text"
                value={formatHeaders(request.headers)}
                options={{
                  readOnly: !isEditing,
                  minimap: { enabled: false },
                  lineNumbers: 'off',
                  folding: false,
                  wordWrap: 'on',
                  fontSize: 12
                }}
                onChange={(value) => {
                  if (isEditing && value) {
                    // Parse headers back to object
                    const headerObj: Record<string, string> = {};
                    value.split('\n').forEach(line => {
                      const [key, ...valueParts] = line.split(':');
                      if (key && valueParts.length > 0) {
                        headerObj[key.trim()] = valueParts.join(':').trim();
                      }
                    });
                    setEditedRequest({ ...editedRequest, headers: headerObj });
                    setIsModified(true);
                  }
                }}
              />
            )}
            {subTab === 'body' && (
              <Editor
                height="100%"
                language={getContentType(request.headers)}
                value={formatBody(request.request_body || '')}
                options={{
                  readOnly: !isEditing,
                  minimap: { enabled: false },
                  wordWrap: 'on',
                  fontSize: 12
                }}
                onChange={(value) => {
                  if (isEditing) {
                    setEditedRequest({ ...editedRequest, request_body: value });
                    setIsModified(true);
                  }
                }}
              />
            )}
          </div>
        )}
        
        {activeTab === 'response' && (
          <div className="h-full">
            {request.response ? (
              <>
                {subTab === 'headers' && (
                  <Editor
                    height="100%"
                    language="text"
                    value={formatHeaders(request.response.headers)}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      lineNumbers: 'off',
                      folding: false,
                      wordWrap: 'on',
                      fontSize: 12
                    }}
                  />
                )}
                {subTab === 'body' && (
                  <Editor
                    height="100%"
                    language={getContentType(request.response.headers)}
                    value={formatBody(request.response.body || '')}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      wordWrap: 'on',
                      fontSize: 12
                    }}
                  />
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Clock className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No response received</p>
                  <p className="text-sm">Request is still pending</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
