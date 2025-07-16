// galdr/interceptor/frontend/src/renderer/components/Recon.tsx
import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Play, 
  Square, 
  Download, 
  Settings, 
  Eye,
  Globe,
  Shield,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { ReconManager, ReconResult, ReconProgress, ReconConfig } from '../services/ReconManager';
import { ReconTargetInput } from './recon/ReconTargetInput';
import { ReconProgress as ReconProgressComponent } from './recon/ReconProgress';
import { ReconResults } from './recon/ReconResults';
import { ReconHistory } from './recon/ReconHistory';
import { ReconConfiguration } from './recon/ReconConfiguration';

interface ReconProps {
  reconManager: ReconManager;
}

type ReconView = 'new_scan' | 'progress' | 'results' | 'history' | 'config';

export const Recon: React.FC<ReconProps> = ({ reconManager }) => {
  const [currentView, setCurrentView] = useState<ReconView>('new_scan');
  const [currentScanId, setCurrentScanId] = useState<string | null>(null);
  const [scanProgress, setScanProgress] = useState<ReconProgress | null>(null);
  const [scanResults, setScanResults] = useState<ReconResult | null>(null);
  const [scanHistory, setScanHistory] = useState<ReconResult[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [config, setConfig] = useState<Partial<ReconConfig>>({
    enable_passive_sources: true,
    enable_api_sources: false,
    timeout_seconds: 30,
    max_concurrent_requests: 10,
    include_subdomains: true,
    include_historical: true
  });

  useEffect(() => {
    // Setup recon manager listeners
    reconManager.onProgress((progress) => {
      setScanProgress(progress);
      if (currentView !== 'progress') {
        setCurrentView('progress');
      }
    });

    reconManager.onCompletion((result) => {
      setScanResults(result);
      setScanProgress(null);
      setIsScanning(false);
      setCurrentView('results');
      
      // Update history
      loadScanHistory();
    });

    reconManager.onError((error) => {
      console.error('Recon error:', error);
      setIsScanning(false);
      setScanProgress(null);
    });

    // Load initial history
    loadScanHistory();

    return () => {
      reconManager.disconnect();
    };
  }, [reconManager, currentView]);

  const loadScanHistory = async () => {
    try {
      const history = await reconManager.getReconHistory();
      setScanHistory(history);
    } catch (error) {
      console.error('Failed to load scan history:', error);
    }
  };

  const handleStartScan = async (target: string) => {
    try {
      setIsScanning(true);
      const scanId = await reconManager.startReconnaissance(target, config);
      setCurrentScanId(scanId);
      setCurrentView('progress');
    } catch (error) {
      console.error('Failed to start scan:', error);
      setIsScanning(false);
    }
  };

  const handleStopScan = async () => {
    if (currentScanId) {
      try {
        await reconManager.stopReconnaissance(currentScanId);
        setIsScanning(false);
        setScanProgress(null);
        setCurrentView('new_scan');
      } catch (error) {
        console.error('Failed to stop scan:', error);
      }
    }
  };

  const handleViewResults = async (scanId: string) => {
    try {
      const results = await reconManager.getReconResults(scanId);
      setScanResults(results);
      setCurrentView('results');
    } catch (error) {
      console.error('Failed to load results:', error);
    }
  };

  const handleExportResults = async (format: 'json' | 'csv' | 'txt') => {
    if (!scanResults) return;
    
    try {
      const blob = await reconManager.exportResults(scanResults.scan_id, format);
      
      // Download the blob
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recon_${scanResults.target.primary_target}_${scanResults.scan_id}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export results:', error);
    }
  };

  const handleUpdateConfig = async (newConfig: Partial<ReconConfig>) => {
    try {
      await reconManager.updateConfig(newConfig);
      setConfig({ ...config, ...newConfig });
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  const getStatusColor = () => {
    if (isScanning) return 'text-yellow-600';
    if (scanResults) return 'text-green-600';
    return 'text-gray-600';
  };

  const getStatusText = () => {
    if (isScanning) return 'Scanning...';
    if (scanResults) return 'Scan Complete';
    return 'Ready';
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'new_scan':
        return (
          <ReconTargetInput
            onStartScan={handleStartScan}
            isScanning={isScanning}
            config={config}
          />
        );
      
      case 'progress':
        return (
          <ReconProgressComponent
            progress={scanProgress}
            onStopScan={handleStopScan}
            isScanning={isScanning}
          />
        );
      
      case 'results':
        return (
          <ReconResults
            results={scanResults}
            onExport={handleExportResults}
            onNewScan={() => setCurrentView('new_scan')}
          />
        );
      
      case 'history':
        return (
          <ReconHistory
            history={scanHistory}
            onViewResults={handleViewResults}
            onRefresh={loadScanHistory}
          />
        );
      
      case 'config':
        return (
          <ReconConfiguration
            config={config}
            onUpdateConfig={handleUpdateConfig}
          />
        );
      
      default:
        return (
          <ReconTargetInput
            onStartScan={handleStartScan}
            isScanning={isScanning}
            config={config}
          />
        );
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Search className="w-6 h-6 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Mimir's Recon</h1>
            </div>
            <div className={`flex items-center space-x-2 text-sm ${getStatusColor()}`}>
              {isScanning ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : scanResults ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Clock className="w-4 h-4" />
              )}
              <span>{getStatusText()}</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setCurrentView('new_scan')}
              className={`px-3 py-1 text-sm font-medium rounded ${
                currentView === 'new_scan' 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              New Scan
            </button>
            <button
              onClick={() => setCurrentView('history')}
              className={`px-3 py-1 text-sm font-medium rounded ${
                currentView === 'history' 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              History
            </button>
            <button
              onClick={() => setCurrentView('config')}
              className={`px-3 py-1 text-sm font-medium rounded ${
                currentView === 'config' 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Configuration
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        {scanResults && (
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-blue-600" />
                <span className="text-sm text-gray-600">Subdomains</span>
              </div>
              <p className="text-lg font-bold text-blue-900">
                {scanResults.statistics.total_subdomains_found}
              </p>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <Eye className="w-4 h-4 text-green-600" />
                <span className="text-sm text-gray-600">URLs</span>
              </div>
              <p className="text-lg font-bold text-green-900">
                {scanResults.statistics.total_urls_found}
              </p>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-purple-600" />
                <span className="text-sm text-gray-600">IPs</span>
              </div>
              <p className="text-lg font-bold text-purple-900">
                {scanResults.statistics.total_ips_found}
              </p>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-yellow-600" />
                <span className="text-sm text-gray-600">Technologies</span>
              </div>
              <p className="text-lg font-bold text-yellow-900">
                {scanResults.statistics.unique_technologies}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderCurrentView()}
      </div>
    </div>
  );
};
