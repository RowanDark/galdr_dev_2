// galdr/interceptor/frontend/src/renderer/components/recon/ReconProgress.tsx
import React, { useState, useEffect } from 'react';
import { 
  Square, 
  Activity, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Search,
  Globe,
  Shield,
  Database
} from 'lucide-react';
import { ReconProgress as ReconProgressType } from '../../services/ReconManager';

interface ReconProgressProps {
  progress: ReconProgressType | null;
  onStopScan: () => void;
  isScanning: boolean;
}

export const ReconProgress: React.FC<ReconProgressProps> = ({
  progress,
  onStopScan,
  isScanning
}) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [scanStartTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - scanStartTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [scanStartTime]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSourceIcon = (sourceName: string) => {
    if (sourceName.includes('wayback') || sourceName.includes('archive')) {
      return <Clock className="w-4 h-4" />;
    }
    if (sourceName.includes('crt') || sourceName.includes('certificate')) {
      return <Shield className="w-4 h-4" />;
    }
    if (sourceName.includes('dns') || sourceName.includes('domain')) {
      return <Globe className="w-4 h-4" />;
    }
    if (sourceName.includes('shodan') || sourceName.includes('censys')) {
      return <Database className="w-4 h-4" />;
    }
    return <Search className="w-4 h-4" />;
  };

  const sources = [
    { name: 'Wayback Machine', status: 'pending' },
    { name: 'crt.sh', status: 'pending' },
    { name: 'DNSDumpster', status: 'pending' },
    { name: 'ThreatCrowd', status: 'pending' },
    { name: 'HackerTarget', status: 'pending' },
    { name: 'URLScan.io', status: 'pending' },
    { name: 'OTX AlienVault', status: 'pending' },
    { name: 'Shodan', status: 'pending' }
  ];

  // Update source statuses based on progress
  if (progress) {
    const completedCount = progress.sources_completed;
    sources.forEach((source, index) => {
      if (index < completedCount) {
        source.status = 'completed';
      } else if (index === completedCount) {
        source.status = 'running';
      }
    });
  }

  return (
    <div className="h-full flex items-center justify-center bg-gray-50">
      <div className="max-w-4xl w-full p-8">
        <div className="bg-white rounded-lg shadow-sm p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Activity className="w-8 h-8 text-blue-600 animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Reconnaissance in Progress</h2>
            <p className="text-gray-600 mt-2">
              {progress ? `Scanning ${progress.scan_id}` : 'Initializing scan...'}
            </p>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-blue-900">Elapsed Time</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">{formatTime(elapsedTime)}</p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-900">Sources Completed</span>
              </div>
              <p className="text-2xl font-bold text-green-900">
                {progress ? `${progress.sources_completed}/${progress.total_sources}` : '0/8'}
              </p>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-purple-900">Overall Progress</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {progress ? `${Math.round(progress.percentage)}%` : '0%'}
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
                {progress ? `${Math.round(progress.percentage)}%` : '0%'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress?.percentage || 0}%` }}
              />
            </div>
          </div>

          {/* Source Status Grid */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Source Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {sources.map((source, index) => (
                <div 
                  key={source.name}
                  className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                    source.status === 'completed' 
                      ? 'border-green-200 bg-green-50' 
                      : source.status === 'running'
                      ? 'border-blue-200 bg-blue-50'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-full ${
                      source.status === 'completed' 
                        ? 'bg-green-100' 
                        : source.status === 'running'
                        ? 'bg-blue-100'
                        : 'bg-gray-100'
                    }`}>
                      {getSourceIcon(source.name)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{source.name}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        {source.status === 'completed' ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <span className="text-xs text-green-600">Complete</span>
                          </>
                        ) : source.status === 'running' ? (
                          <>
                            <Activity className="w-4 h-4 text-blue-600 animate-spin" />
                            <span className="text-xs text-blue-600">Running</span>
                          </>
                        ) : (
                          <>
                            <Clock className="w-4 h-4 text-gray-400" />
                            <span className="text-xs text-gray-500">Pending</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Current Activity */}
          {progress?.current_source && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-3">
                <Activity className="w-5 h-5 text-blue-600 animate-spin" />
                <div>
                  <p className="font-medium text-blue-900">Currently Processing</p>
                  <p className="text-sm text-blue-700">{progress.current_source}</p>
                </div>
              </div>
            </div>
          )}

          {/* Control Button */}
          <div className="text-center">
            <button
              onClick={onStopScan}
              disabled={!isScanning}
              className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed mx-auto"
            >
              <Square className="w-4 h-4" />
              <span>Stop Reconnaissance</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
