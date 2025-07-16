// galdr/interceptor/frontend/src/renderer/components/PassiveCrawler.tsx
import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Play, 
  Square, 
  Settings, 
  Eye,
  Globe,
  Shield,
  Key,
  FileText,
  Download,
  Filter,
  Search,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Mail,
  Link,
  Bug
} from 'lucide-react';
import { 
  CrawlerManager, 
  CrawlEntry, 
  CrawlerStatistics, 
  CrawlerConfig,
  VulnerabilityFinding,
  SecretFinding
} from '../services/CrawlerManager';
import { CrawlerDashboard } from './crawler/CrawlerDashboard';
import { ExtractedData } from './crawler/ExtractedData';
import { SecurityFindings } from './crawler/SecurityFindings';
import { TechnologyStack } from './crawler/TechnologyStack';
import { CrawlerConfiguration } from './crawler/CrawlerConfiguration';

interface PassiveCrawlerProps {
  crawlerManager: CrawlerManager;
}

type CrawlerView = 'dashboard' | 'extracted_data' | 'security' | 'technologies' | 'config';

export const PassiveCrawler: React.FC<PassiveCrawlerProps> = ({ crawlerManager }) => {
  const [currentView, setCurrentView] = useState<CrawlerView>('dashboard');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [statistics, setStatistics] = useState<CrawlerStatistics>({
    active_sessions: 0,
    total_entries: 0,
    extracted_links: 0,
    extracted_emails: 0,
    extracted_files: 0,
    detected_technologies: 0,
    found_vulnerabilities: 0,
    discovered_secrets: 0
  });
  const [recentEntries, setRecentEntries] = useState<CrawlEntry[]>([]);
  const [vulnerabilities, setVulnerabilities] = useState<VulnerabilityFinding[]>([]);
  const [secrets, setSecrets] = useState<SecretFinding[]>([]);
  const [config, setConfig] = useState<Partial<CrawlerConfig>>({
    auto_analyze: true,
    enable_tech_stack_detection: true,
    enable_vulnerability_detection: false,
    enable_ai_analysis: false,
    enable_secrets_detection: true,
    track_js_files: true,
    track_css_files: true,
    track_image_files: false,
    track_document_files: true
  });

  useEffect(() => {
    // Setup crawler manager listeners
    crawlerManager.onEntry((entry) => {
      setRecentEntries(prev => [entry, ...prev].slice(0, 100));
    });

    crawlerManager.onStatistics((stats) => {
      setStatistics(stats);
    });

    crawlerManager.onError((error) => {
      console.error('Crawler error:', error);
    });

    // Load initial data
    loadStatistics();
    loadSecurityFindings();

    // Periodic updates
    const interval = setInterval(() => {
      if (isActive) {
        loadStatistics();
        loadSecurityFindings();
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      crawlerManager.disconnect();
    };
  }, [crawlerManager, isActive]);

  const loadStatistics = async () => {
    try {
      const stats = await crawlerManager.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const loadSecurityFindings = async () => {
    try {
      const [vulns, secretsData] = await Promise.all([
        crawlerManager.getVulnerabilities(),
        crawlerManager.getSecrets()
      ]);
      setVulnerabilities(vulns);
      setSecrets(secretsData);
    } catch (error) {
      console.error('Failed to load security findings:', error);
    }
  };

  const handleStartCrawling = async () => {
    try {
      const sessionId = await crawlerManager.startSession();
      setCurrentSessionId(sessionId);
      setIsActive(true);
    } catch (error) {
      console.error('Failed to start crawler:', error);
    }
  };

  const handleStopCrawling = async () => {
    if (currentSessionId) {
      try {
        await crawlerManager.stopSession(currentSessionId);
        setIsActive(false);
        setCurrentSessionId(null);
      } catch (error) {
        console.error('Failed to stop crawler:', error);
      }
    }
  };

  const handleUpdateConfig = async (newConfig: Partial<CrawlerConfig>) => {
    try {
      await crawlerManager.updateConfig(newConfig);
      setConfig({ ...config, ...newConfig });
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  const handleExportData = async (format: 'json' | 'csv' | 'xlsx', dataType: string) => {
    try {
      const blob = await crawlerManager.exportData(format, dataType as any);
      
      // Download the blob
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crawler_${dataType}_${new Date().getTime()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  const getStatusColor = () => {
    return isActive ? 'text-green-600' : 'text-gray-600';
  };

  const getStatusText = () => {
    return isActive ? 'Active' : 'Inactive';
  };

  const getCriticalAlertsCount = () => {
    const criticalVulns = vulnerabilities.filter(v => v.severity === 'Critical').length;
    const criticalSecrets = secrets.filter(s => s.severity === 'Critical').length;
    return criticalVulns + criticalSecrets;
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <CrawlerDashboard
            statistics={statistics}
            recentEntries={recentEntries}
            vulnerabilities={vulnerabilities}
            secrets={secrets}
            isActive={isActive}
          />
        );
      
      case 'extracted_data':
        return (
          <ExtractedData
            crawlerManager={crawlerManager}
            onExport={handleExportData}
          />
        );
      
      case 'security':
        return (
          <SecurityFindings
            vulnerabilities={vulnerabilities}
            secrets={secrets}
            onRefresh={loadSecurityFindings}
            onExport={handleExportData}
          />
        );
      
      case 'technologies':
        return (
          <TechnologyStack
            crawlerManager={crawlerManager}
            onExport={handleExportData}
          />
        );
      
      case 'config':
        return (
          <CrawlerConfiguration
            config={config}
            onUpdateConfig={handleUpdateConfig}
          />
        );
      
      default:
        return (
          <CrawlerDashboard
            statistics={statistics}
            recentEntries={recentEntries}
            vulnerabilities={vulnerabilities}
            secrets={secrets}
            isActive={isActive}
          />
        );
    }
  };

  const criticalAlerts = getCriticalAlertsCount();

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-6 h-6 text-purple-600" />
              <h1 className="text-xl font-bold text-gray-900">Passive Crawler</h1>
            </div>
            <div className={`flex items-center space-x-2 text-sm ${getStatusColor()}`}>
              {isActive ? (
                <Activity className="w-4 h-4 animate-pulse" />
              ) : (
                <Clock className="w-4 h-4" />
              )}
              <span>{getStatusText()}</span>
            </div>
            {criticalAlerts > 0 && (
              <div className="flex items-center space-x-2 bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>{criticalAlerts} Critical Alerts</span>
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div className="flex items-center space-x-3">
            {isActive ? (
              <button
                onClick={handleStopCrawling}
                className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <Square className="w-4 h-4" />
                <span>Stop Crawling</span>
              </button>
            ) : (
              <button
                onClick={handleStartCrawling}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Play className="w-4 h-4" />
                <span>Start Crawling</span>
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
            onClick={() => setCurrentView('extracted_data')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'extracted_data' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span>Extracted Data</span>
              {statistics.extracted_links + statistics.extracted_emails > 0 && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                  {statistics.extracted_links + statistics.extracted_emails}
                </span>
              )}
            </div>
          </button>
          <button
            onClick={() => setCurrentView('security')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'security' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span>Security</span>
              {(statistics.found_vulnerabilities + statistics.discovered_secrets) > 0 && (
                <span className={`text-xs px-2 py-1 rounded-full ${
                  criticalAlerts > 0 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {statistics.found_vulnerabilities + statistics.discovered_secrets}
                </span>
              )}
            </div>
          </button>
          <button
            onClick={() => setCurrentView('technologies')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              currentView === 'technologies' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span>Technologies</span>
              {statistics.detected_technologies > 0 && (
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                  {statistics.detected_technologies}
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
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Link className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-600">Links</span>
            </div>
            <p className="text-lg font-bold text-blue-900">{statistics.extracted_links}</p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Mail className="w-4 h-4 text-green-600" />
              <span className="text-sm text-gray-600">Emails</span>
            </div>
            <p className="text-lg font-bold text-green-900">{statistics.extracted_emails}</p>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Bug className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-gray-600">Vulnerabilities</span>
            </div>
            <p className="text-lg font-bold text-yellow-900">{statistics.found_vulnerabilities}</p>
          </div>
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <Key className="w-4 h-4 text-red-600" />
              <span className="text-sm text-gray-600">Secrets</span>
            </div>
            <p className="text-lg font-bold text-red-900">{statistics.discovered_secrets}</p>
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
