// galdr/interceptor/frontend/src/renderer/components/spider/SpiderDashboard.tsx
import React, { useState } from 'react';
import { 
  Play, 
  Target, 
  Activity, 
  Globe, 
  Database,
  FormInput,
  Link2,
  Shield,
  AlertTriangle,
  Info,
  CheckCircle
} from 'lucide-react';
import { SpiderStatistics, SpiderSession } from '../../services/SpiderManager';

interface SpiderDashboardProps {
  statistics: SpiderStatistics;
  isActive: boolean;
  currentSession: SpiderSession | null;
  onStartSpider: (targetUrl: string, sessionName?: string) => void;
  onRefresh: () => void;
}

export const SpiderDashboard: React.FC<SpiderDashboardProps> = ({
  statistics,
  isActive,
  currentSession,
  onStartSpider,
  onRefresh
}) => {
  const [targetUrl, setTargetUrl] = useState('');
  const [sessionName, setSessionName] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateUrl = (url: string): boolean => {
    if (!url.trim()) {
      setValidationError('Please enter a target URL');
      return false;
    }

    try {
      const urlObj = new URL(url.trim());
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        setValidationError('URL must use HTTP or HTTPS protocol');
        return false;
      }
      setValidationError(null);
      return true;
    } catch {
      setValidationError('Please enter a valid URL');
      return false;
    }
  };

  const handleStartSpider = () => {
    const trimmedUrl = targetUrl.trim();
    if (validateUrl(trimmedUrl)) {
      onStartSpider(trimmedUrl, sessionName.trim() || undefined);
      setTargetUrl('');
      setSessionName('');
    }
  };

  const getSessionStatusIcon = () => {
    if (!currentSession) return <Target className="w-5 h-5 text-gray-400" />;
    
    switch (currentSession.status) {
      case 'running':
        return <Activity className="w-5 h-5 text-green-600 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default:
        return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      <div className="space-y-6">
        {/* Spider Control */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Start New Spider Session</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target URL
              </label>
              <input
                type="url"
                value={targetUrl}
                onChange={(e) => {
                  setTargetUrl(e.target.value);
                  if (validationError) validateUrl(e.target.value);
                }}
                placeholder="https://example.com"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 ${
                  validationError ? 'border-red-300' : 'border-gray-300'
                }`}
                disabled={isActive}
              />
              {validationError && (
                <div className="mt-2 flex items-center space-x-2 text-red-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{validationError}</span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Session Name (Optional)
              </label>
              <input
                type="text"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                placeholder="Enter session name..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                disabled={isActive}
              />
            </div>

            <button
              onClick={handleStartSpider}
              disabled={isActive || !targetUrl.trim()}
              className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium ${
                isActive || !targetUrl.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-orange-600 text-white hover:bg-orange-700'
              }`}
            >
              <Play className="w-4 h-4" />
              <span>{isActive ? 'Spider Session Active...' : 'Start Active Spider'}</span>
            </button>
          </div>
        </div>

        {/* Current Session Status */}
        {currentSession && (
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Session</h2>
            
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                {getSessionStatusIcon()}
                <div>
                  <h3 className="font-medium text-gray-900">{currentSession.session_id}</h3>
                  <p className="text-sm text-gray-600">{currentSession.target_url}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${
                currentSession.status === 'running' ? 'bg-green-100 text-green-800' :
                currentSession.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                currentSession.status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {currentSession.status}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
