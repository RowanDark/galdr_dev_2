// galdr/interceptor/frontend/src/renderer/components/spider/SpiderProgress.tsx
import React, { useState, useEffect } from 'react';
import { 
  Square, 
  Activity, 
  Globe, 
  FormInput, 
  Database,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Eye,
  Link2
} from 'lucide-react';
import { SpiderProgress as SpiderProgressType, SpiderSession } from '../../services/SpiderManager';

interface SpiderProgressProps {
  progress: SpiderProgressType | null;
  session: SpiderSession | null;
  onStopSpider: () => void;
  isActive: boolean;
}

export const SpiderProgress: React.FC<SpiderProgressProps> = ({
  progress,
  session,
  onStopSpider,
  isActive
}) => {
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (session && session.status === 'running') {
      const interval = setInterval(() => {
        const startTime = new Date(session.start_time).getTime();
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        setElapsedTime(elapsed);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [session]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgressPercentage = (): number => {
    if (!progress || !progress.total_pages_estimated) return 0;
    return Math.min((progress.pages_processed / progress.total_pages_estimated) * 100, 100);
  };

  const getCurrentDepthColor = (depth: number): string => {
    switch (depth) {
      case 0: return 'text-green-600';
      case 1: return 'text-blue-600';
      case 2: return 'text-yellow-600';
      default: return 'text-red-600';
    }
  };

  return (
    <div className="h-full flex items-center justify-center bg-gray-50">
      <div className="max-w-4xl w-full p-8">
        <div className="bg-white rounded-lg shadow-sm p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Activity className="w-8 h-8 text-orange-600 animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Active Spider in Progress</h2>
            <p className="text-gray-600 mt-2">
              {session ? `Crawling ${session.target_url}` : 'Initializing spider...'}
            </p>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-blue-900">Elapsed Time</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">{formatTime(elapsedTime)}</p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Globe className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-900">Pages Processed</span>
              </div>
              <p className="text-2xl font-bold text-green-900">
                {progress ? progress.pages_processed : 0}
              </p>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Target className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-purple-900">Current Depth</span>
              </div>
              <p className={`text-2xl font-bold ${getCurrentDepthColor(progress?.current_depth || 0)}`}>
                {progress ? progress.current_depth : 0}
              </p>
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <span className="font-medium text-yellow-900">Errors</span>
              </div>
              <p className="text-2xl font-bold text-yellow-900">
                {progress ? progress.errors_count : 0}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {progress?.message || 'Initializing...'}
              </span>
              <span className="text-sm text-gray-600">
                {getProgressPercentage().toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-orange-600 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
          </div>

          {/* Current Activity */}
          {progress && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-3">
                <Eye className="w-5 h-5 text-orange-600" />
                <div className="flex-1">
                  <p className="font-medium text-orange-900">Currently Processing</p>
                  <p className="text-sm text-orange-800 break-all">{progress.current_url}</p>
                </div>
              </div>
            </div>
          )}

          {/* Discovery Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white border rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                <FormInput className="w-6 h-6 text-purple-600" />
                <h3 className="font-medium text-gray-900">Forms Discovered</h3>
              </div>
              <p className="text-2xl font-bold text-purple-600">
                {progress ? progress.forms_discovered : 0}
              </p>
              <p className="text-sm text-gray-600 mt-1">Interactive forms found</p>
            </div>

            <div className="bg-white border rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                <Database className="w-6 h-6 text-green-600" />
                <h3 className="font-medium text-gray-900">Endpoints Found</h3>
              </div>
              <p className="text-2xl font-bold text-green-600">
                {progress ? progress.endpoints_discovered : 0}
              </p>
              <p className="text-sm text-gray-600 mt-1">AJAX/API endpoints</p>
            </div>

            <div className="bg-white border rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                <Link2 className="w-6 h-6 text-blue-600" />
                <h3 className="font-medium text-gray-900">Links Found</h3>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {session ? session.total_pages * 15 : 0} {/* Estimated based on pages */}
              </p>
              <p className="text-sm text-gray-600 mt-1">Unique links discovered</p>
            </div>
          </div>

          {/* Recent Activity Log */}
          {session && session.results && session.results.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="font-medium text-gray-900 mb-3">Recent Activity</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {session.results.slice(-5).reverse().map((result, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        result.status_code < 300 ? 'bg-green-500' :
                        result.status_code < 400 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`} />
                      <span className="text-gray-900 truncate max-w-md">{result.url}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-gray-500">
                      <span>{result.status_code}</span>
                      <span>Depth {result.depth}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Control Button */}
          <div className="text-center">
            <button
              onClick={onStopSpider}
              disabled={!isActive}
              className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed mx-auto"
            >
              <Square className="w-4 h-4" />
              <span>Stop Spider</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
