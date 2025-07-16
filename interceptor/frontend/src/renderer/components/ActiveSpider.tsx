// galdr/interceptor/frontend/src/renderer/components/ActiveSpider.tsx
import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Square, 
  Settings, 
  Eye,
  Globe,
  FormInput,
  Link2,
  Database,
  Download,
  RefreshCw,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Layers
} from 'lucide-react';
import { 
  SpiderManager, 
  SpiderSession, 
  SpiderProgress,
  SpiderStatistics, 
  SpiderConfig,
  DiscoveredEndpoint,
  DiscoveredForm
} from '../services/SpiderManager';
import { SpiderDashboard } from './spider/SpiderDashboard';
import { SpiderProgress as SpiderProgressComponent } from './spider/SpiderProgress';
import { SpiderResults } from './spider/SpiderResults';
import { EndpointDiscovery } from './spider/EndpointDiscovery';
import { FormDiscovery } from './spider/FormDiscovery';
import { SpiderConfiguration } from './spider/SpiderConfiguration';

interface ActiveSpiderProps {
  spiderManager: SpiderManager;
}

type SpiderView = 'dashboard' | 'progress' | 'results' | 'endpoints' | 'forms' | 'config';

export const ActiveSpider: React.FC<ActiveSpiderProps> = ({ spiderManager }) => {
  const [currentView, setCurrentView] = useState<SpiderView>('dashboard');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isSpiderActive, setIsSpiderActive] = useState(false);
  const [spiderProgress, setSpiderProgress] = useState<SpiderProgress | null>(null);
  const [spiderSession, setSpiderSession] = useState<SpiderSession | null>(null);
  const [statistics, setStatistics] = useState<SpiderStatistics>({
    active_sessions: 0,
    total_pages_visited: 0,
    total_endpoints_discovered: 0,
    total_forms_discovered: 0,
    collected_links: 0,
    collected_emails: 0,
    collected_files: 0,
    detected_technologies: 0,
    found_vulnerabilities: 0,
    found_secrets: 0
  });
  const [discoveredEndpoints, setDiscoveredEndpoints] = useState<DiscoveredEndpoint[]>([]);
  const [discoveredForms, setDiscoveredForms] = useState<DiscoveredForm[]>([]);
  const [config, setConfig] = useState<Partial<SpiderConfig>>({
    max_depth: 3,
    max_pages_per_domain: 100,
    max_concurrent_pages: 5,
    request_delay: 1.0,
    browser_type: 'chromium',
    headless: true,
    enable_form_submission: true,
    enable_login_forms: false,
    discover_ajax_endpoints: true,
    collect_emails: true,
    collect_files: true,
    detect_technologies: true,
    stay_in_domain: true
  });

  useEffect(() => {
    // Setup spider manager listeners
    spiderManager.onProgress((progress) => {
      setSpiderProgress(progress);
      if (currentView !== 'progress') {
        setCurrentView('progress');
      }
    });

    spiderManager.onSession((session) => {
      setSpiderSession(session);
      setIsSpiderActive(session.status === 'running');
      setSpiderProgress(null);
      
      if (session.status === 'completed') {
        setCurrentView('results');
        loadDiscoveredData();
      }
    });

    spiderManager.onStatistics((stats) => {
      setStatistics(stats);
    });

    spiderManager.onError((error) => {
      console.error('Spider error:', error);
      setIsSpiderActive(false);
      setSpiderProgress(null);
    });

    // Load initial data
    loadStatistics();
    loadDiscoveredData();

    // Periodic updates
    const interval = setInterval(() => {
      if (!isSpiderActive) {
        loadStatistics();
        loadDiscoveredData();
      }
    }, 10000);

    return () => {
      clearInterval(interval);
      spiderManager.disconnect();
    };
  }, [spiderManager, currentView, isSpiderActive]);

  const loadStatistics = async () => {
    try {
      const stats = await spiderManager.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const loadDiscoveredData = async () => {
    try {
      const [endpoints, forms] = await Promise.all([
        spiderManager.getDiscoveredEndpoints(),
        spiderManager.getDiscoveredForms()
      ]);
      setDiscoveredEndpoints(endpoints);
      setDiscoveredForms(forms);
    } catch (error) {
      console.error('Failed to load discovered data:', error);
    }
  };

  const handleStartSpider = async (targetUrl: string, sessionName?: string) => {
    try {
      setIsSpiderActive(true);
      const sessionId = await spiderManager.startSpiderSession(targetUrl, config, sessionName);
      setCurrentSessionId(sessionId);
      setCurrentView('progress');
    } catch (error) {
      console.error('Failed to start spider:', error);
      setIsSpiderActive(false);
    }
  };

  const handleStopSpider = async () => {
    if (currentSessionId) {
      try {
        await spiderManager.stopSpiderSession(currentSessionId);
        setIsSpiderActive(false);
        setSpiderProgress(null);
        setCurrentView('dashboard');
      } catch (error) {
        console.error('Failed to stop spider:', error);
      }
    }
  };

  const handleUpdateConfig = async (newConfig: Partial<SpiderConfig>) => {
    try {
      await spiderManager.updateConfig(newConfig);
      setConfig({ ...config, ...newConfig });
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  const handleExportData = async (format: 'json' | 'csv' | 'xlsx', dataType: string) => {
    try {
      const blob = await spiderManager.exportData(
        format, 
        dataType as any, 
        currentSessionId || undefined
      );
      
      // Download the blob
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `spider_${dataType}_${new Date().getTime()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  const getStatusColor = () => {
    if (isSpiderActive) return 'text-green-600';
    if (spiderSession?.status === 'completed') return 'text-blue-600';
    if (spiderSession?.status === 'error') return 'text-red-600';
    return 'text-gray-600';
  };

  const getStatusText = () => {
    if (isSpiderActive) return 'Active';
    if (spiderSession?.status === 'completed') return 'Completed';
    if (spiderSession?.status === 'error') return 'Error';
    return 'Ready';
  };

  const getStatusIcon = () => {
    if (isSpiderActive) return <Activity className="w-4 h-4 animate-pulse" />;
    if (spiderSession?.status === 'completed') return <CheckCircle className="w-4 h-4" />;
    if (spiderSession?.status === 'error') return <AlertTriangle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <SpiderDashboard
            statistics={statistics}
            discoveredEndpoints={discoveredEndpoints}
            discoveredForms={discoveredForms}
            onStartSpider={handleStartSpider}
            isSpiderActive={isSpiderActive}
            recentSession={spiderSession}
          />
        );
      
      case 'progress':
        return (
          <SpiderProgressComponent
            progress={spiderProgress}
            session={spiderSession}
            onStopSpider={handleStopSpider}
            isSpiderActive={isSpiderActive}
          />
        );
      
      case 'results':
        return (
          <SpiderResults
            session={spiderSession}
            onExport={handleExportData}
            onNewSpider={() => setCurrentView('dashboard')}
          />
        );
      
      case 'endpoints':
        return (
          <EndpointDiscovery
            endpoints={discoveredEndpoints}
            onRefresh={loadDiscoveredData}
            onExport={handleExportData}
          />
        );
      
      case 'forms':
        return (
          <FormDiscovery
            forms={discoveredForms}
            onRefresh={loadDiscoveredData}
            onExport={handleExportData}
          />
        );
      
      case 'config':
        return (
          <SpiderConfiguration
            config={config}
            onUpdateConfig={handleUpdateConfig}
          />
        );
      
      default:
        return (
          <SpiderDashboard
            statistics={statistics}
            discoveredEndpoints={discoveredEndpoints}
            discoveredForms={discoveredForms}
            onStartSpider={handleStartSpider}
            isSpiderActive={isSpiderActive}
            recentSession={spiderSession}
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
              <Target className="w-6 h-6 text-orange-600" />
              <h1 className="text-xl font-bold text-gray-900">Active Spider</h1>
            </div>
            <div className={`flex items-center space-x-2 text-sm ${getStatusColor()}`}>
              {getStatusIcon()}
              <span>{getStatusText()}</span>
            </div>
            {spiderSession && (
              <div className="text-sm text-gray-600">
                Session: {spiderSession.session_id}
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div className="flex items-center space-x-3">
            {isSpiderActive ? (
              <button
                onClick={handleStopSpider}
                className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <Square className="w-4 h-4" />
                <span>Stop Spider</span>
              </button>
            ) : (
              <button
                onClick={() => setCurrentView('dashboard')}
                className="flex items-center space-x-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                disabled={isSpiderActive}
              >
                <Play className="w-4 h-4" />
                <span>New Spider</span>
              </button>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mt-4">
          <button
            onClick={() => setCurrentView('dashboard')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'dashboard' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setCurrentView('results')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'results' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
            disabled={!spiderSession}
          >
            Results
          </button>
          <button
            onClick={() => setCurrentView('endpoints')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'endpoints' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span>Endpoints</span>
              {statistics.total_endpoints_discovered > 0 && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                  {statistics.total_endpoints_discovered}
                </span>
              )}
            </div>
          </button>
          <button
            onClick={() => setCurrentView('forms')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'forms' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span>Forms</span>
              {statistics.total_forms_discovered > 0 && (
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                  {statistics.total_forms_discovered}
                </span>
              )}
            </div>
          </button>
          <button
            onClick={() => setCurrentView('config')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'config' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Configuration
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div className="bg-orange-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-orange-600" />
              <span className="text-sm text-gray-600">Pages Visited</span>
            </div>
            <p className="text-lg font-bold text-orange-900">{statistics.total_pages_visited}</p>
          </div>
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-600">Endpoints</span>
            </div>
            <p className="text-lg font-bold text-blue-900">{statistics.total_endpoints_discovered}</p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <FormInput className="w-4 h-4 text-green-600" />
              <span className="text-sm text-gray-600">Forms</span>
            </div>
            <p className="text-lg font-bold text-green-900">{statistics.total_forms_discovered}</p>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Link2 className="w-4 h-4 text-purple-600" />
              <span className="text-sm text-gray-600">Links</span>
            </div>
            <p className="text-lg font-bold text-purple-900">{statistics.collected_links}</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderCurrentView()}
      </div>
    </div>
  );
};
