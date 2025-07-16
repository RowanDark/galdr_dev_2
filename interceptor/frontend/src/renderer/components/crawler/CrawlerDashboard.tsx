// galdr/interceptor/frontend/src/renderer/components/crawler/CrawlerDashboard.tsx
import React from 'react';
import { 
  Activity, 
  Globe, 
  Shield, 
  Key, 
  Clock, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Info,
  FileText,
  Database
} from 'lucide-react';
import { CrawlEntry, CrawlerStatistics, VulnerabilityFinding, SecretFinding } from '../../services/CrawlerManager';

interface CrawlerDashboardProps {
  statistics: CrawlerStatistics;
  recentEntries: CrawlEntry[];
  vulnerabilities: VulnerabilityFinding[];
  secrets: SecretFinding[];
  isActive: boolean;
}

export const CrawlerDashboard: React.FC<CrawlerDashboardProps> = ({
  statistics,
  recentEntries,
  vulnerabilities,
  secrets,
  isActive
}) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Critical': return 'text-red-600 bg-red-100';
      case 'High': return 'text-orange-600 bg-orange-100';
      case 'Medium': return 'text-yellow-600 bg-yellow-100';
      case 'Low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getHighestSeverityFindings = () => {
    const allFindings = [
      ...vulnerabilities.map(v => ({ ...v, type: 'vulnerability' })),
      ...secrets.map(s => ({ ...s, type: 'secret' }))
    ];
    
    return allFindings
      .sort((a, b) => {
        const severityOrder = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
        return severityOrder[b.severity] - severityOrder[a.severity];
      })
      .slice(0, 5);
  };

  const getRecentTechnologies = () => {
    const technologies = new Set<string>();
    recentEntries.slice(0, 10).forEach(entry => {
      if (entry.analysis_result?.technologies) {
        entry.analysis_result.technologies.forEach(tech => technologies.add(tech));
      }
    });
    return Array.from(technologies).slice(0, 8);
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-6">
      <div className="space-y-6">
        {/* Status Overview */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Crawler Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center space-x-3">
              <div className={`p-3 rounded-full ${isActive ? 'bg-green-100' : 'bg-gray-100'}`}>
                <Activity className={`w-6 h-6 ${isActive ? 'text-green-600' : 'text-gray-600'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <p className={`font-medium ${isActive ? 'text-green-600' : 'text-gray-600'}`}>
                  {isActive ? 'Active - Analyzing Traffic' : 'Inactive'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-100 rounded-full">
                <Database className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Entries Analyzed</p>
                <p className="font-medium text-blue-600">{statistics.total_entries}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-3 bg-purple-100 rounded-full">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Active Sessions</p>
                <p className="font-medium text-purple-600">{statistics.active_sessions}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Extracted Links</h3>
              <Globe className="w-5 h-5 text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{statistics.extracted_links}</p>
            <p className="text-xs text-gray-500 mt-1">Unique URLs found</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Email Addresses</h3>
              <Info className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{statistics.extracted_emails}</p>
            <p className="text-xs text-gray-500 mt-1">Contact information</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Security Issues</h3>
              <Shield className="w-5 h-5 text-yellow-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{statistics.found_vulnerabilities}</p>
            <p className="text-xs text-gray-500 mt-1">Potential vulnerabilities</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Exposed Secrets</h3>
              <Key className="w-5 h-5 text-red-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{statistics.discovered_secrets}</p>
            <p className="text-xs text-gray-500 mt-1">Keys and credentials</p>
          </div>
        </div>

        {/* Security Alerts */}
        {(vulnerabilities.length > 0 || secrets.length > 0) && (
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Security Findings</h2>
            <div className="space-y-3">
              {getHighestSeverityFindings().map((finding, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {finding.type === 'vulnerability' ? (
                      <Shield className="w-5 h-5 text-yellow-600" />
                    ) : (
                      <Key className="w-5 h-5 text-red-600" />
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{finding.type === 'vulnerability' ? finding.type : (finding as any).type}</p>
                      <p className="text-sm text-gray-600">{finding.description || (finding as any).masked_value}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(finding.severity)}`}>
                      {finding.severity}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(finding.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {recentEntries.slice(0, 8).map((entry, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      entry.status_code < 300 ? 'bg-green-500' :
                      entry.status_code < 400 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`} />
                    <div>
                      <p className="font-medium text-gray-900 truncate max-w-xs">{entry.url}</p>
                      <p className="text-sm text-gray-600">{entry.method} • {entry.status_code}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Detected Technologies */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Technologies</h2>
            <div className="flex flex-wrap gap-2">
              {getRecentTechnologies().map((tech, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                >
                  {tech}
                </span>
              ))}
              {getRecentTechnologies().length === 0 && (
                <p className="text-sm text-gray-500">No technologies detected yet</p>
              )}
            </div>
          </div>
        </div>

        {/* File Discovery */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">File Discovery Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <FileText className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <p className="text-lg font-bold text-gray-900">{statistics.extracted_files}</p>
              <p className="text-sm text-gray-600">Files Found</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <Database className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <p className="text-lg font-bold text-gray-900">{statistics.detected_technologies}</p>
              <p className="text-sm text-gray-600">Technologies</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <Globe className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <p className="text-lg font-bold text-gray-900">{statistics.extracted_links}</p>
              <p className="text-sm text-gray-600">Unique Links</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <Activity className="w-8 h-8 text-orange-600 mx-auto mb-2" />
              <p className="text-lg font-bold text-gray-900">{statistics.total_entries}</p>
              <p className="text-sm text-gray-600">Total Entries</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
